"""
SecLab AI Agent Service
职责：
  1. 将前端的聊天请求代理转发至 Dify Agent，并以 SSE 流式返回给前端
  2. 暴露 Docker 工具 HTTP API，供 Dify 通过外部 API 工具调用
"""
import json
import os
import httpx
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing import Optional, Any

from config import DIFY_API_URL, DIFY_API_KEY, CORS_ORIGINS, SERVICE_HOST, SERVICE_PORT
import docker_tools

# 靶机事件内存存储（生产环境建议替换为 Redis/DB）
_lab_events: list[dict] = []

# 内部工具 API Key（供 Dify 调用 Docker 工具时校验）
# 留空 = 不校验（推荐内网/本地开发时使用）
TOOL_API_KEY = os.getenv("TOOL_API_KEY", "")

# 支持两种传递方式：
#   1. 自定义头  X-SecLab-Token: <key>
#   2. 标准 Bearer  Authorization: Bearer <key>  （Dify 默认方式）
_api_key_header = APIKeyHeader(name="X-SecLab-Token", auto_error=False)
_auth_header    = APIKeyHeader(name="Authorization",   auto_error=False)


async def verify_tool_key(
    x_token: Optional[str] = Security(_api_key_header),
    auth:    Optional[str] = Security(_auth_header),
) -> None:
    """当 TOOL_API_KEY 为空时直接放行；否则校验任意一种 Key 格式"""
    if not TOOL_API_KEY:
        return          # 未配置 → 不校验（内网友好模式）
    bearer = auth.replace("Bearer ", "").strip() if auth else None
    if x_token != TOOL_API_KEY and bearer != TOOL_API_KEY:
        raise HTTPException(status_code=403, detail="无效的工具 API Key")

