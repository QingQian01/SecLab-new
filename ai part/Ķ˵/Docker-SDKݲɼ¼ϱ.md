# SecLab 后端改动说明 — Docker SDK 数据采集 & 事件上报

> 改动日期：2026-04-25
> 涉及模块：ai-agent-service (Python FastAPI)、docker-api-server.js (Node.js Express)

---

## 一、改动目标

1. 在后端利用 Docker SDK 自动采集容器运行时数据（日志、资源、进程）
2. 新增 `POST /api/external/events/ingest` 端点，接收前端事件 + 自动补充 Docker 数据
3. 补全 `docker-api-server.js` 中缺失的 API 端点（stop、list、logs、exec、start）

---

## 二、改动文件清单

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `seclab/ai-agent-service/docker_tools.py` | 重写 | 新增 Docker SDK 数据采集函数 |
| `seclab/ai-agent-service/main.py` | 修改 | 新增 `/api/external/events/ingest` 端点 |
| `seclab/docker-api-server.js` | 修改 | 补全缺失的 Docker API 端点 |
| `SecLab-FrontEnd-2/src/api.ts` | 修改 | 修正 `ingestEvents` 请求地址为 Agent 服务 |

---

## 三、各文件详细改动

### 3.1 `seclab/ai-agent-service/docker_tools.py`

**新增导入：**

```python
import re
from datetime import datetime, timezone
```

**新增常量 — 日志分类正则：**

```python
_SQL_PATTERNS = [
    re.compile(r"(sqlmap|union\s+select|order\s+by\s+\d+|'\s*OR\s+1\s*=\s*1|--|;\s*drop\s)", re.IGNORECASE),
]
_XSS_PATTERNS = [
    re.compile(r"(<script|javascript:|onerror\s*=|onload\s*=|alert\s*\()", re.IGNORECASE),
]
_CMD_PATTERNS = [
    re.compile(r"(;\s*(cat|ls|whoami|id|uname|pwd|ifconfig|netstat|ping|wget|curl|nc|bash|sh)\b)", re.IGNORECASE),
]
_FILE_PATTERNS = [
    re.compile(r"(\.\.\/|\.\.\\|/etc/passwd|/etc/shadow|/proc/self)", re.IGNORECASE),
]
_UPLOAD_PATTERNS = [
    re.compile(r"(\.php|\.jsp|\.asp|\.aspx|\.sh|\.py|webshell|backdoor)", re.IGNORECASE),
]
_ERROR_PATTERNS = [
    re.compile(r"(error|exception|syntax\s*error|fatal|warning|mysql).*?(?:near|at\s+line|in\s+)", re.IGNORECASE),
]
_HTTP_PATTERNS = [
    re.compile(r'"\w+\s+(\S+)\s+HTTP', re.IGNORECASE),
]
```

**新增函数 — `collect_container_runtime_data()`：**

```python
def collect_container_runtime_data(container_name: str, tail: int = 200) -> dict:
    """
    采集容器运行时数据，用于事件上报。
    返回结构化的运行时信息，包括：
      - 容器状态（运行/停止、启动时间、运行时长）
      - 资源使用（CPU、内存、网络IO、磁盘IO）
      - 容器日志解析为事件列表（COMMAND_EXEC, ERROR_EVENT, FILE_CHANGE 等）
      - 容器进程列表
    """
```

**采集的数据项：**

| 类别 | 数据项 | Docker SDK API |
|------|--------|----------------|
| 容器信息 | name, status, image, started_at, duration_seconds, ports, exit_code | `container.attrs["State"]` |
| CPU 使用率 | cpu_percent | `container.stats(stream=False)` |
| 内存使用 | memory_usage_mb, memory_limit_mb, memory_percent | `stats["memory_stats"]` |
| 网络 IO | network_rx_bytes, network_tx_bytes | `stats["networks"]` |
| 磁盘 IO | block_read_bytes, block_write_bytes | `stats["blkio_stats"]` |
| 进程列表 | titles, processes (前20条) | `container.top()` |
| 日志事件 | COMMAND_EXEC, ERROR_EVENT, FILE_CHANGE | `container.logs(tail=200)` + 正则分类 |

**日志分类规则：**

