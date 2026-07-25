package me.myot233.seclab.dockerservice

import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.RestController

/**
 * 靶机容器管理 HTTP 接口。
 *
 * 历史实现用 `ProcessBuilder("docker", ...)` 调 CLI；现已切到 [DockerSdkService]（基于 docker-java SDK）。
 * 为保持前端调用方零感知，所有对外响应体（字段名、状态码、`isSuccess`/`status`/`message`/`data` 结构）
 * 严格沿用旧契约。底层异常统一为 [DockerSdkException]，由 [toResponse] 兜底转 502 + 结构化 body。
 *
 * 注意：`labs` 现引用 [LabAllowlist.labs]，供 [TtyLogHandler] / [FrustrationTracker] 复用同一白名单。
 *
 * 挫败指数相关端点（[reportFrustration] / [getFrustrationScore]）：
 * - 作为 WS TTY 监听不可用时的**降级回退**路径，前端可手动上报错误/命令观察；
 * - **不要与 WS 同时启用**，避免双源触发导致同一 session 重复计入 score。
 */
@RestController
class DockerController(
    private val dockerSdkService: DockerSdkService,
    private val frustrationTracker: FrustrationTracker,
    private val guidanceSignalClient: GuidanceSignalClient,
) {

    private val labs: Map<String, LabTarget> get() = LabAllowlist.labs

    @GetMapping("/health")
    fun health(): Map<String, Any> = mapOf(
        "status" to "ok",
        "service" to "docker-service",
        "backend" to "docker-java-sdk",
    )

    @GetMapping("/api/docker/containers/{name}/status")
    fun status(@PathVariable name: String): ResponseEntity<Map<String, Any?>> {
        return runSdk { dockerSdkService.inspectStatus(name) }
            .toResponse("status") { output ->
                mapOf("container" to name, "status" to output.trim())
            }
    }

    @GetMapping("/api/docker/containers/{name}/ports")
    fun ports(@PathVariable name: String): ResponseEntity<Map<String, Any?>> {
        return runSdk { dockerSdkService.portMap(name) }
            .toResponse("ports") { lines ->
                mapOf(
                    "container" to name,
                    "ports" to lines,
                )
            }
    }

    @GetMapping("/api/docker/target-status/{lab}")
    fun targetStatus(@PathVariable lab: String): ResponseEntity<Map<String, Any?>> {
        val target = LabAllowlist.targetByKey(lab)
            ?: return ResponseEntity.badRequest().body(mapOf("success" to false, "message" to "Unknown lab: $lab"))

        return runSdk { dockerSdkService.inspectStatus(target.containerName) }
            .toResponse("target-status") { output ->
                val running = output.trim() == "running"
                mapOf(
                    "lab" to lab,
                    "containerId" to target.containerName,
                    "containerExists" to true,
                    "containerRunning" to running,
                    "hostPort" to target.hostPort,
                    "targetUrl" to "http://localhost:${target.hostPort}",
                    "status" to if (running) "online" else "offline",
                    "message" to if (running) "container is running" else "container is not running",
                )
            }
    }

    @PostMapping("/api/docker/start-{lab}")
    fun startLab(@PathVariable lab: String): ResponseEntity<Map<String, Any?>> {
        val target = LabAllowlist.targetByKey(lab)
            ?: return ResponseEntity.badRequest().body(mapOf("isSuccess" to 0, "message" to "Unknown lab: $lab"))

        return runSdk { dockerSdkService.startContainer(target.containerName); "container started" }
            .toResponse("start-lab") {
                mapOf(
                    "isSuccess" to 1,
                    "status" to 200,
                    "message" to "container started",
                    "data" to mapOf(
                        "lab" to lab,
                        "containerName" to target.containerName,
                        "containerId" to target.containerName,
                        "url" to "http://localhost:${target.hostPort}",
                        "hostPort" to target.hostPort,
                    ),
                )
            }
    }

    @PostMapping("/api/docker/containers/{name}/start")
    fun start(@PathVariable name: String): ResponseEntity<Map<String, Any?>> {
        return runSdk { dockerSdkService.startContainer(name); "started" }
            .toResponse("start") {
                mapOf("container" to name, "started" to true, "output" to it.trim())
            }
    }

    @PostMapping("/api/docker/containers/{name}/stop")
    fun stop(
        @PathVariable name: String,
        @RequestParam(defaultValue = "10") timeoutSeconds: Int,
    ): ResponseEntity<Map<String, Any?>> {
        val clampedTimeout = timeoutSeconds.coerceIn(1, 60)
        return runSdk { dockerSdkService.stopContainer(name, clampedTimeout); "stopped" }
            .toResponse("stop") {
                mapOf("container" to name, "stopped" to true, "output" to it.trim())
            }
    }

    @PostMapping("/api/docker/stop/{name}")
    fun stopCompat(@PathVariable name: String): ResponseEntity<Map<String, Any?>> {
        return runSdk { dockerSdkService.stopContainer(name, 10); "stopped" }
            .toResponse("stop-lab") {
                mapOf(
                    "isSuccess" to 1,
                    "status" to 200,
                    "message" to "container stopped",
                    "data" to mapOf("containerName" to name, "output" to it.trim()),
                )
            }
    }

    // ─────────────────────────────────────────
    //  挫败指数降级端点（WS 不可用时使用）
    // ─────────────────────────────────────────

    /**
     * 手动上报一次挫败观察（错误或命令）。WS TTY 不可用时的降级回退路径。
     *
     * **注意**：不要与 WS 同时启用，避免双源触发导致同一 session 重复计入 score。
     *
     * Body:
     * - lab_session_id: 必填，作为 sessionKey
     * - user_id: 可选
     * - error_slice: 可选，错误摘要（≤1024 字符）
     * - command: 可选，归一化命令字符串
     * - exit_code: 可选，命令退出码
     *
     * 若同时提供 error_slice 和 command，会分别调 observeError + observeCommand。
     * 触发阈值时异步发送 guidance signal。
     */
    @PostMapping("/api/docker/frustration/{lab}")
    fun reportFrustration(
        @PathVariable lab: String,
        @RequestBody body: FrustrationReportRequest,
    ): ResponseEntity<Map<String, Any?>> {
        val target = LabAllowlist.targetByKey(lab)
            ?: return ResponseEntity.badRequest().body(mapOf(
                "isSuccess" to 0,
                "message" to "Unknown lab: $lab",
            ))

        val sessionKey = body.lab_session_id
        var decision: FrustrationTracker.TriggerDecision? = null
        var scoreBefore = frustrationTracker.score(sessionKey)

        if (!body.error_slice.isNullOrBlank()) {
            decision = frustrationTracker.observeError(
                sessionKey = sessionKey,
                errorSlice = body.error_slice,
                exitCode = body.exit_code,
            )
        }
        if (!body.command.isNullOrBlank()) {
            val cmdDecision = frustrationTracker.observeCommand(
                sessionKey = sessionKey,
                normalizedCmd = body.command,
                exitCode = body.exit_code,
            )
            if (decision == null) decision = cmdDecision
        }

        val scoreAfter = frustrationTracker.score(sessionKey)
        val triggered = decision != null

        if (triggered && decision != null) {
            val signalId = guidanceSignalClient.newSignalId()
            guidanceSignalClient.sendSignal {
                GuidanceSignal(
                    signal_id = signalId,
                    request_id = "http-$signalId",
                    trigger_reason = decision.reason,
                    lab_session_id = body.lab_session_id,
                    user_id = body.user_id,
                    class_id = null,
                    course_id = null,
                    module_id = null,
                    task_id = null,
                    container_name = target.containerName,
                    lab_key = lab,
                    error_slice = body.error_slice ?: decision.recentErrors.lastOrNull() ?: "",
                    exit_code = body.exit_code,
                    recent_commands = decision.recentCommands,
                    lab_task_summary = target.labTaskSummary,
                    frustration_score = decision.score,
                    locale = "zh-CN",
                    triggered_at = decision.triggeredAt,
                )
            }
        }

        return ResponseEntity.ok(mapOf(
            "isSuccess" to 1,
            "status" to 200,
            "message" to if (triggered) "frustration triggered" else "observation recorded",
            "data" to mapOf(
                "lab" to lab,
                "lab_session_id" to body.lab_session_id,
                "score_before" to scoreBefore,
                "score_after" to scoreAfter,
                "triggered" to triggered,
                "trigger_reason" to decision?.reason,
                "frustration_score" to decision?.score,
            ),
        ))
    }

    /**
     * 调试用：查询指定 lab + session 的当前挫败指数状态。
     * lab_session_id 与 user_id 至少传一个；优先用 lab_session_id 作 sessionKey。
     */
    @GetMapping("/api/docker/frustration/{lab}/score")
    fun getFrustrationScore(
        @PathVariable lab: String,
        @RequestParam(required = false) labSessionId: String?,
        @RequestParam(required = false) userId: Long?,
    ): ResponseEntity<Map<String, Any?>> {
        val target = LabAllowlist.targetByKey(lab)
            ?: return ResponseEntity.badRequest().body(mapOf(
                "isSuccess" to 0,
                "message" to "Unknown lab: $lab",
            ))

        val sessionKey = labSessionId
            ?: userId?.let { "${target.containerName}:$it" }
            ?: return ResponseEntity.badRequest().body(mapOf(
                "isSuccess" to 0,
                "message" to "Either lab_session_id or user_id must be provided",
            ))

        val score = frustrationTracker.score(sessionKey)
        val snapshot = frustrationTracker.snapshot(sessionKey)
        return ResponseEntity.ok(mapOf(
            "isSuccess" to 1,
            "status" to 200,
            "data" to mapOf(
                "lab" to lab,
                "container_name" to target.containerName,
                "session_key" to sessionKey,
                "score" to score,
                "recent_errors" to (snapshot?.recentErrors?.takeLast(5)?.map { it.excerpt } ?: emptyList<String>()),
                "recent_commands" to (snapshot?.recentCommands?.takeLast(5)?.map { it.normalizedCmd } ?: emptyList<String>()),
                "last_trigger_at" to snapshot?.lastTriggerAt,
            ),
        ))
    }

    // ─────────────────────────────────────────
    //  内部工具
    // ─────────────────────────────────────────

    /**
     * 统一执行 SDK 调用，捕获 [DockerSdkException] 转 [SdkRunResult]。
     * 成功时把 [T] 包成 [SdkRunResult.Success]；失败时把异常包成 [SdkRunResult.Failure]。
     */
    private fun <T> runSdk(block: () -> T): SdkRunResult<T> {
        return try {
            SdkRunResult.Success(block())
        } catch (e: DockerSdkException) {
            SdkRunResult.Failure(e)
        }
    }

    private fun <T> SdkRunResult<T>.toResponse(
        action: String,
        successBody: (T) -> Map<String, Any?>,
    ): ResponseEntity<Map<String, Any?>> {
        return when (this) {
            is SdkRunResult.Success -> ResponseEntity.ok(successBody(value))
            is SdkRunResult.Failure -> {
                val body = mapOf(
                    "action" to action,
                    "success" to false,
                    "exitCode" to error.exitCode,
                    "stdout" to "",
                    "stderr" to error.stderr.trim(),
                    "message" to error.message,
                )
                ResponseEntity.status(HttpStatus.BAD_GATEWAY).body(body)
            }
        }
    }

    private sealed class SdkRunResult<out T> {
        data class Success<T>(val value: T) : SdkRunResult<T>()
        data class Failure(val error: DockerSdkException) : SdkRunResult<Nothing>()
    }
}

/**
 * 挫败指数降级上报请求体。
 *
 * @param lab_session_id 必填，作为 [FrustrationTracker] 的 sessionKey
 * @param user_id 可选，仅用于构造 [GuidanceSignal]
 * @param error_slice 可选，错误摘要（≤1024 字符），非空时调 [FrustrationTracker.observeError]
 * @param command 可选，归一化命令字符串，非空时调 [FrustrationTracker.observeCommand]
 * @param exit_code 可选，命令退出码；同时影响 observeError/observeCommand 的评分
 */
data class FrustrationReportRequest(
    val lab_session_id: String,
    val user_id: Long? = null,
    val error_slice: String? = null,
    val command: String? = null,
    val exit_code: Int? = null,
)