app = FastAPI(
    title="SecLab AI Agent Service",
    description="Dify Agent 代理 + Docker 靶场工具 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
#  请求 / 响应模型
# ─────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = ""
    user: Optional[str] = "student"
    inputs: Optional[dict] = {}


class ExecRequest(BaseModel):
    command: str


class LabEventRequest(BaseModel):
    """靶机发送的事件数据模型"""
    type: str                          # lab_opened / hint_request / timer_milestone / timer_expired / progress_update
    container: Optional[str] = ""     # 容器名称，如 sqli-lab-web-1
    level: Optional[int] = None       # 关卡编号
    levelTitle: Optional[str] = ""    # 关卡标题
    timerSeconds: Optional[int] = None # 总倒计时秒数（lab_opened 时）
    remainingSeconds: Optional[int] = None  # 剩余秒数
    milestone: Optional[str] = ""     # 时间里程碑，如 "50%" / "10%"
    prompt: Optional[str] = ""        # 提示请求的 prompt（hint_request 时）
    timestamp: Optional[str] = ""     # ISO 时间戳
    extra: Optional[Any] = None       # 扩展字段


class EventsIngestRequest(BaseModel):
    """前端事件上报请求模型"""
    batch_id: str
    source_system: str = "external-agent"
    generated_at: str
    user_context: dict
    events: list
    ai_generated_questions: Optional[list] = []
    profile_rebuild: Optional[dict] = None


# ─────────────────────────────────────────
#  健康检查
# ─────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "SecLab AI Agent Service"}


# ─────────────────────────────────────────
#  靶机事件接收 API
# ─────────────────────────────────────────

@app.post("/api/lab/event")
async def receive_lab_event(event: LabEventRequest):
    """
    接收靶场发送的事件信号。
    支持的事件类型：
      - lab_opened       : 学生开启靶机（发送"开机"信号）
      - hint_request     : 学生主动请求 AI 提示
      - timer_milestone  : 沙漏倒计时达到里程碑（50% / 10%）
      - timer_expired    : 倒计时归零
      - progress_update  : 学生操作进度更新
    """
    record = event.dict()
    record["received_at"] = datetime.utcnow().isoformat() + "Z"
    _lab_events.append(record)

    # 保留最近 500 条事件，防止内存无限增长
    if len(_lab_events) > 500:
        _lab_events.pop(0)

    # 根据事件类型决定是否主动触发 Dify Agent
    auto_prompt = None

    if event.type == "lab_opened":
        # ── 自动拉取容器状态与最新日志，附加到通知消息 ──────────────
        container_name = event.container or "sqli-lab-web-1"

        status_info = docker_tools.get_container_status(container_name)
        status_text = ""
        if status_info.get("success") and isinstance(status_info.get("data"), dict):
            d = status_info["data"]
            status_text = (
                f"\n【容器状态】名称={d.get('name','-')} | "
                f"运行状态={d.get('status','-')} | "
                f"镜像={d.get('image','-')} | "
                f"启动时间={d.get('started_at','-')}"
            )

        log_info = docker_tools.get_container_logs(container_name, tail=30)
        log_text = ""
        if log_info.get("success") and log_info.get("logs"):
            log_text = f"\n【最近30行日志】\n{log_info['logs']}"
        elif not log_info.get("success"):
            log_text = f"\n【日志获取失败】{log_info.get('error','')}"

        # 同步记录到事件记录中
        record["docker_status"] = status_info
        record["docker_logs_preview"] = log_info.get("logs", "")[:2000]

        auto_prompt = (
            f"✅ 靶机启动通知：学生已开启容器【{container_name}】\n"
            f"正在挑战「{event.levelTitle}」（Level {event.level}），"
            f"倒计时 {event.timerSeconds} 秒。"
            f"{status_text}"
            f"{log_text}\n"
            f"请记录此开机事件。如果学生后续发出提示请求或倒计时结束，"
            f"请根据容器日志给出阶梯式中文提示（先给最小提示）。"
        )

    elif event.type == "timer_milestone":
        # ── 里程碑时自动拉取最新日志辅助判断进度 ──────────────────
        container_name = event.container or "sqli-lab-web-1"
        log_info = docker_tools.get_container_logs(container_name, tail=20)
        log_text = ""
        if log_info.get("success") and log_info.get("logs"):
            log_text = f"\n【最近20行日志】\n{log_info['logs']}"

        auto_prompt = (
            f"⏳ 倒计时里程碑 [{event.milestone}]：靶机【{container_name}】剩余 {event.remainingSeconds} 秒。\n"
            f"学生正在挑战「{event.levelTitle}」。"
            f"{log_text}\n"
            f"请根据上方日志分析学生当前进度，若学生明显卡住则给出最小提示（一句话）。"
        )

    elif event.type == "timer_expired":
        # ── 时间到时拉取完整日志 ────────────────────────────────────
        container_name = event.container or "sqli-lab-web-1"
        log_info = docker_tools.get_container_logs(container_name, tail=50)
        log_text = ""
        if log_info.get("success") and log_info.get("logs"):
            log_text = f"\n【最近50行日志】\n{log_info['logs']}"

        auto_prompt = (
            f"⌛ 倒计时归零！靶机【{container_name}】，"
            f"学生正在挑战「{event.levelTitle}」（Level {event.level}）。"
            f"{log_text}\n"
            f"请立即分析以上 Apache 日志，给出完整阶梯式提示（从最小提示到完整答案逐步展示，使用中文）。"
        )

    elif event.type == "hint_request" and event.prompt:
        # ── 手动提示请求：附加最新日志 ─────────────────────────────
        container_name = event.container or "sqli-lab-web-1"
        log_info = docker_tools.get_container_logs(container_name, tail=20)
        log_text = ""
        if log_info.get("success") and log_info.get("logs"):
            log_text = f"\n【最近20行日志】\n{log_info['logs']}"

        auto_prompt = f"{event.prompt}{log_text}"

    # 若需要自动触发，异步向 Dify 发送消息
    if auto_prompt:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post(
                    f"{DIFY_API_URL}/chat-messages",
                    headers={
                        "Authorization": f"Bearer {DIFY_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": auto_prompt,
                        "response_mode": "blocking",
                        "conversation_id": "",
                        "user": f"lab-event-{event.container or 'unknown'}",
                        "inputs": {
                            "event_type": event.type,
                            "container": event.container or "",
                            "level": str(event.level or ""),
                        },
                    },
                )
        except Exception:
            pass  # 不阻塞靶机请求，静默失败

    return {
        "status": "ok",
        "event_type": event.type,
        "message": f"事件 [{event.type}] 已记录",
        "auto_triggered": auto_prompt is not None,
    }


@app.get("/api/lab/events")
async def get_lab_events(
    limit: int = Query(50, ge=1, le=200, description="返回最近 N 条事件"),
    event_type: Optional[str] = Query(None, description="按事件类型过滤"),
    _: None = Security(verify_tool_key),
):
    """查询靶机事件历史（供 Dify 工具或管理员调用）"""
    filtered = _lab_events
    if event_type:
        filtered = [e for e in _lab_events if e.get("type") == event_type]
    return {
        "total": len(filtered),
        "events": filtered[-limit:][::-1],  # 最新的在前
    }


# ─────────────────────────────────────────
#  Dify 流式聊天代理
# ─────────────────────────────────────────

@app.post("/api/chat")
async def chat(req: ChatRequest):
    """
    接收前端消息，流式转发至 Dify Agent，并将 SSE 事件原样推送给前端。
    """
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": req.query,
        "response_mode": "streaming",
        "conversation_id": req.conversation_id or "",
        "user": req.user or "student",
        "inputs": req.inputs or {},
    }

    async def event_stream():
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{DIFY_API_URL}/chat-messages",
                headers=headers,
                json=payload,
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    error_msg = body.decode("utf-8", errors="replace")
                    yield f"data: {json.dumps({'error': error_msg})}\n\n"
                    return
                async for line in response.aiter_lines():
                    if line:
                        yield f"{line}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ─────────────────────────────────────────
