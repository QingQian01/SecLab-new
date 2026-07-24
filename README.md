# SecLab 

> 合并仓（以本方平台为基准，合入队友教师端/教学分析/协议分析）
> 分支 `merge/teacher-into-mine`

通用目录：

```powershell
D:\Seclab\SecLab-Combined
```

---

## 一、启动前确认

1. 打开 Docker Desktop，确认 Docker 正常运行。
2. 确认本机 MySQL 已启动（默认端口 `3306`），且项目数据库已初始化。
   - 后端 `ddl-auto: update`，**首次启动会自动建/补教师相关表与 user 表的 `user_role` 列**，无需手工建表。
   - 如需教师端演示数据，另跑 `database\sql\` 下的教师种子脚本（`seed_teacher_showcase.sql`、`reset_and_seed_teacher_demo.sql` 等）。
3. 如果改动过 noVNC 操作环境镜像 `operation-image`，才需要重建镜像（平时不用）：

```powershell
cd D:\Seclab\SecLab-Combined\seclab-backend\operation-image
.\build.ps1
```

---

## 二、首次准备（仅第一次 / 依赖有变时）

合并仓是全新目录，第一次需装前端依赖并建 ai-agent 虚拟环境：

```powershell
# 前端依赖
cd D:\Seclab\SecLab-Combined\SecLab-FrontEnd-2
npm install

# ai-agent 虚拟环境
cd D:\Seclab\SecLab-Combined\seclab-backend\ai-agent-service
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt
```

> 已装好后，日常启动跳过本节。

---

## 三、启动项目（推荐开 3 个 PowerShell 窗口）

### 1. 启动后端与靶场容器

```powershell
cd D:\Seclab\SecLab-Combined\seclab-backend
$env:START_AI_AGENT="false"
.\start-all-services.bat
```

这个脚本（gradle bootRun 从源码构建，首次稍慢）会启动：

- 靶场容器：`8090` 到 `8095`、栈溢出 pwn 靶机 `8096`
- 安全代码容器：`8080`
- 用户服务：`8083`
- 本地已有精简对应的 Eureka、Gateway、实验模块服务、Docker 服务、镜像服务

脚本窗口不要关；里面新弹出的 `SecLab user-service login-register 8083` 窗口也不要关。

### 2. 启动 AI Agent（含教师分析端点 + noVNC 操作环境编排）

```powershell
cd D:\Seclab\SecLab-Combined\seclab-backend\ai-agent-service
.\venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8010
```

这个窗口不要关。noVNC 操作环境、容器编排、实验事件、栈溢出靶机准备、**教师端教学分析**都会用到 `8010`。

### 3. 启动前端

```powershell
cd D:\Seclab\SecLab-Combined\SecLab-FrontEnd-2
npm run dev
```

浏览器打开：

```text
http://localhost:5173
```

---

## 四、启动后检查

```powershell
curl http://127.0.0.1:8010/health
curl http://127.0.0.1:8010/api/docker/list
docker ps
```

常用地址：

```text
前端：            http://localhost:5173
AI Agent：        http://localhost:8010
docker-api：      http://localhost:3000   (前端起靶机用；由 start-all 或单独 node docker-api-server.js 启动)
用户服务：         http://localhost:8083
命令注入：         http://localhost:8090
SQL 注入：         http://localhost:8091
XSS：             http://localhost:8092
CSRF：            http://localhost:8093
文件上传：         http://localhost:8094
目录遍历：         http://localhost:8095
栈溢出 pwn 靶机：  nc <容器名> 70  (host 8096)
安全代码容器：      http://localhost:8080
```

角色落地页（合并后）：

```text
学生登录  -> /user/welcome
管理员    -> /admin/dashboard   （本方原有管理后台，保留）
教师登录  -> /teacher/overview  （队友教师端：教学班 / 教学分析 / 知识风险热力图 / 生成题目）
```

---

## 五、调试

### 前端（Chrome DevTools）

```text
F12 打开控制台看 Console / Network。
实验详情页（栈溢出 module 15）验证：右侧靶机「已就绪」、任务点代码块彩色可见、flag 提交。
教师端 /teacher 验证：用教师账号登录后进入，教学分析取数走 8010 的 /api/teacher/*。
```

### 后端日志

```text
后端服务：start-all-services.bat 弹出的各窗口即为各服务日志。
AI Agent：uvicorn 窗口即日志；改了 config.py / main.py / teacher_*.py 需重启该窗口。
```

### 端口排查

```powershell
$ports = 5173,3000,8010,8083,8084,8085,8086,8087,8761,8080,8090,8091,8092,8093,8094,8095,8096
Get-NetTCPConnection -State Listen -LocalPort $ports -ErrorAction SilentlyContinue |
  Select-Object LocalPort, OwningProcess
```

---

## 六、关闭项目

优先用正常方式关闭：

1. 前端窗口按 `Ctrl+C`。
2. AI Agent 窗口按 `Ctrl+C`。
3. `SecLab user-service login-register 8083` 窗口按 `Ctrl+C` 或直接关闭。
4. `start-all-services.bat` 窗口可以关闭。
5. 如果开了 cpolar，也关闭 cpolar 窗口。

然后执行下面的清理命令（停止 Docker 容器和 noVNC 临时环境）：

```powershell
cd D:\Seclab\SecLab-Combined\seclab-backend

docker compose -f sqli-lab\docker-compose.yml down
docker compose -f xss-lab\docker-compose.yml down
docker compose -f csrf-lab\docker-compose.yml down
docker compose -f file-upload-lab\docker-compose.yml down
docker compose -f directory-traversal-lab\docker-compose.yml down
docker compose -f command-inject\docker-compose.yml down
docker compose -f stack-overflow-lab\docker-compose.yml down

docker rm -f sec-code-container 2>$null

docker ps --filter "name=operation_" -q | ForEach-Object { docker rm -f $_ }
docker network ls --filter "name=seclab-op-" -q | ForEach-Object { docker network rm $_ }

docker rm -f saclab-eureka saclab-gateway saclab-user-service saclab-experiment-module-service saclab-image-service saclab-docker-service seclab-ai-agent 2>$null
```

如果端口还被占用，再按端口强制清理。执行前确认这些端口确实是 SecLab 相关进程：

```powershell
$ports = 5173,3000,8010,8083,8080,8090,8091,8092,8093,8094,8095,8096,8761,8082,8084,8085,8086,8087
Get-NetTCPConnection -State Listen -LocalPort $ports -ErrorAction SilentlyContinue |
  Select-Object LocalPort, OwningProcess
```

确认无误后再停止（注意别误杀 Docker Desktop / wslrelay）：

```powershell
$ports = 5173,3000,8010,8083,8080,8090,8091,8092,8093,8094,8095,8096,8761,8082,8084,8085,8086,8087
Get-NetTCPConnection -State Listen -LocalPort $ports -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

Get-Process cpolar -ErrorAction SilentlyContinue | Stop-Process -Force
```

---

## 七、关闭后检查

```powershell
docker ps

$ports = 5173,3000,8010,8083,8080,8090,8091,8092,8093,8094,8095,8096,8761,8082,8084,8085,8086,8087
Get-NetTCPConnection -State Listen -LocalPort $ports -ErrorAction SilentlyContinue
```

如果 `docker ps` 没有 SecLab 相关容器，并且上述端口没有监听，说明项目已经基本关闭干净。
