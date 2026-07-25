# SecLab网络安全漏洞综合实验平台部署说明文档

## 1. 系统概述

SecLab是一个网络安全漏洞综合实验平台，包含：

- **前端界面**：Vue3 + Vite + TypeScript
- **后端微服务**：Spring Cloud + Docker容器化部署
- **实验环境**：6个漏洞实验容器（SQL注入、XSS、CSRF、文件上传、目录遍历、命令注入）
- **数据库**：MySQL（主系统 + 实验环境）

## 2. 环境要求

### 2.1 基础环境

- **操作系统**：Windows 10/11、Linux或macOS
- **Docker**：Docker Desktop 4.0+
- **Java**：JDK 17（必须）
- **Node.js**：16.0+（前端开发）
- **内存**：至少8GB RAM
- **磁盘空间**：至少10GB可用空间

### 2.2 端口要求

确保以下端口未被占用：

- **前端**：5173（开发）、80（生产）
- **后端服务**：8080-8095, 8761
- **数据库**：3306
- **实验环境**：8090-8095

## 3. 项目结构

```
SecLab项目/
├── SecLab-FrontEnd-2/          # 前端项目（Vue3 + Vite）
├── seclab-backend/             # 后端微服务与靶场源码
│   ├── gateway/                # 网关服务
│   ├── eureka/                 # 服务注册中心
│   ├── user-service/           # 用户服务
│   ├── experiment-module-service/ # 课程模块服务
│   ├── image-service/          # 图片服务
│   ├── docker-service/         # Docker 容器管理服务
│   ├── ai-agent-service/       # AI 辅助服务
│   ├── sqli-lab/               # SQL注入实验
│   ├── xss-lab/                # XSS实验
│   ├── csrf-lab/               # CSRF实验
│   ├── file-upload-lab/        # 文件上传实验
│   ├── directory-traversal-lab/ # 目录遍历实验
│   └── command-inject/         # 命令注入实验
├── database/sql/               # 数据库主初始化脚本
├── shujuku/                    # 数据库细粒度建表脚本
└── SecLab网络安全漏洞综合实验平台部署说明文档.md  # 本文档
```

## 4. 部署流程

### 4.1 环境准备

1. **安装Docker Desktop**
   - 下载并安装Docker Desktop
   - 启动Docker服务
2. **安装JDK 17**
   ```bash
   # 检查Java版本
   java -version
   # 确保显示Java 17
   ```
3. **安装Node.js**
   ```bash
   # 检查Node.js版本
   node -v
   npm -v
   ```

### 4.2 后端服务部署

#### 方法一：一键部署（推荐）

```bash
cd seclab-backend
.\rebuild-all.bat && .\rebuild-services.bat && .\start-all-services.bat
```

（现在用下面这个打开！！！）

```bash
cd D:\SecLab\SecLab\seclab-backend
.\start-all-services.bat
```

cd D:\SecLab\SecLab\seclab-backend\user-service

> > .\gradlew\.bat bootRun

#### 方法二：分步部署

```bash
cd seclab-backend

# 1. 编译微服务
.\rebuild-all.bat

# 2. 构建Docker镜像
.\rebuild-services.bat

# 3. 启动所有服务
.\start-all-services.bat
```

### 4.3 前端项目部署

#### 4.3.1 安装依赖

```bash
cd SecLab-FrontEnd-2

# 清理并重新安装依赖
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json
npm install
```

#### 4.3.2 修复依赖问题

如果遇到 `@lucky-canvas/vue` 相关错误：

```bash
# 卸载冲突的依赖
npm uninstall @lucky-canvas/vue

# 编辑 src/main.ts，删除或注释以下行：
# import VueLuckyCanvas from '@lucky-canvas/vue'
# .use(VueLuckyCanvas)
```

#### 4.3.3 启动前端服务

```bash
# 本地开发模式
npm run dev

# 网络访问模式（允许局域网访问）
npx vite --host

# 或修改 package.json 中的 dev 脚本
# "dev": "vite --host 0.0.0.0"
```

