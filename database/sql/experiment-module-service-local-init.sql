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
  `course_name` VARCHAR(255) NOT NULL,
  `schedule` VARCHAR(255) DEFAULT NULL,
  `course_status` TINYINT DEFAULT 1,
  `tags` LONGTEXT DEFAULT NULL,
  `type` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_course_status_type` (`course_status`, `type`)
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

INSERT IGNORE INTO `course`
  (`id`, `course_description`, `difficulty`, `image_url`, `instructor`, `course_name`, `course_status`, `tags`, `type`)
VALUES
  (1, 'SQL injection fundamentals and defensive practice.', 3, 'a9fe8e50-ba21-45ef-abd5-50b717857502-course-sql-injection.png', 'SecLab Teacher', 'SQL Injection Practice', 1, '["SQL Injection","Web Security"]', 'web'),
  (2, 'XSS and CSRF attack and defense labs.', 2, 'eb678908-4878-4303-94ae-b3434d52612a-course-xss-deep-dive.png', 'SecLab Teacher', 'XSS Deep Dive', 1, '["XSS","CSRF","Web Security"]', 'web'),
  (3, 'File upload vulnerability exploitation and mitigation.', 3, '5780e906-42a1-4a88-ad06-d054bbf92735-3.png', 'SecLab Teacher', 'File Upload Practice', 1, '["File Upload","Web Security"]', 'web');

INSERT IGNORE INTO `module`
  (`module_id`, `difficulty`, `image_id`, `introduction`, `module_name`, `type`)
VALUES
  (1, 3, 101, 'SQL injection lab module.', 'SQL Injection Basic Lab', '["SQL Injection","Web Security"]'),
  (2, 2, 102, 'XSS and CSRF lab module.', 'XSS and CSRF Basic Lab', '["XSS","CSRF","Web Security"]'),
  (3, 3, 103, 'File upload lab module.', 'File Upload Basic Lab', '["File Upload","Web Security"]');

INSERT IGNORE INTO `module_course` (`module_id`, `course_id`) VALUES
  (1, 1),
  (2, 2),
  (3, 3);
