-- XSS实验数据库初始化脚本
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET character_set_connection=utf8mb4;

USE xss_lab;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建留言表
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    session_id VARCHAR(64) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 兼容旧库：给已存在的 messages 表补上 session_id 字段
SET @add_session_id = (
    SELECT IF(
        EXISTS(
            SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'xss_lab'
              AND TABLE_NAME = 'messages'
              AND COLUMN_NAME = 'session_id'
        ),
        'SELECT 1',
        'ALTER TABLE messages ADD COLUMN session_id VARCHAR(64) NULL AFTER message, ADD INDEX idx_messages_session (session_id)'
    )
);
PREPARE stmt FROM @add_session_id;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 插入测试数据
INSERT INTO users (username, password, email) VALUES
('admin', 'admin123', 'admin@example.com'),
('user1', 'password123', 'user1@example.com'),
('test', 'test123', 'test@example.com');

-- 插入一些测试留言
INSERT INTO messages (username, message) VALUES
('admin', '欢迎来到XSS实验环境！'),
('user1', '这是一个测试留言。'),
('test', '请尝试进行XSS攻击。'); 