### 4.4 AI Agent 服务部署

#### 4.4.1 环境准备

```bash
cd seclab-backend/ai-agent-service

# 复制环境变量配置文件
Copy-Item .env.example .env

# 编辑 .env 文件，根据需要修改配置（特别是 DIFY_API_KEY）
notepad .env
```

#### 4.4.2 安装 Python 依赖

```bash
# 确保已安装 Python 3.8+
python --version

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate

# 安装依赖
pip install -r requirements.txt
```

#### 4.4.3 启动 Agent 服务

**方式一：Python 直接运行（开发环境）**

```bash
# 确保在 ai-agent-service 目录下
cd seclab-backend/ai-agent-service

# 激活虚拟环境（如果使用）
.\venv\Scripts\Activate


# 启动 FastAPI 服务
python main.py
```

**方式二：Docker 运行（生产环境）**

```bash
cd seclab-backend/ai-agent-service

# 使用 Docker Compose 启动
docker-compose up -d

# 查看日志
docker logs -f seclab-ai-agent
```

#### 4.4.4 Proactive Guidance 全域智能引导配置（可选）

全域智能引导助手通过 WebSocket 旁路监听终端输出与代码报错，构建"数据拦截-状态评估-动态反馈"闭环。当 `docker-service` 的 `FrustrationTracker` 检测到学生挫败指数超阈值时，会向 `ai-agent-service` 发送信号，由后者调用 Dify 生成启发式诊断并通过 SSE 推送到前端。

**ai-agent-service 环境变量**（在 `.env` 中配置）：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DIFY_API_KEY` | （必填） | Dify 应用的 API Key |
| `DIFY_API_URL` | `https://api.dify.ai/v1` | Dify API 基址 |
| `DIFY_GUIDANCE_USER` | `guidance-proactive` | Proactive guidance 调用 Dify 时使用的 user 标识 |
| `DIFY_GUIDANCE_TIMEOUT` | `120` | Dify 流式调用超时（秒） |
| `TOOL_API_KEY` | （空） | 内部接口鉴权密钥；为空时放行。需与 `docker-service` 的 `seclab.agent.signal-token` 保持一致 |

**docker-service 配置**（`application.yml`）：

```yaml
seclab:
  frustration:
    threshold: 3              # 挫败指数触发阈值
    cooldown-seconds: 90      # 两次触发间的冷却时间
    repeat-window-seconds: 300
    state-ttl-minutes: 30
  agent:
    signal-url: http://localhost:8010/api/guidance/signal
    signal-token: ${TOOL_API_KEY}   # 与 ai-agent-service 的 TOOL_API_KEY 一致
    timeout-ms: 5000
```

**部署约束**：

- **单 worker 约束**：`ai-agent-service` 的 guidance SSE 广播使用进程内 `asyncio.Queue`，仅支持单 uvicorn worker。多 worker 部署需改用 Redis Pub/Sub（当前未实现）。
  - 开发模式 `python main.py`（`reload=True`）默认单 worker，无需额外配置。
  - 生产模式 `uvicorn main:app --workers 1`（**必须 `--workers 1`**）。
- **CORS**：前端通过 `VITE_AGENT_BASE_URL` 直连 ai-agent-service（不走 vite 代理），需确保 `CORS_ORIGINS` 包含前端 origin（如 `http://localhost:5173`）。
- **Dify 应用**：需在 Dify 云端预先创建应用，并配置 `error_slice` / `recent_commands` / `lab_task_summary` 等输入变量。

**验证**：

