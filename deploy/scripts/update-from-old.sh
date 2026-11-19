#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# SecLab 旧版 → 最新版 升级脚本
#
# 前提条件：
#   1. 新版代码已打包为 tar.gz 并上传到服务器（如 /tmp/SecLab-deploy.tar.gz）
#   2. 旧版部署在 /opt/seclab/SecLab（或通过 OLD_PROJECT_DIR 指定）
#   3. MySQL 数据在 Docker 卷中（/opt/seclab/data/mysql），不会被删除
#
# 安全保证：
#   - MySQL 数据卷不动，只做 mysqldump 备份
#   - 旧代码目录重命名为 .old，可随时回滚
#   - .env 配置文件自动迁移到新代码
#   - bootstrap-mysql.sh 幂等执行，只补缺不删数据
#
# 用法：
#   # 1. 先上传新代码包到服务器
#   #    scp SecLab-deploy.tar.gz user@server:/tmp/
#   #
#   # 2. 在服务器上执行升级
#   bash update-from-old.sh /tmp/SecLab-deploy.tar.gz
#
# 可选环境变量：
#   OLD_PROJECT_DIR=/opt/seclab/SecLab     旧代码路径
#   MYSQL_ROOT_PASSWORD=han0.521           MySQL root 密码
#   BACKUP_DIR=/opt/seclab/backup          备份目录
# ════════════════════════════════════════════════════════════════
set -euo pipefail

# ── 颜色 ──────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }
step()  { echo -e "\n${CYAN}━━━ $* ━━━${NC}"; }

# ── 参数解析 ──────────────────────────────────────────────────
NEW_TAR="${1:-/tmp/SecLab-deploy.tar.gz}"
OLD_PROJECT_DIR="${OLD_PROJECT_DIR:-/opt/seclab/SecLab}"
MYSQL_CONTAINER="${MYSQL_CONTAINER:-seclab-mysql}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-han0.521}"
BACKUP_DIR="${BACKUP_DIR:-/opt/seclab/backup}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  SecLab 旧版 → 最新版 升级脚本${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "  新代码包:     $NEW_TAR"
echo "  旧代码目录:   $OLD_PROJECT_DIR"
echo "  MySQL 容器:   $MYSQL_CONTAINER"
echo "  备份目录:     $BACKUP_DIR/$TIMESTAMP"
echo ""

# 确认
read -p "确认开始升级？(yes/no) " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
    echo "已取消。"
    exit 0
fi

# ── 前置检查 ──────────────────────────────────────────────────
step "0/8 前置检查"

if [[ ! -f "$NEW_TAR" ]]; then
    error "新代码包不存在: $NEW_TAR"
    echo "请先上传: scp SecLab-deploy.tar.gz user@server:/tmp/"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} 新代码包存在 ($(du -h "$NEW_TAR" | cut -f1))"

if [[ ! -d "$OLD_PROJECT_DIR" ]]; then
    error "旧代码目录不存在: $OLD_PROJECT_DIR"
    echo "如果旧版部署在其他路径，请指定: OLD_PROJECT_DIR=/your/path bash $0"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} 旧代码目录存在"

if ! docker info >/dev/null 2>&1; then
    error "Docker 未运行"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Docker 正常"

# ── 1. 备份 MySQL ─────────────────────────────────────────────
step "1/8 备份 MySQL 数据"

mkdir -p "$BACKUP_DIR/$TIMESTAMP"

if docker ps -a --format '{{.Names}}' | grep -qx "$MYSQL_CONTAINER"; then
    info "导出 MySQL 数据库备份..."

    # 检查 MySQL 是否在运行
    if ! docker ps --format '{{.Names}}' | grep -qx "$MYSQL_CONTAINER"; then
        warn "MySQL 容器未运行，尝试启动..."
        docker start "$MYSQL_CONTAINER"
        sleep 5
    fi

    # 等待 MySQL 就绪
    for i in $(seq 1 30); do
        if docker exec "$MYSQL_CONTAINER" mysqladmin ping -uroot -p"$MYSQL_ROOT_PASSWORD" --silent >/dev/null 2>&1; then
            break
        fi
        sleep 2
    done

    # 导出所有数据库
    docker exec "$MYSQL_CONTAINER" mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" \
        --databases userservice seclab_profile imagedb \
        --single-transaction --routines --triggers --events \
        --default-character-set=utf8mb4 \
        > "$BACKUP_DIR/$TIMESTAMP/mysql-backup.sql" 2>/dev/null

    BACKUP_SIZE=$(du -h "$BACKUP_DIR/$TIMESTAMP/mysql-backup.sql" | cut -f1)
    echo -e "  ${GREEN}✓${NC} MySQL 备份完成 ($BACKUP_SIZE)"
    echo "      → $BACKUP_DIR/$TIMESTAMP/mysql-backup.sql"

    # 同时导出用户表（快速检查用）
    docker exec "$MYSQL_CONTAINER" mysql -uroot -p"$MYSQL_ROOT_PASSWORD" userservice \
        -e "SELECT user_id, user_student_number, user_name, user_role FROM user ORDER BY user_id;" \
        > "$BACKUP_DIR/$TIMESTAMP/users-before.txt" 2>/dev/null
