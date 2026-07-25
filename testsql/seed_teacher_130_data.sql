-- 教师端测试数据：130名学生完整数据集
-- 用途：生成可作为教师端测试展示的合理数据，包含学生、教学班、训练、问题、事件和分析
-- 前缀：teacher-demo-20260716-*
-- 前置条件：已执行 database/sql/user-service-local-init.sql 和 experiment-module-service-local-init.sql
-- 教师账号：T20260001 / 123456

START TRANSACTION;

SET @teacher_id := (SELECT `user_id` FROM `userservice`.`user` WHERE `user_student_number` = 'T20260001' LIMIT 1);
SET @admin_class_id := (SELECT `class_id` FROM `userservice`.`class` WHERE `class_name` = '网络安全232班' LIMIT 1);

INSERT INTO `userservice`.`teaching_class` (
  `class_name`, `academic_year`, `semester`, `teacher_id`,
  `start_date`, `end_date`, `status`
) VALUES (
  '网络安全工程实践-01班', '2026-2027', 1, @teacher_id,
  '2026-09-07', '2027-01-08', 'ACTIVE'
) ON DUPLICATE KEY UPDATE `status` = 'ACTIVE';

SET @teaching_class_id := (SELECT `teaching_class_id` FROM `userservice`.`teaching_class`
  WHERE `class_name` = '网络安全工程实践-01班' AND `teacher_id` = @teacher_id LIMIT 1);

DELETE FROM `seclab_profile`.`teacher_typical_question`
WHERE `generated_question_id` LIKE 'teacher-demo-20260716-%';

DELETE FROM `seclab_profile`.`question_knowledge_point`
WHERE `generated_question_id` LIKE 'teacher-demo-20260716-%';

DELETE FROM `seclab_profile`.`generated_question_attempt`
WHERE `attempt_id` LIKE 'teacher-demo-20260716-%';

DELETE FROM `seclab_profile`.`generated_question`
WHERE `generated_question_id` LIKE 'teacher-demo-20260716-%';

DELETE FROM `seclab_profile`.`learning_event`
WHERE `event_id` LIKE 'teacher-demo-20260716-%';

DELETE FROM `seclab_profile`.`training_session`
WHERE `training_session_id` LIKE 'teacher-demo-20260716-%';

DELETE tsa
FROM `seclab_profile`.`teacher_student_analysis` tsa
INNER JOIN `userservice`.`user` u ON u.`user_id` = tsa.`student_id`
WHERE tsa.`teaching_class_id` = @teaching_class_id
  AND u.`user_student_number` BETWEEN '202321040501' AND '202321040630';

DELETE tcs
FROM `userservice`.`teaching_class_student` tcs
INNER JOIN `userservice`.`user` u ON u.`user_id` = tcs.`student_id`
WHERE tcs.`teaching_class_id` = @teaching_class_id
  AND u.`user_student_number` BETWEEN '202321040501' AND '202321040630';

DELETE FROM `userservice`.`user`
WHERE `user_student_number` BETWEEN '202321040501' AND '202321040630';

