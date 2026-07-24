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

# 复制前端服务地址模板
Copy-Item .env.example .env
```

前端 `.env` 应包含以下服务地址：

- `VITE_API_BASE_URL`：用户服务，默认 `http://localhost:8083`
- `VITE_EXPERIMENT_MODULE_BASE_URL`：实验模块服务，默认 `http://localhost:8084`
- `VITE_IMAGE_SERVICE_BASE_URL`：图片服务，默认 `http://localhost:8086/api/images`
- `VITE_DOCKER_API_URL`：Docker API，默认 `http://localhost:3000`
- `VITE_AGENT_BASE_URL`：AI Agent，默认 `http://localhost:8010`

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

# 启动前检查必填项、占位符和变量格式；检查结果不会输出密钥值
python runtime_config_validator.py .env
```

检查器返回 `[OK]` 后再启动服务。若返回 `[ERROR]`，按提示补齐对应变量名；不要把真实 `.env` 提交到 Git。

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

方式三：本机一键启动 AI Agent + cpolar

```bash
cd D:\SecLab\SecLab\seclab-backend
.\start-ai-agent-cpolar.bat
```

**服务访问地址：**

- 本地访问：<http://localhost:8010>
- API 文档：<http://localhost:8010/docs>
- 健康检查：<http://localhost:8010/health>
- Dify 连接检查：<http://localhost:8010/health/ai-analysis>

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

### 8.4 管理功能

- 课程管理
- 实验发布
- 用户管理
- 数据统计

***

**注意**：本文档基于当前项目状态编写，如有更新请及时同步修改。
