-- =====================================================================
-- 补充 module 4-6 + module_course 关联（让课程 5-8 有实验可展示）
-- ---------------------------------------------------------------------
-- 背景：database/sql/experiment-module-service-local-init.sql 只初始化了
--       module 1-3（关联 course 2/3/4）。seed_teacher_demo.sql 的学习事件
--       引用了 module_id 1-6（MOD(seq-1,6)+1），且课程 5-8 无实验，教师端
--       课程库展示单薄。本脚本补建 module 4-6 并关联到 course 5/6/7/8。
-- 幂等：ON DUPLICATE KEY UPDATE + INSERT IGNORE，可重复执行。
-- 前置：database/sql/experiment-module-service-local-init.sql（course 1-8 已存在）
-- =====================================================================

USE `userservice`;

INSERT INTO `module`
  (`module_id`, `difficulty`, `image_id`, `introduction`, `module_name`, `type`)
VALUES
  (4, 2, NULL, '在靶场中完成目录遍历漏洞验证、路径归一化与任意文件读取防护。', '目录遍历基础实验', '["目录遍历","Web安全"]'),
  (5, 3, NULL, '分析命令拼接缺陷并实践白名单与无 shell 调用等命令注入防护。', '命令注入实验', '["命令注入","系统安全"]'),
  (6, 2, NULL, '完成 CSRF 攻击复现与令牌校验、SameSite 防护实践。', 'CSRF 综合实验', '["CSRF","Web安全"]')
ON DUPLICATE KEY UPDATE
  `difficulty` = VALUES(`difficulty`),
  `introduction` = VALUES(`introduction`),
  `module_name` = VALUES(`module_name`),
  `type` = VALUES(`type`);

DELETE FROM `module_course`
WHERE (`module_id` = 4 AND `course_id` = 5)
   OR (`module_id` = 5 AND `course_id` = 6)
   OR (`module_id` = 6 AND `course_id` = 7)
   OR (`module_id` = 6 AND `course_id` = 8);

INSERT IGNORE INTO `module_course` (`module_id`, `course_id`) VALUES
  (4, 5),
  (5, 6),
  (6, 7),
  (6, 8);

SELECT
  m.`module_id`, m.`module_name`, GROUP_CONCAT(mc.`course_id` ORDER BY mc.`course_id`) AS `course_ids`
FROM `module` m
LEFT JOIN `module_course` mc ON mc.`module_id` = m.`module_id`
WHERE m.`module_id` BETWEEN 1 AND 6
GROUP BY m.`module_id`, m.`module_name`
ORDER BY m.`module_id`;