INSERT INTO `userservice`.`user` (
  `user_student_number`, `user_password`, `user_name`, `user_gender`,
  `user_academy`, `user_email`, `class_id_class_id`,
  `is_admin`, `user_role`, `is_deleted`
) VALUES
  ('202321040501', 'e10adc3949ba59abbe56e057f20f883e', '陈宇航', 1, '网络空间安全学院', '202321040501@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040502', 'e10adc3949ba59abbe56e057f20f883e', '周雨桐', 0, '网络空间安全学院', '202321040502@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040503', 'e10adc3949ba59abbe56e057f20f883e', '王子睿', 1, '网络空间安全学院', '202321040503@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040504', 'e10adc3949ba59abbe56e057f20f883e', '林佳宁', 0, '网络空间安全学院', '202321040504@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040505', 'e10adc3949ba59abbe56e057f20f883e', '张博文', 1, '网络空间安全学院', '202321040505@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040506', 'e10adc3949ba59abbe56e057f20f883e', '吴思琪', 0, '网络空间安全学院', '202321040506@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040507', 'e10adc3949ba59abbe56e057f20f883e', '郑凯', 1, '网络空间安全学院', '202321040507@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040508', 'e10adc3949ba59abbe56e057f20f883e', '赵欣怡', 0, '网络空间安全学院', '202321040508@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040509', 'e10adc3949ba59abbe56e057f20f883e', '刘子涵', 0, '网络空间安全学院', '202321040509@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040510', 'e10adc3949ba59abbe56e057f20f883e', '孙浩然', 1, '网络空间安全学院', '202321040510@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040511', 'e10adc3949ba59abbe56e057f20f883e', '李沐阳', 1, '网络空间安全学院', '202321040511@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040512', 'e10adc3949ba59abbe56e057f20f883e', '黄诗涵', 0, '网络空间安全学院', '202321040512@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040513', 'e10adc3949ba59abbe56e057f20f883e', '徐嘉诚', 1, '网络空间安全学院', '202321040513@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040514', 'e10adc3949ba59abbe56e057f20f883e', '何雨欣', 0, '网络空间安全学院', '202321040514@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040515', 'e10adc3949ba59abbe56e057f20f883e', '高梓轩', 1, '网络空间安全学院', '202321040515@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040516', 'e10adc3949ba59abbe56e057f20f883e', '罗梦琪', 0, '网络空间安全学院', '202321040516@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040517', 'e10adc3949ba59abbe56e057f20f883e', '唐俊杰', 1, '网络空间安全学院', '202321040517@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040518', 'e10adc3949ba59abbe56e057f20f883e', '梁若曦', 0, '网络空间安全学院', '202321040518@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040519', 'e10adc3949ba59abbe56e057f20f883e', '宋承泽', 1, '网络空间安全学院', '202321040519@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040520', 'e10adc3949ba59abbe56e057f20f883e', '马依诺', 0, '网络空间安全学院', '202321040520@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040521', 'e10adc3949ba59abbe56e057f20f883e', '胡俊熙', 1, '网络空间安全学院', '202321040521@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040522', 'e10adc3949ba59abbe56e057f20f883e', '郭语彤', 0, '网络空间安全学院', '202321040522@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040523', 'e10adc3949ba59abbe56e057f20f883e', '袁浩宇', 1, '网络空间安全学院', '202321040523@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040524', 'e10adc3949ba59abbe56e057f20f883e', '邓婉清', 0, '网络空间安全学院', '202321040524@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040525', 'e10adc3949ba59abbe56e057f20f883e', '许泽宇', 1, '网络空间安全学院', '202321040525@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040526', 'e10adc3949ba59abbe56e057f20f883e', '曹心怡', 0, '网络空间安全学院', '202321040526@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040527', 'e10adc3949ba59abbe56e057f20f883e', '彭奕辰', 1, '网络空间安全学院', '202321040527@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040528', 'e10adc3949ba59abbe56e057f20f883e', '曾可欣', 0, '网络空间安全学院', '202321040528@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040529', 'e10adc3949ba59abbe56e057f20f883e', '萧景程', 1, '网络空间安全学院', '202321040529@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040530', 'e10adc3949ba59abbe56e057f20f883e', '程悦然', 0, '网络空间安全学院', '202321040530@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040531', 'e10adc3949ba59abbe56e057f20f883e', '沈嘉乐', 1, '网络空间安全学院', '202321040531@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040532', 'e10adc3949ba59abbe56e057f20f883e', '杜若彤', 0, '网络空间安全学院', '202321040532@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040533', 'e10adc3949ba59abbe56e057f20f883e', '陈逸飞', 1, '网络空间安全学院', '202321040533@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040534', 'e10adc3949ba59abbe56e057f20f883e', '李思涵', 0, '网络空间安全学院', '202321040534@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040535', 'e10adc3949ba59abbe56e057f20f883e', '王浩宇', 1, '网络空间安全学院', '202321040535@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040536', 'e10adc3949ba59abbe56e057f20f883e', '张思琪', 0, '网络空间安全学院', '202321040536@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040537', 'e10adc3949ba59abbe56e057f20f883e', '刘宇航', 1, '网络空间安全学院', '202321040537@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040538', 'e10adc3949ba59abbe56e057f20f883e', '陈诗雨', 0, '网络空间安全学院', '202321040538@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040539', 'e10adc3949ba59abbe56e057f20f883e', '周子涵', 1, '网络空间安全学院', '202321040539@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040540', 'e10adc3949ba59abbe56e057f20f883e', '赵可欣', 0, '网络空间安全学院', '202321040540@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040541', 'e10adc3949ba59abbe56e057f20f883e', '黄俊杰', 1, '网络空间安全学院', '202321040541@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040542', 'e10adc3949ba59abbe56e057f20f883e', '林雨萱', 0, '网络空间安全学院', '202321040542@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040543', 'e10adc3949ba59abbe56e057f20f883e', '孙怡然', 1, '网络空间安全学院', '202321040543@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040544', 'e10adc3949ba59abbe56e057f20f883e', '周欣怡', 0, '网络空间安全学院', '202321040544@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040545', 'e10adc3949ba59abbe56e057f20f883e', '徐梓轩', 1, '网络空间安全学院', '202321040545@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040546', 'e10adc3949ba59abbe56e057f20f883e', '吴雨桐', 0, '网络空间安全学院', '202321040546@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040547', 'e10adc3949ba59abbe56e057f20f883e', '郑浩然', 1, '网络空间安全学院', '202321040547@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040548', 'e10adc3949ba59abbe56e057f20f883e', '马诗涵', 0, '网络空间安全学院', '202321040548@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040549', 'e10adc3949ba59abbe56e057f20f883e', '高雨欣', 0, '网络空间安全学院', '202321040549@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040550', 'e10adc3949ba59abbe56e057f20f883e', '罗子轩', 1, '网络空间安全学院', '202321040550@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040551', 'e10adc3949ba59abbe56e057f20f883e', '唐佳怡', 0, '网络空间安全学院', '202321040551@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040552', 'e10adc3949ba59abbe56e057f20f883e', '梁浩宇', 1, '网络空间安全学院', '202321040552@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040553', 'e10adc3949ba59abbe56e057f20f883e', '宋雨桐', 0, '网络空间安全学院', '202321040553@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040554', 'e10adc3949ba59abbe56e057f20f883e', '胡宇航', 1, '网络空间安全学院', '202321040554@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040555', 'e10adc3949ba59abbe56e057f20f883e', '郭佳宁', 0, '网络空间安全学院', '202321040555@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040556', 'e10adc3949ba59abbe56e057f20f883e', '袁思琪', 0, '网络空间安全学院', '202321040556@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040557', 'e10adc3949ba59abbe56e057f20f883e', '邓浩然', 1, '网络空间安全学院', '202321040557@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040558', 'e10adc3949ba59abbe56e057f20f883e', '许诗涵', 0, '网络空间安全学院', '202321040558@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040559', 'e10adc3949ba59abbe56e057f20f883e', '曹宇航', 1, '网络空间安全学院', '202321040559@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040560', 'e10adc3949ba59abbe56e057f20f883e', '彭欣怡', 0, '网络空间安全学院', '202321040560@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040561', 'e10adc3949ba59abbe56e057f20f883e', '曾浩宇', 1, '网络空间安全学院', '202321040561@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040562', 'e10adc3949ba59abbe56e057f20f883e', '萧思琪', 0, '网络空间安全学院', '202321040562@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040563', 'e10adc3949ba59abbe56e057f20f883e', '程宇航', 1, '网络空间安全学院', '202321040563@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040564', 'e10adc3949ba59abbe56e057f20f883e', '沈佳宁', 0, '网络空间安全学院', '202321040564@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040565', 'e10adc3949ba59abbe56e057f20f883e', '杜浩宇', 1, '网络空间安全学院', '202321040565@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040566', 'e10adc3949ba59abbe56e057f20f883e', '张雨涵', 0, '网络空间安全学院', '202321040566@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040567', 'e10adc3949ba59abbe56e057f20f883e', '李梓轩', 1, '网络空间安全学院', '202321040567@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040568', 'e10adc3949ba59abbe56e057f20f883e', '王雨欣', 0, '网络空间安全学院', '202321040568@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040569', 'e10adc3949ba59abbe56e057f20f883e', '刘浩然', 1, '网络空间安全学院', '202321040569@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040570', 'e10adc3949ba59abbe56e057f20f883e', '陈佳怡', 0, '网络空间安全学院', '202321040570@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040571', 'e10adc3949ba59abbe56e057f20f883e', '周浩宇', 1, '网络空间安全学院', '202321040571@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040572', 'e10adc3949ba59abbe56e057f20f883e', '赵诗涵', 0, '网络空间安全学院', '202321040572@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040573', 'e10adc3949ba59abbe56e057f20f883e', '黄宇轩', 1, '网络空间安全学院', '202321040573@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040574', 'e10adc3949ba59abbe56e057f20f883e', '林欣怡', 0, '网络空间安全学院', '202321040574@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040575', 'e10adc3949ba59abbe56e057f20f883e', '孙佳宁', 0, '网络空间安全学院', '202321040575@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040576', 'e10adc3949ba59abbe56e057f20f883e', '郑宇航', 1, '网络空间安全学院', '202321040576@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040577', 'e10adc3949ba59abbe56e057f20f883e', '马思琪', 0, '网络空间安全学院', '202321040577@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040578', 'e10adc3949ba59abbe56e057f20f883e', '高浩然', 1, '网络空间安全学院', '202321040578@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040579', 'e10adc3949ba59abbe56e057f20f883e', '罗雨欣', 0, '网络空间安全学院', '202321040579@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040580', 'e10adc3949ba59abbe56e057f20f883e', '唐奕辰', 1, '网络空间安全学院', '202321040580@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040581', 'e10adc3949ba59abbe56e057f20f883e', '梁诗涵', 0, '网络空间安全学院', '202321040581@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040582', 'e10adc3949ba59abbe56e057f20f883e', '宋浩宇', 1, '网络空间安全学院', '202321040582@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040583', 'e10adc3949ba59abbe56e057f20f883e', '胡佳宁', 0, '网络空间安全学院', '202321040583@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040584', 'e10adc3949ba59abbe56e057f20f883e', '郭雨桐', 0, '网络空间安全学院', '202321040584@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040585', 'e10adc3949ba59abbe56e057f20f883e', '袁子轩', 1, '网络空间安全学院', '202321040585@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040586', 'e10adc3949ba59abbe56e057f20f883e', '邓思琪', 0, '网络空间安全学院', '202321040586@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040587', 'e10adc3949ba59abbe56e057f20f883e', '许浩然', 1, '网络空间安全学院', '202321040587@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040588', 'e10adc3949ba59abbe56e057f20f883e', '曹诗涵', 0, '网络空间安全学院', '202321040588@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040589', 'e10adc3949ba59abbe56e057f20f883e', '彭浩宇', 1, '网络空间安全学院', '202321040589@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040590', 'e10adc3949ba59abbe56e057f20f883e', '曾雨欣', 0, '网络空间安全学院', '202321040590@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040591', 'e10adc3949ba59abbe56e057f20f883e', '萧佳怡', 0, '网络空间安全学院', '202321040591@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040592', 'e10adc3949ba59abbe56e057f20f883e', '程浩宇', 1, '网络空间安全学院', '202321040592@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040593', 'e10adc3949ba59abbe56e057f20f883e', '沈思琪', 0, '网络空间安全学院', '202321040593@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040594', 'e10adc3949ba59abbe56e057f20f883e', '杜雨涵', 0, '网络空间安全学院', '202321040594@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040595', 'e10adc3949ba59abbe56e057f20f883e', '张宇航', 1, '网络空间安全学院', '202321040595@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040596', 'e10adc3949ba59abbe56e057f20f883e', '李雨欣', 0, '网络空间安全学院', '202321040596@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040597', 'e10adc3949ba59abbe56e057f20f883e', '王诗涵', 0, '网络空间安全学院', '202321040597@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040598', 'e10adc3949ba59abbe56e057f20f883e', '刘浩宇', 1, '网络空间安全学院', '202321040598@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040599', 'e10adc3949ba59abbe56e057f20f883e', '陈思琪', 0, '网络空间安全学院', '202321040599@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040600', 'e10adc3949ba59abbe56e057f20f883e', '周佳宁', 0, '网络空间安全学院', '202321040600@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040601', 'e10adc3949ba59abbe56e057f20f883e', '赵浩宇', 1, '网络空间安全学院', '202321040601@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040602', 'e10adc3949ba59abbe56e057f20f883e', '黄宇涵', 0, '网络空间安全学院', '202321040602@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040603', 'e10adc3949ba59abbe56e057f20f883e', '林宇航', 1, '网络空间安全学院', '202321040603@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040604', 'e10adc3949ba59abbe56e057f20f883e', '孙雨欣', 0, '网络空间安全学院', '202321040604@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040605', 'e10adc3949ba59abbe56e057f20f883e', '郑诗涵', 0, '网络空间安全学院', '202321040605@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040606', 'e10adc3949ba59abbe56e057f20f883e', '马浩宇', 1, '网络空间安全学院', '202321040606@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040607', 'e10adc3949ba59abbe56e057f20f883e', '高佳怡', 0, '网络空间安全学院', '202321040607@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040608', 'e10adc3949ba59abbe56e057f20f883e', '罗浩宇', 1, '网络空间安全学院', '202321040608@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040609', 'e10adc3949ba59abbe56e057f20f883e', '唐思琪', 0, '网络空间安全学院', '202321040609@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040610', 'e10adc3949ba59abbe56e057f20f883e', '梁浩宇', 1, '网络空间安全学院', '202321040610@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040611', 'e10adc3949ba59abbe56e057f20f883e', '宋玉涵', 0, '网络空间安全学院', '202321040611@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040612', 'e10adc3949ba59abbe56e057f20f883e', '胡雨涵', 0, '网络空间安全学院', '202321040612@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040613', 'e10adc3949ba59abbe56e057f20f883e', '郭浩宇', 1, '网络空间安全学院', '202321040613@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040614', 'e10adc3949ba59abbe56e057f20f883e', '袁诗涵', 0, '网络空间安全学院', '202321040614@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040615', 'e10adc3949ba59abbe56e057f20f883e', '邓宇航', 1, '网络空间安全学院', '202321040615@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040616', 'e10adc3949ba59abbe56e057f20f883e', '许佳宁', 0, '网络空间安全学院', '202321040616@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040617', 'e10adc3949ba59abbe56e057f20f883e', '曹浩宇', 1, '网络空间安全学院', '202321040617@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040618', 'e10adc3949ba59abbe56e057f20f883e', '彭思琪', 0, '网络空间安全学院', '202321040618@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040619', 'e10adc3949ba59abbe56e057f20f883e', '曾浩然', 1, '网络空间安全学院', '202321040619@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040620', 'e10adc3949ba59abbe56e057f20f883e', '萧雨涵', 0, '网络空间安全学院', '202321040620@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040621', 'e10adc3949ba59abbe56e057f20f883e', '程思琪', 0, '网络空间安全学院', '202321040621@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040622', 'e10adc3949ba59abbe56e057f20f883e', '沈浩宇', 1, '网络空间安全学院', '202321040622@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040623', 'e10adc3949ba59abbe56e057f20f883e', '杜诗涵', 0, '网络空间安全学院', '202321040623@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040624', 'e10adc3949ba59abbe56e057f20f883e', '张佳怡', 0, '网络空间安全学院', '202321040624@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040625', 'e10adc3949ba59abbe56e057f20f883e', '李浩宇', 1, '网络空间安全学院', '202321040625@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040626', 'e10adc3949ba59abbe56e057f20f883e', '王诗涵', 0, '网络空间安全学院', '202321040626@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040627', 'e10adc3949ba59abbe56e057f20f883e', '刘雨涵', 0, '网络空间安全学院', '202321040627@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040628', 'e10adc3949ba59abbe56e057f20f883e', '陈浩然', 1, '网络空间安全学院', '202321040628@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040629', 'e10adc3949ba59abbe56e057f20f883e', '周思琪', 0, '网络空间安全学院', '202321040629@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0),
  ('202321040630', 'e10adc3949ba59abbe56e057f20f883e', '赵佳宁', 0, '网络空间安全学院', '202321040630@stu.seclab.edu.cn', @admin_class_id, b'0', 'STUDENT', 0)
ON DUPLICATE KEY UPDATE
  `user_name` = VALUES(`user_name`),
  `user_gender` = VALUES(`user_gender`),
  `user_academy` = VALUES(`user_academy`),
  `user_email` = VALUES(`user_email`),
  `class_id_class_id` = VALUES(`class_id_class_id`),
  `is_admin` = b'0',
  `user_role` = 'STUDENT',
  `is_deleted` = 0;

INSERT INTO `userservice`.`teaching_class_student`
  (`teaching_class_id`, `student_id`, `source`, `joined_at`)
SELECT @teaching_class_id, u.`user_id`, 'EXCEL_IMPORT', NOW(6) - INTERVAL 30 DAY
FROM `userservice`.`user` u
WHERE u.`user_student_number` BETWEEN '202321040501' AND '202321040630'
ON DUPLICATE KEY UPDATE `source` = VALUES(`source`), `joined_at` = VALUES(`joined_at`);

DELETE FROM `userservice`.`teaching_class_course`
WHERE `teaching_class_id` = @teaching_class_id;

INSERT INTO `userservice`.`teaching_class_course`
  (`teaching_class_id`, `course_id`, `teaching_order`, `planned_start_date`, `planned_end_date`, `created_at`, `updated_at`)
VALUES
  (@teaching_class_id, 1, 1, '2026-09-07', '2026-09-18', NOW(6), NOW(6)),
  (@teaching_class_id, 2, 2, '2026-09-21', '2026-10-09', NOW(6), NOW(6)),
  (@teaching_class_id, 3, 3, '2026-10-12', '2026-10-23', NOW(6), NOW(6)),
  (@teaching_class_id, 4, 4, '2026-10-26', '2026-11-06', NOW(6), NOW(6)),
  (@teaching_class_id, 5, 5, '2026-11-09', '2026-11-20', NOW(6), NOW(6)),
  (@teaching_class_id, 6, 6, '2026-11-23', '2026-12-04', NOW(6), NOW(6)),
  (@teaching_class_id, 7, 7, '2026-12-07', '2026-12-18', NOW(6), NOW(6)),
  (@teaching_class_id, 8, 8, '2026-12-21', '2027-01-08', NOW(6), NOW(6));

DROP TEMPORARY TABLE IF EXISTS `demo_students`;
CREATE TEMPORARY TABLE `demo_students` AS
SELECT
  ROW_NUMBER() OVER (ORDER BY u.`user_student_number`) AS `seq`,
  u.`user_id`,
  u.`user_student_number`,
  u.`user_name`
FROM `userservice`.`user` u
WHERE u.`user_student_number` BETWEEN '202321040501' AND '202321040630';

DROP TEMPORARY TABLE IF EXISTS `demo_question_templates`;
CREATE TEMPORARY TABLE `demo_question_templates` (
  `seq` INT PRIMARY KEY,
  `knowledge_point_id` BIGINT NOT NULL,
  `module_id` BIGINT NOT NULL,
  `task_id` BIGINT NOT NULL,
  `difficulty` VARCHAR(32) NOT NULL,
  `question_type` VARCHAR(64) NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `stem` TEXT NOT NULL,
  `options_json` JSON NULL,
  `standard_answer` TEXT NULL,
  `reference_answer` TEXT NOT NULL,
  `explanation` TEXT NOT NULL
);

INSERT INTO `demo_question_templates` VALUES
  (1, 101, 1, 1, 'medium', 'short_answer', 'UNION 查询列数判断', '在不知道原查询列数时，如何使用 ORDER BY 确定 UNION SELECT 的列数？', NULL, NULL, '从 ORDER BY 1 开始递增，首次报错的序号减一即为原查询列数。', 'ORDER BY 引用的列序号超过结果列数时数据库会报错，可据此确定边界。'),
  (2, 102, 1, 2, 'hard', 'short_answer', '时间盲注基准验证', '使用 IF(condition,SLEEP(3),0) 判断条件前，为什么要先测量正常请求的响应时间？', NULL, NULL, '先取得多次正常请求的响应时间基线，再比较条件成立和不成立时的延迟差异。', '建立基准并重复测量可以降低网络波动造成的误判。'),
  (3, 201, 2, 1, 'medium', 'single_choice', 'HTML 属性上下文编码', '用户输入被放入 HTML 属性值时，最应该采取的防护措施是？', JSON_ARRAY('仅过滤 script 标签', '进行属性上下文编码并限制危险协议', '只设置 HttpOnly Cookie', '删除所有特殊字符'), 'B', '进行属性上下文编码并限制危险协议', '攻击者可用引号结束属性值并注入事件属性，不同输出位置需要不同编码策略。'),
  (4, 301, 2, 2, 'medium', 'single_choice', 'CSRF Token 会话绑定', 'CSRF 令牌最关键的验证要求是？', JSON_ARRAY('令牌必须足够长', '令牌必须与会话绑定并在服务端校验', '令牌必须存储在 LocalStorage', '令牌只在前端生成'), 'B', '令牌必须与会话绑定并在服务端校验', '绑定会话可确认令牌属于当前用户，服务端必须比较请求令牌与会话中的预期值。'),
  (5, 401, 3, 1, 'medium', 'short_answer', '无空格命令执行排查', '当输入中的空格被过滤时，如何从防御角度验证命令是否仍可被拼接执行？', NULL, NULL, '检查 IFS、变量展开和重定向等替代空格方式，并在服务端使用参数化调用和白名单。', '黑名单过滤容易遗漏等价表达，防御应避免把用户输入交给 shell 解析。'),
  (6, 402, 3, 2, 'hard', 'short_answer', '命令黑名单绕过原因', '为什么仅屏蔽分号和常见命令名称不足以防止命令注入？', NULL, NULL, 'shell 还支持管道、换行、变量展开和编码拼接，应改用无 shell 的安全 API。', '枚举危险字符无法覆盖全部语法，根本措施是隔离数据与命令结构。'),
  (7, 501, 4, 1, 'medium', 'single_choice', '上传文件类型校验', '防止恶意文件上传最有效的后端措施是？', JSON_ARRAY('仅检查 Content-Type', '校验文件内容特征并重命名文件', '只检查文件扩展名', '限制文件大小'), 'B', '校验文件内容特征并重命名文件', 'Content-Type 可伪造，客户端元数据不可信，需要内容校验与安全存储共同控制。'),
  (8, 601, 5, 1, 'medium', 'short_answer', '目录遍历路径归一化', '校验用户路径前为什么要先进行 URL 解码和路径归一化？', NULL, NULL, '编码和重复分隔符可能掩盖 ../，应先解码归一化，再确认最终路径位于允许目录。', '在原始字符串上做黑名单检查会漏掉等价路径表达。');

INSERT INTO `seclab_profile`.`training_session` (
  `training_session_id`, `user_id`, `class_id`, `course_id`, `source_type`,
  `diagnose_result_json`, `training_context_json`, `created_at`
)
SELECT
  CONCAT('teacher-demo-20260716-ts-', s.`user_student_number`),
  s.`user_id`, @teaching_class_id,
  CASE WHEN MOD(s.`seq`, 8) = 0 THEN 8 ELSE MOD(s.`seq`, 8) END,
  'personalized_training',
  JSON_OBJECT('weakKnowledgePoints', JSON_ARRAY(101 + MOD(s.`seq` - 1, 8))),
  JSON_OBJECT('source', 'student_profile', 'teachingClassId', @teaching_class_id),
  NOW(6) - INTERVAL (131 - s.`seq`) HOUR
FROM `demo_students` s;

INSERT INTO `seclab_profile`.`generated_question` (
  `generated_question_id`, `question_numeric_id`, `training_session_id`, `question_type`,
  `knowledge_point_id`, `module_id`, `task_id`, `difficulty`, `title`, `stem`,
  `options_json`, `standard_answer`, `reference_answer`, `explanation`,
  `source_model`, `raw_ai_json`, `created_at`
)
SELECT
  CONCAT('teacher-demo-20260716-q-', LPAD(s.`seq`, 3, '0')),
  89000000 + s.`seq`,
  CONCAT('teacher-demo-20260716-ts-', s.`user_student_number`),
  t.`question_type`, t.`knowledge_point_id`, t.`module_id`, t.`task_id`, t.`difficulty`,
  t.`title`, t.`stem`, t.`options_json`, t.`standard_answer`, t.`reference_answer`, t.`explanation`,
  'dify', JSON_OBJECT('generationReason', '根据该生最近一次实验中的具体错误生成'),
  NOW(6) - INTERVAL (132 - s.`seq`) HOUR
FROM `demo_students` s
INNER JOIN `demo_question_templates` t ON t.`seq` = MOD(s.`seq` - 1, 8) + 1;

INSERT INTO `seclab_profile`.`generated_question` (
  `generated_question_id`, `question_numeric_id`, `training_session_id`, `question_type`,
  `knowledge_point_id`, `module_id`, `task_id`, `difficulty`, `title`, `stem`,
  `options_json`, `standard_answer`, `reference_answer`, `explanation`,
  `source_model`, `raw_ai_json`, `created_at`
)
SELECT
  CONCAT('teacher-demo-20260716-q-', LPAD(130 + s.`seq`, 3, '0')),
  89000130 + s.`seq`,
  CONCAT('teacher-demo-20260716-ts-', s.`user_student_number`),
  t.`question_type`, t.`knowledge_point_id`, t.`module_id`, t.`task_id`, t.`difficulty`,
  CONCAT(t.`title`, '（巩固）'), CONCAT('结合实验现象说明：', t.`stem`),
  t.`options_json`, t.`standard_answer`, t.`reference_answer`, t.`explanation`,
  'dify', JSON_OBJECT('generationReason', '针对首次作答暴露的问题生成巩固题'),
  NOW(6) - INTERVAL (100 - s.`seq`) HOUR
FROM `demo_students` s
INNER JOIN `demo_question_templates` t ON t.`seq` = MOD(s.`seq` + 2, 8) + 1
WHERE s.`seq` <= 40;

INSERT INTO `seclab_profile`.`generated_question_attempt` (
  `attempt_id`, `training_session_id`, `generated_question_id`, `user_id`,
  `answer_json`, `is_correct`, `score`, `cost_time`, `submitted_at`
)
SELECT
  REPLACE(gq.`generated_question_id`, '-q-', '-attempt-'),
  gq.`training_session_id`, gq.`generated_question_id`, ts.`user_id`,
  CASE WHEN gq.`question_type` = 'single_choice'
    THEN JSON_QUOTE(CASE WHEN MOD(gq.`question_numeric_id`, 5) IN (0, 1, 3) THEN gq.`standard_answer` ELSE 'A' END)
    ELSE JSON_QUOTE(CASE WHEN MOD(gq.`question_numeric_id`, 5) IN (0, 1, 3)
      THEN gq.`reference_answer`
      ELSE '只写出了部分步骤，缺少验证依据。' END) END,
  CASE WHEN MOD(gq.`question_numeric_id`, 5) IN (0, 1, 3) THEN 1 ELSE 0 END,
  CASE WHEN MOD(gq.`question_numeric_id`, 5) IN (0, 1, 3)
    THEN 88 + MOD(gq.`question_numeric_id`, 12)
    ELSE 45 + MOD(gq.`question_numeric_id`, 30) END,
  30 + MOD(gq.`question_numeric_id`, 200),
  gq.`created_at` + INTERVAL 15 MINUTE
FROM `seclab_profile`.`generated_question` gq
INNER JOIN `seclab_profile`.`training_session` ts
  ON ts.`training_session_id` = gq.`training_session_id`
WHERE gq.`generated_question_id` LIKE 'teacher-demo-20260716-q-%';

INSERT INTO `seclab_profile`.`learning_event` (
  `event_id`, `user_id`, `class_id`, `course_id`, `module_id`, `task_id`,
  `event_type`, `event_time`, `payload_json`, `source`
)
SELECT
  CONCAT('teacher-demo-20260716-event-lab-', LPAD(s.`seq`, 3, '0')),
  s.`user_id`, @teaching_class_id,
  CASE WHEN MOD(s.`seq`, 8) = 0 THEN 8 ELSE MOD(s.`seq`, 8) END,
  MOD(s.`seq` - 1, 6) + 1, 1, 'LAB_COMPLETE',
  NOW(6) - INTERVAL (135 - s.`seq`) HOUR,
  JSON_OBJECT('summary', '完成本周安全实验并提交实验结果'), 'student-web'
FROM `demo_students` s;

INSERT INTO `seclab_profile`.`learning_event` (
  `event_id`, `user_id`, `class_id`, `course_id`, `module_id`, `task_id`,
  `event_type`, `event_time`, `payload_json`, `source`
)
SELECT
  CONCAT('teacher-demo-20260716-event-review-', LPAD(s.`seq`, 3, '0')),
  s.`user_id`, @teaching_class_id,
  CASE WHEN MOD(s.`seq`, 8) = 0 THEN 8 ELSE MOD(s.`seq`, 8) END,
  MOD(s.`seq` - 1, 6) + 1, 1,
  CASE WHEN MOD(s.`seq`, 3) = 0 THEN 'HINT_REQUEST'
       WHEN MOD(s.`seq`, 4) = 0 THEN 'CHALLENGE_COMPLETE'
       ELSE 'AI_INTERACTION' END,
  NOW(6) - INTERVAL (133 - s.`seq`) HOUR,
  JSON_OBJECT('summary', '根据实验错误请求针对性练习并完成复盘'), 'student-web'
FROM `demo_students` s;

INSERT INTO `seclab_profile`.`learning_event` (
  `event_id`, `user_id`, `class_id`, `course_id`, `module_id`, `task_id`,
  `event_type`, `event_time`, `payload_json`, `source`
)
SELECT
  CONCAT('teacher-demo-20260716-event-flag-', LPAD(s.`seq`, 3, '0')),
  s.`user_id`, @teaching_class_id,
  CASE WHEN MOD(s.`seq`, 8) = 0 THEN 8 ELSE MOD(s.`seq`, 8) END,
  MOD(s.`seq` - 1, 6) + 1, 1,
  CASE WHEN MOD(s.`seq`, 7) = 0 THEN 'FLAG_SUBMIT_FAILED' ELSE 'FLAG_SUBMIT_SUCCESS' END,
  NOW(6) - INTERVAL (130 - s.`seq`) HOUR,
  CASE WHEN MOD(s.`seq`, 7) = 0 THEN JSON_OBJECT('summary', '提交的flag未通过验证')
       ELSE JSON_OBJECT('summary', '成功提交实验flag') END, 'student-web'
FROM `demo_students` s;

INSERT INTO `seclab_profile`.`teacher_class_analysis` (
  `teaching_class_id`, `requested_by`, `analysis_status`, `data_cutoff_at`,
  `analysis_json`, `source_stats_json`, `last_attempt_at`,
  `last_error_message`, `generated_at`
) VALUES (
  @teaching_class_id, @teacher_id, 'READY', NOW(6),
  JSON_OBJECT(
    'overallComment', '本班130名学生整体表现良好，对基础Web漏洞原理已有基本认识。但在判断输入进入的具体上下文、根据报错调整验证步骤方面仍有明显共性问题。约42%的学生在生成题作答中存在不同程度的理解偏差，建议下一次课先用三道典型错误题目作对比讲解，再安排短时排错练习。',
    'commonProblems', JSON_ARRAY(
      JSON_OBJECT(
        'title', 'XSS 输出上下文判断不稳定',
        'studentCount', 38,
        'evidence', '38名学生生成了相关题目，近期作答中有31次错误，主要混淆HTML文本、属性与脚本上下文。',
        'teacherAction', '课堂上并列展示文本、属性和脚本三种输出位置，让学生先标注上下文再选择编码方式。',
        'questionIds', JSON_ARRAY('teacher-demo-20260716-q-003', 'teacher-demo-20260716-q-011')
      ),
      JSON_OBJECT(
        'title', '盲注验证步骤缺少基准对照',
        'studentCount', 29,
        'evidence', '29名学生的生成题集中在条件构造，常见问题是直接加入延时语句，没有先确认真假分支差异。',
        'teacherAction', '先演示恒真、恒假两个基准请求，再让学生补全延时条件和判断依据。',
        'questionIds', JSON_ARRAY('teacher-demo-20260716-q-002', 'teacher-demo-20260716-q-010')
      ),
      JSON_OBJECT(
        'title', '命令注入过滤策略理解片面',
        'studentCount', 24,
        'evidence', '24名学生在命令注入相关题目中仅关注了黑名单字符，忽略了管道、变量展开等绕过方式。',
        'teacherAction', '对比展示黑名单过滤的局限性，引入无shell执行的安全API概念。',
        'questionIds', JSON_ARRAY('teacher-demo-20260716-q-005', 'teacher-demo-20260716-q-013')
      )
    )
  ),
  JSON_OBJECT('studentCount', 130, 'generatedQuestionCount', 170, 'incorrectCount', 71),
  NOW(6), NULL, NOW(6)
)
ON DUPLICATE KEY UPDATE
  `requested_by` = VALUES(`requested_by`),
  `analysis_status` = 'READY',
  `data_cutoff_at` = VALUES(`data_cutoff_at`),
  `analysis_json` = VALUES(`analysis_json`),
  `source_stats_json` = VALUES(`source_stats_json`),
  `last_attempt_at` = VALUES(`last_attempt_at`),
  `last_error_message` = NULL,
  `generated_at` = VALUES(`generated_at`);

INSERT INTO `seclab_profile`.`teacher_student_analysis` (
  `teacher_id`, `teaching_class_id`, `student_id`, `analysis_status`,
  `data_cutoff_at`, `analysis_json`, `source_stats_json`, `last_attempt_at`,
  `last_error_message`, `generated_at`
)
SELECT
  @teacher_id, @teaching_class_id, s.`user_id`, 'READY', NOW(6),
  JSON_OBJECT(
    'studentName', s.`user_name`,
    'weakKnowledgePoints', JSON_ARRAY(101 + MOD(s.`seq` - 1, 8)),
    'recommendedActions', JSON_ARRAY(
      '针对薄弱知识点补充练习',
      '复习相关实验操作流程',
      '完成巩固性训练题目'
    ),
    'overallAssessment', CASE WHEN MOD(s.`seq`, 5) IN (0, 1) THEN '优秀'
                              WHEN MOD(s.`seq`, 5) IN (2, 3) THEN '良好'
                              ELSE '需关注' END
  ),
  JSON_OBJECT('questionCount', 1 + CASE WHEN s.`seq` <= 40 THEN 1 ELSE 0 END,
              'correctCount', CASE WHEN MOD(s.`seq`, 5) IN (0, 1, 3) THEN 1 + CASE WHEN s.`seq` <= 40 THEN 1 ELSE 0 END ELSE 0 END),
  NOW(6), NULL, NOW(6)
FROM `demo_students` s
WHERE s.`seq` <= 30;

DROP TEMPORARY TABLE IF EXISTS `demo_question_templates`;
DROP TEMPORARY TABLE IF EXISTS `demo_students`;

SELECT
  130 AS expected_students,
  COUNT(DISTINCT u.`user_id`) AS actual_students
FROM `userservice`.`user` u
WHERE u.`user_student_number` BETWEEN '202321040501' AND '202321040630';

SELECT
  170 AS expected_questions,
  COUNT(*) AS actual_questions
FROM `seclab_profile`.`generated_question` gq
WHERE gq.`generated_question_id` LIKE 'teacher-demo-20260716-q-%';

SELECT
  170 AS expected_attempts,
  COUNT(*) AS actual_attempts,
  SUM(CASE WHEN `is_correct` = 1 THEN 1 ELSE 0 END) AS correct_attempts,
  SUM(CASE WHEN `is_correct` = 0 THEN 1 ELSE 0 END) AS incorrect_attempts
FROM `seclab_profile`.`generated_question_attempt`
WHERE `attempt_id` LIKE 'teacher-demo-20260716-%';

SELECT
  390 AS expected_events,
  COUNT(*) AS actual_events
FROM `seclab_profile`.`learning_event`
WHERE `event_id` LIKE 'teacher-demo-20260716-%';

SELECT
  30 AS expected_student_analyses,
  COUNT(*) AS actual_student_analyses
FROM `seclab_profile`.`teacher_student_analysis` tsa
WHERE tsa.`teaching_class_id` = @teaching_class_id;

COMMIT;