```bash
# 1. 检查 ai-agent-service 端点已注册
curl http://localhost:8010/openapi.json | python -m json.tool | findstr guidance

# 2. 检查 SSE 订阅端点（应返回 200 + text/event-stream）
curl -N http://localhost:8010/api/guidance/stream/test-session

# 3. 模拟 docker-service 发送信号（需替换 TOOL_API_KEY）
curl -X POST http://localhost:8010/api/guidance/signal ^
  -H "Content-Type: application/json" ^
  -H "X-SecLab-Token: %TOOL_API_KEY%" ^
  -d "{\"signal_id\":\"sig-test\",\"lab_session_id\":\"test-session\",\"trigger_reason\":\"repeated_error\",\"error_slice\":\"permission denied\"}"
```

方式三：本机一键启动 AI Agent + cpolar

```bash
cd D:\SecLab\SecLab\seclab-backend
.\start-ai-agent-cpolar.bat
```

**服务访问地址：**

- 本地访问：<http://localhost:8010>
- API 文档：<http://localhost:8010/docs>
- 健康检查：<http://localhost:8010/health>

### 4.5 cpolar 内网穿透部署

#### 4.5.1 安装 cpolar

**方式一：官网下载安装**

1. 访问 <https://www.cpolar.com/> 注册账号
2. 下载 Windows 版本的 cpolar 客户端
3. 解压并安装

**方式二：使用 PowerShell 安装**

```powershell
# 下载 cpolar
Invoke-WebRequest -Uri "https://www.cpolar.com/static/downloads/releases/latest/cpolar-stable-windows-amd64.zip" -OutFile "cpolar.zip"

# 解压
Expand-Archive -Path "cpolar.zip" -DestinationPath "C:\cpolar" -Force

# 添加到 PATH（可选）
$env:Path += ";C:\cpolar"
```

#### 4.5.2 配置 cpolar

```bash
# 进入 cpolar 目录
cd d:\cpolar

# 认证（使用在官网注册的 authtoken）
.\cpolar authtoken YOUR_AUTH_TOKEN
```

#### 4.5.3 启动内网穿透

**穿透 Agent 服务（8010 端口）：**

```bash
# HTTP 隧道
.\cpolar http 8010

# 或指定子域名（需升级套餐）
.\cpolar http -subdomain=your-subdomain 8010
```

**穿透前端服务（5173 端口）：**

```bash
.\cpolar http 5173
```

#### 4.5.4 cpolar 后台管理

启动后，可以访问 cpolar 后台管理界面查看隧道信息：

- 本地管理地址：<http://localhost:4040>
- 可以查看所有活跃隧道、流量统计等

**提示：** 建议创建一个批处理脚本方便一键启动：

```batch
@echo off
echo 正在启动 AI Agent 服务...
start "AI Agent" cmd /k "cd /d d:\SecLab\SecLab\seclab-backend\ai-agent-service && venv\Scripts\activate && python main.py"
echo 正在启动 cpolar 内网穿透...
start "cpolar" cmd /k "cd /d C:\cpolar && cpolar http 8010"
echo 服务启动完成！
pause
```

### 4.6 数据库配置

#### 4.6.1 导入主系统数据库

```bash
# 确认MySQL容器已启动
docker ps | findstr mysql

# 导入数据库
docker exec -i seclab-mysql mysql -uroot -pseclab123 seclab_db < ./database/sql/init_seclab_db.sql
```

#### 4.6.2 导入实验环境数据库

```bash
# SQL注入实验数据库
docker exec -i sqli-lab_db_1 mysql -uroot -p123456 sqli_lab < ./seclab-backend/sqli-lab/init.sql
```

#### 4.6.3 导入画像与 AI 会话数据库

```bash
# 画像库（含 error_event / ai_conversation / ai_message / guidance_proactive_notes 等表）
docker exec -i seclab-mysql mysql -uroot -pseclab123 < ./database/sql/init_seclab_profile.sql

# 如需单独初始化 proactive guidance 主动提示历史表，可执行：
docker exec -i seclab-mysql mysql -uroot -pseclab123 < ./shujuku/guidance_proactive_notes.sql
```

