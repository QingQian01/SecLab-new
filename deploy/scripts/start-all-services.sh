#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# SecLab Linux 一键启动脚本（等价于 Windows 的 start-all-services.bat）
#
# 功能：
#   1. 启动 MySQL 容器并等待就绪
#   2. 启动 8 个靶场容器（sqli/xss/csrf/upload/dir/cmd/stack-overflow/protocol）
#   3. 启动 sec-code 安全代码容器
#   4. 启动 user-service / experiment-module-service / image-service（Gradle bootRun）
#   5. 启动 ai-agent-service（Python uvicorn）
#   6. 打印所有服务地址和验证命令
#
# 用法：
#   cd /opt/seclab/SecLab
#   bash deploy/scripts/start-all-services.sh
#
# 可选环境变量（带默认值）：
#   PROJECT_DIR=/opt/seclab/SecLab
#   MYSQL_ROOT_PASSWORD=han0.521
#   MYSQL_APP_USER=seclab_app
#   MYSQL_APP_PASSWORD=Seclab@123
#   START_LOCAL_USER_SERVICE=true   设为 false 跳过本地 user-service
#   START_AI_AGENT=true             设为 false 跳过 AI Agent
# ════════════════════════════════════════════════════════════════
set -euo pipefail

# ── 颜色输出 ──────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }
step()  { echo -e "\n${CYAN}━━━ $* ━━━${NC}"; }

# ── 配置 ──────────────────────────────────────────────────────
PROJECT_DIR="${PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
BACKEND_DIR="$PROJECT_DIR/seclab-backend"
FRONTEND_DIR="$PROJECT_DIR/SecLab-FrontEnd-2"
LOG_DIR="${LOG_DIR:-/opt/seclab/logs}"
MYSQL_CONTAINER="${MYSQL_CONTAINER:-seclab-mysql}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-han0.521}"
MYSQL_APP_USER="${MYSQL_APP_USER:-seclab_app}"
MYSQL_APP_PASSWORD="${MYSQL_APP_PASSWORD:-Seclab@123}"
MYSQL_DATA_DIR="${MYSQL_DATA_DIR:-/opt/seclab/data/mysql}"

START_LOCAL_USER_SERVICE="${START_LOCAL_USER_SERVICE:-true}"
START_LOCAL_EXPERIMENT_MODULE_SERVICE="${START_LOCAL_EXPERIMENT_MODULE_SERVICE:-true}"
START_LOCAL_IMAGE_SERVICE="${START_LOCAL_IMAGE_SERVICE:-true}"
START_AI_AGENT="${START_AI_AGENT:-true}"

mkdir -p "$LOG_DIR"

info "项目目录: $PROJECT_DIR"
info "后端目录: $BACKEND_DIR"
info "日志目录: $LOG_DIR"
info "MySQL 容器: $MYSQL_CONTAINER"

# ── 前置检查 ──────────────────────────────────────────────────
step "0/6 前置环境检查"

check_cmd() {
    if command -v "$1" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $1 ($(command -v "$1"))"
    else
        echo -e "  ${RED}✗${NC} $1 未安装"
        return 1
    fi
}

MISSING=0
check_cmd docker || MISSING=1
check_cmd java || MISSING=1
check_cmd python3 || MISSING=1
check_cmd node || MISSING=1
check_cmd npm || MISSING=1

if [[ "$MISSING" -eq 1 ]]; then
    error "缺少必要命令，请先安装依赖。"
    error "Debian/Ubuntu: sudo apt install -y openjdk-17-jdk python3 python3-venv nodejs npm docker.io docker-compose-plugin"
    exit 1
fi

# 检查 docker daemon
if ! docker info >/dev/null 2>&1; then
    error "Docker daemon 未运行，请先启动: sudo systemctl start docker"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Docker daemon 正常"

# Java 版本检查
JAVA_VER=$(java -version 2>&1 | head -1 | awk -F '"' '{print $2}' | cut -d. -f1)
if [[ "$JAVA_VER" != "17" && "$JAVA_VER" != "21" ]]; then
    warn "Java 版本为 $JAVA_VER，推荐 JDK 17。部分 Spring Boot 功能可能不兼容。"
fi

# ── 1. 启动 MySQL ─────────────────────────────────────────────
step "1/6 启动 MySQL 容器"

mkdir -p "$MYSQL_DATA_DIR"

if ! docker ps -a --format '{{.Names}}' | grep -qx "$MYSQL_CONTAINER"; then
    info "创建 MySQL 容器..."
    docker run -d --name "$MYSQL_CONTAINER" \
        --restart unless-stopped \
        -p 127.0.0.1:3306:3306 \
        -v "$MYSQL_DATA_DIR:/var/lib/mysql" \
        -e MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD" \
        -e MYSQL_DATABASE=userservice \
        -e MYSQL_USER="$MYSQL_APP_USER" \
        -e MYSQL_PASSWORD="$MYSQL_APP_PASSWORD" \
        -e MYSQL_CHARACTER_SET_SERVER=utf8mb4 \
        -e MYSQL_COLLATION_SERVER=utf8mb4_unicode_ci \
        mysql:8.0 --default-authentication-plugin=mysql_native_password
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
        error "MySQL 启动超时，请检查: docker logs $MYSQL_CONTAINER"
        exit 1
    fi
    sleep 2
