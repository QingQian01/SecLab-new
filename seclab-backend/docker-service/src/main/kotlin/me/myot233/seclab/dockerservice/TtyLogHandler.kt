package me.myot233.seclab.dockerservice

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Component
import org.springframework.web.socket.CloseStatus
import org.springframework.web.socket.TextMessage
import org.springframework.web.socket.WebSocketSession
import org.springframework.web.socket.handler.TextWebSocketHandler
import org.springframework.web.util.UriComponentsBuilder
import java.util.concurrent.ConcurrentHashMap

/**
 * WebSocket 旁路监听 TTY/容器日志的入口。
 *
 * URI: `ws://host:8087/ws/tty/{containerName}?lab_session_id=xxx&user_id=yyy`
 *
 * 握手流程：
 * 1. 从 URI path 提取 `containerName`，校验 [LabAllowlist.isAllowed]；
 * 2. 从 query string 提取 `lab_session_id` / `user_id`（评审缺口 4 修复）；
 * 3. `sessionKey = lab_session_id ?: "${containerName}:${user_id ?: 'anon'}"`；
 * 4. 创建 [TtyLogStreamService.Subscriber]（带 `onTrigger` 回调）订阅 [TtyLogStreamService]。
 *
 * 推送帧格式：`{"ts":"...","stream":"stdout|stderr","line":"..."}`
 *
 * 触发挫败信号时，[handleTrigger] 异步调用 [GuidanceSignalClient.sendSignal]，
 * 不阻塞 WS 推送主路径。
 *
 * 资源清理：
 * - `afterConnectionClosed` 用 try-catch 兜底 `unsubscribe`（评审缺口 6 修复）；
 * - 发送失败时主动关闭 session，由 `afterConnectionClosed` 统一清理订阅。
 */
