#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# SecLab MySQL 数据库引导脚本
# 创建数据库、用户、导入表结构和种子数据。
# 可重复执行（所有 SQL 使用 CREATE TABLE IF NOT EXISTS / INSERT ... WHERE NOT EXISTS）。
#
# 用法：
#   bash deploy/scripts/bootstrap-mysql.sh
#
# 可选环境变量：
#   PROJECT_DIR=/opt/seclab/SecLab
#   MYSQL_CONTAINER=seclab-mysql
#   MYSQL_ROOT_PASSWORD=han0.521
#   MYSQL_APP_USER=seclab_app
#   MYSQL_APP_PASSWORD=Seclab@123
# ════════════════════════════════════════════════════════════════
set -euo pipefail

# ── 颜色输出 ──────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
step()  { echo -e "\n${CYAN}━━━ $* ━━━${NC}"; }

PROJECT_DIR="${PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
MYSQL_CONTAINER="${MYSQL_CONTAINER:-seclab-mysql}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-han0.521}"
MYSQL_APP_USER="${MYSQL_APP_USER:-seclab_app}"
MYSQL_APP_PASSWORD="${MYSQL_APP_PASSWORD:-Seclab@123}"
MYSQL_DATA_DIR="${MYSQL_DATA_DIR:-/opt/seclab/data/mysql}"

info "项目目录: $PROJECT_DIR"
info "MySQL 容器: $MYSQL_CONTAINER"

# ── 1. 启动 MySQL 容器 ────────────────────────────────────────
step "1/5 启动 MySQL 容器"

mkdir -p "$MYSQL_DATA_DIR"

if ! docker ps -a --format '{{.Names}}' | grep -qx "$MYSQL_CONTAINER"; then
    info "创建 MySQL 8.0 容器..."
    # 2GB 云服务器内存优化：限制容器内存 + 收紧 InnoDB/连接/performance_schema
    docker run -d --name "$MYSQL_CONTAINER" \
        --restart unless-stopped \
        --memory=512m \
        -p 127.0.0.1:3306:3306 \
        -v "$MYSQL_DATA_DIR:/var/lib/mysql" \
        -e MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD" \
        -e MYSQL_DATABASE=userservice \
        -e MYSQL_USER="$MYSQL_APP_USER" \
        -e MYSQL_PASSWORD="$MYSQL_APP_PASSWORD" \
        -e MYSQL_CHARACTER_SET_SERVER=utf8mb4 \
        -e MYSQL_COLLATION_SERVER=utf8mb4_unicode_ci \
        mysql:8.0 \
        --default-authentication-plugin=mysql_native_password \
        --innodb-buffer-pool-size=256M \
        --max-connections=50 \
        --performance-schema=OFF \
        --skip-name-resolve
else
    info "MySQL 容器已存在，启动中..."
    docker start "$MYSQL_CONTAINER" >/dev/null
fi

info "等待 MySQL 就绪（最多 120 秒）..."
for i in $(seq 1 60); do
    if docker exec "$MYSQL_CONTAINER" mysqladmin ping -uroot -p"$MYSQL_ROOT_PASSWORD" --silent >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} MySQL 已就绪"
        break
    fi
    if [[ $i -eq 60 ]]; then
        echo -e "  ${RED}✗${NC} MySQL 启动超时"
        exit 1
    fi
    sleep 2
done

# ── MySQL 命令封装 ────────────────────────────────────────────
mysql_root() {
    docker exec -i "$MYSQL_CONTAINER" mysql -uroot -p"$MYSQL_ROOT_PASSWORD" --default-character-set=utf8mb4 "$@"
}

# ── 2. 创建数据库和用户 ───────────────────────────────────────
step "2/5 创建数据库和用户"