else
    warn "MySQL 容器 $MYSQL_CONTAINER 不存在，跳过数据库备份"
    warn "如果你的旧版 MySQL 不是 Docker 容器，请手动备份！"
fi

# ── 2. 备份旧代码目录 ─────────────────────────────────────────
step "2/8 备份旧代码和配置"

OLD_BACKUP="$BACKUP_DIR/$TIMESTAMP/old-code"

# 备份关键配置文件（不备份整个目录，太大了）
mkdir -p "$OLD_BACKUP/configs"

# 备份 .env 文件
if [[ -f "$OLD_PROJECT_DIR/seclab-backend/ai-agent-service/.env" ]]; then
    cp "$OLD_PROJECT_DIR/seclab-backend/ai-agent-service/.env" \
       "$OLD_BACKUP/configs/ai-agent.env"
    echo -e "  ${GREEN}✓${NC} 备份 ai-agent-service/.env"
fi

if [[ -f "$OLD_PROJECT_DIR/SecLab-FrontEnd-2/.env" ]]; then
    cp "$OLD_PROJECT_DIR/SecLab-FrontEnd-2/.env" \
       "$OLD_BACKUP/configs/frontend.env"
    echo -e "  ${GREEN}✓${NC} 备份 SecLab-FrontEnd-2/.env"
fi

# 备份 nginx 配置
if [[ -f "/etc/nginx/sites-enabled/seclab" ]]; then
    cp /etc/nginx/sites-enabled/seclab "$OLD_BACKUP/configs/nginx-seclab.conf"
    echo -e "  ${GREEN}✓${NC} 备份 nginx 配置"
fi

# 备份 systemd 单元
if ls /etc/systemd/system/seclab-*.service >/dev/null 2>&1; then
    cp /etc/systemd/system/seclab-*.service "$OLD_BACKUP/configs/" 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} 备份 systemd 单元"
fi

echo "      → $OLD_BACKUP/configs/"

# ── 3. 停止旧服务 ─────────────────────────────────────────────
step "3/8 停止旧服务"

info "停止 systemd 服务..."
for svc in seclab-ai-agent seclab-user-service seclab-experiment-module seclab-image-service; do
    if systemctl is-enabled "$svc" >/dev/null 2>&1; then
        sudo systemctl stop "$svc" 2>/dev/null && echo -e "  ${GREEN}✓${NC} 停止 $svc" || true
    fi
done

info "停止进程（兜底）..."
pkill -f 'user-service.*bootRun' 2>/dev/null && echo -e "  ${GREEN}✓${NC} 停止 user-service 进程" || true
pkill -f 'experiment-module-service.*bootRun' 2>/dev/null && echo -e "  ${GREEN}✓${NC} 停止 experiment-module-service 进程" || true
pkill -f 'image-service.*bootRun' 2>/dev/null && echo -e "  ${GREEN}✓${NC} 停止 image-service 进程" || true
pkill -f 'ai-agent-service.*main.py' 2>/dev/null && echo -e "  ${GREEN}✓${NC} 停止 ai-agent-service 进程" || true
pkill -f 'docker-api-server.js' 2>/dev/null || true

info "停止旧靶场容器..."
for lab in sqli-lab xss-lab csrf-lab file-upload-lab directory-traversal-lab \
           command-inject stack-overflow-lab protocol-analysis-lab; do
    if [[ -f "$OLD_PROJECT_DIR/seclab-backend/$lab/docker-compose.yml" ]]; then
        cd "$OLD_PROJECT_DIR/seclab-backend/$lab"
        docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true
    fi
done

docker stop sec-code-container 2>/dev/null && docker rm sec-code-container 2>/dev/null || true