done

# ── 2. 启动靶场容器 ───────────────────────────────────────────
step "2/6 启动靶场容器"

LABS=(
    "sqli-lab:8091"
    "xss-lab:8092"
    "csrf-lab:8093"
    "file-upload-lab:8094"
    "directory-traversal-lab:8095"
    "command-inject:8090"
    "stack-overflow-lab:8096"
    "protocol-analysis-lab:8896"
)

for entry in "${LABS[@]}"; do
    LAB_DIR="${entry%%:*}"
    PORT="${entry##*:}"
    if [[ -f "$BACKEND_DIR/$LAB_DIR/docker-compose.yml" ]]; then
        info "启动 $LAB_DIR (端口 $PORT)..."
        cd "$BACKEND_DIR/$LAB_DIR"
        if docker compose version >/dev/null 2>&1; then
            docker compose up -d --build
        else
            docker-compose up -d --build
        fi
    else
        warn "$LAB_DIR/docker-compose.yml 不存在，跳过"
    fi
done

cd "$BACKEND_DIR"

# ── 3. 启动 sec-code 容器 ─────────────────────────────────────
step "3/6 启动安全代码容器 (sec-code 8080)"

docker stop sec-code-container 2>/dev/null || true
docker rm sec-code-container 2>/dev/null || true
docker run -d --name sec-code-container -p 8080:80 gsycl2004/sec-code
echo -e "  ${GREEN}✓${NC} sec-code 已启动 → http://localhost:8080"

# ── 4. 启动后端 Java 微服务 ───────────────────────────────────
step "4/6 启动后端微服务"

# 设置数据库环境变量（供 Gradle bootRun 读取）
export MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
export MYSQL_PORT="${MYSQL_PORT:-3306}"
export MYSQL_USER="$MYSQL_APP_USER"
export MYSQL_PASSWORD="$MYSQL_APP_PASSWORD"
export USER_SERVICE_DB_HOST="$MYSQL_HOST"
export USER_SERVICE_DB_PORT="$MYSQL_PORT"
export USER_SERVICE_DB_USERNAME="$MYSQL_APP_USER"
export USER_SERVICE_DB_PASSWORD="$MYSQL_APP_PASSWORD"
export USER_SERVICE_DB_NAME="${USER_SERVICE_DB_NAME:-userservice}"
export EXPERIMENT_MODULE_DB_HOST="$MYSQL_HOST"
export EXPERIMENT_MODULE_DB_PORT="$MYSQL_PORT"
export EXPERIMENT_MODULE_DB_USERNAME="$MYSQL_APP_USER"
export EXPERIMENT_MODULE_DB_PASSWORD="$MYSQL_APP_PASSWORD"
export IMAGE_SERVICE_DB_HOST="$MYSQL_HOST"
export IMAGE_SERVICE_DB_PORT="$MYSQL_PORT"
export IMAGE_SERVICE_DB_USERNAME="$MYSQL_APP_USER"
export IMAGE_SERVICE_DB_PASSWORD="$MYSQL_APP_PASSWORD"

start_gradle_service() {
    local svc_name="$1"
    local svc_dir="$2"
    local port="$3"

    # 检查端口是否已被占用
    if ss -tlnp 2>/dev/null | grep -q ":$port " || netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        warn "$svc_name 已在端口 $port 监听，跳过"
        return 0
    fi

    if [[ ! -f "$svc_dir/gradlew" ]]; then
        error "$svc_name Gradle wrapper 不存在: $svc_dir/gradlew"
        return 1
    fi

    info "启动 $svc_name (端口 $port)..."
    chmod +x "$svc_dir/gradlew"
    cd "$svc_dir"
    nohup ./gradlew bootRun > "$LOG_DIR/${svc_name}.log" 2>&1 &
    echo $! > "$LOG_DIR/${svc_name}.pid"
    cd "$BACKEND_DIR"
    echo -e "  ${GREEN}✓${NC} $svc_name PID=$(cat "$LOG_DIR/${svc_name}.pid") → 日志: $LOG_DIR/${svc_name}.log"
}

if [[ "$START_LOCAL_USER_SERVICE" == "true" ]]; then
    start_gradle_service "user-service" "$BACKEND_DIR/user-service" "8083"
fi

if [[ "$START_LOCAL_EXPERIMENT_MODULE_SERVICE" == "true" ]]; then
    start_gradle_service "experiment-module-service" "$BACKEND_DIR/experiment-module-service" "8084"
