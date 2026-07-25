-- SecLab main business database initialization.
-- Scope: users/classes, course/module catalog, and image metadata.
-- Profile/event tables belong in init_seclab_profile.sql.

CREATE DATABASE IF NOT EXISTS `seclab_db`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `seclab_db`;

CREATE TABLE IF NOT EXISTS `class` (
  `class_id` BIGINT NOT NULL AUTO_INCREMENT,
  `admin_id` INT NULL,
  `class_detail` VARCHAR(255) NULL,
  `class_name` VARCHAR(255) NOT NULL,
  `is_end` INT NULL DEFAULT 0,
  PRIMARY KEY (`class_id`),
  UNIQUE KEY `uk_class_name` (`class_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `user` (
  `user_id` BIGINT NOT NULL AUTO_INCREMENT,
  `create_time` DATETIME(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  `is_admin` BIT(1) NULL DEFAULT b'0',
  `user_role` VARCHAR(16) NOT NULL DEFAULT 'STUDENT',
  `is_deleted` INT NULL DEFAULT 0,
  `user_academy` VARCHAR(255) NULL,
  `user_email` VARCHAR(255) NULL,
  `user_gender` INT NULL DEFAULT 2,
  `user_image` VARCHAR(255) NULL,
  `user_name` VARCHAR(255) NULL,
  `user_password` VARCHAR(255) NOT NULL,
  `user_student_number` VARCHAR(13) NOT NULL,
  `user_tel` VARCHAR(11) NULL,
  `class_id_class_id` BIGINT NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `uk_user_student_number` (`user_student_number`),
  KEY `idx_user_class_id` (`class_id_class_id`),
  KEY `idx_user_admin_deleted` (`is_admin`, `is_deleted`),
  KEY `idx_user_role_deleted` (`user_role`, `is_deleted`),
  CONSTRAINT `fk_user_class`
    FOREIGN KEY (`class_id_class_id`) REFERENCES `class` (`class_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `course` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `cost_time` INT NULL,
  `course_description` VARCHAR(1024) NOT NULL,
  `difficulty` INT NULL,
  `image_url` VARCHAR(255) NULL,
  `instructor` VARCHAR(255) NULL,
  `created_by` BIGINT NULL,
  `course_name` VARCHAR(255) NOT NULL,
  `schedule` VARCHAR(255) NULL,
  `course_status` TINYINT NULL DEFAULT 1,
  `tags` LONGTEXT NULL,
  `type` VARCHAR(255) NULL,
  PRIMARY KEY (`id`),
  KEY `idx_course_status_type` (`course_status`, `type`),
  KEY `idx_course_creator_status` (`created_by`, `course_status`),
  CONSTRAINT `fk_course_creator`
    FOREIGN KEY (`created_by`) REFERENCES `user` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `module` (
  `module_id` INT NOT NULL AUTO_INCREMENT,
  `difficulty` INT NULL,
  `image_id` INT NULL,
  `introduction` VARCHAR(1024) NULL,
  `module_name` VARCHAR(255) NULL,
  `task_points` LONGTEXT NULL,
  `type` LONGTEXT NULL,
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

CREATE TABLE IF NOT EXISTS `images` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `content_type` VARCHAR(50) NULL,
  `filename` VARCHAR(255) NULL,
  `original_filename` VARCHAR(255) NULL,
  `path` VARCHAR(255) NULL,
  `size` BIGINT NULL,
  `upload_time` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `url` VARCHAR(255) NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_images_filename` (`filename`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO `class` (`class_id`, `class_name`, `class_detail`, `is_end`) VALUES
(1, '网络安全232班', 'SecLab 默认班级', 0),
(2, '网络安全231班', '网络安全231班', 0),
(3, '网络安全233班', '网络安全233班', 0);

-- password: 123456; user-service upgrades legacy MD5 to BCrypt on successful login.
INSERT IGNORE INTO `user`
  (`user_id`, `user_student_number`, `user_password`, `user_name`, `user_gender`, `class_id_class_id`, `is_admin`, `user_role`, `is_deleted`)
VALUES
  (1, 'admin', 'e10adc3949ba59abbe56e057f20f883e', 'Administrator', 1, 1, b'1', 'TEACHER', 0),
  (2, '202400000001', 'e10adc3949ba59abbe56e057f20f883e', 'Demo Student', 1, 1, b'0', 'STUDENT', 0);

INSERT IGNORE INTO `course`
  (`id`, `cost_time`, `course_description`, `difficulty`, `image_url`, `instructor`, `course_name`, `schedule`, `course_status`, `tags`, `type`)
VALUES
  (1, 8, 'SQL injection fundamentals and defensive practice.', 3, 'a9fe8e50-ba21-45ef-abd5-50b717857502-course-sql-injection.png', 'SecLab Teacher', 'SQL注入攻防实战', '每周一', 1, '["SQL注入","Web安全"]', 'web'),
  (2, 6, 'XSS and CSRF attack and defense labs.', 2, 'eb678908-4878-4303-94ae-b3434d52612a-course-xss-deep-dive.png', 'SecLab Teacher', 'XSS漏洞深度解析', '每周二', 1, '["XSS","CSRF","Web安全"]', 'web'),
  (3, 7, 'File upload vulnerability exploitation and mitigation.', 3, '5780e906-42a1-4a88-ad06-d054bbf92735-3.文件上传漏洞突破.png', 'SecLab Teacher', '文件上传漏洞突破', '每周三', 1, '["文件上传","Web安全"]', 'web');

INSERT IGNORE INTO `module`
  (`module_id`, `difficulty`, `image_id`, `introduction`, `module_name`, `task_points`, `type`)
VALUES
  (1, 3, 101, 'SQL injection lab module.', 'SQL注入基础实验', '[]', '["SQL注入","Web安全"]'),
  (2, 2, 102, 'XSS and CSRF lab module.', 'XSS与CSRF基础实验', '[]', '["XSS","CSRF","Web安全"]'),
  (3, 3, 103, 'File upload lab module.', '文件上传基础实验', '[]', '["文件上传","Web安全"]');

INSERT IGNORE INTO `module_course` (`module_id`, `course_id`) VALUES
(1, 1),
(2, 2),
(3, 3);

-- 新增四个二进制 / 协议分析实验的课程种子（id 13-16）
-- image_url 与前端 SecLab-FrontEnd-2/public 下的静态资源路径保持一致
INSERT IGNORE INTO `course`
  (`id`, `cost_time`, `course_description`, `difficulty`, `image_url`, `instructor`, `course_name`, `schedule`, `course_status`, `tags`, `type`)
VALUES
  (13, 8, '本课程从栈结构原理出发，系统讲解栈溢出漏洞的成因与利用方法。通过在 Linux 操作环境中编写含后门的漏洞程序、使用 pwndbg 定位溢出偏移、用 pwntools 编写 exp 劫持函数返回地址，完成从理论到 getshell 的完整栈溢出学习闭环，掌握二进制安全基础与 PWN 核心技能。', 3, 'cover-stack-overflow.png', 'SecLab 教研组', '栈溢出攻击实战', '每周一', 1, '["栈溢出","二进制安全","PWN"]', 'system'),
  (14, 8, '本课程围绕网络协议分析展开，使用 Wireshark 对 HTTP、TCP、UDP 等常见协议进行深度抓包与解析。通过分析三次握手、HTTP 请求响应、明文传输风险与 HTTPS/TLS 加密防护，帮助学习者掌握网络流量分析方法，理解协议级安全风险与防护手段。', 3, '13.png', 'SecLab 教研组', '协议分析实战', '每周二', 1, '["协议分析","Wireshark","网络安全"]', 'network'),
  (15, 10, '本课程深入讲解 glibc 堆管理机制与堆溢出利用技术。涵盖 chunk 结构、fastbin/smallbin 组织、unlink 利用、fastbin attack 等核心攻击手法，通过实战 exp 编写完成堆溢出利用与控制流劫持，提升二进制漏洞利用进阶能力。', 4, 'cover-heap-overflow.png', 'SecLab 教研组', '堆溢出攻击实战', '每周三', 1, '["堆溢出","二进制安全","PWN"]', 'system'),
  (16, 10, '本课程系统讲解格式化字符串漏洞原理与利用。从 printf 函数机制出发，覆盖栈上任意地址泄露、利用 %n 完成任意地址写入、结合 GOT 表劫持与控制流转移等进阶技术，帮助学习者掌握这一经典且威力巨大的漏洞利用手法。', 4, 'cover-format-string.png', 'SecLab 教研组', '格式化字符串漏洞实战', '每周四', 1, '["格式化字符串","二进制安全","PWN"]', 'system');

-- 新增四个实验对应的 module 种子（module_id 15-18，与前端 data/*.js 中的实验 id 严格对齐）
-- task_points 在前端 data/index.js 维护，这里保留 [] 占位以保证后端表结构完整
INSERT IGNORE INTO `module`
  (`module_id`, `difficulty`, `image_id`, `introduction`, `module_name`, `task_points`, `type`)
VALUES
  (15, 3, NULL, '编写漏洞程序、定位溢出偏移、用 pwntools 编写 exp 劫持返回地址。', '栈溢出实验', '[]', '["系统安全","栈溢出"]'),
  (16, 3, NULL, '使用 Wireshark 抓包分析 HTTP/TCP 协议，理解明文传输与加密防护。', '协议分析实验', '[]', '["网络安全","协议分析"]'),
  (17, 5, NULL, '理解 glibc 堆管理，利用 unlink 与 fastbin attack 完成堆溢出利用。', '堆溢出实验', '[]', '["系统安全","堆溢出"]'),
  (18, 4, NULL, '利用 printf 格式化字符串漏洞完成栈泄露与任意地址写入。', '格式化字符串实验', '[]', '["系统安全","格式化字符串"]');

-- 新增 module_course 关联：module_id -> course_id
INSERT IGNORE INTO `module_course` (`module_id`, `course_id`) VALUES
(15, 13),
(16, 14),
(17, 15),
(18, 16);
