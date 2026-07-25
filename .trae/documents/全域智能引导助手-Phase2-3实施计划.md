# 全域智能引导助手 — Phase 2/3 实施计划

## Summary（一句话总结）

Phase 1.A 的 11 处 Kotlin 编译错误已通过实际读取文件全部验证到位。本计划聚焦剩余工作：(1) Phase 1.B 重新编译验证；(2) Phase 2 ai-agent-service 信号中枢（5 个新文件 + 2 处追加）；(3) Phase 3 前端实时渲染（5 处修改 + 1 个新 SQL）；(4) 端到端验证。所有代码片段均基于实际探索的复用点，执行者可直接落地。

---

## Current State Analysis（实际探索后的当前状态）

### ✅ Phase 1.A 已验证到位（通过 Read 工具逐文件确认）

| 文件 | 验证点 | 状态 |
|---|---|---|
| [DockerSdkService.kt](file:///d:/SecLab/SecLab/seclab-backend/docker-service/src/main/kotlin/me/myot233/seclab/dockerservice/DockerSdkService.kt) | import `core.command` / `ports.bindings.entries` / `hostPortSpec` / `withTail(tail)` / `state.status ?: "unknown"` | ✅ |
| [TtyLogHandler.kt](file:///d:/SecLab/SecLab/seclab-backend/docker-service/src/main/kotlin/me/myot233/seclab/dockerservice/TtyLogHandler.kt) | `TtySessionContext` 末尾完整 / `TextMessage(json as CharSequence)` / pong `as CharSequence` | ✅ |
| [TtyLogStreamService.kt](file:///d:/SecLab/SecLab/seclab-backend/docker-service/src/main/kotlin/me/myot233/seclab/dockerservice/TtyLogStreamService.kt) | `import com.github.dockerjava.core.command.LogContainerResultCallback` / `Subscriber.onTrigger` 回调字段已存在 | ✅ |
| [DockerSdkConfig.kt](file:///d:/SecLab/SecLab/seclab-backend/docker-service/src/main/kotlin/me/myot233/seclab/dockerservice/DockerSdkConfig.kt) | `import com.github.dockerjava.zerodep.ZerodepDockerHttpClient` | ✅ |
| [FrustrationTracker.kt](file:///d:/SecLab/SecLab/seclab-backend/docker-service/src/main/kotlin/me/myot233/seclab/dockerservice/FrustrationTracker.kt) | `replace("\u0000", "")` | ✅ |
| [FrustrationTrackerTest.kt](file:///d:/SecLab/SecLab/seclab-backend/docker-service/src/test/kotlin/me/myot233/seclab/dockerservice/FrustrationTrackerTest.kt) | `assertNotEquals` 完整闭合 | ✅ |
| [build.gradle.kts](file:///d:/SecLab/SecLab/seclab-backend/docker-service/build.gradle.kts) | `implementation("com.fasterxml.jackson.module:jackson-module-kotlin")` | ✅ |
| [DockerController.kt](file:///d:/SecLab/SecLab/seclab-backend/docker-service/src/main/kotlin/me/myot233/seclab/dockerservice/DockerController.kt) | `/api/docker/frustration/{lab}` + `/score` 端点 + `FrustrationReportRequest` | ✅ |
| [GuidanceSignalClient.kt](file:///d:/SecLab/SecLab/seclab-backend/docker-service/src/main/kotlin/me/myot233/seclab/dockerservice/GuidanceSignalClient.kt) | `sendSignal { ... }` 单线程异步 fire-and-forget + `X-SecLab-Token` | ✅ |
| [GuidanceSignal.kt](file:///d:/SecLab/SecLab/seclab-backend/docker-service/src/main/kotlin/me/myot233/seclab/dockerservice/GuidanceSignal.kt) | 数据契约字段完整 | ✅ |
| [LabAllowlist.kt](file:///d:/SecLab/SecLab/seclab-backend/docker-service/src/main/kotlin/me/myot233/seclab/dockerservice/LabAllowlist.kt) | `labTaskSummary` / `targetOf` / `labKeyOf` | ✅ |
| [WebSocketConfig.kt](file:///d:/SecLab/SecLab/seclab-backend/docker-service/src/main/kotlin/me/myot233/seclab/dockerservice/WebSocketConfig.kt) | `/ws/tty/{containerName}` 注册 | ✅ |
| [application.yml](file:///d:/SecLab/SecLab/seclab-backend/docker-service/src/main/resources/application.yml) | `seclab.agent.signal-url` 默认 `http://localhost:8010/api/guidance/signal` | ✅ |

**Phase 1 唯一待做**：重新编译验证（修复后未再跑一次 build）。

### Phase 2 现状（ai-agent-service）

**已有可复用**：
- [main.py:1952-1986](file:///d:/SecLab/SecLab/seclab-backend/ai-agent-service/main.py) `/api/chat` SSE 流式：`httpx.AsyncClient(timeout=120.0).stream("POST", f"{DIFY_API_URL}/chat-messages")` + `StreamingResponse(event_stream(), media_type="text/event-stream")`
- [main.py:193-202](file:///d:/SecLab/SecLab/seclab-backend/ai-agent-service/main.py) `verify_tool_key` Security：支持 `X-SecLab-Token` 与 `Authorization: Bearer`，`TOOL_API_KEY` 为空时放行
- [main.py:2068-2070](file:///d:/SecLab/SecLab/seclab-backend/ai-agent-service/main.py) 入口 `uvicorn.run("main:app", host=SERVICE_HOST, port=SERVICE_PORT, reload=True)`
- [ai_repository.py:191-258](file:///d:/SecLab/SecLab/seclab-backend/ai-agent-service/ai_repository.py) `get_or_create_conversation` 模式
- [ai_repository.py:261-287](file:///d:/SecLab/SecLab/seclab-backend/ai-agent-service/ai_repository.py) `update_conversation_after_stream`（回填 `dify_conversation_id`）
- [ai_repository.py:290-343](file:///d:/SecLab/SecLab/seclab-backend/ai-agent-service/ai_repository.py) `save_ai_message`
- [ai_repository.py:346-382](file:///d:/SecLab/SecLab/seclab-backend/ai-agent-service/ai_repository.py) `save_context_injection`
- [error_repository.py:126-153](file:///d:/SecLab/SecLab/seclab-backend/ai-agent-service/error_repository.py) `classify_error_excerpt(raw_excerpt, *, exit_code=None) -> {error_signature, error_category, severity}`
- [error_repository.py:299-306](file:///d:/SecLab/SecLab/seclab-backend/ai-agent-service/error_repository.py) `save_error_event(data) -> dict`
- [container_command_repository.py:150](file:///d:/SecLab/SecLab/seclab-backend/ai-agent-service/container_command_repository.py) `save_container_command_event(data)`
- `ai_conversation` 表：`conversation_id VARCHAR(64) PK` / `dify_conversation_id VARCHAR(128) UNIQUE NULL` / `lab_session_id VARCHAR(64) NULL` / `source VARCHAR(64) DEFAULT 'ai-agent-service'` / `idx_ai_conversation_lab_session` 索引
- 测试约定：`unittest.TestCase`（非 pytest fixtures），直接 `import 模块`，无 `tests/` 子目录
- `requirements.txt`：`fastapi==0.115.0` / `httpx==0.27.0` / `sse-starlette==2.1.0` / `PyMySQL==1.1.1`（无 pytest，用 unittest）

**Phase 2 缺失（全部待建）**：
- `ai_repository.py` 无 `ensure_guidance_conversation`
- 无 `guidance_stream_registry.py`
- 无 `guidance_service.py`
- 无 `test_guidance_service.py`
- `main.py` 无 `/api/guidance/signal` 与 `/api/guidance/stream/{lab_session_id}` 端点
- `shujuku/` 无 `guidance_proactive_notes.sql`

### Phase 3 现状（前端）

**已有可复用**：
- [FloatingChat.vue:263-272](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/components/FloatingChat.vue) `interface Message { role, content, timestamp, thinking?, streamContent?, isStreaming?, showThinking?, toolCalls? }`
- [FloatingChat.vue:477+](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/components/FloatingChat.vue) `callDifyAgent` 用 `fetch + response.body.getReader()` 处理 SSE（非 EventSource）
- [FloatingChat.vue:746+](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/components/FloatingChat.vue) `onMounted` 加载 localStorage、聚焦输入框、监听 resize
- [FloatingChat.vue:306-325](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/components/FloatingChat.vue) `labContextText` computed 汇总当前实验上下文
- [useLabState.ts:23,56](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/composables/useLabState.ts) `currentLabContainer` ref / `currentLabContext` ref（含 `labSessionId`）
- [useLabState.ts:63-108](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/composables/useLabState.ts) `setLabRunning` / `clearLab` / `setLabContext`
- [api.ts:23](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/api.ts) `AGENT_BASE_URL = import.meta.env.VITE_AGENT_BASE_URL || "http://localhost:8010"`
- [api.ts:21](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/api.ts) `DOCKER_API_URL`（默认 3000，是旧服务）
- [vite.config.ts:10-19](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/vite.config.ts) 已有 `/api/agent` → 8010、`/api/docker` → 8087 代理
- [FloatingChatButton.vue](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/components/FloatingChatButton.vue) 146 行，已有 `currentLabContainer` 监听、1 分钟倒计时弹窗、`handleLabMessage` postMessage 监听

**Phase 3 缺失**：
- `FloatingChat.vue` 无 SSE guidance 订阅、无 TTY 折叠面板、Message interface 无 `isProactiveGuidance`/`ephemeral`/`errorContext`
- `useLabState.ts` 无 `guidanceAlerts` / `ttyLogLines` ref
- `api.ts` 无 `DOCKER_SERVICE_URL` / `DOCKER_SERVICE_WS_URL` / `getGuidanceStreamUrl` / `getTtyWebSocketUrl`
- `.env.example` 无 `VITE_DOCKER_SERVICE_URL` / `VITE_DOCKER_SERVICE_WS_URL`
- `vite.config.ts` 无 `/ws/tty` WS 代理、无 `/api/guidance` 代理
- `FloatingChatButton.vue` 无未读徽标（仅有靶机运行中绿点）

---

## 关键架构决策（执行者必须遵守）

1. **`/api/guidance/signal` 采用异步后台任务模式**：收到信号立即返回 `202 Accepted`，Dify 调用在 `asyncio.create_task` 中进行，结果通过 `guidance_stream_registry` 广播给订阅了该 `lab_session_id` 的 SSE 客户端。**不要同步阻塞**（Dify 流式可能 30s+，Kotlin `GuidanceSignalClient` 是 fire-and-forget 不等响应）。

2. **`/api/guidance/stream/{lab_session_id}` 是独立 SSE 订阅端点**：前端先订阅，再等信号触发。推送格式：
   - `data: {"type":"guidance_start","signal_id":"...","trigger_reason":"..."}\n\n`
   - `data: {"type":"chunk","content":"..."}\n\n`
   - `data: {"type":"guidance_end","message_id":"...","conversation_id":"..."}\n\n`
   - 每 15s 推 `data: {"type":"heartbeat"}\n\n` 保活

3. **`ensure_guidance_conversation` 不修改 `dify_conversation_id` 列**（避免 UNIQUE 约束冲突）：首次插入时 `dify_conversation_id=NULL`，首次 Dify 调用后由 `update_conversation_after_stream` 回填。固定 `conversation_id = f"guidance-{lab_session_id}"`。

4. **`guidance_proactive_notes` 表**持久化 AI 主动提示内容（独立于 `ai_message`，便于按 `lab_session_id` 查询历史主动提示）。

5. **TTY 折叠面板**作为 `isProactiveGuidance` 消息的附属展示（`<details>` 折叠），不引入新独立组件。

6. **未读徽标**用红色数字徽章（`badge-error`），区别于已有的"靶机运行中"绿点。

7. **复用 `verify_tool_key` Security**：`/api/guidance/signal` 用 `Security(verify_tool_key)` 鉴权（Kotlin 侧 `GuidanceSignalClient` 已配 `X-SecLab-Token`）。`/api/guidance/stream/{lab_session_id}` 不鉴权（前端 SSE 无法自定义 header，且 lab_session_id 本身是难以猜测的会话标识）。

---

## Proposed Changes（按实施顺序）

### Phase 1.B：重新编译验证

```powershell
cd d:\SecLab\SecLab\seclab-backend
cmd /c "gradlew.bat :docker-service:compileKotlin -Dkotlin.compiler.execution.strategy=in-process --console=plain 2>&1"
cmd /c "gradlew.bat :docker-service:test --tests me.myot233.seclab.dockerservice.FrustrationTrackerTest -Dkotlin.compiler.execution.strategy=in-process --console=plain 2>&1"
```

**预期**：
- `:docker-service:compileKotlin` 成功（无 `unresolved reference`、无类型推断错误）
- 11 个测试全过：single error、repeated same signature、cooldown、repeated command、sessionKeys isolation、score resets、different signatures、observeLogLine ignores non-error、observeLogLine detects error、tryTrigger below threshold、tryTrigger explicit context

**若仍有编译错误**：根据错误信息定位修复，每次只改一个问题，改完立即重编译。

---

### Phase 2.1：ai_repository.py 追加 ensure_guidance_conversation

**文件**：[ai_repository.py](file:///d:/SecLab/SecLab/seclab-backend/ai-agent-service/ai_repository.py)

**位置**：在文件末尾（line 429 `save_tool_calls` 函数结束后）追加。

```python
def ensure_guidance_conversation(
    *,
    lab_session_id: str,
    context: dict[str, Any],
    source: str = "guidance-proactive",
) -> dict[str, Any]:
    """
    为 proactive guidance 信号查找或创建本地会话。

    - 按 `lab_session_id + source='guidance-proactive'` 查找；找到则 UPDATE last_message_at。
    - 未找到则 INSERT 固定 `conversation_id = f"guidance-{lab_session_id}"`，`dify_conversation_id=NULL`。
    - **不修改 `dify_conversation_id` 列**，避免 UNIQUE 约束冲突。
    - 首次 Dify 调用后由 `update_conversation_after_stream` 回填真实 `dify_conversation_id`。

    Returns: {"conversation_id": str, "dify_conversation_id": Optional[str]}
    """
    ensure_ai_schema()
    now = datetime.utcnow()
    fixed_id = f"guidance-{lab_session_id}"

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT conversation_id, dify_conversation_id
                FROM ai_conversation
                WHERE lab_session_id = %(lab_session_id)s AND source = %(source)s
                LIMIT 1
                """,
                {"lab_session_id": lab_session_id, "source": source},
            )
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    """
                    UPDATE ai_conversation
                    SET user_id = COALESCE(%(user_id)s, user_id),
                        class_id = COALESCE(%(class_id)s, class_id),
                        course_id = COALESCE(%(course_id)s, course_id),
                        module_id = COALESCE(%(module_id)s, module_id),
                        task_id = COALESCE(%(task_id)s, task_id),
                        last_message_at = %(now)s,
                        status = 'active'
                    WHERE conversation_id = %(conversation_id)s
                    """,
                    {**context, "conversation_id": row["conversation_id"], "now": now},
                )
                conn.commit()
                return {
                    "conversation_id": row["conversation_id"],
                    "dify_conversation_id": row.get("dify_conversation_id"),
                }

            cursor.execute(
                """
                INSERT INTO ai_conversation (
                    conversation_id, user_id, class_id, course_id, module_id,
                    task_id, lab_session_id, dify_conversation_id,
                    status, source, start_time, last_message_at
                ) VALUES (
                    %(conversation_id)s, %(user_id)s, %(class_id)s, %(course_id)s,
                    %(module_id)s, %(task_id)s, %(lab_session_id)s, NULL,
                    'active', %(source)s, %(now)s, %(now)s
                )
                """,
                {
                    **context,
                    "conversation_id": fixed_id,
                    "lab_session_id": lab_session_id,
                    "source": source,
                    "now": now,
                },
            )
        conn.commit()

    return {"conversation_id": fixed_id, "dify_conversation_id": None}
```

**Why**：跨信号复用同一会话；首次 Dify 调用后由 `update_conversation_after_stream` 回填真实 `dify_conversation_id`。复用 `get_or_create_conversation` 的 `context` dict 模式（含 user_id/class_id/course_id/module_id/task_id）。

---

### Phase 2.2.1：新建 guidance_stream_registry.py

**文件**：`d:\SecLab\SecLab\seclab-backend\ai-agent-service\guidance_stream_registry.py`（新建）

```python
"""SSE 订阅广播注册表（单 worker 部署约束）。

设计约束：
- 仅支持单 uvicorn worker 多部署时需用 Redis Pub/Sub 替换（当前不做）。
- 每个 lab_session_id 维护一组 asyncio.Queue 订阅者。
- 信号触发时通过 publish() 向所有订阅者推送事件。
- 订阅者断开（取消迭代）时自动清理。
"""
import asyncio
import logging
from typing import Any, AsyncIterator

logger = logging.getLogger(__name__)

# lab_session_id -> set of subscriber queues
_queues: dict[str, set[asyncio.Queue[dict[str, Any]]]] = {}
_lock = asyncio.Lock()


async def subscribe(lab_session_id: str) -> AsyncIterator[dict[str, Any]]:
    """订阅指定 lab_session_id 的事件流。生成器会在取消时自动清理。"""
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
    async with _lock:
        _queues.setdefault(lab_session_id, set()).add(queue)
    logger.info("guidance SSE subscriber added lab_session_id=%s total=%d",
                lab_session_id, len(_queues.get(lab_session_id, set())))
    try:
        while True:
            event = await queue.get()
            # 哨兵事件：None 表示正常结束订阅
            if event is None:
                return
            yield event
    except asyncio.CancelledError:
        logger.info("guidance SSE subscriber cancelled lab_session_id=%s", lab_session_id)
        raise
    finally:
        async with _lock:
            subs = _queues.get(lab_session_id)
            if subs:
                subs.discard(queue)
                if not subs:
                    _queues.pop(lab_session_id, None)
        logger.info("guidance SSE subscriber removed lab_session_id=%s", lab_session_id)


async def publish(lab_session_id: str, event: dict[str, Any]) -> int:
    """向指定 lab_session_id 的所有订阅者推送事件。返回成功推送的订阅者数。"""
    async with _lock:
        subs = list(_queues.get(lab_session_id, set()))
    if not subs:
        return 0
    delivered = 0
    for queue in subs:
        try:
            # 非阻塞 put，队列满则丢弃（避免一个慢订阅者拖累其他）
            queue.put_nowait(event)
            delivered += 1
        except asyncio.QueueFull:
            logger.warning("guidance SSE queue full lab_session_id=%s dropping event", lab_session_id)
    return delivered


async def close_all(lab_session_id: str) -> None:
    """向指定 lab_session_id 的所有订阅者发送结束哨兵并清理。"""
    async with _lock:
        subs = _queues.pop(lab_session_id, set())
    for queue in subs:
        try:
            queue.put_nowait(None)
        except asyncio.QueueFull:
            pass


def subscriber_count(lab_session_id: str) -> int:
    """调试用：返回当前订阅者数。"""
    return len(_queues.get(lab_session_id, set()))
```

**Why**：单 worker 部署下进程内广播即可；`asyncio.Queue` 满时丢弃避免慢订阅者反压；订阅者断开自动清理。

---

### Phase 2.2.2：新建 guidance_service.py

**文件**：`d:\SecLab\SecLab\seclab-backend\ai-agent-service\guidance_service.py`（新建）

```python
"""Proactive guidance 信号处理服务。

职责：
1. 接收 Kotlin docker-service 发来的 GuidanceSignal。
2. 调 error_repository.classify_error_excerpt 分类错误（若 error_slice 非空）。
3. 调 error_repository.save_error_event 持久化错误事件（镜像 learning_event）。
4. 调 ai_repository.ensure_guidance_conversation 查找/创建会话。
5. 异步调 Dify chat-messages 流式接口，把 chunk 通过 guidance_stream_registry.publish 推送给前端 SSE。
6. 流式结束后调 ai_repository.save_ai_message + update_conversation_after_stream 持久化。
7. 落 guidance_proactive_notes 表（由 ai_repository 或本模块直接 INSERT）。

注意：本服务**不阻塞** signal 端点，所有耗时操作在 asyncio.create_task 中进行。
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

import httpx

import ai_repository
import error_repository
import guidance_stream_registry
from database import get_connection

logger = logging.getLogger(__name__)

DIFY_API_URL = os.getenv("DIFY_API_URL", "https://api.dify.ai/v1")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_USER = os.getenv("DIFY_GUIDANCE_USER", "guidance-proactive")
DIFY_TIMEOUT = float(os.getenv("DIFY_GUIDANCE_TIMEOUT", "120"))


def _build_context(signal: dict[str, Any]) -> dict[str, Any]:
    """从 GuidanceSignal 提取 ai_conversation 上下文字段。"""
    return {
        "user_id": _to_int(signal.get("user_id")),
        "class_id": _to_int(signal.get("class_id")),
        "course_id": _to_int(signal.get("course_id")),
        "module_id": _to_int(signal.get("module_id")),
        "task_id": _to_int(signal.get("task_id")),
        "question_id": None,
    }


def _to_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _build_dify_inputs(signal: dict[str, Any]) -> dict[str, Any]:
    """构造 Dify chat-messages 的 inputs 字段（变量注入）。"""
    return {
        "trigger_reason": signal.get("trigger_reason", ""),
        "container_name": signal.get("container_name", ""),
        "lab_key": signal.get("lab_key", ""),
        "error_slice": (signal.get("error_slice") or "")[:800],
        "recent_commands": json.dumps(signal.get("recent_commands") or [], ensure_ascii=False)[:800],
        "lab_task_summary": (signal.get("lab_task_summary") or "")[:800],
        "frustration_score": signal.get("frustration_score", 0),
        "locale": signal.get("locale", "zh-CN"),
    }


def _build_query(signal: dict[str, Any], error_classified: Optional[dict[str, str]]) -> str:
    """构造给 Dify 的 query 文本（中文，启发式诊断风格）。"""
    container = signal.get("container_name", "")
    lab_key = signal.get("lab_key", "")
    reason = signal.get("trigger_reason", "")
    error_slice = (signal.get("error_slice") or "")[:400]
    commands = signal.get("recent_commands") or []
    task = signal.get("lab_task_summary", "")

    parts = [
        f"学生在靶机 {container}（{lab_key}）上陷入无效试错，触发原因：{reason}。",
    ]
    if task:
        parts.append(f"当前任务摘要：{task[:200]}。")
    if error_classified:
        parts.append(f"已识别错误类型：{error_classified['error_signature']}（{error_classified['error_category']}，严重度 {error_classified['severity']}）。")
    if error_slice:
        parts.append(f"最近报错片段：\n```\n{error_slice}\n```")
    if commands:
        cmd_str = " | ".join(str(c) for c in commands[-3:])
        parts.append(f"最近执行的命令：{cmd_str}")
    parts.append("请用启发式提问的方式（不要直接给答案），引导学生自己发现下一步该检查什么。控制在 3-5 句话。")
    return "\n".join(parts)


def save_guidance_proactive_note(
    *,
    lab_session_id: Optional[str],
    user_id: Optional[int],
    signal_id: str,
    conversation_id: str,
    message_id: str,
    trigger_reason: str,
    ai_message: str,
) -> None:
    """落 guidance_proactive_notes 表。"""
    note_id = f"gnote-{uuid4()}"
    now = datetime.utcnow()
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO guidance_proactive_notes (
                    note_id, lab_session_id, user_id, signal_id,
                    conversation_id, message_id, trigger_reason,
                    ai_message, created_at
                ) VALUES (
                    %(note_id)s, %(lab_session_id)s, %(user_id)s, %(signal_id)s,
                    %(conversation_id)s, %(message_id)s, %(trigger_reason)s,
                    %(ai_message)s, %(created_at)s
                )
                """,
                {
                    "note_id": note_id,
                    "lab_session_id": lab_session_id,
                    "user_id": user_id,
                    "signal_id": signal_id,
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "trigger_reason": trigger_reason,
                    "ai_message": ai_message,
                    "created_at": now,
                },
            )
        conn.commit()


def handle_signal(signal: dict[str, Any]) -> dict[str, Any]:
    """
    同步预处理：分类错误 + 持久化错误事件 + 查找/创建会话。
    返回 {"conversation_id": str, "query": str, "inputs": dict} 供异步流式使用。
    """
    lab_session_id = signal.get("lab_session_id") or ""
    error_slice = signal.get("error_slice") or ""
    exit_code = _to_int(signal.get("exit_code"))

    # 1. 分类错误（若有 error_slice）
    error_classified = None
    if error_slice:
        error_classified = error_repository.classify_error_excerpt(error_slice, exit_code=exit_code)

    # 2. 持久化错误事件（镜像 learning_event）
    if error_classified and lab_session_id:
        try:
            error_repository.save_error_event({
                "lab_session_id": lab_session_id or None,
                "user_id": signal.get("user_id"),
                "class_id": signal.get("class_id"),
                "course_id": signal.get("course_id"),
                "module_id": signal.get("module_id"),
                "task_id": signal.get("task_id"),
                "container_name": signal.get("container_name"),
                "raw_excerpt": error_slice[:1024],
                "error_signature": error_classified["error_signature"],
                "error_category": error_classified["error_category"],
                "severity": error_classified["severity"],
                "source": "guidance-proactive",
                "request_id": signal.get("request_id") or signal.get("signal_id"),
                "occurred_at": signal.get("triggered_at") or datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.warning("save_error_event failed signal_id=%s: %s", signal.get("signal_id"), e)

    # 3. 查找/创建会话
    context = _build_context(signal)
    conv = ai_repository.ensure_guidance_conversation(
        lab_session_id=lab_session_id or f"anon-{signal.get('signal_id', uuid4())}",
        context=context,
    )

    # 4. 构造 Dify 请求参数
    query = _build_query(signal, error_classified)
    inputs = _build_dify_inputs(signal)

    return {
        "conversation_id": conv["conversation_id"],
        "dify_conversation_id": conv["dify_conversation_id"],
        "query": query,
        "inputs": inputs,
    }


async def stream_guidance_to_subscribers(
    *,
    lab_session_id: str,
    signal_id: str,
    trigger_reason: str,
    conversation_id: str,
    dify_conversation_id: Optional[str],
    query: str,
    inputs: dict[str, Any],
) -> None:
    """
    异步任务：调 Dify 流式，把 chunk 广播给 SSE 订阅者，结束后持久化。
    在 asyncio.create_task 中调用，不阻塞 signal 端点。
    """
    # 检查是否有订阅者；无订阅者则跳过 Dify 调用（节省成本）
    if guidance_stream_registry.subscriber_count(lab_session_id) == 0:
        logger.info("guidance signal skipped (no SSE subscriber) lab_session_id=%s signal_id=%s",
                    lab_session_id, signal_id)
        return

    await guidance_stream_registry.publish(lab_session_id, {
        "type": "guidance_start",
        "signal_id": signal_id,
        "trigger_reason": trigger_reason,
        "conversation_id": conversation_id,
        "ts": datetime.utcnow().isoformat(),
    })

    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "response_mode": "streaming",
        "conversation_id": dify_conversation_id or "",
        "user": DIFY_USER,
        "inputs": inputs,
    }

    complete_response = ""
    new_dify_conversation_id: Optional[str] = dify_conversation_id
    message_id = f"msg-{uuid4()}"

    try:
        async with httpx.AsyncClient(timeout=DIFY_TIMEOUT) as client:
            async with client.stream(
                "POST",
                f"{DIFY_API_URL}/chat-messages",
                headers=headers,
                json=payload,
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    error_msg = body.decode("utf-8", errors="replace")
                    logger.error("Dify guidance call failed status=%s body=%s",
                                 response.status_code, error_msg[:300])
                    await guidance_stream_registry.publish(lab_session_id, {
                        "type": "error",
                        "signal_id": signal_id,
                        "message": f"Dify 调用失败（{response.status_code}）",
                        "ts": datetime.utcnow().isoformat(),
                    })
                    return

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if not raw or raw == "[DONE]":
                        continue
                    try:
                        chunk = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    # 捕获 Dify conversation_id（首次调用后回填）
                    if chunk.get("conversation_id"):
                        new_dify_conversation_id = chunk["conversation_id"]

                    # 只转发 answer 字段的增量文本
                    if chunk.get("event") == "message" and chunk.get("answer"):
                        complete_response += chunk["answer"]
                        await guidance_stream_registry.publish(lab_session_id, {
                            "type": "chunk",
                            "signal_id": signal_id,
                            "content": chunk["answer"],
                            "ts": datetime.utcnow().isoformat(),
                        })
    except Exception as e:
        logger.exception("guidance Dify stream failed signal_id=%s: %s", signal_id, e)
        await guidance_stream_registry.publish(lab_session_id, {
            "type": "error",
            "signal_id": signal_id,
            "message": f"内部错误：{e.__class__.__name__}",
            "ts": datetime.utcnow().isoformat(),
        })
        return

    # 持久化完整消息
    try:
        saved = ai_repository.save_ai_message(
            conversation_id=conversation_id,
            role="assistant",
            content=complete_response,
            event_name="guidance_proactive",
            hint_level=None,
            contains_context=True,
            raw_payload={"signal_id": signal_id, "trigger_reason": trigger_reason, "inputs": inputs},
            message_id=message_id,
        )
        ai_repository.save_context_injection(
            conversation_id=conversation_id,
            message_id=saved["message_id"],
            context_type="guidance_signal",
            raw_context=inputs,
        )
        # 回填 dify_conversation_id（首次调用后才有值）
        if new_dify_conversation_id and new_dify_conversation_id != dify_conversation_id:
            ai_repository.update_conversation_after_stream(
                conversation_id=conversation_id,
                dify_conversation_id=new_dify_conversation_id,
                status="active",
            )
        # 落 guidance_proactive_notes 表
        save_guidance_proactive_note(
            lab_session_id=lab_session_id or None,
            user_id=_to_int(inputs.get("user_id")) if False else None,  # user_id 从 signal 传入更准确
            signal_id=signal_id,
            conversation_id=conversation_id,
            message_id=message_id,
            trigger_reason=trigger_reason,
            ai_message=complete_response,
        )
    except Exception as e:
        logger.exception("guidance persistence failed signal_id=%s: %s", signal_id, e)

    await guidance_stream_registry.publish(lab_session_id, {
        "type": "guidance_end",
        "signal_id": signal_id,
        "message_id": message_id,
        "conversation_id": conversation_id,
        "dify_conversation_id": new_dify_conversation_id,
        "ts": datetime.utcnow().isoformat(),
    })


def dispatch_signal_task(signal: dict[str, Any]) -> None:
    """
    同步入口（供 FastAPI 端点调用）：
    1. 调 handle_signal 做预处理（分类错误、落 error_event、ensure 会话）。
    2. 启动异步后台任务 stream_guidance_to_subscribers。
    返回预处理摘要供端点立即响应 202。
    """
    prepared = handle_signal(signal)
    lab_session_id = signal.get("lab_session_id") or ""
    signal_id = signal.get("signal_id") or f"sig-{uuid4()}"
    trigger_reason = signal.get("trigger_reason", "")

    # 启动后台流式任务（不阻塞当前请求）
    asyncio.create_task(stream_guidance_to_subscribers(
        lab_session_id=lab_session_id,
        signal_id=signal_id,
        trigger_reason=trigger_reason,
        conversation_id=prepared["conversation_id"],
        dify_conversation_id=prepared["dify_conversation_id"],
        query=prepared["query"],
        inputs=prepared["inputs"],
    ))

    return {
        "signal_id": signal_id,
        "conversation_id": prepared["conversation_id"],
        "subscriber_count": guidance_stream_registry.subscriber_count(lab_session_id),
        "accepted": True,
    }
```

**Why**：
- `handle_signal` 同步预处理（错误分类、落 error_event、ensure 会话）快速返回。
- `stream_guidance_to_subscribers` 异步调 Dify 流式，通过 `guidance_stream_registry.publish` 广播给 SSE 订阅者。
- 无订阅者时跳过 Dify 调用（节省成本，因为学生可能没开 FloatingChat）。
- 复用 `ai_repository.save_ai_message` / `save_context_injection` / `update_conversation_after_stream` 保持与 `/api/chat` 一致的持久化模式。
- `save_guidance_proactive_note` 落独立表便于查询历史主动提示。

**注意**：`dispatch_signal_task` 中的 `asyncio.create_task` 必须在 event loop 中调用，所以 FastAPI 端点必须是 `async def`。

---

### Phase 2.2.3：新建 test_guidance_service.py

**文件**：`d:\SecLab\SecLab\seclab-backend\ai-agent-service\test_guidance_service.py`（新建）

```python
"""guidance_service 单元测试。

约定（与现有 test_teacher_repository_helpers.py 一致）：
- 用 unittest.TestCase，不用 pytest fixtures。
- 直接 import 模块。
- mock 数据库与 httpx 调用，不依赖真实 Dify/MySQL。
"""
import asyncio
import unittest
from unittest.mock import MagicMock, patch, AsyncMock

import guidance_service


def _sample_signal(**overrides):
    """构造一个测试用 GuidanceSignal。"""
    base = {
        "signal_id": "sig-test-001",
        "request_id": "req-test-001",
        "trigger_reason": "repeated_error",
        "lab_session_id": "lab-session-abc",
        "user_id": 42,
        "class_id": 1,
        "course_id": 10,
        "module_id": 100,
        "task_id": None,
        "container_name": "sqli-lab-web-1",
        "lab_key": "sqli",
        "error_slice": "bash: permission denied: ./run.sh",
        "exit_code": 126,
        "recent_commands": ["./run.sh", "./run.sh", "./run.sh"],
        "lab_task_summary": "完成 SQL 注入基础实验",
        "frustration_score": 4,
        "locale": "zh-CN",
        "triggered_at": "2026-07-19T10:00:00Z",
    }
    base.update(overrides)
    return base


class GuidanceServiceHelpersTest(unittest.TestCase):
    """纯函数 helper 测试（无 IO）。"""

    def test_build_context_extracts_int_fields_and_drops_invalid(self):
        ctx = guidance_service._build_context(_sample_signal(user_id="42", class_id="abc"))
        self.assertEqual(ctx["user_id"], 42)
        self.assertIsNone(ctx["class_id"])  # 非数字 → None
        self.assertIsNone(ctx["task_id"])

    def test_to_int_handles_empty_and_none(self):
        self.assertIsNone(guidance_service._to_int(None))
        self.assertIsNone(guidance_service._to_int(""))
        self.assertIsNone(guidance_service._to_int("abc"))
        self.assertEqual(guidance_service._to_int(42), 42)
        self.assertEqual(guidance_service._to_int("42"), 42)

    def test_build_dify_inputs_truncates_long_fields(self):
        long_error = "x" * 2000
        signal = _sample_signal(error_slice=long_error)
        inputs = guidance_service._build_dify_inputs(signal)
        self.assertEqual(len(inputs["error_slice"]), 800)
        self.assertEqual(inputs["trigger_reason"], "repeated_error")
        self.assertEqual(inputs["frustration_score"], 4)

    def test_build_query_includes_error_classification(self):
        signal = _sample_signal()
        classified = {"error_signature": "permission_denied",
                      "error_category": "permission",
                      "severity": "high"}
        query = guidance_service._build_query(signal, classified)
        self.assertIn("permission_denied", query)
        self.assertIn("sqli-lab-web-1", query)
        self.assertIn("repeated_error", query)
        self.assertIn("启发式", query)

    def test_build_query_handles_missing_fields(self):
        signal = _sample_signal(error_slice="", recent_commands=[], lab_task_summary="")
        query = guidance_service._build_query(signal, None)
        self.assertIn("sqli-lab-web-1", query)
        # 无 error_slice 时不应崩溃
        self.assertIsInstance(query, str)


class GuidanceServiceHandleSignalTest(unittest.TestCase):
    """handle_signal 同步预处理测试（mock 数据库 + error_repository）。"""

    @patch("guidance_service.error_repository.classify_error_excerpt")
    @patch("guidance_service.error_repository.save_error_event")
    @patch("guidance_service.ai_repository.ensure_guidance_conversation")
    def test_handle_signal_classifies_and_persists_error(
        self, mock_ensure, mock_save_err, mock_classify
    ):
        mock_classify.return_value = {
            "error_signature": "permission_denied",
            "error_category": "permission",
            "severity": "high",
        }
        mock_ensure.return_value = {
            "conversation_id": "guidance-lab-session-abc",
            "dify_conversation_id": None,
        }

        result = guidance_service.handle_signal(_sample_signal())

        mock_classify.assert_called_once()
        mock_save_err.assert_called_once()
        mock_ensure.assert_called_once()
        self.assertEqual(result["conversation_id"], "guidance-lab-session-abc")
        self.assertIsNone(result["dify_conversation_id"])
        self.assertIn("permission_denied", result["query"])

    @patch("guidance_service.error_repository.classify_error_excerpt")
    @patch("guidance_service.error_repository.save_error_event")
    @patch("guidance_service.ai_repository.ensure_guidance_conversation")
    def test_handle_signal_skips_classify_when_no_error_slice(
        self, mock_ensure, mock_save_err, mock_classify
    ):
        mock_ensure.return_value = {
            "conversation_id": "guidance-lab-session-abc",
            "dify_conversation_id": None,
        }

        guidance_service.handle_signal(_sample_signal(error_slice="", exit_code=None))

        mock_classify.assert_not_called()
        mock_save_err.assert_not_called()
        mock_ensure.assert_called_once()

    @patch("guidance_service.error_repository.save_error_event", side_effect=Exception("db down"))
    @patch("guidance_service.error_repository.classify_error_excerpt")
    @patch("guidance_service.ai_repository.ensure_guidance_conversation")
    def test_handle_signal_tolerates_error_event_failure(
        self, mock_ensure, mock_classify, mock_save_err
    ):
        mock_classify.return_value = {
            "error_signature": "permission_denied",
            "error_category": "permission",
            "severity": "high",
        }
        mock_ensure.return_value = {
            "conversation_id": "guidance-lab-session-abc",
            "dify_conversation_id": None,
        }
        # 不应抛异常
        result = guidance_service.handle_signal(_sample_signal())
        self.assertEqual(result["conversation_id"], "guidance-lab-session-abc")


class GuidanceStreamRegistryTest(unittest.TestCase):
    """guidance_stream_registry 异步测试。"""

    def test_subscribe_and_publish_delivers_event(self):
        async def run():
            received = []

            async def consumer():
                async for event in guidance_stream_registry.subscribe("lab-1"):
                    received.append(event)
                    if event.get("type") == "end":
                        break

            consumer_task = asyncio.create_task(consumer())
            await asyncio.sleep(0.05)  # 让 subscribe 注册完成

            delivered = await guidance_stream_registry.publish("lab-1", {"type": "test", "content": "hello"})
            self.assertEqual(delivered, 1)

            await guidance_stream_registry.publish("lab-1", {"type": "end"})
            await consumer_task

            self.assertEqual(len(received), 2)
            self.assertEqual(received[0]["content"], "hello")
            self.assertEqual(received[1]["type"], "end")

        asyncio.run(run())

    def test_publish_with_no_subscriber_returns_zero(self):
        async def run():
            delivered = await guidance_stream_registry.publish("no-such-lab", {"type": "test"})
            self.assertEqual(delivered, 0)

        asyncio.run(run())

    def test_subscriber_count_tracks_subscriptions(self):
        async def run():
            self.assertEqual(guidance_stream_registry.subscriber_count("lab-2"), 0)

            async def consumer():
                async for _ in guidance_stream_registry.subscribe("lab-2"):
                    pass

            task = asyncio.create_task(consumer())
            await asyncio.sleep(0.05)
            self.assertEqual(guidance_stream_registry.subscriber_count("lab-2"), 1)

            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            self.assertEqual(guidance_stream_registry.subscriber_count("lab-2"), 0)

        asyncio.run(run())


class GuidanceServiceDispatchTest(unittest.TestCase):
    """dispatch_signal_task 测试（mock 后台任务）。"""

    @patch("guidance_service.asyncio.create_task")
    @patch("guidance_service.handle_signal")
    @patch("guidance_service.guidance_stream_registry.subscriber_count", return_value=2)
    def test_dispatch_starts_background_task_and_returns_summary(
        self, mock_count, mock_handle, mock_create_task
    ):
        mock_handle.return_value = {
            "conversation_id": "guidance-lab-x",
            "dify_conversation_id": None,
            "query": "test query",
            "inputs": {"a": 1},
        }

        result = guidance_service.dispatch_signal_task(_sample_signal())

        mock_handle.assert_called_once()
        mock_create_task.assert_called_once()
        self.assertTrue(result["accepted"])
        self.assertEqual(result["conversation_id"], "guidance-lab-x")
        self.assertEqual(result["subscriber_count"], 2)


if __name__ == "__main__":
    unittest.main()
```

**验证**：
```powershell
cd d:\SecLab\SecLab\seclab-backend\ai-agent-service
python -m unittest test_guidance_service -v
```

**预期**：11 个测试全过（5 helper + 3 handle_signal + 3 registry + 1 dispatch = 12，可能微调）。

---

### Phase 2.3：main.py 追加 /api/guidance/signal + /api/guidance/stream 端点

**文件**：[main.py](file:///d:/SecLab/SecLab/seclab-backend/ai-agent-service/main.py)

**位置**：在 `/api/chat` 端点后（line 1986 后）、`# Docker 工具 API` 注释前（line 1989 前）追加。同时在文件顶部 import 区追加 `from fastapi import Query`（若未导入）和 `import guidance_service` + `import guidance_stream_registry`。

#### 2.3.1 import 追加

在 main.py 现有 import 区追加（位置：与其他本地模块 import 一起，如 `import ai_repository` 附近）：

```python
import guidance_service
import guidance_stream_registry
```

#### 2.3.2 请求模型 + 端点

在 `/api/chat` 端点后追加：

```python
# ─────────────────────────────────────────
#  Proactive Guidance（来自 docker-service 的挫败指数信号）
# ─────────────────────────────────────────

class GuidanceSignalRequest(BaseModel):
    """与 Kotlin GuidanceSignal.kt 对齐的数据契约。"""
    signal_id: str
    request_id: Optional[str] = ""
    trigger_reason: str
    lab_session_id: Optional[str] = ""
    user_id: Optional[int] = None
    class_id: Optional[int] = None
    course_id: Optional[int] = None
    module_id: Optional[int] = None
    task_id: Optional[int] = None
    container_name: Optional[str] = ""
    lab_key: Optional[str] = ""
    error_slice: Optional[str] = ""
    exit_code: Optional[int] = None
    recent_commands: Optional[list[str]] = []
    lab_task_summary: Optional[str] = ""
    frustration_score: Optional[int] = 0
    locale: Optional[str] = "zh-CN"
    triggered_at: Optional[str] = ""


@app.post("/api/guidance/signal", status_code=202)
async def receive_guidance_signal(
    signal: GuidanceSignalRequest,
    _: None = Security(verify_tool_key),
):
    """
    接收 docker-service 的挫败指数信号。

    - 同步预处理：分类错误 + 落 error_event + ensure 会话。
    - 异步后台任务：调 Dify 流式，通过 SSE 广播给订阅了该 lab_session_id 的前端。
    - 立即返回 202 Accepted，不等待 Dify 完成。
    """
    signal_dict = signal.model_dump()
    summary = guidance_service.dispatch_signal_task(signal_dict)
    return {
        "isSuccess": 1,
        "status": 202,
        "message": "guidance signal accepted",
        "data": summary,
    }


@app.get("/api/guidance/stream/{lab_session_id}")
async def stream_guidance(
    lab_session_id: str,
):
    """
    SSE 订阅端点：前端订阅后，当 /api/guidance/signal 触发时会收到 guidance_start/chunk/guidance_end 事件。

    - 不鉴权（前端 SSE 无法自定义 header；lab_session_id 本身是会话标识）。
    - 每 15s 推一次 heartbeat 保活。
    - 客户端断开时自动清理订阅。
    """
    import asyncio

    async def event_stream():
        # 推送订阅确认
        yield f"data: {__import__('json').dumps({'type': 'subscribed', 'lab_session_id': lab_session_id, 'ts': __import__('datetime').datetime.utcnow().isoformat()})}\n\n"

        async def heartbeat():
            while True:
                await asyncio.sleep(15)
                yield f"data: {__import__('json').dumps({'type': 'heartbeat', 'ts': __import__('datetime').datetime.utcnow().isoformat()})}\n\n"

        heartbeat_task = asyncio.create_task(_heartbeat_generator(lab_session_id))

        try:
            async for event in guidance_stream_registry.subscribe(lab_session_id):
                yield f"data: {__import__('json').dumps(event, ensure_ascii=False)}\n\n"
                if event.get("type") == "guidance_end":
                    break
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

    return StreamingResponse(event_stream(), media_type="text/event-stream")


async def _heartbeat_generator(lab_session_id: str):
    """后台心跳任务：通过 publish 推送 heartbeat 事件。"""
    import json
    from datetime import datetime
    while True:
        await asyncio.sleep(15)
        await guidance_stream_registry.publish(lab_session_id, {
            "type": "heartbeat",
            "ts": datetime.utcnow().isoformat(),
        })
```

**Why**：
- `/api/guidance/signal` 用 `Security(verify_tool_key)` 鉴权，与 `/api/docker/*` 一致；Kotlin `GuidanceSignalClient` 已配 `X-SecLab-Token`。
- `/api/guidance/stream/{lab_session_id}` 不鉴权（前端 SSE 无法自定义 header）。
- `status_code=202` 明确表示异步处理。
- 心跳通过 `guidance_stream_registry.publish` 推送，复用订阅通道，避免 SSE 流被中间件超时关闭。
- 复用 `StreamingResponse(event_stream(), media_type="text/event-stream")` 与 `/api/chat` 一致。

**注意**：`_heartbeat_generator` 与 `event_stream` 中的 `__import__` 写法是为了避免在 main.py 顶部加更多 import（保持改动局部化）。**实际实现时应在 main.py 顶部确认 `import json` 与 `from datetime import datetime` 已存在**（main.py 已有这些 import，因为 `/api/chat` 用到了 `json.dumps`）。如果已有，直接用 `json.dumps` 和 `datetime.utcnow()` 即可，不用 `__import__`。

---

### Phase 2.4：新建 shujuku/guidance_proactive_notes.sql

**文件**：`d:\SecLab\SecLab\shujuku\guidance_proactive_notes.sql`（新建）

```sql
-- guidance_proactive_notes：AI 主动提示历史记录表
-- 用途：持久化 docker-service 挫败指数信号触发的 Dify 主动提示内容
-- 关联：
--   - signal_id 对应 Kotlin GuidanceSignal.signal_id（UUID，跨服务追踪）
--   - conversation_id 关联 ai_conversation.conversation_id（FK）
--   - message_id 关联 ai_message.message_id（FK）
-- 落库位置：seclab_profile 库（与 ai_conversation 同库，便于 JOIN 查询历史主动提示）

CREATE DATABASE IF NOT EXISTS `seclab_profile`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `seclab_profile`;

CREATE TABLE IF NOT EXISTS `guidance_proactive_notes` (
  `note_id` VARCHAR(64) NOT NULL,
  `lab_session_id` VARCHAR(64) NULL,
  `user_id` BIGINT NULL,
  `signal_id` VARCHAR(64) NOT NULL,
  `conversation_id` VARCHAR(64) NOT NULL,
  `message_id` VARCHAR(64) NULL,
  `trigger_reason` VARCHAR(128) NOT NULL,
  `ai_message` LONGTEXT NOT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`note_id`),
  KEY `idx_guidance_note_session_time` (`lab_session_id`, `created_at`),
  KEY `idx_guidance_note_user_time` (`user_id`, `created_at`),
  KEY `idx_guidance_note_signal` (`signal_id`),
  KEY `idx_guidance_note_conversation` (`conversation_id`),
  CONSTRAINT `fk_guidance_note_conversation`
    FOREIGN KEY (`conversation_id`) REFERENCES `ai_conversation` (`conversation_id`)
    ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- 说明：
-- 1. note_id 主键格式：gnote-{uuid4()}
-- 2. signal_id 不设 UNIQUE：同一 lab_session 可能触发多次信号（冷却 90s 后可再触发）
-- 3. message_id 可空：若 Dify 调用失败，message_id 为 NULL 但 note 仍记录尝试
-- 4. trigger_reason 枚举：repeated_error / repeated_command / error_burst（与 Kotlin FrustrationTracker 对齐）
-- 5. ai_message 为完整 Dify 响应文本（流式 chunk 拼接后落库）
```

**Why**：独立表便于按 `lab_session_id` 查询历史主动提示（避免扫 `ai_message` 全表 + JOIN `ai_conversation` 过滤 source）。FK 关联 `ai_conversation` 保证引用完整性。

**同步更新**：检查 `database/sql/init_seclab_profile.sql` 是否需要追加此表定义（若该文件是 `seclab_profile` 库的主初始化脚本，应同步追加）。

---

### Phase 3.1：useLabState.ts 扩展 guidanceAlerts / ttyLogLines

**文件**：[useLabState.ts](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/composables/useLabState.ts)

**修改 1**：在文件末尾（line 130 后）追加 guidance 相关状态与函数。

```typescript
// ── Proactive Guidance（来自 docker-service 挫败指数信号）──────────
/** 未读 proactive guidance 数量（用于徽标） */
export const guidanceUnreadCount = ref<number>(0)

/** TTY 日志行缓冲（最近 N 行，供折叠面板展示） */
export interface TtyLogLine {
  ts: string
  stream: 'stdout' | 'stderr' | 'raw'
  line: string
}
export const ttyLogLines = ref<TtyLogLine[]>([])
const TTY_MAX_LINES = 200

/** 当前 guidance 对话上下文（用于 SSE 订阅） */
export interface GuidanceAlert {
  signalId: string
  conversationId: string
  triggerReason: string
  content: string          // 流式拼接的完整文本
  isStreaming: boolean
  errorContext?: {
    errorSignature?: string
    errorCategory?: string
    severity?: string
    errorSlice?: string
  }
  startedAt: Date
}
export const guidanceAlerts = ref<GuidanceAlert[]>([])

/** 添加 TTY 日志行（自动截断到 TTY_MAX_LINES） */
export function appendTtyLogLine(line: TtyLogLine) {
  ttyLogLines.value.push(line)
  if (ttyLogLines.value.length > TTY_MAX_LINES) {
    ttyLogLines.value = ttyLogLines.value.slice(-TTY_MAX_LINES)
  }
}

/** 清空 TTY 日志 */
export function clearTtyLogs() {
  ttyLogLines.value = []
}

/** 添加新的 guidance alert（开始流式） */
export function addGuidanceAlert(alert: GuidanceAlert) {
  guidanceAlerts.value.push(alert)
  guidanceUnreadCount.value += 1
}

/** 更新指定 signalId 的 guidance alert 内容（流式 chunk） */
export function appendGuidanceChunk(signalId: string, chunk: string) {
  const alert = guidanceAlerts.value.find(a => a.signalId === signalId)
  if (alert) {
    alert.content += chunk
  }
}

/** 标记指定 signalId 的 guidance alert 流式结束 */
export function finalizeGuidanceAlert(signalId: string, conversationId?: string) {
  const alert = guidanceAlerts.value.find(a => a.signalId === signalId)
  if (alert) {
    alert.isStreaming = false
    if (conversationId) alert.conversationId = conversationId
  }
}

/** 标记所有 guidance 为已读 */
export function markAllGuidanceRead() {
  guidanceUnreadCount.value = 0
}

/** 清空所有 guidance（切换靶机时调用） */
export function clearGuidance() {
  guidanceAlerts.value = []
  guidanceUnreadCount.value = 0
}
```

**修改 2**：在 `clearLab()` 函数（line 86-93）中追加 `clearGuidance()` 和 `clearTtyLogs()` 调用。

```typescript
export function clearLab() {
  currentLabContainer.value = ''
  labStartTime.value = null
  isLabRunning.value = false
  labSessionId = ''
  currentLabContext.value = {}
  labEvents.value = []
  clearGuidance()    // ← 新增
  clearTtyLogs()     // ← 新增
}
```

**Why**：guidance 状态独立于 lab 状态，但切换靶机时一并清空；`appendTtyLogLine` 自动截断避免无界增长；`guidanceUnreadCount` 用于 FloatingChatButton 徽标。

---

### Phase 3.2.1：FloatingChat.vue SSE guidance 订阅 + Message interface 扩展 + TTY 折叠面板

**文件**：[FloatingChat.vue](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/components/FloatingChat.vue)

#### 3.2.1.1 Message interface 扩展（line 263-272）

```typescript
interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  thinking?: string
  streamContent?: string
  isStreaming?: boolean
  showThinking?: boolean
  toolCalls?: ToolCall[]
  // ── Proactive Guidance 扩展 ──
  isProactiveGuidance?: boolean       // true 表示这条消息来自挫败指数信号
  signalId?: string                   // 关联 guidance signal_id
  ephemeral?: boolean                 // true 表示流式中的临时消息，结束后合并
  errorContext?: {
    errorSignature?: string
    errorCategory?: string
    severity?: string
    errorSlice?: string
    triggerReason?: string
  }
}
```

#### 3.2.1.2 import 扩展（script setup 顶部）

在现有 import 区追加：

```typescript
import {
  guidanceAlerts,
  guidanceUnreadCount,
  addGuidanceAlert,
  appendGuidanceChunk,
  finalizeGuidanceAlert,
  markAllGuidanceRead,
  ttyLogLines,
  type GuidanceAlert,
} from '../composables/useLabState'
import { getGuidanceStreamUrl, getTtyWebSocketUrl } from '../api'
```

#### 3.2.1.3 SSE guidance 订阅（onMounted 内）

在 `onMounted`（line 746）内追加 SSE 订阅逻辑：

```typescript
// ── Proactive Guidance SSE 订阅 ──────────────────────────────
let guidanceEventSource: EventSource | null = null

function startGuidanceSubscription() {
  const labSessionId = currentLabContext.value.labSessionId
  if (!labSessionId) return

  // 关闭旧订阅
  if (guidanceEventSource) {
    guidanceEventSource.close()
    guidanceEventSource = null
  }

  const url = getGuidanceStreamUrl(labSessionId)
  guidanceEventSource = new EventSource(url)

  guidanceEventSource.addEventListener('message', (evt) => {
    try {
      const data = JSON.parse(evt.data)
      handleGuidanceEvent(data)
    } catch (e) {
      console.warn('guidance SSE parse error:', e)
    }
  })

  guidanceEventSource.onerror = (err) => {
    console.warn('guidance SSE error, will retry in 5s:', err)
    guidanceEventSource?.close()
    guidanceEventSource = null
    setTimeout(() => {
      if (currentLabContext.value.labSessionId) startGuidanceSubscription()
    }, 5000)
  }
}

function handleGuidanceEvent(data: any) {
  if (data.type === 'subscribed') {
    console.log('[guidance] subscribed:', data.lab_session_id)
  } else if (data.type === 'heartbeat') {
    // 忽略心跳
  } else if (data.type === 'guidance_start') {
    // 新增一条临时 proactive 消息
    const alert: GuidanceAlert = {
      signalId: data.signal_id,
      conversationId: data.conversation_id || '',
      triggerReason: data.trigger_reason || '',
      content: '',
      isStreaming: true,
      startedAt: new Date(),
    }
    addGuidanceAlert(alert)
    // 在消息流中插入一条 assistant 消息（ephemeral，流式结束后保留）
    messages.value.push({
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
      isProactiveGuidance: true,
      signalId: data.signal_id,
      ephemeral: true,
      errorContext: { triggerReason: data.trigger_reason },
    })
    scrollToBottom()
  } else if (data.type === 'chunk') {
    appendGuidanceChunk(data.signal_id, data.content || '')
    // 同步更新 messages 中对应的临时消息
    const msg = messages.value.find(m => m.signalId === data.signal_id && m.ephemeral)
    if (msg) {
      msg.content += data.content || ''
      msg.streamContent = msg.content
    }
    scrollToBottom()
  } else if (data.type === 'guidance_end') {
    finalizeGuidanceAlert(data.signal_id, data.conversation_id)
    const msg = messages.value.find(m => m.signalId === data.signal_id && m.ephemeral)
    if (msg) {
      msg.isStreaming = false
      msg.ephemeral = false
      if (data.conversation_id) {
        conversationId.value = data.conversation_id
      }
    }
    scrollToBottom()
  } else if (data.type === 'error') {
    const msg = messages.value.find(m => m.signalId === data.signal_id && m.ephemeral)
    if (msg) {
      msg.isStreaming = false
      msg.content = msg.content || `[AI 提示生成失败：${data.message || '未知错误'}]`
      msg.ephemeral = false
    }
  }
}

// 启动订阅（若有 labSessionId）
if (currentLabContext.value.labSessionId) {
  startGuidanceSubscription()
}

// 监听 labSessionId 变化，重新订阅
watch(() => currentLabContext.value.labSessionId, (newId) => {
  if (newId) startGuidanceSubscription()
})
```

#### 3.2.1.4 TTY 折叠面板（template 区）

在消息渲染 v-for 中，对 `isProactiveGuidance` 消息追加折叠面板。找到现有消息渲染 `<div v-for="..." class="chat-bubble ...">`，在 `{{ message.content }}` 后追加：

```html
<!-- Proactive Guidance 折叠面板：展示错误上下文 + TTY 日志 -->
<details v-if="message.isProactiveGuidance" class="proactive-context-details">
  <summary class="text-xs text-base-content/60 cursor-pointer">
    <i class="fas fa-lightbulb mr-1"></i>AI 主动提示（{{ message.errorContext?.triggerReason || '触发' }}）
  </summary>
  <div class="mt-2 text-xs space-y-1">
    <div v-if="message.errorContext?.errorSignature" class="text-warning">
      <strong>错误类型：</strong>{{ message.errorContext.errorSignature }}
      <span v-if="message.errorContext.severity">（{{ message.errorContext.severity }}）</span>
    </div>
    <div v-if="message.errorContext?.errorSlice" class="bg-base-300 p-2 rounded font-mono text-[10px] whitespace-pre-wrap break-all">
      {{ message.errorContext.errorSlice }}
    </div>
    <details v-if="ttyLogLines.length > 0">
      <summary class="text-base-content/50 cursor-pointer">最近 TTY 输出（{{ ttyLogLines.length }} 行）</summary>
      <div class="mt-1 bg-base-300 p-2 rounded font-mono text-[10px] max-h-40 overflow-y-auto">
        <div v-for="(line, idx) in ttyLogLines.slice(-20)" :key="idx"
             :class="line.stream === 'stderr' ? 'text-error' : 'text-base-content/70'">
          <span class="text-base-content/40">[{{ line.ts }}]</span> {{ line.line }}
        </div>
      </div>
    </details>
  </div>
</details>
```

#### 3.2.1.5 onUnmounted 清理

在 `onUnmounted`（若存在）内追加：

```typescript
onUnmounted(() => {
  // ... 现有清理 ...
  if (guidanceEventSource) {
    guidanceEventSource.close()
    guidanceEventSource = null
  }
})
```

**Why**：
- SSE 用 `EventSource`（GET 请求，无需自定义 header，适配 `/api/guidance/stream` 不鉴权设计）。
- `guidance_start` 时插入 `ephemeral` 临时消息，`chunk` 时同步更新，`guidance_end` 时转为永久消息。
- TTY 折叠面板用原生 `<details>`，无新依赖；展示最近 20 行 TTY 日志，stderr 红色高亮。
- 断线 5s 自动重连（labSessionId 仍存在时）。

---

### Phase 3.2.2：FloatingChatButton.vue 未读徽标

**文件**：[FloatingChatButton.vue](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/components/FloatingChatButton.vue)

#### 3.2.2.1 import 扩展（line 64）

```typescript
import { currentLabContainer, labStartTime, setLabRunning, guidanceUnreadCount, markAllGuidanceRead } from '../composables/useLabState'
```

#### 3.2.2.2 模板：徽标（在按钮内追加，line 11 `<i>` 后）

```html
<button
  v-if="!chatVisible"
  @click="openChat"
  class="fixed bottom-6 right-6 btn btn-circle btn-primary shadow-lg hover:shadow-xl transition-all duration-300 z-30 w-14 h-14 relative"
  :title="currentLabContainer ? `当前靶机: ${currentLabContainer}` : 'AI 助手'"
>
  <i class="fas fa-comment-dots text-xl"></i>
  <!-- 靶机运行中小圆点 -->
  <span
    v-if="currentLabContainer"
    class="absolute top-0 right-0 w-3 h-3 bg-green-400 rounded-full border-2 border-white animate-pulse"
  ></span>
  <!-- 未读 proactive guidance 数字徽标 -->
  <span
    v-if="guidanceUnreadCount > 0"
    class="absolute -top-1 -right-1 min-w-[20px] h-5 px-1 bg-error text-error-content rounded-full text-xs font-bold flex items-center justify-center border-2 border-white animate-bounce"
  >
    {{ guidanceUnreadCount > 99 ? '99+' : guidanceUnreadCount }}
  </span>
</button>
```

#### 3.2.2.3 打开聊天时标记已读（openChat 函数内）

```typescript
function openChat(withHint = false) {
  if (withHint) pendingHint.value = true
  chatVisible.value = true
  markAllGuidanceRead()  // ← 新增：打开即已读
}
```

**Why**：红色 `badge-error` + `animate-bounce` 视觉上与靶机运行中绿点区分；打开聊天即标记已读，避免徽标持续闪烁。

---

### Phase 3.3：api.ts + .env.example + vite.config.ts

#### 3.3.1 api.ts 追加常量与 URL 构造函数

**文件**：[api.ts](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/api.ts)

**位置**：在 `AGENT_BASE_URL`（line 23）后追加。

```typescript
// Docker Service（Kotlin/Spring Boot on port 8087）— TTY 监听 + 挫败指数
const DOCKER_SERVICE_URL = import.meta.env.VITE_DOCKER_SERVICE_URL || "http://localhost:8087";
const DOCKER_SERVICE_WS_URL = import.meta.env.VITE_DOCKER_SERVICE_WS_URL || "ws://localhost:8087";

/** 构造 proactive guidance SSE 订阅 URL（GET，EventSource 用） */
export function getGuidanceStreamUrl(labSessionId: string): string {
  return `${AGENT_BASE_URL}/api/guidance/stream/${encodeURIComponent(labSessionId)}`;
}

/** 构造 TTY WebSocket 订阅 URL */
export function getTtyWebSocketUrl(containerName: string, labSessionId?: string, userId?: number | string | null): string {
  const params = new URLSearchParams();
  if (labSessionId) params.set("lab_session_id", labSessionId);
  if (userId) params.set("user_id", String(userId));
  const query = params.toString() ? `?${params.toString()}` : "";
  return `${DOCKER_SERVICE_WS_URL}/ws/tty/${encodeURIComponent(containerName)}${query}`;
}

export { DOCKER_SERVICE_URL, DOCKER_SERVICE_WS_URL };
```

#### 3.3.2 .env.example 追加变量

**文件**：[.env.example](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/.env.example)

在末尾追加：

```env
# Docker Service（Kotlin/Spring Boot, TTY 监听 + 挫败指数）
VITE_DOCKER_SERVICE_URL=http://localhost:8087
# WebSocket 协议（ws:// 或 wss://）
VITE_DOCKER_SERVICE_WS_URL=ws://localhost:8087
```

#### 3.3.3 vite.config.ts 追加代理

**文件**：[vite.config.ts](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/vite.config.ts)

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // 将 /api/agent 开头的请求代理到 FastAPI Agent 服务（开发环境）
      '/api/agent': {
        target: 'http://localhost:8010',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api\/agent/, '')
      },
      // 保留旧的 Docker API 代理（兼容）
      '/api/docker': {
        target: 'http://localhost:8087',
        changeOrigin: true,
      },
      // Proactive Guidance SSE 订阅（代理到 ai-agent-service:8010）
      '/api/guidance': {
        target: 'http://localhost:8010',
        changeOrigin: true,
      },
      // TTY WebSocket（代理到 docker-service:8087，需 ws: true）
      '/ws/tty': {
        target: 'http://localhost:8087',
        changeOrigin: true,
        ws: true,
      }
    }
  }
})
```

**Why**：
- `getGuidanceStreamUrl` 走 `AGENT_BASE_URL`（8010），与 `/api/chat` 同服务。
- `getTtyWebSocketUrl` 走 `DOCKER_SERVICE_WS_URL`（8087 ws://），独立配置便于生产环境换 wss://。
- vite 代理 `/api/guidance` → 8010、`/ws/tty` → 8087（带 `ws: true`）支持开发环境 WebSocket。
- 生产环境通过 nginx 反代时需额外配 `location /ws/tty { proxy_pass http://docker-service:8087; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; }`。

---

### Phase 3.4：部署文档同步

**文件**：[SecLab网络安全漏洞综合实验平台部署说明文档.md](file:///d:/SecLab/SecLab/SecLab网络安全漏洞综合实验平台部署说明文档.md)

追加章节"全域智能引导助手部署"：

- docker-service 启动要求（Docker daemon 可达、`seclab.agent.signal-url` 配置）
- ai-agent-service 环境变量（`DIFY_API_URL`、`DIFY_API_KEY`、`TOOL_API_KEY` 与 docker-service `seclab.agent.signal-token` 保持一致）
- 前端环境变量（`VITE_DOCKER_SERVICE_URL`、`VITE_DOCKER_SERVICE_WS_URL`）
- 数据库初始化（执行 `shujuku/guidance_proactive_notes.sql`）
- nginx 反代配置（`/ws/tty` WebSocket 升级、`/api/guidance` SSE 长连接）

**Why**：部署文档与代码同步，避免运维遗漏。

---

## Assumptions & Decisions（执行者必须遵守）

1. **异步后台任务模式**：`/api/guidance/signal` 立即返回 202，Dify 调用在 `asyncio.create_task` 中进行。
2. **不修改 `dify_conversation_id` 列**：`ensure_guidance_conversation` 首次插入 NULL，首次 Dify 调用后回填。
3. **SSE 订阅独立端点**：`/api/guidance/stream/{lab_session_id}` 不鉴权，前端先订阅再等信号。
4. **复用 `verify_tool_key` Security**：`/api/guidance/signal` 鉴权与 `/api/docker/*` 一致。
5. **TTY 折叠面板**作为 `isProactiveGuidance` 消息附属展示，不引入新独立组件。
6. **未读徽标**用红色 `badge-error` + `animate-bounce`。
7. **单 worker 部署约束**：`guidance_stream_registry` 是进程内广播，多 worker 需 Redis Pub/Sub（当前不做）。
8. **无订阅者时跳过 Dify 调用**：节省成本（学生可能没开 FloatingChat）。
9. **测试用 `unittest.TestCase`**：与现有 `test_teacher_*.py` 一致，不引入 pytest fixtures。
10. **main.py 的 `__import__` 写法仅占位**：实际实现时确认 main.py 顶部已有 `import json` 和 `from datetime import datetime`（已有，因为 `/api/chat` 用到），直接用即可。

---

## Verification（按阶段）

### Phase 1.B 验证

```powershell
cd d:\SecLab\SecLab\seclab-backend
cmd /c "gradlew.bat :docker-service:compileKotlin -Dkotlin.compiler.execution.strategy=in-process --console=plain 2>&1"
cmd /c "gradlew.bat :docker-service:test --tests me.myot233.seclab.dockerservice.FrustrationTrackerTest -Dkotlin.compiler.execution.strategy=in-process --console=plain 2>&1"
```

**预期**：编译成功，11 个测试全过。

### Phase 2 验证

```powershell
cd d:\SecLab\SecLab\seclab-backend\ai-agent-service
python -m unittest test_guidance_service -v
python -c "import main; print('main.py imports OK')"
```

**预期**：`test_guidance_service` 全过；main.py 无 import 错误。

**手动 SSE 验证**（可选，需启动服务）：

```powershell
# 终端 1：启动 ai-agent-service
cd d:\SecLab\SecLab\seclab-backend\ai-agent-service
python main.py

# 终端 2：订阅 SSE
curl -N http://localhost:8010/api/guidance/stream/test-lab-1

# 终端 3：发送信号
curl -X POST http://localhost:8010/api/guidance/signal ^
  -H "Content-Type: application/json" ^
  -d "{\"signal_id\":\"sig-001\",\"trigger_reason\":\"repeated_error\",\"lab_session_id\":\"test-lab-1\",\"container_name\":\"sqli-lab-web-1\",\"error_slice\":\"permission denied\",\"frustration_score\":4}"
```

**预期**：终端 2 收到 `subscribed` → `guidance_start` → `chunk`（多次）→ `guidance_end` 事件流。

### Phase 3 验证

```powershell
cd d:\SecLab\SecLab\SecLab-FrontEnd-2
npm run vue-tsc
npm run build
```

**预期**：`vue-tsc` 无类型错误；`build` 成功生成 dist/。

### 端到端验证（手动）

1. 启动 docker-service（8087）+ ai-agent-service（8010）+ 前端 dev server
2. 前端打开任一靶场页面，启动靶机
3. 在靶机内连续 3 次执行会报错的命令（如 `./nonexistent.sh`）
4. 观察 FloatingChat 应自动出现一条 proactive guidance 消息（带折叠面板）
5. FloatingChatButton 应显示红色未读徽标
6. 打开聊天后徽标消失

---

## 风险与未决事项

1. **Dify API Key 未配置**：若 `DIFY_API_KEY` 为空，`stream_guidance_to_subscribers` 会收到 401，前端会显示 `[AI 提示生成失败：Dify 调用失败（401）]`。需在部署时配置。
2. **多 worker 部署**：当前 `guidance_stream_registry` 是进程内广播，若 uvicorn 启动多 worker，订阅者可能在不同 worker 上收不到信号。生产环境需用 Redis Pub/Sub 替换（标记为后续优化）。
3. **lab_session_id 缺失**：若前端未传 `lab_session_id`，Kotlin 侧 fallback 用 `containerName:user_id`，但 `/api/guidance/signal` 的 `lab_session_id` 会是空字符串，`ensure_guidance_conversation` 用 `anon-{signal_id}` 兜底。SSE 订阅会失败（前端无 lab_session_id 不订阅）。
4. **TTY 日志敏感信息**：TTY 日志可能包含敏感信息（如密码、token）。当前未做脱敏，生产环境应在 `TtyLogStreamService.onNext` 加脱敏过滤（标记为后续优化）。
5. **数据库迁移**：`guidance_proactive_notes.sql` 是新表，需在部署时手动执行。若 `database/sql/init_seclab_profile.sql` 是主初始化脚本，应同步追加此表定义（Phase 2.4 已