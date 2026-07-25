package me.myot233.seclab.dockerservice

/**
 * 单个 lab_session 的挫败指数累积状态。
 *
 * 由 [FrustrationTracker] 在 Caffeine 缓存中维护，按 `lab_session_id`（或 fallback `containerName:user_id`）为 key。
 * 所有可变字段均通过 `synchronized(state)` 块访问，保证并发安全。
 *
 * @param score 当前累积分数（每次触发后清零）
 * @param lastTriggerAt 上次触发信号的时间戳（epoch millis），用于冷却判断
 * @param recentErrors 最近 60 秒内的错误记录（用于"同 signature 重复"加权）
 * @param recentCommands 最近 5 分钟内的命令记录（用于"同命令重复"加权）
 */
data class FrustrationState(
    @Volatile var score: Int = 0,
    @Volatile var lastTriggerAt: Long = 0L,
    val recentErrors: MutableList<ErrorRecord> = mutableListOf(),
    val recentCommands: MutableList<CommandRecord> = mutableListOf(),
) {
    /** 单条错误记录 */
    data class ErrorRecord(
        val signature: String,
        val timestamp: Long,
        val excerpt: String,
    )

    /** 单条命令记录 */
    data class CommandRecord(
        val normalizedCmd: String,
        val timestamp: Long,
    )
}