| 正则匹配 | 事件类型 | extra.category |
|----------|----------|----------------|
| SQL 注入特征 (sqlmap, union select, order by, OR 1=1) | `COMMAND_EXEC` | `sql_injection` |
| XSS 特征 (script, javascript:, onerror, alert) | `COMMAND_EXEC` | `xss_attack` |
| 命令注入特征 (; cat, ; ls, ; whoami, ; bash) | `COMMAND_EXEC` | `command_injection` |
| 路径遍历特征 (../, /etc/passwd, /proc/self) | `FILE_CHANGE` | `path_traversal` |
| 恶意上传特征 (.php, .jsp, webshell) | `FILE_CHANGE` | `malicious_upload` |
| 错误特征 (error, exception, syntax error) | `ERROR_EVENT` | `syntax` |
| HTTP 请求特征 ("GET/POST ... HTTP") | `COMMAND_EXEC` | `http_request` |

**新增函数 — `build_ingest_payload()`：**

```python
def build_ingest_payload(
    container_name: str,
    user_id: int,
    class_id: int,
    course_id: int,
    module_id: int,
    lab_session_id: str,
    frontend_events: Optional[list] = None,
    duration_seconds: int = 0,
    is_completed: bool = False,
) -> dict:
    """
    构建完整的事件上报 payload。
    自动采集 Docker 容器运行时数据，与前端传入事件合并。
    """
```

此函数：
1. 调用 `collect_container_runtime_data()` 获取容器运行时数据
2. 将 Docker 日志事件与前端事件合并
3. 追加 `LAB_STOP` 事件（含容器信息和资源使用数据）
4. 组装完整的 `events/ingest` payload

---

### 3.2 `seclab/ai-agent-service/main.py`

**新增请求模型：**

```python
class EventsIngestRequest(BaseModel):
    """前端事件上报请求模型"""
    batch_id: str
    source_system: str = "external-agent"
    generated_at: str
    user_context: dict
    events: list
    ai_generated_questions: Optional[list] = []
    profile_rebuild: Optional[dict] = None
```

**新增端点 — `POST /api/external/events/ingest`：**

```python
@app.post("/api/external/events/ingest")
async def ingest_events(req: EventsIngestRequest):
    """
    接收前端上报的实验事件数据。
    后端自动通过 Docker SDK 补充容器运行时数据（日志、资源、进程），
    合并后存储到内存事件列表。
    """
```

**处理流程：**

```
前端 POST /api/external/events/ingest
         │
         ▼
   解析请求中的 container_name
         │
         ▼
   调用 docker_tools.collect_container_runtime_data()
   (采集容器状态、资源、日志、进程)
         │
         ▼
   去重合并：前端事件 + Docker 日志事件
         │
         ▼
   为每条事件附加 docker_runtime 信息
   (container_info, resource_usage)
         │
         ▼
   存入 _lab_events 内存列表
   (最多保留 500 条)
         │
         ▼
   返回统计信息
   (total_events, frontend_events, docker_enriched_events)
```

**返回格式：**

```json
{
  "isSuccess": 1,
  "status": 200,
  "message": "事件上报成功，共 8 条事件（含 3 条 Docker SDK 补充）",
  "data": {
    "batch_id": "batch-20260425-3",
    "total_events": 8,
    "frontend_events": 5,
    "docker_enriched_events": 3,
    "container_runtime_available": true
  }
}
```

---

### 3.3 `seclab/docker-api-server.js`

