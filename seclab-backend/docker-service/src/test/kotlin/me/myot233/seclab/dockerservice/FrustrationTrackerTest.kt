package me.myot233.seclab.dockerservice

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotEquals
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

/**
 * [FrustrationTracker] 单元测试。
 *
 * 不依赖 Docker daemon 与 Spring 容器，CI 必跑。
 * 直接构造 [FrustrationTracker] 实例，注入测试阈值（threshold=3, cooldown=90s, repeat-window=300s, ttl=30min）。
 *
 * 评分规则回顾（与实现一致）：
 * - 每次错误 +1（基础）；同 signature 60s 内重复 ≥2 次 → 额外 +2（即 delta=1+2=3）。
 * - 每次非零 exit 命令 +1；5min 窗口同 normalizedCmd ≥3 次 → 额外 +1（即 delta=1+1=2）。
 * - observeError / observeCommand 内部自动调 tryTrigger：score >= threshold 且距上次触发 > cooldown → 返回 [FrustrationTracker.TriggerDecision]，并清零 score。
 *
 * 关键推论（threshold=3）：
 * - 同 signature 第 2 次错误：score = 1（前次）+ 3（delta）= 4 ≥ 3 → 第 2 次即触发，而非第 3 次。
 * - 不同 signature 第 3 次错误：score = 1+1+1 = 3 ≥ 3 → 第 3 次触发。
 */
class FrustrationTrackerTest {

    private fun newTracker(
        threshold: Int = 3,
        cooldownSeconds: Long = 90L,
        repeatWindowSeconds: Long = 300L,
        stateTtlMinutes: Long = 30L,
    ): FrustrationTracker = FrustrationTracker(
        threshold = threshold,
        cooldownSeconds = cooldownSeconds,
        repeatWindowSeconds = repeatWindowSeconds,
        stateTtlMinutes = stateTtlMinutes,
    )

    @Test
    fun `single error does not trigger`() {
        val tracker = newTracker()
        val decision = tracker.observeError(
            sessionKey = "session-1",
            errorSlice = "permission denied: /etc/shadow",
            exitCode = null,
        )
        assertNull(decision, "单次错误 score=1 < threshold=3，不应触发")
        assertEquals(1, tracker.score("session-1"))
    }

    @Test
    fun `repeated same signature within 60s triggers`() {
        val tracker = newTracker()
        val sessionKey = "session-repeated-error"
        // 第一次：score=1（基础 +1，count=1 < 2 不加权）
        tracker.observeError(sessionKey, "permission denied: /etc/shadow")
        assertEquals(1, tracker.score(sessionKey))
        // 第二次：同 signature，count=2 >= 2 → delta=1（基础）+2（重复加权）=3
        //         score = 1 + 3 = 4 >= threshold(3) → 触发，score 清零
        val decision = tracker.observeError(sessionKey, "permission denied: /var/lib/mysql")
        assertNotNull(decision, "同 signature 60s 内 2 次即触发（score=4 >= threshold=3）")
        assertEquals("repeated_error", decision!!.reason)
        assertEquals(4, decision.score, "触发时 score 应为 4（1+1+2）")
        assertEquals(0, tracker.score(sessionKey), "触发后 score 应清零")
    }

    @Test
    fun `cooldown suppresses second trigger`() {
        val tracker = newTracker()
        val sessionKey = "session-cooldown"
        // 第一次错误：score=1
        tracker.observeError(sessionKey, "permission denied: /file-1")
        // 第二次错误：score=4 → 触发，清零，lastTriggerAt=now
        val firstDecision = tracker.observeError(sessionKey, "permission denied: /file-2")
        assertNotNull(firstDecision, "第二次错误应触发首次信号")
        assertEquals(0, tracker.score(sessionKey), "触发后 score 应清零")
        // 冷却内继续观察：score 累积但不应触发
        tracker.observeError(sessionKey, "permission denied: /file-after-1")
        tracker.observeError(sessionKey, "permission denied: /file-after-2")
        val decision = tracker.observeError(sessionKey, "permission denied: /file-after-3")
        assertNull(decision, "90s 冷却内第二次触发应被抑制")
        assertTrue(tracker.score(sessionKey) >= 3, "冷却期内 score 不应被清零，实际 ${tracker.score(sessionKey)}")
    }