mysql_root <<SQL
CREATE DATABASE IF NOT EXISTS userservice
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS seclab_profile
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS imagedb
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS seclab_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS '${MYSQL_APP_USER}'@'%' IDENTIFIED BY '${MYSQL_APP_PASSWORD}';
GRANT ALL PRIVILEGES ON userservice.*    TO '${MYSQL_APP_USER}'@'%';
GRANT ALL PRIVILEGES ON seclab_profile.* TO '${MYSQL_APP_USER}'@'%';
GRANT ALL PRIVILEGES ON imagedb.*        TO '${MYSQL_APP_USER}'@'%';
GRANT ALL PRIVILEGES ON seclab_db.*      TO '${MYSQL_APP_USER}'@'%';
GRANT CREATE, DROP ON *.* TO '${MYSQL_APP_USER}'@'%';
FLUSH PRIVILEGES;
SQL
echo -e "  ${GREEN}✓${NC} 数据库和用户已创建"

# ── 3. 导入表结构 ─────────────────────────────────────────────
step "3/5 导入表结构"

import_sql() {
    local file="$1"
    local db="${2:-}"
    local ignore_dups="${3:-}"
    if [[ -f "$file" ]]; then
        info "导入 $file"
        # 导入期禁用外键检查：user-service-local-init.sql 的 teaching_class_course
        # 引用 course 表（由 experiment-module-service-local-init.sql 创建），存在跨文件
        # 循环外键依赖，需放开 FK 检查才能按任意顺序导入。
        local content
        if [[ -n "$ignore_dups" ]]; then
            # INSERT IGNORE 容忍主键冲突：补充 seed 与 experiment-module init 在
            # course/module 的 id 1-3 上冲突（不同课程名），IGNORE 保留先导入的实验课程。
            content=$(sed 's/INSERT INTO/INSERT IGNORE INTO/g' "$file")
        else
            content=$(cat "$file")
        fi
        if [[ -n "$db" ]]; then
            { echo "SET FOREIGN_KEY_CHECKS=0;"; printf '%s\n' "$content"; echo "SET FOREIGN_KEY_CHECKS=1;"; } | mysql_root "$db"
        else
            { echo "SET FOREIGN_KEY_CHECKS=0;"; printf '%s\n' "$content"; echo "SET FOREIGN_KEY_CHECKS=1;"; } | mysql_root
        fi
    else
        warn "SQL 文件不存在，跳过: $file"
    fi
}

# 3.1 userservice 库：用户、班级、课程、模块基础表 + 教师账号 T20260001
import_sql "$PROJECT_DIR/database/sql/user-service-local-init.sql"

# 3.2 补充 admin 管理员账号（user_id 通常为 1，user_role=TEACHER 才能访问教师端）
info "确保 admin 管理员账号存在..."
mysql_root userservice <<'SQL'
-- 确保 admin 账号存在：学号 admin / 密码 123456 (MD5: e10adc3949ba59abbe56e057f20f883e)
INSERT INTO `user` (
  `user_student_number`, `user_password`, `user_name`, `user_gender`,
  `user_academy`, `user_email`, `class_id_class_id`,
  `is_admin`, `user_role`, `is_deleted`
)
SELECT
  'admin',
  'e10adc3949ba59abbe56e057f20f883e',
  'Administrator',
  1,
  '网络安全学院',
  'admin@seclab.edu.cn',
  (SELECT `class_id` FROM `class` ORDER BY `class_id` LIMIT 1),
  b'1',
  'TEACHER',
  0
WHERE NOT EXISTS (
  SELECT 1 FROM `user` WHERE `user_student_number` = 'admin'
);

-- 确保 admin 的 user_role 为 TEACHER（允许访问教师端）
UPDATE `user` SET `user_role` = 'TEACHER' WHERE `user_student_number` = 'admin';
SQL
echo -e "  ${GREEN}✓${NC} admin 账号已就绪（admin / 123456）"

# 3.3 experiment-module-service 表结构（course/module/module_course）
#     必须在 created_by 检查之前导入：course 表由本文件创建（已含 created_by 列）。
import_sql "$PROJECT_DIR/database/sql/experiment-module-service-local-init.sql"

# 3.4 给 course 表补 created_by 列（experiment-module-service 的 CourseEntity 需要此列）
info "检查 course 表 created_by 列..."
mysql_root userservice <<'SQL'
SET @sql := IF(
  EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'userservice'
      AND table_name = 'course'
      AND column_name = 'created_by'
  ),
  'SELECT 1',
  'ALTER TABLE `course` ADD COLUMN `created_by` BIGINT NULL AFTER `course_status`'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 补外键和索引（可重复执行，用 information_schema 防御）