**新增端点：**

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/docker/list` | 获取所有容器列表（名称+状态） |
| GET | `/api/docker/containers` | 获取指定容器详情（?name=xxx） |
| GET | `/api/docker/logs/:container_name` | 获取容器日志（?tail=100） |
| POST | `/api/docker/exec/:container_name` | 在容器内执行命令（body: {command}） |
| POST | `/api/docker/stop/:container_name` | 停止指定容器 |
| POST | `/api/docker/start/:container_name` | 启动指定容器 |

**修复：** 原文件中存在乱码注释（UTF-8 编码问题），已一并修复。

---

### 3.4 `SecLab-FrontEnd-2/src/api.ts`

**修正 `ingestEvents` 请求地址：**

```diff
  export async function ingestEvents(payload: EventsIngestPayload): Promise<Result<unknown>> {
+     const AGENT_BASE_URL = import.meta.env.VITE_AGENT_BASE_URL || "http://localhost:8010";
      try {
-         const response = await axios.post(`${BASE_URL}/external/events/ingest`, payload, {
+         const response = await axios.post(`${AGENT_BASE_URL}/api/external/events/ingest`, payload, {
              headers: { 'Content-Type': 'application/json' }
          })
```

**说明：** 事件上报端点在 Python FastAPI Agent 服务（端口 8010）上，而非 Spring Boot 后端（端口 8083）。使用 `VITE_AGENT_BASE_URL` 环境变量，默认 `http://localhost:8010`。

---

## 四、完整数据流

```
前端：用户点击"结束实验"
         │
         ▼
   前端收集事件 (LAB_START, FLAG_SUBMIT)
         │
         ▼
   POST http://localhost:8010/api/external/events/ingest
   (含前端事件 + user_context)
         │
         ▼
   后端 FastAPI 接收请求
         │
         ├─→ docker_tools.collect_container_runtime_data()
         │     ├─ container.attrs → 容器信息
         │     ├─ container.stats() → CPU/内存/网络/磁盘
         │     ├─ container.top() → 进程列表
         │     └─ container.logs() → 日志解析为事件
         │           ├─ SQL 注入 → COMMAND_EXEC (sql_injection)
         │           ├─ XSS 攻击 → COMMAND_EXEC (xss_attack)
         │           ├─ 命令注入 → COMMAND_EXEC (command_injection)
         │           ├─ 路径遍历 → FILE_CHANGE (path_traversal)
         │           ├─ 恶意上传 → FILE_CHANGE (malicious_upload)
         │           ├─ 错误日志 → ERROR_EVENT (syntax)
         │           └─ HTTP 请求 → COMMAND_EXEC (http_request)
         │
         ├─→ 去重合并前端事件 + Docker 事件
         │
         ├─→ 为每条事件附加 docker_runtime 信息
         │
         ├─→ 存入 _lab_events 内存列表
         │
         └─→ 返回统计信息给前端
         │
         ▼
   前端：POST http://localhost:3000/api/docker/stop/{container}
   (停止容器)
         │
         ▼
   clearLab() 清理状态
```

---

## 五、Docker SDK 采集数据示例

### 容器信息

```json
{
  "name": "sqli-lab-web-1",
  "status": "running",
  "image": "sqli-lab-web:latest",
  "image_id": "sha256:abc123def456",
  "started_at": "2026-04-25T10:00:00Z",
  "duration_seconds": 1800,
  "ports": {"80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8091"}]},
  "exit_code": null,
  "error": ""
}
```

### 资源使用

```json
{
  "cpu_percent": 2.35,
  "memory_usage_mb": 45.67,
  "memory_limit_mb": 512.00,
  "memory_percent": 8.92,
  "network_rx_bytes": 125829,
  "network_tx_bytes": 524288,
  "block_read_bytes": 1048576,
  "block_write_bytes": 524288
}
```

### 日志解析事件

```json
[
  {
    "event_id": "evt-cmd-a1b2c3d4e5f6",
    "event_type": "COMMAND_EXEC",
    "event_time": "2026-04-25T10:05:00Z",
    "container_name": "sqli-lab-web-1",
    "command": "GET /item?id=1' OR 1=1-- HTTP/1.1",
    "output_digest": "GET /item?id=1' OR 1=1-- HTTP/1.1",
    "extra": {
      "category": "sql_injection",
      "raw_log": "192.168.1.100 - - [25/Apr/2026:10:05:00] \"GET /item?id=1' OR 1=1-- HTTP/1.1\" 200 1234"
    }
  },
  {
    "event_id": "evt-error-g7h8i9j0k1l2",
    "event_type": "ERROR_EVENT",
    "event_time": "2026-04-25T10:08:00Z",
    "container_name": "sqli-lab-web-1",
    "error_signature": "syntax_error",
    "error_category": "syntax",
    "raw_excerpt": "SQL syntax error near '...' at line 1",
    "severity": "medium",
    "extra": {
      "raw_log": "SQL syntax error near '...' at line 1"
    }
  }
]
```

---

## 六、部署注意事项

1. **Python 依赖**：`docker_tools.py` 已有的 `docker==7.1.0` 依赖无需变更，所有新功能均基于现有 Docker SDK

2. **FastAPI 服务地址**：
   - 本地开发：`http://localhost:8010`
   - 生产环境：通过 cpolar 暴露为 `http://2c58645.r6.cpolar.top`
   - 前端通过 `VITE_AGENT_BASE_URL` 环境变量配置

3. **Node.js Docker API 服务**：
   - 新增的端点与 OpenAPI spec 中定义的路径完全一致
   - 前端通过 `VITE_DOCKER_API_URL`（默认 `http://localhost:3000`）访问

4. **数据存储**：当前事件存储在内存 `_lab_events` 列表中（最多 500 条），生产环境建议替换为 Redis 或数据库

5. **安全**：Docker 工具 API 通过白名单 `ALLOWED_CONTAINER_PREFIXES` 限制可操作的容器，仅允许靶场相关容器