    @Test
    fun `repeated command within 5min window adds score`() {
        val tracker = newTracker()
        val sessionKey = "session-repeated-command"
        // 3 次同一命令 + 非零 exit
        // 第一次：exit_code != 0 → +1；同 cmd count=1 → 不加权
        val d1 = tracker.observeCommand(sessionKey, "cat /etc/shadow", exitCode = 1)
        assertNull(d1)
        assertEquals(1, tracker.score(sessionKey))
        // 第二次：exit_code != 0 → +1；同 cmd count=2 → 不加权
        val d2 = tracker.observeCommand(sessionKey, "cat /etc/shadow", exitCode = 1)
        assertNull(d2)
        assertEquals(2, tracker.score(sessionKey))
        // 第三次：exit_code != 0 → +1；同 cmd count=3 → +1（总 delta=2）
        //         score = 2 + 2 = 4 >= 3 → 触发
        val d3 = tracker.observeCommand(sessionKey, "cat /etc/shadow", exitCode = 1)
        assertNotNull(d3, "3 次同命令 + 非零 exit 应触发")
        assertEquals("repeated_command", d3!!.reason)
        assertTrue(d3.score >= 3, "触发时 score 应 ≥ 3，实际 ${d3.score}")
    }

    @Test
    fun `different sessionKeys are isolated`() {
        val tracker = newTracker()
        // session A 第一次：score=1
        tracker.observeError("session-A", "permission denied: /a1")
        assertEquals(1, tracker.score("session-A"))
        // session A 第二次：同 signature，score=4 → 触发，清零
        tracker.observeError("session-A", "permission denied: /a2")
        assertEquals(0, tracker.score("session-A"), "A 第二次已触发并清零")
        // session B 不应受影响
        assertEquals(0, tracker.score("session-B"))
        // session A 第三次：冷却内 score 累积但不触发
        tracker.observeError("session-A", "permission denied: /a3")
        assertTrue(tracker.score("session-A") >= 3, "A 冷却内 score 应累积，实际 ${tracker.score("session-A")}")
        assertEquals(0, tracker.score("session-B"), "B 仍为 0")
    }

    @Test
    fun `score resets after trigger`() {
        val tracker = newTracker()
        val sessionKey = "session-reset"
        // 第一次：score=1
        tracker.observeError(sessionKey, "permission denied: /file-1")
        assertEquals(1, tracker.score(sessionKey))
        // 第二次：同 signature，score=4 → 触发，清零
        val triggered = tracker.observeError(sessionKey, "permission denied: /file-2")
        assertNotNull(triggered, "第二次应触发")
        assertEquals(0, tracker.score(sessionKey), "触发后 score 应为 0")
        // 第三次：冷却内，score 累积但不触发
        val decision = tracker.observeError(sessionKey, "permission denied: /file-3")
        assertNull(decision, "冷却内不应再触发")
        assertTrue(tracker.score(sessionKey) >= 3, "冷却内 score 应累积，实际 ${tracker.score(sessionKey)}")
    }

