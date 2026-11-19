-- Local bootstrap for experiment-module-service when it is configured to use
-- the userservice database in application.yml.

CREATE DATABASE IF NOT EXISTS `userservice`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `userservice`;

CREATE TABLE IF NOT EXISTS `course` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `cost_time` INT DEFAULT NULL,
  `course_description` VARCHAR(1024) NOT NULL,
  `difficulty` INT DEFAULT NULL,
  `image_url` VARCHAR(255) DEFAULT NULL,
  `instructor` VARCHAR(255) DEFAULT NULL,
  `created_by` BIGINT NULL,
  `course_name` VARCHAR(255) NOT NULL,
  `schedule` VARCHAR(255) DEFAULT NULL,
  `course_status` TINYINT DEFAULT 1,
  `tags` LONGTEXT DEFAULT NULL,
  `type` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_course_status_type` (`course_status`, `type`),
  KEY `idx_course_creator_status` (`created_by`, `course_status`),
  CONSTRAINT `fk_course_creator`
    FOREIGN KEY (`created_by`) REFERENCES `user` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `module` (
  `module_id` INT NOT NULL AUTO_INCREMENT,
  `difficulty` INT DEFAULT NULL,
  `image_id` INT DEFAULT NULL,
  `introduction` VARCHAR(1024) DEFAULT NULL,
  `module_name` VARCHAR(255) DEFAULT NULL,
  `task_points` LONGTEXT DEFAULT NULL,
  `type` LONGTEXT DEFAULT NULL,
  PRIMARY KEY (`module_id`),
  KEY `idx_module_difficulty` (`difficulty`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `module_course` (
  `module_id` INT NOT NULL,
  `course_id` INT NOT NULL,
  PRIMARY KEY (`module_id`, `course_id`),
  KEY `idx_module_course_course` (`course_id`),
  CONSTRAINT `fk_module_course_module`
    FOREIGN KEY (`module_id`) REFERENCES `module` (`module_id`),
  CONSTRAINT `fk_module_course_course`
    FOREIGN KEY (`course_id`) REFERENCES `course` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- lab_package：教师上传的实验包（zip）登记表
-- 本期范围：仅上传 + 元数据登记，不触发 docker build / 启动。
-- status 取值：UPLOADED（已上传，本期固定）/ BUILT（已构建，后续迭代）/ REGISTERED（已注册到白名单，后续迭代）
CREATE TABLE IF NOT EXISTS `lab_package` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  `module_id` INT DEFAULT NULL COMMENT '关联实验模块，可空（上传时未指定则空）',
  `lab_key` VARCHAR(64) NOT NULL COMMENT '实验唯一标识，如 stack-overflow',
  `image_name` VARCHAR(255) DEFAULT NULL COMMENT '预期镜像名，如 stack-overflow-lab-web:latest',
  `host_port` INT DEFAULT NULL COMMENT '预期宿主端口，如 8096',
  `flag` VARCHAR(255) DEFAULT NULL COMMENT '实验 flag（用于后续启动注入与校验）',
  `package_path` VARCHAR(512) NOT NULL COMMENT 'zip 落盘相对路径（相对存储目录）',
  `original_filename` VARCHAR(255) DEFAULT NULL COMMENT '原始上传文件名',
  `size_bytes` BIGINT DEFAULT NULL COMMENT 'zip 文件大小（字节）',
  `uploaded_by` BIGINT DEFAULT NULL COMMENT '上传教师 user_id',
  `status` VARCHAR(32) NOT NULL DEFAULT 'UPLOADED' COMMENT 'UPLOADED / BUILT / REGISTERED',
  `remark` VARCHAR(1024) DEFAULT NULL COMMENT '备注',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_lab_package_lab_key` (`lab_key`),
  KEY `idx_lab_package_module` (`module_id`),
  KEY `idx_lab_package_uploader` (`uploaded_by`),
  KEY `idx_lab_package_status` (`status`),
  CONSTRAINT `fk_lab_package_module`
    FOREIGN KEY (`module_id`) REFERENCES `module` (`module_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='教师上传的实验包登记表';

INSERT INTO `course`
  (`id`, `course_description`, `difficulty`, `image_url`, `instructor`, `course_name`, `course_status`, `tags`, `type`)
VALUES
  (1, '介绍网络安全基本概念、常见威胁与实验环境使用规范。', 1, 'a9fe8e50-ba21-45ef-abd5-50b717857502-course-sql-injection.png', '李伟', '网络安全导论', 1, '["安全基础","实验规范"]', '网络安全基础'),
  (2, '结合靶场理解 SQL 注入的形成原因、利用方式与参数化查询防护。', 2, 'a9fe8e50-ba21-45ef-abd5-50b717857502-course-sql-injection.png', '李伟', 'SQL 注入原理与防护', 1, '["SQL注入","Web安全"]', 'Web安全'),
  (3, '通过反射型与存储型 XSS 实验学习输入输出编码和内容安全策略。', 2, 'eb678908-4878-4303-94ae-b3434d52612a-course-xss-deep-dive.png', '李伟', '跨站脚本攻击与防护', 1, '["XSS","Web安全"]', 'Web安全'),
  (4, '分析不安全上传校验、文件解析差异和安全存储策略。', 3, '5780e906-42a1-4a88-ad06-d054bbf92735-3.png', '李伟', '文件上传漏洞', 1, '["文件上传","Web安全"]', 'Web安全'),
  (5, '学习目录遍历漏洞成因、路径规范化处理与最小权限配置。', 2, NULL, '李伟', '目录遍历漏洞', 1, '["目录遍历","访问控制"]', 'Web安全'),
  (6, '通过命令拼接案例理解系统命令注入及白名单防护。', 3, NULL, '李伟', '命令注入漏洞', 1, '["命令注入","系统安全"]', '系统安全'),
  (7, '理解跨站请求伪造攻击流程，并实践令牌校验和 SameSite 防护。', 2, NULL, '李伟', 'CSRF 攻击与防护', 1, '["CSRF","Web安全"]', 'Web安全'),
  (8, '综合运用信息收集、漏洞定位、利用验证和修复说明完成阶段实训。', 4, NULL, '李伟', 'Web 安全综合实训', 1, '["综合实训","漏洞分析"]', '综合实践')
ON DUPLICATE KEY UPDATE
  `course_description` = VALUES(`course_description`),
  `difficulty` = VALUES(`difficulty`),
  `instructor` = VALUES(`instructor`),
  `course_name` = VALUES(`course_name`),
  `course_status` = VALUES(`course_status`),
  `tags` = VALUES(`tags`),
  `type` = VALUES(`type`);

INSERT INTO `module`
  (`module_id`, `difficulty`, `image_id`, `introduction`, `module_name`, `type`)
VALUES
  (1, 3, 101, '在靶场中完成 SQL 注入定位、验证和参数化修复。', 'SQL 注入基础实验', '["SQL注入","Web安全"]'),
  (2, 2, 102, '完成 XSS 与 CSRF 攻击验证并比较不同防护方式。', 'XSS 与 CSRF 基础实验', '["XSS","CSRF","Web安全"]'),
  (3, 3, 103, '分析上传校验缺陷并给出后端校验与隔离建议。', '文件上传安全实验', '["文件上传","Web安全"]')
ON DUPLICATE KEY UPDATE
  `difficulty` = VALUES(`difficulty`),
  `introduction` = VALUES(`introduction`),
  `module_name` = VALUES(`module_name`),
  `type` = VALUES(`type`);

DELETE FROM `module_course`
WHERE (`module_id` = 1 AND `course_id` = 1)
   OR (`module_id` = 2 AND `course_id` = 2)
   OR (`module_id` = 3 AND `course_id` = 3);

INSERT IGNORE INTO `module_course` (`module_id`, `course_id`) VALUES
  (1, 2),
  (2, 3),
  (3, 4);
