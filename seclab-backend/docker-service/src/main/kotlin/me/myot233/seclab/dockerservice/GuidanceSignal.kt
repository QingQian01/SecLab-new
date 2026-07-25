package me.myot233.seclab.dockerservice

import java.time.Instant

/**
 * docker-service → ai-agent-service 的引导信号数据契约。
 *
 * 字段对齐 ai-agent-service 的 `GuidanceSignal` Pydantic 模型（guidance_service.py）。
 *
 * 重要（评审 Q4）：本类**不**携带 `error_signature` / `error_category`，由 Python 侧
 * `error_repository.classify_error_excerpt()` 统一分类，单一真相源，避免 Kotlin/Python 双源不一致。
 *
 * @param signal_id UUID，幂等去重
 * @param request_id 与 signal_id 同源，便于跨服务追踪
 * @param trigger_reason 触发原因："repeated_error" / "repeated_command" / "stuck_loop"
 * @param lab_session_id 实验 session id（WS 握手提供；缺失时为 null）
 * @param user_id / class_id / course_id / module_id / task_id 学习上下文（可选）
 * @param container_name docker 容器名（如 sqli-lab-web-1）
 * @param lab_key 靶机 key（如 "sqli"）
 * @param error_slice 最近 N 行报错摘要（≤1024 字符）
 * @param exit_code 触发该次信号的命令 exit code（可空）
 * @param recent_commands 最近 5 条 normalizedCmd（仅当 trigger_reason 含 command 时非空）
 * @param lab_task_summary 当前靶机任务摘要（从 [LabAllowlist] 反查）
 * @param frustration_score 触发时的分数
 * @param dify_conversation_id 可空；首次触发后由 ai-agent-service 回填，后续同 session 复用
 * @param locale 提示语言，默认 zh-CN
 * @param triggered_at ISO8601 UTC 时间戳
 */
data class GuidanceSignal(
    val signal_id: String,
    val request_id: String,
    val trigger_reason: String,
    val lab_session_id: String?,
    val user_id: Long?,
    val class_id: Long?,
    val course_id: Long?,
    val module_id: Long?,
    val task_id: Long?,
    val container_name: String,
    val lab_key: String,
    val error_slice: String,
    val exit_code: Int?,
    val recent_commands: List<String>,
    val lab_task_summary: String,
    val frustration_score: Int,
    val dify_conversation_id: String? = null,
    val locale: String = "zh-CN",
    val triggered_at: String = Instant.now().toString(),
)
