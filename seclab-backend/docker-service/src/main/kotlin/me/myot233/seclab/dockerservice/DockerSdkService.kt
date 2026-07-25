package me.myot233.seclab.dockerservice

import com.github.dockerjava.api.DockerClient
import com.github.dockerjava.api.exception.NotFoundException
import com.github.dockerjava.api.model.Frame
import com.github.dockerjava.core.command.ExecStartResultCallback
import com.github.dockerjava.core.command.LogContainerResultCallback
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Service
import java.io.ByteArrayOutputStream
import java.util.concurrent.TimeUnit

/**
 * 用 Docker Java SDK 封装的容器操作服务。
 *
 * - 替换 [DockerController] 原 `runDocker()` 的 CLI 调用方式，统一抛 [DockerSdkException]。
 * - 方法签名对齐 controller 现有需求，保留 stdout/stderr/exitCode 三元组语义，
 *   使 controller 层无需修改对外响应体即可切换底层实现。
 */
@Service
class DockerSdkService(
    private val dockerClient: DockerClient,
) {

    private val log = LoggerFactory.getLogger(javaClass)

    /** 获取容器状态字符串（"running" / "exited" / "created" / ...） */
    fun inspectStatus(name: String): String {
        return try {
            dockerClient.inspectContainerCmd(name).exec().state.status ?: "unknown"
        } catch (e: NotFoundException) {
            throw DockerSdkException("container '$name' not found", stderr = e.message ?: "")
        } catch (e: Exception) {
            throw DockerSdkException("inspect status failed for '$name': ${e.message}", cause = e)
        }
    }

    /**
     * 获取容器端口映射，按 `docker port` 命令格式输出。
     * 返回形如 `"8080/tcp -> 0.0.0.0:8091"` 的列表。
     */
    fun portMap(name: String): List<String> {
        return try {
            val inspect = dockerClient.inspectContainerCmd(name).exec()
            val ports = inspect.networkSettings.ports
            if (ports == null || ports.bindings.isEmpty()) {
                return emptyList()
            }
            ports.bindings.entries.flatMap { (exposed, bindings) ->
                val exposedStr = exposed.toString()
                if (bindings.isNullOrEmpty()) {
                    listOf("$exposedStr (no binding)")
                } else {
                    bindings.map { binding ->
                        val host = binding.hostIp ?: "0.0.0.0"
                        val port = binding.hostPortSpec ?: ""
                        "$exposedStr -> $host:$port"
                    }
                }
            }
        } catch (e: NotFoundException) {
            throw DockerSdkException("container '$name' not found", stderr = e.message ?: "")
        } catch (e: Exception) {
            throw DockerSdkException("port map failed for '$name': ${e.message}", cause = e)
        }
    }

    /** 启动容器 */
    fun startContainer(name: String) {
        try {
            dockerClient.startContainerCmd(name).exec()
        } catch (e: NotFoundException) {
            throw DockerSdkException("container '$name' not found", stderr = e.message ?: "")
        } catch (e: Exception) {
            throw DockerSdkException("start container failed for '$name': ${e.message}", cause = e)
        }
    }

    /** 停止容器 */
    fun stopContainer(name: String, timeoutSeconds: Int) {
        try {
            dockerClient.stopContainerCmd(name).withTimeout(timeoutSeconds).exec()
        } catch (e: NotFoundException) {
            throw DockerSdkException("container '$name' not found", stderr = e.message ?: "")
        } catch (e: Exception) {
            throw DockerSdkException("stop container failed for '$name': ${e.message}", cause = e)
        }
    }

    /**
     * 在容器内执行命令（同步等待完成）。
     *
     * @return [ExecResult] 含 exitCode 与合并的 stdout/stderr
     */
    fun execInContainer(name: String, command: String): ExecResult {
        return try {
            val parts = command.trim().split(Regex("\\s+")).filter { it.isNotEmpty() }
            val execId = dockerClient.execCreateCmd(name)
                .withAttachStdout(true)
                .withAttachStderr(true)
                .withCmd(*parts.toTypedArray())
                .exec()
                .id
            val stdout = ByteArrayOutputStream()
            val stderr = ByteArrayOutputStream()
            val callback = ExecStartResultCallback(stdout, stderr)
            dockerClient.execStartCmd(execId).exec(callback).awaitCompletion(30, TimeUnit.SECONDS)
            val exitCode = try {
                dockerClient.inspectExecCmd(execId).exec().exitCodeLong?.toInt() ?: -1
            } catch (e: Exception) {
                log.warn("inspectExecCmd failed for execId={} on container '{}': {}", execId, name, e.message)
                -1
            }
            ExecResult(
                exitCode = exitCode,
                stdout = stdout.toString(Charsets.UTF_8.name()),
                stderr = stderr.toString(Charsets.UTF_8.name()),
            )
        } catch (e: NotFoundException) {
            throw DockerSdkException("container '$name' not found", stderr = e.message ?: "")
        } catch (e: Exception) {
            throw DockerSdkException("exec failed on '$name': ${e.message}", cause = e)
        }
    }

    /**
     * 拉取容器最近 N 行日志（一次性）。
     *
     * @param tail 取最近多少行
     * @return 合并的日志字符串（stdout + stderr），保留原始换行
     */
    fun tailLogs(name: String, tail: Int): String {
        return try {
            val sink = FrameCollectingCallback()
            dockerClient.logContainerCmd(name)
                .withTail(tail)
                .withStdOut(true)
                .withStdErr(true)
                .withTimestamps(true)
                .exec(sink)
                .awaitCompletion(15, TimeUnit.SECONDS)
            sink.combinedText()
        } catch (e: NotFoundException) {
            throw DockerSdkException("container '$name' not found", stderr = e.message ?: "")
        } catch (e: Exception) {
            throw DockerSdkException("tail logs failed for '$name': ${e.message}", cause = e)
        }
    }

    data class ExecResult(
        val exitCode: Int,
        val stdout: String,
        val stderr: String,
    )

    /**
     * 日志回调：把每个 [Frame] 的字节累积到缓冲区，最后合成字符串。
     * 仅用于 [tailLogs] 这种一次性同步拉取场景。
     * 实时流式订阅走 [TtyLogStreamService]，不复用此实现。
     */
    private class FrameCollectingCallback : LogContainerResultCallback() {
        private val buffer = ByteArrayOutputStream()
        override fun onNext(item: Frame) {
            buffer.write(item.payload)
            super.onNext(item)
        }

        fun combinedText(): String = buffer.toString(Charsets.UTF_8.name())
    }
}