fi

if [[ "$START_LOCAL_IMAGE_SERVICE" == "true" ]]; then
    start_gradle_service "image-service" "$BACKEND_DIR/image-service" "8086"
fi

# ── 5. 启动 AI Agent 服务 ─────────────────────────────────────
step "5/6 启动 AI Agent 服务"

if [[ "$START_AI_AGENT" == "true" ]]; then
    if ss -tlnp 2>/dev/null | grep -q ":8010 " || netstat -tlnp 2>/dev/null | grep -q ":8010 "; then
        warn "ai-agent-service 已在端口 8010 监听，跳过"
    elif [[ ! -f "$BACKEND_DIR/ai-agent-service/main.py" ]]; then
        warn "ai-agent-service/main.py 不存在，跳过"
    else
        info "启动 ai-agent-service (端口 8010)..."
        cd "$BACKEND_DIR/ai-agent-service"

        # 设置 MySQL 环境变量
        export MYSQL_HOST="$MYSQL_HOST"
        export MYSQL_PORT="$MYSQL_PORT"
        export MYSQL_USER="$MYSQL_APP_USER"
        export MYSQL_PASSWORD="$MYSQL_APP_PASSWORD"
        export MYSQL_DATABASE="${PROFILE_DB_NAME:-seclab_profile}"

        # 优先使用虚拟环境
        if [[ -f "venv/bin/activate" ]]; then
            source venv/bin/activate
            nohup python3 main.py > "$LOG_DIR/ai-agent-service.log" 2>&1 &
        elif [[ -f ".venv/bin/activate" ]]; then
            source .venv/bin/activate
            nohup python3 main.py > "$LOG_DIR/ai-agent-service.log" 2>&1 &
        else
            warn "Python 虚拟环境不存在，正在创建..."
            python3 -m venv venv
            source venv/bin/activate
            pip install -r requirements.txt
            nohup python3 main.py > "$LOG_DIR/ai-agent-service.log" 2>&1 &
        fi
        echo $! > "$LOG_DIR/ai-agent-service.pid"
        cd "$BACKEND_DIR"
        echo -e "  ${GREEN}✓${NC} ai-agent-service PID=$(cat "$LOG_DIR/ai-agent-service.pid") → 日志: $LOG_DIR/ai-agent-service.log"
    fi
fi

# ── 6. 构建操作环境 noVNC 镜像 ────────────────────────────────
step "6/6 检查操作环境镜像 (noVNC)"

if [[ -f "$BACKEND_DIR/operation-image/Dockerfile" ]]; then
    if ! docker image inspect seclab-op-web-tools:1.0 >/dev/null 2>&1; then
        info "构建 seclab-op-web-tools:1.0 镜像..."
        cd "$BACKEND_DIR/operation-image"
        docker build -t seclab-op-web-tools:1.0 .
        cd "$BACKEND_DIR"
    else
        echo -e "  ${GREEN}✓${NC} seclab-op-web-tools:1.0 镜像已存在"
    fi
else
    warn "operation-image/Dockerfile 不存在，跳过 noVNC 镜像构建"
fi

# ── 汇总 ──────────────────────────────────────────────────────
step "启动完成"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SecLab 所有服务已启动"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "后端微服务："
echo "  user-service:              http://localhost:8083"
echo "  experiment-module-service:  http://localhost:8084"
echo "  image-service:              http://localhost:8086"
echo "  AI Agent:                   http://localhost:8010"
echo "  AI Agent API 文档:          http://localhost:8010/docs"
echo ""
echo "靶场环境："
echo "  SQL 注入:       http://localhost:8091"
echo "  XSS:            http://localhost:8092"
echo "  CSRF:           http://localhost:8093"
echo "  文件上传:       http://localhost:8094"
echo "  目录遍历:       http://localhost:8095"
echo "  命令注入:       http://localhost:8090"
echo "  栈溢出:         http://localhost:8096"
echo "  协议分析:       http://localhost:8896"
echo "  安全代码:       http://localhost:8080"
echo ""
echo "前端（需 nginx 或手动启动）："
echo "  开发模式: cd $FRONTEND_DIR && npm run dev"
echo "  生产模式: 已构建的 dist 由 nginx 代理 → http://<服务器IP>:8088"
echo ""
echo "验证命令："
echo "  curl http://127.0.0.1:8010/health"
echo "  curl http://127.0.0.1:8083/stu/login"
echo "  curl http://127.0.0.1:8084/course/overview-list"
echo "  docker ps"
echo ""
echo "查看日志："
echo "  tail -f $LOG_DIR/user-service.log"
echo "  tail -f $LOG_DIR/experiment-module-service.log"
echo "  tail -f $LOG_DIR/ai-agent-service.log"
echo ""
echo "停止所有服务："
echo "  bash $PROJECT_DIR/deploy/scripts/stop-all-services.sh"
echo ""
