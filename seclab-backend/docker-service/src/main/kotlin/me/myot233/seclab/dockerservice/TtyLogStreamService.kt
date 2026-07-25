package me.myot233.seclab.dockerservice

import com.github.dockerjava.api.DockerClient
import com.github.dockerjava.api.model.Frame
import com.github.dockerjava.api.model.StreamType
import com.github.dockerjava.core.command.LogContainerResultCallback
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Service
import java.time.Instant
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CopyOnWriteArraySet

/**
 * 容器日志实时订阅中枢（WebSocket 旁路监听的数据源）。
 *
 * 设计要点：
 * - 每个容器维护一个 [FramedLogsStream]，通过 docker-java SDK 的 `logContainerCmd(followStream=true)`
 *   订阅实时 stdout/stderr 流。SDK 在内部线程上调用 callback，**不阻塞** WS handler 线程池（评审 Q6）。
 * - 多个 WS 客户端可订阅同一容器；每条日志帧广播给所有订阅者，并按各自 sessionKey 喂给 [FrustrationTracker]。
 * - 最后一个订阅者断开时关闭 SDK callback 并移除 stream，避免泄漏（评审缺口 6）。
 *
 * 注意：容器 die 事件的主动清理留待后续增强（依赖 `dockerClient.eventsCmd`）；当前依赖
 * SDK callback 的 `onComplete` / `onClose` 自然终止 + WS 客户端断开来清理订阅。
 */
@Service
class TtyLogStreamService(
    private val dockerClient: DockerClient,
    private val frustrationTracker: FrustrationTracker,
) {

    private val log = LoggerFactory.getLogger(javaClass)
    private val streams = ConcurrentHashMap<String, FramedLogsStream>()

    /**
     * 订阅指定容器的实时日志流。
     *
     * @param containerName 容器名（必须通过 [LabAllowlist.isAllowed] 校验）
     * @param subscriber 订阅者句柄（含 sink 与 sessionKey）
     */
    fun subscribe(containerName: String, subscriber: Subscriber) {
        val stream = streams.computeIfAbsent(containerName) { name ->
            FramedLogsStream(name)
        }
        stream.addSubscriber(subscriber)
    }

    /**
     * 取消订阅。若该容器已无订阅者，关闭 SDK callback 并从 [streams] 移除。
     */
    fun unsubscribe(containerName: String, subscriber: Subscriber) {
        val stream = streams[containerName] ?: return
        if (stream.removeSubscriber(subscriber) && stream.isEmpty()) {
            // 用 remove(key, expectedValue) 避免误删被复用的新 stream
            streams.remove(containerName, stream)
            stream.shutdown()
        }
    }

    /** 当前活跃的容器流数量（监控用） */
    fun activeStreamCount(): Int = streams.size

    /** 订阅者总数量（监控用） */
    fun totalSubscriberCount(): Int = streams.values.sumOf { it.subscriberCount() }

    /**
     * 单条日志帧（推送给 WS 客户端的 JSON 结构）。
     */
    data class TtyLogFrame(
        val ts: String,
        val stream: String,
        val line: String,
    )

    /**
     * 接收日志帧的回调接口（函数式）。
     */
    fun interface TtyLogSink {
        fun onNext(frame: TtyLogFrame)
    }

    /**
     * 订阅者句柄。非 data class，使用引用相等性作 CopyOnWriteArraySet 的去重依据，
     * 保证同一 sink 多次注册不会重复，但不同 WS 会话即使 sessionKey 相同也各自独立。
     *
     * @param onTrigger 当 [FrustrationTracker.observeLogLine] 返回非 null TriggerDecision 时触发；
     *                  由 [TtyLogHandler] 注入，用于把决策转 [GuidanceSignal] 异步发送。
     *                  保持 TtyLogStreamService 对触发后续动作无感（单一职责）。
     */
    class Subscriber(
        val sink: TtyLogSink,
        val sessionKey: String,
        val onTrigger: ((FrustrationTracker.TriggerDecision) -> Unit)? = null,
    )

    /**
     * 单容器的日志流包装：持有 SDK callback 引用与订阅者集合。
     */
    private inner class FramedLogsStream(val containerName: String) : LogContainerResultCallback() {

        private val subscribers = CopyOnWriteArraySet<Subscriber>()
        @Volatile private var started = false
        @Volatile private var shutdown = false

        @Synchronized
        fun addSubscriber(sub: Subscriber) {
            subscribers.add(sub)
            if (!started && !shutdown) {
                try {
                    dockerClient.logContainerCmd(containerName)
                        .withFollowStream(true)
                        .withTailAll()
                        .withStdOut(true)
                        .withStdErr(true)
                        .withTimestamps(true)
                        .exec(this)
                    started = true
                    log.info("TTY log stream started for container={} subscribers={}", containerName, subscribers.size)
                } catch (e: Exception) {
                    log.error("Failed to start log stream for container={}: {}", containerName, e.message, e)
                    // 启动失败时移除已添加的订阅者，避免空流占用资源
                    subscribers.remove(sub)
                }
            }
        }

        fun removeSubscriber(sub: Subscriber): Boolean = subscribers.remove(sub)

        fun isEmpty(): Boolean = subscribers.isEmpty()

        fun subscriberCount(): Int = subscribers.size

        override fun onNext(item: Frame) {
            if (shutdown || subscribers.isEmpty()) return
            val streamType = when (item.streamType) {
                StreamType.STDOUT -> "stdout"
                StreamType.STDERR -> "stderr"
                else -> "raw"
            }
            val payload = String(item.payload, Charsets.UTF_8).trimEnd('\n', '\r')
            if (payload.isEmpty()) return

            val frame = TtyLogFrame(
                ts = Instant.now().toString(),
                stream = streamType,
                line = payload,
            )

            // 收集唯一 sessionKey，避免同 sessionKey 多订阅者（如同一学生多 tab）导致 score 重复计数
            val uniqueSessionKeys = subscribers.map { it.sessionKey }.distinct()
            val decisionsByKey = LinkedHashMap<String, FrustrationTracker.TriggerDecision?>()
            for (sessionKey in uniqueSessionKeys) {
                try {
                    decisionsByKey[sessionKey] = frustrationTracker.observeLogLine(
                        sessionKey, payload, streamType, containerName,
                    )
                } catch (e: Exception) {
                    log.warn("frustrationTracker.observeLogLine failed for sessionKey={}: {}", sessionKey, e.message)
                }
            }

            for (sub in subscribers) {
                try {
                    sub.sink.onNext(frame)
                } catch (e: Exception) {
                    log.warn("sink onNext failed for container={}: {}", containerName, e.message)
                }
                // 同一 sessionKey 仅首个订阅者触发 onTrigger，避免多 tab 重复发送信号
                val decision = decisionsByKey.remove(sub.sessionKey)
                if (decision != null) {
                    try {
                        sub.onTrigger?.invoke(decision)
                    } catch (e: Exception) {
                        log.warn("onTrigger failed for sessionKey={}: {}", sub.sessionKey, e.message)
                    }
                }
            }
        }

        override fun onComplete() {
            log.info("TTY log stream completed for container={} subscribers={}", containerName, subscribers.size)
            super.onComplete()
        }

        override fun onError(throwable: Throwable) {
            log.warn("TTY log stream error for container={}: {}", containerName, throwable.message)
            super.onError(throwable)
        }

        fun shutdown() {
            if (shutdown) return
            shutdown = true
            try {
                close()
            } catch (e: Exception) {
                log.warn("close stream failed for container={}: {}", containerName, e.message)
            }
        }
    }
}