> **说明**：`init_seclab_profile.sql` 已包含 `guidance_proactive_notes` 表的建表语句，
> 正常部署无需单独执行 `shujuku/guidance_proactive_notes.sql`。
> 后端 `ai-agent-service` 启动时也会通过 `ensure_guidance_schema()` 自愈建表。

## 5. 服务访问

### 5.1 本地访问

- **前端界面**：<http://localhost:5173>
- **Eureka服务注册中心**：<http://localhost:8761>
- **Gateway网关**：<http://localhost:8085>
- **用户服务**：<http://localhost:8081>
- **实验模块服务**：<http://localhost:8082>
- **AI Agent 服务**：<http://localhost:8010>
- **Agent API 文档**：<http://localhost:8010/docs>
- **cpolar 管理后台**：<http://localhost:4040>

### 5.2 公网访问（通过 cpolar）

启动 cpolar 后，会获得公网访问地址，例如：

- **前端公网地址**：<https://xxx.cpolar.io>
- **AI Agent 公网地址**：<https://yyy.cpolar.io>

### 5.3 实验环境访问

- **SQL注入实验**：<http://localhost:8091>
- **XSS实验**：<http://localhost:8092>
- **CSRF实验**：<http://localhost:8093>
- **文件上传实验**：<http://localhost:8094>
- **目录遍历实验**：<http://localhost:8095>
- **命令注入实验**：<http://localhost:8090>

## 6. 开发调试

### 6.1 前端调试

```bash
cd SecLab-FrontEnd-2
npm run dev
```

### 6.2 后端调试

```bash
cd seclab-backend
# 查看服务日志
docker logs saclab-gateway
docker logs saclab-user-service
```

### 6.3 数据库调试

```bash
# 连接主数据库
docker exec -it seclab-mysql mysql -uroot -pseclab123

# 连接实验数据库
docker exec -it sqli-lab_db_1 mysql -uroot -p123456
```

## 7. 停止服务

```bash
# 停止所有Docker容器
cd seclab-backend
.\stop-all-services.bat

# 或手动停止
docker stop $(docker ps -q)
```

## 8. 系统功能

### 8.1 用户功能

- 用户注册/登录
- 个人信息管理
- 头像上传
- 学习进度跟踪

### 8.2 实验功能

- 6个漏洞实验环境
- 实验指导文档
- 在线答题系统
- 实验报告生成

### 8.3 AI 助手功能

- **智能提示助手**：基于 Dify Agent 的 AI 助手，可根据学生操作提供阶梯式提示
- **Docker 容器监控**：实时监控靶场容器状态，读取容器日志
- **自动事件触发**：
  - 靶机启动时自动记录并初始化会话
  - 倒计时里程碑（50%、10%）时自动触发提示
  - 时间耗尽时提供完整解答
- **工具调用能力**：支持获取容器状态、读取日志、执行命令、停止容器等操作
- **内网穿透支持**：通过 cpolar 实现公网访问，便于远程调试和协作
- **全域智能引导（Proactive Guidance）**：
  - **挫败指数追踪**：`docker-service` 的 `FrustrationTracker` 实时分析终端输出与命令执行，按"同 signature 重复错误 +2 / 重复命令 +1"规则累计分数，超阈值（默认 3）触发信号
  - **启发式诊断**：信号到达 `ai-agent-service` 后，结合错误切片与靶机任务上下文调用 Dify RAG 生成启发式（非直接答案）诊断
  - **SSE 实时推送**：诊断结果通过 `/api/guidance/stream/{lab_session_id}` 流式推送到前端，FloatingChat 中以"主动提示"徽标渲染
  - **未读徽标**：FloatingChatButton 显示未读主动提示计数，打开聊天即标记已读
  - **历史回溯**：所有主动提示落 `guidance_proactive_notes` 表，可按 `lab_session_id` / `user_id` 查询

### 8.4 管理功能

- 课程管理
- 实验发布
- 用户管理
- 数据统计

***

**注意**：本文档基于当前项目状态编写，如有更新请及时同步修改。
