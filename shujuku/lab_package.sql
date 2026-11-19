-- lab_package：教师上传的实验包（zip）登记表
-- 用途：记录教师通过"创建课程"或独立入口上传的实验容器 zip 包元数据。
-- 本期范围：仅上传 + 元数据登记，不触发 docker build / 启动。
-- status 取值：UPLOADED（已上传，本期固定）/ BUILT（已构建，后续迭代）/ REGISTERED（已注册到白名单，后续迭代）
-- 关联：module_id 关联 module.module_id，教师上传时可选择同时创建 module 并绑定，
--       删除 module 时本表 module_id 由 ON DELETE SET NULL 置空，但 lab_package 记录保留以备追溯。

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
