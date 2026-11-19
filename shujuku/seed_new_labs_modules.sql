-- 补建学生端新增的四个二进制 / 协议分析实验模块（module 15-18）
-- 对应前端 src/data/ 下的 StackOverflowExperiment / ProtocolAnalysisExperiment
--   / HeapOverflowExperiment / FormatStringExperiment，id 与 AllExperiments 严格对齐。
-- 用途：让教师端课程库的"实验池"能看到这四个新实验，并加入课程。
-- 幂等：ON DUPLICATE KEY UPDATE，可重复执行。

USE `userservice`;

INSERT INTO `module`
  (`module_id`, `difficulty`, `image_id`, `introduction`, `module_name`, `type`)
VALUES
  (15, 3, NULL,
   '从零理解并实践栈溢出：编写含后门的漏洞程序，用 pwndbg 定位溢出点，再用 pwntools 编写 exp 劫持返回地址，拿到 shell 并读取 flag。',
   '栈溢出实验',
   '["栈溢出","PWN","二进制安全"]'),
  (16, 3, NULL,
   '使用 Wireshark 抓取并解析 HTTP、TCP、UDP 等常见协议，理解报文结构、三次握手与四次挥手，通过抓包分析明文传输风险并获取 flag。',
   '协议分析实验',
   '["协议分析","Wireshark","网络安全"]'),
  (17, 5, NULL,
   '深入 glibc 堆管理机制，理解 chunk 结构与 fastbin/smallbin 组织，掌握 unlink 与 fastbin attack 两大经典手法，编写 exp 完成任意地址写与控制流劫持。',
   '堆溢出实验',
   '["堆溢出","PWN","二进制安全"]'),
  (18, 4, NULL,
   '理解 printf 变参机制与格式化字符串漏洞成因，用 %x/%p 泄露栈数据、%s 读取任意地址、%n 任意地址写入，结合 GOT 劫持拿 shell 读 flag。',
   '格式化字符串实验',
   '["格式化字符串","PWN","二进制安全"]')
ON DUPLICATE KEY UPDATE
  `difficulty` = VALUES(`difficulty`),
  `introduction` = VALUES(`introduction`),
  `module_name` = VALUES(`module_name`),
  `type` = VALUES(`type`);

-- 验证
SELECT module_id, module_name, difficulty FROM `module` WHERE module_id IN (15,16,17,18) ORDER BY module_id;