cd /opt/seclab
echo -e "  ${GREEN}✓${NC} 旧服务已停止"

# ── 4. 替换代码目录 ───────────────────────────────────────────
step "4/8 替换代码目录"

info "重命名旧代码目录..."
mv "$OLD_PROJECT_DIR" "${OLD_PROJECT_DIR}.old"
echo -e "  ${GREEN}✓${NC} $OLD_PROJECT_DIR → ${OLD_PROJECT_DIR}.old"

info "解压新代码..."
mkdir -p "$(dirname "$OLD_PROJECT_DIR")"
cd "$(dirname "$OLD_PROJECT_DIR")"
tar -xzf "$NEW_TAR" --strip-components=1 -C "$(basename "$OLD_PROJECT_DIR")" 2>/dev/null || {
    # 如果 tar 的 --strip-components 不生效，手动处理
    mkdir -p "$(basename "$OLD_PROJECT_DIR")"
    tar -xzf "$NEW_TAR" -C /tmp/seclab-extract-$TIMESTAMP
    # 找到解压后的顶层目录
    EXTRACTED=$(ls /tmp/seclab-extract-$TIMESTAMP/ | head -1)
    cp -a /tmp/seclab-extract-$TIMESTAMP/$EXTRACTED/* "$(basename "$OLD_PROJECT_DIR")/"
    rm -rf /tmp/seclab-extract-$TIMESTAMP
}
echo -e "  ${GREEN}✓${NC} 新代码已解压到 $OLD_PROJECT_DIR"

# 设置权限
chmod +x "$OLD_PROJECT_DIR/deploy/scripts/"*.sh 2>/dev/null || true
chmod +x "$OLD_PROJECT_DIR/seclab-backend/gradlew" 2>/dev/null || true
find "$OLD_PROJECT_DIR" -name "*.sh" -exec dos2unix {} \; 2>/dev/null || true

# ── 5. 迁移配置文件 ───────────────────────────────────────────
step "5/8 迁移旧配置到新代码"

# 迁移 ai-agent-service/.env
if [[ -f "$OLD_BACKUP/configs/ai-agent.env" ]]; then
    cp "$OLD_BACKUP/configs/ai-agent.env" \
       "$OLD_PROJECT_DIR/seclab-backend/ai-agent-service/.env"
    echo -e "  ${GREEN}✓${NC} 迁移 ai-agent-service/.env（含 DIFY_API_KEY）"
else
    warn "旧版无 ai-agent-service/.env，首次部署需手动配置 DIFY_API_KEY"
    if [[ -f "$OLD_PROJECT_DIR/seclab-backend/ai-agent-service/.env.example" ]]; then
        cp "$OLD_PROJECT_DIR/seclab-backend/ai-agent-service/.env.example" \
           "$OLD_PROJECT_DIR/seclab-backend/ai-agent-service/.env"
        warn "已从 .env.example 创建 .env，请稍后编辑填入 DIFY_API_KEY"
    fi
fi

# 迁移前端 .env（如有自定义）
if [[ -f "$OLD_BACKUP/configs/frontend.env" ]]; then
    # 旧 .env 可能有旧的 API 地址配置，不直接覆盖 .env.production
    warn "检测到旧版前端 .env，请检查是否需要合并到 .env.production"
    warn "旧 .env 已备份到: $OLD_BACKUP/configs/frontend.env"
    warn "新版使用 .env.production（已包含正确的 nginx 相对路径配置）"
fi

# 修复 Gradle JDK 路径（Windows → Linux）
echo "org.gradle.java.installations.paths=/usr/lib/jvm/java-17-openjdk-amd64" \
    > "$OLD_PROJECT_DIR/seclab-backend/gradle.properties"
echo -e "  ${GREEN}✓${NC} 修复 gradle.properties（Linux JDK 路径）"

cd "$OLD_PROJECT_DIR"
echo -e "  ${GREEN}✓${NC} 配置迁移完成"

# ── 6. 数据库迁移（幂等） ─────────────────────────────────────
step "6/8 数据库迁移"

info "运行 bootstrap-mysql.sh（幂等，只补缺不删数据）..."
export PROJECT_DIR="$OLD_PROJECT_DIR"
export MYSQL_CONTAINER="$MYSQL_CONTAINER"
export MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD"

bash "$OLD_PROJECT_DIR/deploy/scripts/bootstrap-mysql.sh" || {
    warn "bootstrap-mysql.sh 部分失败，但已有备份，可手动修复"
    warn "备份文件: $BACKUP_DIR/$TIMESTAMP/mysql-backup.sql"
}

# ── 7. 重新构建 ───────────────────────────────────────────────
step "7/8 重新构建后端和前端"

# 7.1 构建后端 JAR
info "构建后端微服务 JAR..."
cd "$OLD_PROJECT_DIR/seclab-backend"
chmod +x gradlew
./gradlew :user-service:bootJar :experiment-module-service:bootJar :image-service:bootJar \
    -x test 2>&1 | tail -5
echo -e "  ${GREEN}✓${NC} 后端 JAR 构建完成"

# 7.2 配置 AI Agent Python 环境
info "配置 AI Agent Python 环境..."
cd "$OLD_PROJECT_DIR/seclab-backend/ai-agent-service"
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt 2>&1 | tail -3
deactivate
echo -e "  ${GREEN}✓${NC} Python 依赖已安装"

# 7.3 构建前端
info "构建前端..."
cd "$OLD_PROJECT_DIR/SecLab-FrontEnd-2"
if [[ ! -d "node_modules" ]]; then
    npm install 2>&1 | tail -3
fi
npm run build 2>&1 | tail -5
echo -e "  ${GREEN}✓${NC} 前端构建完成"

# 7.4 构建 noVNC 镜像
info "构建 noVNC 操作环境镜像..."
cd "$OLD_PROJECT_DIR/seclab-backend/operation-image"
docker build -t seclab-op-web-tools:1.0 . 2>&1 | tail -3
echo -e "  ${GREEN}✓${NC} noVNC 镜像已构建"

cd "$OLD_PROJECT_DIR"

# ── 8. 启动服务 + 更新 nginx ──────────────────────────────────
step "8/8 启动服务并更新 Nginx"

# 8.1 更新 nginx 配置
info "更新 Nginx 配置..."
sudo cp "$OLD_PROJECT_DIR/deploy/nginx/seclab.conf" /etc/nginx/sites-available/seclab
sudo ln -sfn /etc/nginx/sites-available/seclab /etc/nginx/sites-enabled/seclab
sudo nginx -t 2>&1 && echo -e "  ${GREEN}✓${NC} Nginx 配置测试通过" || {
    error "Nginx 配置测试失败，请检查"
    exit 1
}
sudo systemctl reload nginx

# 8.2 更新 systemd 单元
info "更新 systemd 单元..."
for unit in seclab-ai-agent seclab-user-service seclab-experiment-module seclab-image-service; do
    SRC="$OLD_PROJECT_DIR/deploy/systemd/${unit}.service"
    if [[ -f "$SRC" ]]; then
        sudo cp "$SRC" /etc/systemd/system/
        echo -e "  ${GREEN}✓${NC} 更新 $unit.service"
    fi
done
sudo systemctl daemon-reload

# 8.3 启动所有服务
info "启动所有服务..."
bash "$OLD_PROJECT_DIR/deploy/scripts/start-all-services.sh" 2>&1 | tail -20

# ── 汇总 ──────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  升级完成！${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "备份位置:"
echo "  MySQL 备份:   $BACKUP_DIR/$TIMESTAMP/mysql-backup.sql"
echo "  旧配置备份:   $BACKUP_DIR/$TIMESTAMP/old-code/configs/"
echo "  旧代码目录:   ${OLD_PROJECT_DIR}.old/"
echo ""
echo "验证:"
echo "  curl http://127.0.0.1:8088/"
echo "  curl -X POST http://127.0.0.1:8088/stu/login \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"userStudentNumber\":\"admin\",\"userPassword\":\"123456\"}'"
echo ""
echo "如需回滚:"
echo "  1. bash $OLD_PROJECT_DIR/deploy/scripts/stop-all-services.sh"
echo "  2. mv $OLD_PROJECT_DIR ${OLD_PROJECT_DIR}.failed"
echo "  3. mv ${OLD_PROJECT_DIR}.old $OLD_PROJECT_DIR"
echo "  4. docker exec -i $MYSQL_CONTAINER mysql -uroot -p$MYSQL_ROOT_PASSWORD < $BACKUP_DIR/$TIMESTAMP/mysql-backup.sql"
echo "  5. bash $OLD_PROJECT_DIR/deploy/scripts/start-all-services.sh"
echo "  6. sudo systemctl reload nginx"
echo ""
echo "确认无误后可删除旧代码:"
echo "  rm -rf ${OLD_PROJECT_DIR}.old"
echo ""