    @Test
    fun `different signatures do not stack repeat bonus`() {
        val tracker = newTracker()
        val sessionKey = "session-diff-sig"
        // 3 次不同 signature 的错误：每次基础 +1，无重复加权
        tracker.observeError(sessionKey, "permission denied: /file-1") // signature=permission_denied
        assertEquals(1, tracker.score(sessionKey))
        tracker.observeError(sessionKey, "command not found: foo") // signature=command_not_found
        assertEquals(2, tracker.score(sessionKey))
        // 第三次不同 signature，score=3 >= threshold(3) → 触发
        val decision = tracker.observeError(sessionKey, "no such file or directory: /tmp/x") // signature=file_not_found
        assertNotNull(decision, "3 次不同 signature 错误 score=3 应触发")
        assertTrue(decision!!.score >= 3, "score 应 ≥ 3，实际 ${decision.score}")
        // 不同 signature 不应加重复 +2 加权
        // 第三次只 +1，所以触发时 score=3（恰好等于 threshold）
        assertEquals(3, decision.score, "不同 signature 不应加重复加权，触发时 score 应正好为 3")
    }

    @Test
    fun `observeLogLine ignores non-error lines`() {
        val tracker = newTracker()
        val sessionKey = "session-logline"
        // 普通日志行不应被识别为错误
        val decision = tracker.observeLogLine(
            sessionKey = sessionKey,
            line = "[2026-07-19] INFO: server started on port 80",
            streamType = "stdout",
            containerName = "sqli-lab-web-1",
        )
        assertNull(decision, "非错误日志行不应触发 observeError")
        assertEquals(0, tracker.score(sessionKey))
    }

    @Test
    fun `observeLogLine detects error lines and triggers on repeat`() {
        val tracker = newTracker()
        val sessionKey = "session-logline-trigger"
        // 第一次错误日志行：score=1
        tracker.observeLogLine(sessionKey, "ERROR: permission denied for user 'root'@'localhost'", "stderr", "sqli-lab-web-1")
        assertEquals(1, tracker.score(sessionKey))
        // 第二次同 signature 错误日志行：score=4 >= 3 → 触发
        val decision = tracker.observeLogLine(sessionKey, "ERROR: permission denied for table 'users'", "stderr", "sqli-lab-web-1")
        assertNotNull(decision, "2 次同 signature 错误日志行应触发（score=4 >= 3）")
        assertEquals("repeated_error", decision!!.reason)
        assertEquals(0, tracker.score(sessionKey), "触发后 score 应清零")
    }

    @Test
    fun `tryTrigger returns null when below threshold`() {
        val tracker = newTracker()
        val sessionKey = "session-trytrigger-below"
        tracker.observeError(sessionKey, "permission denied: /file-1")
        // score=1 < 3
        val decision = tracker.tryTrigger(sessionKey)
        assertNull(decision)
    }

    @Test
    fun `tryTrigger with explicit recent context returns decision`() {
        val tracker = newTracker()
        val sessionKey = "session-trytrigger-explicit"
        // 用不同 signature 避免重复加权，让 score 精确累积到 2（< threshold=3，不触发）
        tracker.observeError(sessionKey, "permission denied: /file-1")  // sig=permission_denied, score=1
        tracker.observeError(sessionKey, "command not found: foo")      // sig=command_not_found, score=2
        assertEquals(2, tracker.score(sessionKey))
        // 此时 score=2 < 3，显式 tryTrigger 应返回 null
        val belowDecision = tracker.tryTrigger(
            sessionKey = sessionKey,
            reason = "stuck_loop",
            recentErrors = listOf("custom error 1", "custom error 2"),
            recentCommands = listOf("cmd1", "cmd2"),
        )
        assertNull(belowDecision, "score=2 < threshold=3，tryTrigger 应返回 null")
        // 再加一次不同 signature 错误，score=3 >= 3 → observeError 内部自动触发
        val decision = tracker.observeError(sessionKey, "no such file or directory: /tmp/x")
        assertNotNull(decision, "score=3 >= threshold=3 应触发")
        assertEquals("repeated_error", decision!!.reason)
        // recentErrors 应来自 state（最近 3 条错误摘要），而非显式传入
        assertTrue(decision.recentErrors.isNotEmpty(), "recentErrors 应非空")
        assertNotEquals(
            "",
            decision.triggeredAt,
            "triggeredAt 应为非空 ISO8601 时间戳",
        )
    }
}