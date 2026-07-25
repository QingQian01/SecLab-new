package me.myot233.seclab.dockerservice

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.HttpEntity
import org.springframework.http.HttpHeaders
import org.springframework.http.HttpMethod
import org.springframework.http.MediaType
import org.springframework.stereotype.Component
import org.springframework.web.client.RestTemplate
import java.util.UUID
import java.util.concurrent.CompletableFuture
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

/**
 * 引导信号发送客户端：把 [GuidanceSignal] 异步 POST 到 ai-agent-service 的 `/api/guidance/signal`。
 *
 * 设计要点：
 * - **fire-and-forget**：通过单线程异步执行器发送，绝不阻塞 WS TTY 流或 controller 线程。
 * - 失败仅 `log.warn` 不抛（评审缺口 3 / Q1）：挫败信号丢失可接受，绝不能反压日志采集。
 * - 携带 `X-SecLab-Token` 鉴权头（值来自 `seclab.agent.signal-token`，与 ai-agent-service `TOOL_API_KEY` 共享）。
 * - 每个信号生成 `signal_id = UUID`，`request_id = "tty-" + signal_id`，便于跨服务追踪与幂等去重。
 */
@Component
class GuidanceSignalClient(
    @Value("\${seclab.agent.signal-url:http://localhost:8010/api/guidance/signal}") private val signalUrl: String,
    @Value("\${seclab.agent.signal-token:}") private val signalToken: String,
    @Value("\${seclab.agent.timeout-ms:5000}") private val timeoutMs: Int,
) {

    private val log = LoggerFactory.getLogger(javaClass)
    private val objectMapper = jacksonObjectMapper().findAndRegisterModules()

    /**
     * 单线程异步发送池：信号量低（每个 lab_session 触发有 90s 冷却），单线程足够。
     * 队列无界，但实际积压极少。
     */
    private val executor = Executors.newSingleThreadExecutor { r ->
        Thread(r, "guidance-signal-sender").apply { isDaemon = true }
    }

    private val restTemplate: RestTemplate = RestTemplate().apply {
        // 设置连接与读取超时
        val factory = org.springframework.http.client.SimpleClientHttpRequestFactory()
        factory.setConnectTimeout(timeoutMs)
        factory.setReadTimeout(timeoutMs)
        requestFactory = factory
    }

    /**
     * 异步发送信号。立即返回，失败不抛。
     *
     * @param signalBuilder 由调用方基于 [FrustrationTracker.TriggerDecision] + session 上下文构造的信号字段
     */
    fun sendSignal(signalBuilder: () -> GuidanceSignal) {
        val signal = try {
            signalBuilder()
        } catch (e: Exception) {
            log.warn("failed to build guidance signal: {}", e.message)
            return
        }
        CompletableFuture.runAsync({
            doSend(signal)
        }, executor)
    }

    private fun doSend(signal: GuidanceSignal) {
        try {
            val headers = HttpHeaders().apply {
                contentType = MediaType.APPLICATION_JSON
                if (signalToken.isNotBlank()) {
                    set("X-SecLab-Token", signalToken)
                }
            }
            val body = objectMapper.writeValueAsString(signal)
            val entity = HttpEntity(body, headers)
            log.info(
                "sending guidance signal signal_id={} lab_session_id={} score={} reason={}",
                signal.signal_id, signal.lab_session_id, signal.frustration_score, signal.trigger_reason,
            )
            val response = restTemplate.exchange(signalUrl, HttpMethod.POST, entity, String::class.java)
            log.info(
                "guidance signal accepted signal_id={} status={}",
                signal.signal_id, response.statusCode.value(),
            )
        } catch (e: Exception) {
            log.warn(
                "guidance signal send failed signal_id={} lab_session_id={}: {}",
                signal.signal_id, signal.lab_session_id, e.message,
            )
        }
    }

    /** 生成新的 signal_id（UUID，去横线） */
    fun newSignalId(): String = UUID.randomUUID().toString().replace("-", "")

    /** 优雅关闭（应用 shutdown 时调用） */
    fun shutdown() {
        executor.shutdown()
        try {
            if (!executor.awaitTermination(5, TimeUnit.SECONDS)) {
                executor.shutdownNow()
            }
        } catch (_: InterruptedException) {
            executor.shutdownNow()
            Thread.currentThread().interrupt()
        }
    }
}
