package me.myot233.seclab.dockerservice

import com.github.benmanes.caffeine.cache.Cache
import com.github.benmanes.caffeine.cache.Caffeine
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Component
import java.time.Instant
import java.util.concurrent.TimeUnit

/**
 * 挫败指数追踪器。
 *
 * 评分规则（评分函数 [observeError] / [observeCommand] / [observeLogLine]）：
 * - 每次错误事件 +1 分；同 error_signature 60 秒内重复 +2 分（额外加权）。
 * - 每次非零 exit 命令 +1 分；5 分钟窗口内同一 normalizedCmd 重复 3+ 次 +1 分。
 *
 * 触发条件（[tryTrigger]）：
 * - `score >= threshold` 且距上次触发 > `cooldownSeconds` → 返回 [TriggerDecision] 并清零 score。
 * - 否则返回 null。
 *
 * 线程安全：
 * - 缓存用 Caffeine `expireAfterAccess(stateTtlMinutes)`，避免无界增长（评审缺口 5）。
 * - 单个 [FrustrationState] 的可变字段通过 `synchronized(state)` 访问。
 *
 * 评分阈值与冷却时间均通过 `seclab.frustration.*` 配置注入，便于线上调参。
 */
@Component
class FrustrationTracker(
    @Value("\${seclab.frustration.threshold:3}") private val threshold: Int,
    @Value("\${seclab.frustration.cooldown-seconds:90}") private val cooldownSeconds: Long,
    @Value("\${seclab.frustration.repeat-window-seconds:300}") private val repeatWindowSeconds: Long,
    @Value("\${seclab.frustration.state-ttl-minutes:30}") private val stateTtlMinutes: Long,
) {

    private val log = LoggerFactory.getLogger(javaClass)

    private val cache: Cache<String, FrustrationState> = Caffeine.newBuilder()
        .expireAfterAccess(stateTtlMinutes, TimeUnit.MINUTES)
        .maximumSize(10_000)
        .build()

    /** 同 signature 重复加权的窗口（60 秒） */
    private val errorRepeatWindowMs: Long = 60_000L

    /** 错误日志正则：与 docker_tools.py 的 _ERROR_PATTERNS 对齐（轻量版，只判定是否为错误行） */
    private val errorLinePattern = Regex(
        "(?i)(error|exception|syntax\\s*error|fatal|warning|mysql|sqlstate|traceback|" +
            "segmentation fault|permission denied|operation not permitted|command not found|" +
            "no such file or directory|cannot stat|file not found|connection refused|" +
            "could not connect|couldn't connect|timed out|timeout|unexpected token|parse error)"
    )

    /**
     * 从原始日志行中提取轻量 signature（仅用于"同 signature 重复"判定，
     * Python 侧 `classify_error_excerpt` 仍做权威分类）。
     */
    private fun extractSignature(line: String): String {
        val lower = line.lowercase()
        return when {
            "permission denied" in lower || "operation not permitted" in lower -> "permission_denied"
            "command not found" in lower -> "command_not_found"
            "syntax error" in lower || "unexpected token" in lower || "parse error" in lower -> "syntax_error"
            "connection refused" in lower || "could not connect" in lower -> "connection_refused"
            "no such file" in lower || "cannot stat" in lower || "file not found" in lower -> "file_not_found"
            "timed out" in lower || "timeout" in lower -> "timeout"
            "traceback" in lower || "exception" in lower || "fatal" in lower -> "runtime_error"
            else -> "other"
        }
    }

    /**
     * 观察一条容器日志行。
     * 仅当日志行匹配错误模式时才更新 score；否则忽略。
     *
     * @return 若触发则返回 [TriggerDecision]，否则 null
     */
    fun observeLogLine(
        sessionKey: String,
        line: String,
        @Suppress("UNUSED_PARAMETER") streamType: String,
        @Suppress("UNUSED_PARAMETER") containerName: String,
    ): TriggerDecision? {
        if (!errorLinePattern.containsMatchIn(line)) return null
        val signature = extractSignature(line)
        return observeError(sessionKey, line, exitCode = null, signatureOverride = signature)
    }

    /**
     * 显式观察一次错误事件（由 [DockerController] 的 `POST /api/docker/frustration/{lab}` 降级路径调用）。
     *
     * @param sessionKey lab_session_id 或 fallback `containerName:user_id`
     * @param errorSlice 错误摘要（≤1024 字符）
     * @param exitCode 命令 exit code（可空）
     * @param signatureOverride 显式 signature（可空，由 [observeLogLine] 提供时使用）
     */
    fun observeError(
        sessionKey: String,
        errorSlice: String,
        exitCode: Int? = null,
        signatureOverride: String? = null,
    ): TriggerDecision? {
        val signature = signatureOverride ?: extractSignature(errorSlice)
        val now = System.currentTimeMillis()
        val state = cache.get(sessionKey) { FrustrationState() } ?: return null

        val (recentError, recentCmd, isRepeated) = synchronized(state) {
            // 清理过期错误记录（超过 60s）
            state.recentErrors.removeAll { now - it.timestamp > errorRepeatWindowMs }
            state.recentErrors.add(FrustrationState.ErrorRecord(signature, now, errorSnippet(errorSlice)))

            // 评分：基础 +1
            var delta = 1
            // 同 signature 60s 内重复 +2
            val sameSigCount = state.recentErrors.count { it.signature == signature }
            if (sameSigCount >= 2) delta += 2

            state.score += delta
            log.debug("observeError sessionKey={} sig={} delta={} score={}", sessionKey, signature, delta, state.score)

            Triple(
                state.recentErrors.takeLast(5).map { it.excerpt },
                state.recentCommands.takeLast(5).map { it.normalizedCmd },
                sameSigCount >= 2,
            )
        }

        // 走 WS TTY 错误路径触发时统一标记为 repeated_error；
        // 单次错误不会跨阈值（threshold=3），所以触发一定源于重复累积。
        val reason = if (isRepeated) "repeated_error" else "repeated_error"
        return tryTrigger(sessionKey, reason = reason, recentError, recentCmd)
    }

    /**
     * 观察一次命令执行（来自 [DockerController] 的降级路径或容器 exec hook）。
     */
    fun observeCommand(
        sessionKey: String,
        normalizedCmd: String,
        exitCode: Int? = null,
    ): TriggerDecision? {
        val now = System.currentTimeMillis()
        val state = cache.get(sessionKey) { FrustrationState() } ?: return null

        val (recentErr, recentCmd) = synchronized(state) {
            // 清理过期命令记录（超过 5 分钟）
            state.recentCommands.removeAll { now - it.timestamp > repeatWindowSeconds * 1000 }
            state.recentCommands.add(FrustrationState.CommandRecord(normalizedCmd, now))

            var delta = 0
            // 非零 exit +1
            if (exitCode != null && exitCode != 0) delta += 1
            // 5 分钟窗口内同一 normalizedCmd 重复 3+ 次 +1
            val sameCmdCount = state.recentCommands.count { it.normalizedCmd == normalizedCmd }
            if (sameCmdCount >= 3) delta += 1

            if (delta > 0) {
                state.score += delta
                log.debug("observeCommand sessionKey={} cmd={} delta={} score={}", sessionKey, normalizedCmd, delta, state.score)
            }

            Pair(
                state.recentErrors.takeLast(5).map { it.excerpt },
                state.recentCommands.takeLast(5).map { it.normalizedCmd },
            )
        }

        return tryTrigger(sessionKey, reason = "repeated_command", recentErr, recentCmd)
    }

    /**
     * 检查并尝试触发信号。
     * - score >= threshold 且距上次触发 > cooldown → 返回 [TriggerDecision] 并清零 score
     * - 否则返回 null（不触发）
     */
    fun tryTrigger(
        sessionKey: String,
        reason: String = "stuck_loop",
        recentErrors: List<String> = emptyList(),
        recentCommands: List<String> = emptyList(),
    ): TriggerDecision? {
        val state = cache.getIfPresent(sessionKey) ?: return null
        val now = System.currentTimeMillis()
        return synchronized(state) {
            if (state.score < threshold) return@synchronized null
            if (now - state.lastTriggerAt < cooldownSeconds * 1000) {
                log.info("cooldown active for sessionKey={} ({}s remaining)", sessionKey, cooldownSeconds - (now - state.lastTriggerAt) / 1000)
                return@synchronized null
            }
            val decision = TriggerDecision(
                reason = reason,
                score = state.score,
                recentErrors = recentErrors,
                recentCommands = recentCommands,
                triggeredAt = Instant.now().toString(),
            )
            // 触发后清零 score，但保留 lastTriggerAt 用于冷却判定
            state.score = 0
            state.lastTriggerAt = now
            log.info("frustration triggered sessionKey={} reason={} score={}", sessionKey, reason, decision.score)
            decision
        }
    }

    /** 查询当前分数（调试用） */
    fun score(sessionKey: String): Int {
        val state = cache.getIfPresent(sessionKey) ?: return 0
        return synchronized(state) { state.score }
    }

    /** 查询当前状态快照（调试用） */
    fun snapshot(sessionKey: String): FrustrationState? = cache.getIfPresent(sessionKey)

    /** 把错误摘要截断到 1024 字符（与 error_repository.MAX_EXCERPT_LENGTH 对齐） */
    private fun errorSnippet(slice: String): String =
        slice.replace("\u0000", "").trim().take(1024)

    /**
     * 触发决策。WS handler / 降级端点拿到后，结合 session 上下文构造 [GuidanceSignal]
     * 并通过 [GuidanceSignalClient] 发送给 ai-agent-service。
     */
    data class TriggerDecision(
        val reason: String,
        val score: Int,
        val recentErrors: List<String>,
        val recentCommands: List<String>,
        val triggeredAt: String,
    )
}
