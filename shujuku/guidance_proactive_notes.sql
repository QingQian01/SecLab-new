-- guidance_proactive_notes：proactive guidance 主动提示历史表
--
-- 用途：
--   每当 docker-service 的 FrustrationTracker 触发挫败指数阈值，ai-agent-service
--   会异步调用 Dify 生成一段启发式诊断并推送给前端 SSE；同时在本地落一条记录
--   到本表，便于按 lab_session_id / user_id 回溯学生收到的所有主动提示历史。
--
-- 关联关系（软关联，不加 FK 约束，与 error_event.sql 风格一致）：
--   - conversation_id → ai_conversation.conversation_id（ai_repository.py 维护）
--   - message_id      → ai_message.message_id（ai_repository.save_ai_message 维护）
--   - signal_id       → docker-service GuidanceSignalClient 生成的 UUID
--   - lab_session_id  → lab_repository.start_lab_session 生成的会话 ID
--
-- 落库时机：guidance_service.stream_guidance_to_subscribers 完成 Dify 流式调用后
--   由 save_guidance_proactive_note() INSERT 一行（ai_message 持久化之后）。
--
-- 不重复上报处理：本表只追加（INSERT），不更新；同一 signal_id 不会重复落库，
--   因为 dispatch_signal_task 每个 signal 只触发一次 stream_guidance_to_subscribers。

CREATE DATABASE IF NOT EXISTS `seclab_profile`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `seclab_profile`;

CREATE TABLE IF NOT EXISTS `guidance_proactive_notes` (
  `note_id` VARCHAR(64) NOT NULL COMMENT '主动提示记录 ID（gnote-{uuid}）',
  `lab_session_id` VARCHAR(64) NULL COMMENT '靶机会话 ID，关联 lab_session',
  `user_id` BIGINT NULL COMMENT '学生 ID，便于按学生查历史',
  `signal_id` VARCHAR(64) NOT NULL COMMENT 'docker-service 触发的 signal ID',
  `conversation_id` VARCHAR(64) NOT NULL COMMENT '本地 ai_conversation ID（guidance-{lab_session_id}）',
  `message_id` VARCHAR(64) NOT NULL COMMENT '本地 ai_message ID（msg-{uuid}）',
  `trigger_reason` VARCHAR(64) NULL COMMENT '触发原因：repeated_error / stuck_loop / repeated_command 等',
  `ai_message` LONGTEXT NULL COMMENT 'Dify 生成的完整启发式诊断文本',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '落库时间',
  PRIMARY KEY (`note_id`),
  KEY `idx_guidance_note_session_time` (`lab_session_id`, `created_at`),
  KEY `idx_guidance_note_user_time` (`user_id`, `created_at`),
  KEY `idx_guidance_note_signal` (`signal_id`),
  KEY `idx_guidance_note_conversation` (`conversation_id`),
  KEY `idx_guidance_note_message` (`message_id`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