SET @sql := IF(
  EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE table_schema = 'userservice'
      AND table_name = 'course'
      AND constraint_name = 'fk_course_creator'
  ),
  'SELECT 1',
  'ALTER TABLE `course` ADD CONSTRAINT `fk_course_creator` FOREIGN KEY (`created_by`) REFERENCES `user`(`user_id`)'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := IF(
  EXISTS (
    SELECT 1 FROM information_schema.statistics
    WHERE table_schema = 'userservice'
      AND table_name = 'course'
      AND index_name = 'idx_course_creator_status'
  ),
  'SELECT 1',
  'ALTER TABLE `course` ADD INDEX `idx_course_creator_status` (`created_by`, `course_status`)'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
SQL
echo -e "  ${GREEN}✓${NC} course 表 created_by 列已检查"

# 3.4 seclab_profile 库：事件、画像、AI 会话、教师分析表
import_sql "$PROJECT_DIR/database/sql/init_seclab_profile.sql"

# 3.5 教师工作台表（teaching_class 等，跨 userservice 和 seclab_profile）
import_sql "$PROJECT_DIR/database/sql/teacher_teaching_class.sql"

# 3.6 教师分析补充表
import_sql "$PROJECT_DIR/database/sql/teacher_course_analysis.sql"
import_sql "$PROJECT_DIR/database/sql/teacher_intervention.sql"
import_sql "$PROJECT_DIR/database/sql/teacher_knowledge_analysis.sql"

# ── 4. 导入种子数据 ───────────────────────────────────────────
step "4/5 导入种子数据"

# 4.1 教师端展示数据（32 名学生、40 道生成题、班级分析）
#     此脚本依赖 admin 账号 user_id=1 和 class_id=3
#     传入 seclab_profile 作默认库：文件含多表 DELETE（DELETE alias FROM db.tbl alias JOIN ...），
#     MySQL 该语法即使全限定表名也要求有默认数据库。
import_sql "$PROJECT_DIR/database/sql/seed_teacher_showcase.sql" seclab_profile

# 4.2 引导提示历史表（如 init_seclab_profile.sql 未包含）
import_sql "$PROJECT_DIR/shujuku/guidance_proactive_notes.sql" seclab_profile

# 4.3 课程和模块种子数据（来自前端映射的原始数据，自带 USE userservice）
#     用 INSERT IGNORE：与 experiment-module init 的 course/module id 1-3 冲突时保留实验课程
import_sql "$PROJECT_DIR/shujuku/userservice_course_seed_from_frontend.sql" userservice ignore_dups
import_sql "$PROJECT_DIR/shujuku/userservice_module_seed_from_frontend.sql" userservice ignore_dups

# ── 5. 验证 ───────────────────────────────────────────────────
step "5/5 验证数据"

echo ""
info "userservice.user 表记录数:"
mysql_root userservice -e "SELECT COUNT(*) AS user_count FROM \`user\`;" 2>/dev/null

echo ""
info "admin 账号信息:"
mysql_root userservice -e "SELECT user_id, user_student_number, user_name, user_role, is_admin FROM \`user\` WHERE user_student_number IN ('admin', 'T20260001') ORDER BY user_id;" 2>/dev/null

echo ""
info "userservice.course 表结构（created_by 列）:"
mysql_root userservice -e "SHOW COLUMNS FROM \`course\` LIKE 'created_by';" 2>/dev/null

echo ""
info "seclab_profile 主要表记录数:"
mysql_root seclab_profile -e "
  SELECT 'learning_event' AS tbl, COUNT(*) AS cnt FROM learning_event
  UNION ALL SELECT 'teacher_class_analysis', COUNT(*) FROM teacher_class_analysis
  UNION ALL SELECT 'teacher_typical_question', COUNT(*) FROM teacher_typical_question;
" 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  MySQL 数据库引导完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "管理员账号: admin / 123456"
echo "教师账号:   T20260001 / 123456"
echo ""
echo "连接数据库:"
echo "  docker exec -it $MYSQL_CONTAINER mysql -uroot -p$MYSQL_ROOT_PASSWORD"
echo ""