@Component
class TtyLogHandler(
    private val ttyLogStreamService: TtyLogStreamService,
    private val guidanceSignalClient: GuidanceSignalClient,
) : TextWebSocketHandler() {

    private val log = LoggerFactory.getLogger(javaClass)
    private val objectMapper = jacksonObjectMapper().findAndRegisterModules()
    private val sessionContexts = ConcurrentHashMap<WebSocketSession, TtySessionContext>()

    override fun afterConnectionEstablished(session: WebSocketSession) {
        val containerName = extractContainerName(session)
        if (containerName == null) {
            log.warn("WS handshake rejected: missing containerName in URI {}", session.uri)
            safeClose(session, CloseStatus.POLICY_VIOLATION)
            return
        }
        if (!LabAllowlist.isAllowed(containerName)) {
            log.warn("WS handshake rejected: container {} not in allowlist", containerName)
            safeClose(session, CloseStatus.POLICY_VIOLATION)
            return
        }
        val params = extractQueryParams(session)
        val sessionKey = params.labSessionId ?: "${containerName}:${params.userId ?: "anon"}"
        val context = TtySessionContext(
            containerName = containerName,
            sessionKey = sessionKey,
            labSessionId = params.labSessionId,
            userId = params.userId,
        )
        sessionContexts[session] = context

        val subscriber = TtyLogStreamService.Subscriber(
            sink = TtyLogStreamService.TtyLogSink { frame -> broadcastFrame(session, frame) },
            sessionKey = sessionKey,
            onTrigger = { decision -> handleTrigger(decision, context) },
        )
        context.subscriber = subscriber

        ttyLogStreamService.subscribe(containerName, subscriber)
        log.info(
            "WS TTY subscribed container={} sessionKey={} session={}",
            containerName, sessionKey, session.id,
        )
    }

    override fun handleTextMessage(session: WebSocketSession, message: TextMessage) {
        // 仅支持 {"type":"ping"} 心跳；其余客户端→服务端文本忽略
        val payload = message.payload.trim()
        if (payload.contains("\"ping\"")) {
            try {
                session.sendMessage(TextMessage("""{"type":"pong"}""" as CharSequence))
            } catch (e: Exception) {
                log.debug("pong send failed session={}: {}", session.id, e.message)
            }
        }
    }

    override fun afterConnectionClosed(session: WebSocketSession, status: CloseStatus) {
        val context = sessionContexts.remove(session) ?: return
        try {
            context.subscriber?.let { ttyLogStreamService.unsubscribe(context.containerName, it) }
            log.info(
                "WS TTY unsubscribed container={} sessionKey={} session={} status={}",
                context.containerName, context.sessionKey, session.id, status,
            )
        } catch (e: Exception) {
            log.warn("unsubscribe failed session={}: {}", session.id, e.message)
        }
    }

    /**
     * 把单帧日志广播给 WS 客户端。
     * 发送失败时主动关闭 session，由 [afterConnectionClosed] 清理订阅。
     */
    private fun broadcastFrame(session: WebSocketSession, frame: TtyLogStreamService.TtyLogFrame) {
        try {
            val json = objectMapper.writeValueAsString(frame)
            session.sendMessage(TextMessage(json as CharSequence))
        } catch (e: Exception) {
            log.debug("WS send failed session={}: {}", session.id, e.message)
            safeClose(session, CloseStatus.SERVER_ERROR)
        }
    }

    /**
     * 当 [FrustrationTracker] 返回 [FrustrationTracker.TriggerDecision] 时，
     * [TtyLogStreamService] 通过 `Subscriber.onTrigger` 回调调用本方法。
     *
     * 构造 [GuidanceSignal] 并异步发送给 ai-agent-service，
     * 绝不阻塞 WS 推送主路径（[GuidanceSignalClient.sendSignal] 是 fire-and-forget）。
     */
    internal fun handleTrigger(decision: FrustrationTracker.TriggerDecision, context: TtySessionContext) {
        val target = LabAllowlist.targetOf(context.containerName)
        val signalId = guidanceSignalClient.newSignalId()
        try {
            guidanceSignalClient.sendSignal {
                GuidanceSignal(
                    signal_id = signalId,
                    request_id = "tty-$signalId",
                    trigger_reason = decision.reason,
                    lab_session_id = context.labSessionId,
                    user_id = context.userId,
                    class_id = null,
                    course_id = null,
                    module_id = null,
                    task_id = null,
                    container_name = context.containerName,
                    lab_key = LabAllowlist.labKeyOf(context.containerName) ?: "unknown",
                    error_slice = decision.recentErrors.lastOrNull() ?: "",
                    exit_code = null,
                    recent_commands = decision.recentCommands,
                    lab_task_summary = target?.labTaskSummary ?: "",
                    frustration_score = decision.score,
                    locale = "zh-CN",
                    triggered_at = decision.triggeredAt,
                )
            }
            log.info(
                "guidance signal dispatched signal_id={} sessionKey={} reason={} score={}",
                signalId, context.sessionKey, decision.reason, decision.score,
            )
        } catch (e: Exception) {
            log.warn("handleTrigger failed signal_id={}: {}", signalId, e.message)
        }
    }

    // ============ 工具方法 ============

    private fun extractContainerName(session: WebSocketSession): String? {
        val uri = session.uri ?: return null
        val path = uri.path.trimEnd('/')
        val idx = path.lastIndexOf('/')
        return if (idx >= 0 && idx < path.length - 1) path.substring(idx + 1) else null
    }

    private fun extractQueryParams(session: WebSocketSession): QueryParams {
        val uri = session.uri ?: return QueryParams()
        val params = UriComponentsBuilder.fromUri(uri).build().queryParams
        return QueryParams(
            labSessionId = params.getFirst("lab_session_id")?.takeIf { it.isNotBlank() },
            userId = params.getFirst("user_id")?.takeIf { it.isNotBlank() }?.toLongOrNull(),
        )
    }

    private fun safeClose(session: WebSocketSession, status: CloseStatus) {
        try {
            session.close(status)
        } catch (e: Exception) {
            log.debug("safeClose failed: {}", e.message)
        }
    }

    private data class QueryParams(
        val labSessionId: String? = null,
        val userId: Long? = null,
    )

    internal data class TtySessionContext(
        val containerName: String,
        val sessionKey: String,
        val labSessionId: String?,
        val userId: Long?,
        var subscriber: TtyLogStreamService.Subscriber? = null,
    )
}