#  事件上报 API（前端结束实验时调用）
# ─────────────────────────────────────────

@app.post("/api/external/events/ingest")
async def ingest_events(req: EventsIngestRequest):
    """
    接收前端上报的实验事件数据。
    后端自动通过 Docker SDK 补充容器运行时数据（日志、资源、进程），
    合并后存储到内存事件列表。
    """
    user_ctx = req.user_context or {}
    container_name = None

    for evt in req.events:
        if evt.get("container_name"):
            container_name = evt["container_name"]
            break

    docker_runtime_data = {}
    docker_log_events = []
    if container_name:
        try:
            docker_runtime_data = docker_tools.collect_container_runtime_data(container_name)
            docker_log_events = docker_runtime_data.get("log_events", [])
        except Exception as e:
            docker_runtime_data = {"error": str(e)}

    enriched_events = list(req.events)

    for de in docker_log_events:
        already_exists = any(
            e.get("event_id") == de.get("event_id") or
            (e.get("event_type") == de.get("event_type") and e.get("event_time") == de.get("event_time"))
            for e in enriched_events
        )
        if not already_exists:
            de.update({
                "user_id": user_ctx.get("user_id", 0),
                "class_id": user_ctx.get("class_id", 0),
                "course_id": user_ctx.get("course_id", 0),
                "module_id": user_ctx.get("module_id", 0),
                "task_id": user_ctx.get("task_id"),
                "question_id": user_ctx.get("question_id"),
                "lab_session_id": user_ctx.get("lab_session_id", ""),
                "source": "external-agent",
            })
            enriched_events.append(de)

    for evt in enriched_events:
        record = {
            "type": evt.get("event_type", "unknown"),
            "container": evt.get("container_name", container_name or ""),
            "timestamp": evt.get("event_time", ""),
            "received_at": datetime.utcnow().isoformat() + "Z",
            "event_data": evt,
            "source": "events_ingest",
        }
        if docker_runtime_data and container_name:
            record["docker_runtime"] = {
                "container_info": docker_runtime_data.get("container_info", {}),
                "resource_usage": docker_runtime_data.get("resource_usage", {}),
            }
        _lab_events.append(record)

    while len(_lab_events) > 500:
        _lab_events.pop(0)

    return {
        "isSuccess": 1,
        "status": 200,
        "message": f"事件上报成功，共 {len(enriched_events)} 条事件（含 {len(docker_log_events)} 条 Docker SDK 补充）",
        "data": {
            "batch_id": req.batch_id,
            "total_events": len(enriched_events),
            "frontend_events": len(req.events),
            "docker_enriched_events": len(docker_log_events),
            "container_runtime_available": bool(docker_runtime_data and docker_runtime_data.get("success")),
        }
    }


# ─────────────────────────────────────────
#  Docker 工具 API（供 Dify 外部工具调用）
# ─────────────────────────────────────────
# --- 新增：获取容器列表 (读取容器名字) ---
@app.get("/api/docker/list")
async def list_all_containers(
    _: None = Security(verify_tool_key)
):
    """获取所有容器列表（Dify 工具：list_containers）"""
    result = docker_tools.list_containers() # 需要在 docker_tools 里实现
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

# --- 新增：启动容器 ---
@app.post("/api/docker/start/{container_name}")
async def start_container(
    container_name: str,
    _: None = Security(verify_tool_key)
):
    """开启容器（Dify 工具：start_container）"""
    result = docker_tools.start_container(container_name) # 需要在 docker_tools 里实现
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result
@app.get("/api/docker/containers")
async def list_containers(
    name: Optional[str] = Query(None, description="容器名称，不填则返回全部靶场容器"),
    _: None = Security(verify_tool_key)
):
    """获取容器状态（Dify 工具：get_container_status）"""
    result = docker_tools.get_container_status(name)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@app.get("/api/docker/logs/{container_name}")
async def container_logs(
    container_name: str,
    tail: int = Query(100, ge=1, le=200, description="返回最近 N 行日志"),
    _: None = Security(verify_tool_key)
):
    """获取容器日志（Dify 工具：get_container_logs）"""
    result = docker_tools.get_container_logs(container_name, tail)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@app.post("/api/docker/exec/{container_name}")
async def exec_command(
    container_name: str,
    body: ExecRequest,
    _: None = Security(verify_tool_key)
):
    """在容器内执行指令（Dify 工具：exec_in_container）"""
    result = docker_tools.exec_in_container(container_name, body.command)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@app.post("/api/docker/stop/{container_name}")
async def stop_container(
    container_name: str,
    _: None = Security(verify_tool_key)
):
    """停止容器（Dify 工具：stop_container）"""
    result = docker_tools.stop_container(container_name)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


# ─────────────────────────────────────────
#  入口
# ─────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=SERVICE_HOST, port=SERVICE_PORT, reload=True)

