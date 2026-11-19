#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# SecLab Linux 一键停止脚本
# 停止所有由 start-all-services.sh 启动的服务。
#
# 用法：
#   bash deploy/scripts/stop-all-services.sh
#
# 可选环境变量：
#   PROJECT_DIR=/opt/seclab/SecLab
#   STOP_MYSQL=false   设为 true 同时停止 MySQL 容器
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
BACKEND_DIR="$PROJECT_DIR/seclab-backend"
LOG_DIR="${LOG_DIR:-/opt/seclab/logs}"
MYSQL_CONTAINER="${MYSQL_CONTAINER:-seclab-mysql}"
STOP_MYSQL="${STOP_MYSQL:-false}"

info "项目目录: $PROJECT_DIR"

# ── 停止 AI Agent ─────────────────────────────────────────────
step "1/5 停止 AI Agent 服务"

if [[ -f "$LOG_DIR/ai-agent-service.pid" ]]; then
    PID=$(cat "$LOG_DIR/ai-agent-service.pid")
    if kill -0 "$PID" 2>/dev/null; then
        info "停止 ai-agent-service (PID=$PID)..."
        kill "$PID" 2>/dev/null || true
        sleep 2
        kill -9 "$PID" 2>/dev/null || true
        echo -e "  ${GREEN}✓${NC} 已停止"
    else
        warn "ai-agent-service 进程不存在 (PID=$PID)"
    fi
    rm -f "$LOG_DIR/ai-agent-service.pid"
else
    # 兜底：按端口查找并杀掉
    if command -v fuser >/dev/null 2>&1; then
        fuser -k 8010/tcp 2>/dev/null && info "已按端口 8010 停止 ai-agent-service" || warn "端口 8010 无进程"
    fi
fi

# ── 停止后端 Java 微服务 ──────────────────────────────────────
step "2/5 停止后端微服务"

for svc in user-service experiment-module-service image-service; do
    PID_FILE="$LOG_DIR/${svc}.pid"
    if [[ -f "$PID_FILE" ]]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            info "停止 $svc (PID=$PID)..."
            kill "$PID" 2>/dev/null || true
            sleep 2
            kill -9 "$PID" 2>/dev/null || true
            echo -e "  ${GREEN}✓${NC} 已停止"
        else
            warn "$svc 进程不存在 (PID=$PID)"
        fi
        rm -f "$PID_FILE"
    else
        # 兜底：杀掉 Gradle bootRun 进程
        pkill -f "${svc}.*bootRun" 2>/dev/null && info "已按名称停止 $svc" || warn "$svc 未在运行"
    fi
done

# ── 停止 sec-code 容器 ────────────────────────────────────────
step "3/5 停止安全代码容器"

if docker ps -a --format '{{.Names}}' | grep -qx "sec-code-container"; then
    docker stop sec-code-container 2>/dev/null && info "已停止 sec-code-container" || true
else
    warn "sec-code-container 不存在"
fi

# ── 停止靶场容器 ──────────────────────────────────────────────
step "4/5 停止靶场容器"

LABS=(
    sqli-lab
    xss-lab
    csrf-lab
    file-upload-lab
    directory-traversal-lab
    command-inject
    stack-overflow-lab
    protocol-analysis-lab
)

for lab in "${LABS[@]}"; do
    if [[ -f "$BACKEND_DIR/$lab/docker-compose.yml" ]]; then
        info "停止 $lab..."
        cd "$BACKEND_DIR/$lab"
        if docker compose version >/dev/null 2>&1; then
            docker compose down 2>/dev/null || true
        else
            docker-compose down 2>/dev/null || true
        fi
    fi
done
cd "$BACKEND_DIR"

# ── 可选：停止 MySQL ──────────────────────────────────────────
step "5/5 MySQL 容器"

if [[ "$STOP_MYSQL" == "true" ]]; then
    if docker ps -a --format '{{.Names}}' | grep -qx "$MYSQL_CONTAINER"; then
        info "停止 MySQL 容器 $MYSQL_CONTAINER..."
        docker stop "$MYSQL_CONTAINER" 2>/dev/null || true
        echo -e "  ${GREEN}✓${NC} MySQL 已停止（数据保留在 $MYSQL_DATA_DIR）"
    fi
else
    info "保留 MySQL 容器运行（STOP_MYSQL=false）"
    info "如需停止 MySQL: STOP_MYSQL=true bash $0"
fi

# ── 汇总 ──────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SecLab 所有服务已停止"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "验证："
echo "  docker ps   # 应无 SecLab 容器（除非保留 MySQL）"
echo "  ss -tlnp | grep -E '8010|8083|8084|8086'"
echo ""
echo "重新启动："
echo "  bash $PROJECT_DIR/deploy/scripts/start-all-services.sh"
echo ""
