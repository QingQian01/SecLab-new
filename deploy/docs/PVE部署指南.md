# SecLab 平台 PVE 服务器部署指南

> 本文档面向在 Windows 上开发、需要部署到 Linux（PVE/Debian/Ubuntu）服务器的场景。
> 覆盖完整流程：**Windows 打包 → 上传 → 解压 → 环境准备 → 数据库导入 → 服务启动 → 验证**。

---

## 目录

1. [部署架构总览](#1-部署架构总览)
2. [服务器环境准备](#2-服务器环境准备)
3. [在 Windows 上打包项目](#3-在-windows-上打包项目)
4. [上传到服务器](#4-上传到服务器)
5. [在服务器上解压](#5-在服务器上解压)
6. [数据库导入与验证](#6-数据库导入与验证)
7. [配置环境变量](#7-配置环境变量)
8. [构建后端服务](#8-构建后端服务)
9. [构建前端](#9-构建前端)
10. [启动所有服务](#10-启动所有服务)
11. [配置 Nginx 反向代理](#11-配置-nginx-反向代理)
12. [验证部署](#12-验证部署)
13. [日常运维](#13-日常运维)
14. [常见问题排查](#14-常见问题排查)

---

## 1. 部署架构总览

```
                         校园网终端浏览器
                              │
                       http://<服务器IP>:8088
                              │
                    ┌─────────┴─────────┐
                    │   Nginx (8088)    │  反向代理 + 静态前端
                    └─────────┬─────────┘
          ┌─────────┬─────────┼─────────┬──────────┐
          │         │         │         │          │
     /stu/ /admin/  /course/  /api/   /targets/   / (静态)
     /stu/module/             /api/docker/        dist/
          │         │         │         │
     ┌────┴────┐ ┌──┴──┐ ┌───┴────┐ ┌──┴──────┐
     │user-svc │ │exp-│ │ai-agent│ │ 靶场容器 │
     │  :8083  │ │mod │ │  svc   │ │8090-8096│
     │         │ │:8084│ │ :8010  │ │  8896   │
     └────┬────┘ └──┬──┘ └───┬────┘ └─────────┘
          │         │        │
     ┌────┴─────────┴────────┴────┐
     │     MySQL 8.0 (:3306)      │  Docker 容器
     │  userservice / seclab_     │
     │  profile / imagedb         │
     └────────────────────────────┘
```

### 服务清单

| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx | 8088 | 统一入口，反向代理 + 前端静态文件 |
| user-service | 8083 | 用户登录/注册/资料（Spring Boot） |
| experiment-module-service | 8084 | 课程/模块/实验（Spring Boot） |
| image-service | 8086 | 图片上传/头像（Spring Boot） |
| ai-agent-service | 8010 | AI 助手 + Docker 管理 + 事件采集（FastAPI） |
| MySQL | 3306 | 主数据库（Docker 容器） |
| sqli-lab | 8091 | SQL 注入靶场 |
| xss-lab | 8092 | XSS 靶场 |
| csrf-lab | 8093 | CSRF 靶场 |
| file-upload-lab | 8094 | 文件上传靶场 |
| directory-traversal-lab | 8095 | 目录遍历靶场 |
| command-inject | 8090 | 命令注入靶场 |
| stack-overflow-lab | 8096 | 栈溢出靶场 |
| protocol-analysis-lab | 8896 | 协议分析靶场 |
| sec-code | 8080 | 安全代码容器 |

### 默认账号

| 角色 | 学号 | 密码 | 说明 |
|------|------|------|------|
| 管理员 | `admin` | `123456` | user_role=TEACHER，可访问教师端 |
| 教师 | `T20260001` | `123456` | 种子教师账号 |

---

## 2. 服务器环境准备

### 2.1 系统要求

- **OS**：Debian 12+ / Ubuntu 22.04+（PVE 虚拟机或 LXC 容器均可）
- **CPU**：≥ 4 核
- **内存**：≥ 8 GB（推荐 16 GB，8 个靶场容器 + 3 个 Java 服务 + MySQL）
- **磁盘**：≥ 40 GB 可用空间
- **网络**：校园局域网可达，端口 8088 对外开放

### 2.2 SSH 连接服务器

```bash
# 在 Windows PowerShell 中连接
ssh root@<服务器IP>
# 或
ssh <用户名>@<服务器IP>
```

### 2.3 安装基础依赖

```bash
# 更新包索引
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y curl wget git unzip vim \
    ca-certificates gnupg lsb-release \
    build-essential

# 安装 Docker
curl -fsSL https://get.docker.com | sudo bash

# 将当前用户加入 docker 组（免 sudo 调用 docker）
sudo usermod -aG docker $USER

# 安装 Docker Compose 插件（apt 源已包含）
sudo apt install -y docker-compose-plugin

# 验证 Docker
docker --version
docker compose version
```

> **重要**：加入 docker 组后需要**重新登录 SSH**才能生效。

### 2.4 安装 JDK 17

```bash
sudo apt install -y openjdk-17-jdk

# 验证
java -version
# 应输出 openjdk version "17.x.x"
```

### 2.5 安装 Node.js 18+（构建前端用）

```bash
# 使用 NodeSource 仓库安装 Node.js 18 LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 验证
node -v   # 应 ≥ v18
npm -v
```

### 2.6 安装 Python 3.10+（AI Agent 服务用）

```bash
sudo apt install -y python3 python3-venv python3-pip

# 验证
python3 --version   # 应 ≥ 3.10
```

### 2.7 安装 Nginx

```bash
sudo apt install -y nginx

# 验证
nginx -v
sudo systemctl enable nginx
```

### 2.8 验证所有环境

```bash
echo "=== 环境验证 ==="
echo "Docker:       $(docker --version)"
echo "Compose:      $(docker compose version --short)"
echo "Java:         $(java -version 2>&1 | head -1)"
echo "Node.js:      $(node -v)"
echo "npm:          $(npm -v)"
echo "Python:       $(python3 --version)"
echo "Nginx:        $(nginx -v 2>&1)"
echo "=== 完成 ==="
```

预期输出全部正常后，继续下一步。

---

## 3. 在 Windows 上打包项目

### 3.1 清理不需要的文件

在打包前，清理大体积和无用的文件，减小压缩包体积：

```powershell
# 进入项目根目录
cd D:\SecLab\SecLab

# 删除 node_modules（服务器上会重新 npm install）
Remove-Item -Recurse -Force SecLab-FrontEnd-2\node_modules -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force seclab-backend\node_modules -ErrorAction SilentlyContinue

# 删除构建产物（服务器上会重新构建）
Remove-Item -Recurse -Force SecLab-FrontEnd-2\dist -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force seclab-backend\build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force seclab-backend\*\build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force seclab-backend\.gradle -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force seclab-backend\*\.gradle -ErrorAction SilentlyContinue

# 删除 Python 虚拟环境和缓存
Remove-Item -Recurse -Force seclab-backend\ai-agent-service\venv -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force seclab-backend\ai-agent-service\.venv -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force seclab-backend\ai-agent-service\__pycache__ -ErrorAction SilentlyContinue

# 删除日志文件
Get-ChildItem -Recurse -Filter "*.log" | Remove-Item -Force -ErrorAction SilentlyContinue
```

### 3.2 确认关键文件存在

```powershell
# 确认部署脚本存在
Test-Path deploy\scripts\start-all-services.sh
Test-Path deploy\scripts\stop-all-services.sh
Test-Path deploy\scripts\bootstrap-mysql.sh
Test-Path deploy\nginx\seclab.conf
Test-Path SecLab-FrontEnd-2\.env.production

# 确认数据库 SQL 存在
Test-Path database\sql\user-service-local-init.sql
Test-Path database\sql\init_seclab_profile.sql
Test-Path database\sql\seed_teacher_showcase.sql

# 确认靶场 docker-compose 存在
Test-Path seclab-backend\sqli-lab\docker-compose.yml
Test-Path seclab-backend\stack-overflow-lab\docker-compose.yml
Test-Path seclab-backend\protocol-analysis-lab\docker-compose.yml
```

所有路径应返回 `True`。

### 3.3 打包为 tar.gz

> **为什么用 tar.gz 而不是 zip**：tar.gz 在 Linux 上解压更自然，且会保留文件的 Unix 权限位（shell 脚本的可执行位）。Windows 自带 tar 命令支持 tar.gz 格式。

```powershell
cd D:\SecLab

# 使用 Windows 自带 tar 命令打包
# 排除 node_modules、build、.gradle、venv、日志等大目录
tar -czf SecLab-deploy.tar.gz `
    --exclude='SecLab/node_modules' `
    --exclude='SecLab/SecLab-FrontEnd-2/node_modules' `
    --exclude='SecLab/seclab-backend/node_modules' `
    --exclude='SecLab/SecLab-FrontEnd-2/dist' `
    --exclude='SecLab/build' `
    --exclude='SecLab/seclab-backend/build' `
    --exclude='SecLab/seclab-backend/*/build' `
    --exclude='SecLab/.gradle' `
    --exclude='SecLab/seclab-backend/.gradle' `
    --exclude='SecLab/seclab-backend/*/.gradle' `
    --exclude='SecLab/seclab-backend/ai-agent-service/venv' `
    --exclude='SecLab/seclab-backend/ai-agent-service/.venv' `
    --exclude='SecLab/seclab-backend/ai-agent-service/__pycache__' `
    --exclude='SecLab/**/*.log' `
    --exclude='SecLab/.vscode' `
    --exclude='SecLab/.trae' `
    SecLab

# 查看压缩包大小
Get-Item SecLab-deploy.tar.gz | Select-Object Name, @{N='SizeMB';E={[math]::Round($_.Length/1MB,1)}}
```

预期压缩包大小约 **50-150 MB**（取决于源码和 SQL 数据量）。

### 3.4 替代方案：使用 7-Zip

如果 `tar` 命令不可用（Windows 10 1803 之前），安装 [7-Zip](https://www.7-zip.org/) 后：

```powershell
# 先用 7z 打包为 tar
& "C:\Program Files\7-Zip\7z.exe" a -ttar SecLab-deploy.tar SecLab `
    -xr!node_modules -xr!dist -xr!build -xr!.gradle -xr!venv -xr!.venv -xr!__pycache__ -xr!*.log

# 再压缩为 gzip
& "C:\Program Files\7-Zip\7z.exe" a -tgzip SecLab-deploy.tar.gz SecLab-deploy.tar
Remove-Item SecLab-deploy.tar
```

---

## 4. 上传到服务器

### 4.1 使用 scp 上传

```powershell
# 在 Windows PowerShell 中执行
# 将压缩包上传到服务器的 /tmp 目录
scp D:\SecLab\SecLab-deploy.tar.gz <用户名>@<服务器IP>:/tmp/
```

示例：
```powershell
scp D:\SecLab\SecLab-deploy.tar.gz root@192.168.1.100:/tmp/
```

### 4.2 使用 rsync 上传（推荐，支持断点续传）

```powershell
# Windows 需先安装 rsync（可通过 Git Bash 或 WSL）
rsync -avz --progress D:\SecLab\SecLab-deploy.tar.gz <用户名>@<服务器IP>:/tmp/
```

### 4.3 大文件替代方案

如果压缩包超过 200MB，可在服务器上安装 Git 后直接 `git clone`：

```bash
# 在服务器上
cd /opt/seclab
git clone <你的仓库地址> SecLab
```

但这要求仓库已推送最新代码，且不含 `.env` 等被 gitignore 的文件。

---

## 5. 在服务器上解压

### 5.1 创建部署目录

```bash
# SSH 登录服务器后
sudo mkdir -p /opt/seclab
sudo chown -R $USER:$USER /opt/seclab
```

### 5.2 解压压缩包

```bash
# 解压到 /opt/seclab
cd /opt/seclab
tar -xzf /tmp/SecLab-deploy.tar.gz --strip-components=1

# --strip-components=1 去掉顶层的 SecLab/ 目录，
# 使文件直接解压到 /opt/seclab/ 下

# 验证目录结构
ls -la /opt/seclab/
# 应看到：
# drwxr-xr-x  SecLab-FrontEnd-2/
# drwxr-xr-x  seclab-backend/
# drwxr-xr-x  database/
# drwxr-xr-x  shujuku/
# drwxr-xr-x  deploy/
# -rw-r--r--  AGENTS.md
# ...
```

### 5.3 设置脚本执行权限

```bash
# 给所有部署脚本添加执行权限
chmod +x /opt/seclab/deploy/scripts/*.sh

# 给 Gradle wrapper 添加执行权限
chmod +x /opt/seclab/seclab-backend/gradlew
chmod +x /opt/seclab/seclab-backend/*/gradlew 2>/dev/null || true

# 验证
ls -la /opt/seclab/deploy/scripts/
```

### 5.4 修复文件换行符（重要）

> Windows 上编辑的 shell 脚本可能含有 CRLF 换行符，在 Linux 上会导致 `bash: ./script.sh: /bin/bash^M: bad interpreter` 错误。

```bash
# 安装 dos2unix
sudo apt install -y dos2unix

# 转换所有 shell 脚本
find /opt/seclab/deploy -name "*.sh" -exec dos2unix {} \;

# 转换 Gradle wrapper
dos2unix /opt/seclab/seclab-backend/gradlew 2>/dev/null || true

# 转换靶场启动脚本（如 start.sh）
find /opt/seclab/seclab-backend -name "*.sh" -exec dos2unix {} \; 2>/dev/null || true
```

### 5.5 验证关键文件

```bash
echo "=== 验证部署文件 ==="

echo "1. 部署脚本："
ls -la /opt/seclab/deploy/scripts/*.sh

echo "2. 数据库 SQL："
ls /opt/seclab/database/sql/*.sql | head -5

echo "3. 靶场 docker-compose："
ls /opt/seclab/seclab-backend/*/docker-compose.yml

echo "4. 前端 .env.production："
cat /opt/seclab/SecLab-FrontEnd-2/.env.production | head -5

echo "=== 验证完成 ==="
```

---

## 6. 数据库导入与验证

### 6.1 一键引导（推荐）

使用 `bootstrap-mysql.sh` 脚本自动完成：创建 MySQL 容器 → 建库建用户 → 导入表结构 → 导入种子数据 → 验证。

```bash
cd /opt/seclab
bash deploy/scripts/bootstrap-mysql.sh
```

脚本执行流程：
1. 创建 MySQL 8.0 Docker 容器（端口 3306，数据持久化到 `/opt/seclab/data/mysql`）
2. 等待 MySQL 就绪
3. 创建 4 个数据库：`userservice`、`seclab_profile`、`imagedb`、`seclab_db`
4. 创建应用用户 `seclab_app`
5. 导入 `user-service-local-init.sql`（用户/班级/课程/模块表 + 教师账号 T20260001）
6. 创建 admin 管理员账号（`admin` / `123456`，user_role=TEACHER）
7. 给 `course` 表补 `created_by` 列（教师端课程列表需要）
8. 导入 `init_seclab_profile.sql`（事件/画像/AI会话/教师分析表）
9. 导入教师工作台表（`teacher_teaching_class.sql` 等）
10. 导入 `seed_teacher_showcase.sql`（32 名学生、40 道题、班级分析）
11. 验证数据

### 6.2 手动导入（如需自定义）

如果一键脚本失败或需要手动控制，可分步执行：

```bash
# 设置变量
MYSQL_CONTAINER="seclab-mysql"
MYSQL_ROOT_PASSWORD="han0.521"
PROJECT_DIR="/opt/seclab"

# 1. 创建 MySQL 容器
docker run -d --name $MYSQL_CONTAINER \
    --restart unless-stopped \
    -p 127.0.0.1:3306:3306 \
    -v /opt/seclab/data/mysql:/var/lib/mysql \
    -e MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD \
    -e MYSQL_DATABASE=userservice \
    -e MYSQL_USER=seclab_app \
    -e MYSQL_PASSWORD=Seclab@123 \
    -e MYSQL_CHARACTER_SET_SERVER=utf8mb4 \
    -e MYSQL_COLLATION_SERVER=utf8mb4_unicode_ci \
    mysql:8.0 --default-authentication-plugin=mysql_native_password

# 2. 等待就绪
echo "等待 MySQL..."
until docker exec $MYSQL_CONTAINER mysqladmin ping -uroot -p$MYSQL_ROOT_PASSWORD --silent; do
    sleep 2
    echo -n "."
done
echo " MySQL 就绪"

# 3. 创建数据库和用户
docker exec -i $MYSQL_CONTAINER mysql -uroot -p$MYSQL_ROOT_PASSWORD <<'SQL'
CREATE DATABASE IF NOT EXISTS userservice CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS seclab_profile CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS imagedb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'seclab_app'@'%' IDENTIFIED BY 'Seclab@123';
GRANT ALL PRIVILEGES ON userservice.* TO 'seclab_app'@'%';
GRANT ALL PRIVILEGES ON seclab_profile.* TO 'seclab_app'@'%';
GRANT ALL PRIVILEGES ON imagedb.* TO 'seclab_app'@'%';
GRANT CREATE, DROP ON *.* TO 'seclab_app'@'%';
FLUSH PRIVILEGES;
SQL

# 4. 导入 userservice 表结构
docker exec -i $MYSQL_CONTAINER mysql -uroot -p$MYSQL_ROOT_PASSWORD userservice \
    < $PROJECT_DIR/database/sql/user-service-local-init.sql

# 5. 导入 seclab_profile 表结构
docker exec -i $MYSQL_CONTAINER mysql -uroot -p$MYSQL_ROOT_PASSWORD \
    < $PROJECT_DIR/database/sql/init_seclab_profile.sql

# 6. 导入教师工作台表
docker exec -i $MYSQL_CONTAINER mysql -uroot -p$MYSQL_ROOT_PASSWORD \
    < $PROJECT_DIR/database/sql/teacher_teaching_class.sql
docker exec -i $MYSQL_CONTAINER mysql -uroot -p$MYSQL_ROOT_PASSWORD \
    < $PROJECT_DIR/database/sql/teacher_course_analysis.sql
docker exec -i $MYSQL_CONTAINER mysql -uroot -p$MYSQL_ROOT_PASSWORD \
    < $PROJECT_DIR/database/sql/teacher_intervention.sql
docker exec -i $MYSQL_CONTAINER mysql -uroot -p$MYSQL_ROOT_PASSWORD \
    < $PROJECT_DIR/database/sql/teacher_knowledge_analysis.sql

# 7. 导入种子数据
docker exec -i $MYSQL_CONTAINER mysql -uroot -p$MYSQL_ROOT_PASSWORD \
    < $PROJECT_DIR/database/sql/seed_teacher_showcase.sql
```

### 6.3 验证数据库

```bash
# 进入 MySQL 命令行
docker exec -it seclab-mysql mysql -uroot -phan0.521

# 在 MySQL 中执行以下验证：
```

```sql
-- 1. 检查数据库
SHOW DATABASES;
-- 应包含：userservice, seclab_profile, imagedb, seclab_db

-- 2. 检查 admin 账号
USE userservice;
SELECT user_id, user_student_number, user_name, user_role, is_admin
FROM user WHERE user_student_number IN ('admin', 'T20260001');
-- 应返回 2 行：admin (TEACHER) 和 T20260001 (TEACHER)

-- 3. 检查 course 表 created_by 列
SHOW COLUMNS FROM course LIKE 'created_by';
-- 应返回 1 行：Field=created_by, Type=bigint

-- 4. 检查教师工作台表
SHOW TABLES FROM userservice LIKE 'teaching_class%';
-- 应返回：teaching_class, teaching_class_course, teaching_class_student, teaching_class_import_batch

-- 5. 检查画像库表
USE seclab_profile;
SHOW TABLES;
-- 应包含：learning_event, teacher_class_analysis, teacher_typical_question 等

-- 6. 检查种子学生数据
SELECT COUNT(*) AS student_count
FROM userservice.user
WHERE user_student_number BETWEEN '202321040501' AND '202321040532';
-- 应返回 32

-- 7. 检查班级分析数据
SELECT teaching_class_id, analysis_status, generated_at
FROM seclab_profile.teacher_class_analysis;
-- 应返回 1 行，status=READY

-- 8. 检查字符编码（防乱码）
SELECT default_character_set_name, default_collation_name
FROM information_schema.SCHEMATA
WHERE schema_name IN ('userservice', 'seclab_profile');
-- 应全部为 utf8mb4 / utf8mb4_unicode_ci

EXIT;
```

---

## 7. 配置环境变量

### 7.1 AI Agent 服务配置

```bash
cd /opt/seclab/seclab-backend/ai-agent-service

# 从模板创建 .env
cp .env.example .env

# 编辑 .env，填入 Dify API Key 和其他配置
vim .env
```

`.env` 关键配置项：

```bash
# Dify Agent 配置（必填，否则 AI 助手无法工作）
DIFY_API_URL=https://api.dify.ai/v1
DIFY_API_KEY=你的Dify_API_Key

# 服务监听
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8010

# CORS（添加服务器 IP）
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://<服务器IP>:8088

# Docker 容器白名单（已包含所有靶场前缀）
ALLOWED_CONTAINER_PREFIXES=sqli,xss,csrf,upload,dir,command-inject,sec-code,stack-overflow,protocol-analysis,heap-overflow,format-string

# MySQL（与 bootstrap-mysql.sh 保持一致）
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=seclab_app
MYSQL_PASSWORD=Seclab@123
MYSQL_DATABASE=seclab_profile
```

### 7.2 后端服务环境变量

后端 Spring Boot 服务通过环境变量读取数据库配置。在 `start-all-services.sh` 中已自动设置，如需自定义：

```bash
# 可在启动前 export，或写入 /opt/seclab/.env
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_USER=seclab_app
export MYSQL_PASSWORD=Seclab@123
export USER_SERVICE_DB_NAME=userservice
```

### 7.3 修复 Gradle 配置

> `gradle.properties` 中的 JDK 路径是 Windows 格式，在 Linux 上需要修改。

```bash
# 覆盖为 Linux JDK 路径
echo "org.gradle.java.installations.paths=/usr/lib/jvm/java-17-openjdk-amd64" \
    > /opt/seclab/seclab-backend/gradle.properties

# 验证
cat /opt/seclab/seclab-backend/gradle.properties
```

---

## 8. 构建后端服务

### 8.1 构建 Java 微服务 JAR

```bash
cd /opt/seclab/seclab-backend

# 给 gradlew 执行权限
chmod +x gradlew

# 构建所有服务（user-service, experiment-module-service, image-service）
./gradlew :user-service:bootJar :experiment-module-service:bootJar :image-service:bootJar -x test

# 构建产物在各服务的 build/libs/ 目录下
ls -la user-service/build/libs/*.jar
ls -la experiment-module-service/build/libs/*.jar
ls -la image-service/build/libs/*.jar
```

构建过程需要下载 Gradle 和 Spring Boot 依赖，首次约 **5-15 分钟**。

### 8.2 构建 noVNC 操作环境镜像

```bash
cd /opt/seclab/seclab-backend/operation-image
docker build -t seclab-op-web-tools:1.0 .
cd /opt/seclab
```

### 8.3 配置 AI Agent Python 环境

```bash
cd /opt/seclab/seclab-backend/ai-agent-service

# 创建虚拟环境
python3 -m venv venv

# 激活并安装依赖
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 验证
python3 -c "import fastapi, uvicorn, pymysql; print('依赖安装成功')"
deactivate
```

---

## 9. 构建前端

### 9.1 安装前端依赖

```bash
cd /opt/seclab/SecLab-FrontEnd-2

# 安装依赖（首次约 2-5 分钟）
npm install
```

如果遇到 `@lucky-canvas/vue` 错误：

```bash
npm uninstall @lucky-canvas/vue
# 然后编辑 src/main.ts 删除相关 import 和 .use(VueLuckyCanvas)
```

### 9.2 确认生产环境变量

```bash
# 确认 .env.production 存在且配置正确
cat .env.production
```

应包含（所有 API 地址使用相对路径，由 nginx 代理）：

```
VITE_API_BASE_URL=
VITE_EXPERIMENT_MODULE_BASE_URL=
VITE_IMAGE_SERVICE_BASE_URL=/api/images
VITE_DOCKER_API_URL=
VITE_AGENT_BASE_URL=
VITE_NOVNC_URL=
VITE_OSS_BASE_URL=https://seclab2026.oss-cn-hangzhou.aliyuncs.com
```

### 9.3 构建生产包

```bash
# TypeScript 类型检查
npx vue-tsc --noEmit

# 构建
npm run build

# 验证产物
ls -la dist/
ls -la dist/assets/ | head -5
```

构建产物在 `dist/` 目录，由 nginx 直接作为静态文件提供。

---

## 10. 启动所有服务

### 方式一：一键启动脚本（推荐）

```bash
cd /opt/seclab
bash deploy/scripts/start-all-services.sh
```

脚本会按顺序启动：
1. MySQL 容器（如未运行）
2. 8 个靶场容器（自动 docker compose up -d --build）
3. sec-code 安全代码容器
4. user-service（Gradle bootRun，端口 8083）
5. experiment-module-service（端口 8084）
6. image-service（端口 8086）
7. ai-agent-service（Python uvicorn，端口 8010）
8. 构建 noVNC 镜像（如不存在）

日志输出到 `/opt/seclab/logs/` 目录。

### 方式二：使用 systemd（生产推荐）

systemd 方式更稳定，服务崩溃会自动重启，开机自启。

```bash
cd /opt/seclab

# 1. 创建 seclab 系统用户
sudo useradd --system --create-home --shell /usr/sbin/nologin seclab
sudo usermod -aG docker seclab

# 2. 设置目录权限
sudo chown -R seclab:seclab /opt/seclab/logs
sudo mkdir -p /opt/seclab/logs /opt/seclab/data/mysql
sudo chown -R seclab:seclab /opt/seclab/logs

# 3. 安装 systemd 单元
sudo cp deploy/systemd/seclab-*.service /etc/systemd/system/
sudo systemctl daemon-reload

# 4. 启用并启动
sudo systemctl enable --now seclab-user-service
sudo systemctl enable --now seclab-experiment-module-service
sudo systemctl enable --now seclab-image-service
sudo systemctl enable --now seclab-ai-agent

# 5. 启动靶场容器（非 systemd 管理）
for lab in sqli-lab xss-lab csrf-lab file-upload-lab directory-traversal-lab \
           command-inject stack-overflow-lab protocol-analysis-lab; do
    cd /opt/seclab/seclab-backend/$lab
    docker compose up -d --build
done
cd /opt/seclab
```

### 方式三：deploy-all.sh 全自动部署

```bash
# 一键完成：MySQL + Python 依赖 + Java 构建 + 靶场容器 + 前端构建 + systemd + nginx
sudo bash deploy/scripts/deploy-all.sh
```

> **注意**：`deploy-all.sh` 会覆盖 systemd 和 nginx 配置，适合首次部署。

### 等待服务就绪

```bash
# 等待后端服务启动（Spring Boot 首次启动约 30-60 秒）
echo "等待后端服务就绪..."
sleep 30

# 检查端口
ss -tlnp | grep -E '8083|8084|8086|8010|3306'
# 应看到所有端口处于 LISTEN 状态
```

---

## 11. 配置 Nginx 反向代理

### 11.1 安装 Nginx 配置

```bash
# 复制配置
sudo cp /opt/seclab/deploy/nginx/seclab.conf /etc/nginx/sites-available/seclab

# 创建软链接启用
sudo ln -sfn /etc/nginx/sites-available/seclab /etc/nginx/sites-enabled/seclab

# 删除默认站点（避免冲突）
sudo rm -f /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t
# 应输出: configuration file /etc/nginx/nginx.conf test is successful
```

### 11.2 启动 Nginx

```bash
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 11.3 Nginx 路由说明

| URL 路径 | 转发目标 | 说明 |
|----------|----------|------|
| `/` | `dist/` 静态文件 | 前端 SPA |
| `/stu/` | `127.0.0.1:8083` | 用户服务（登录/注册/资料） |
| `/admin/` | `127.0.0.1:8083` | 用户服务（管理员） |
| `/course/` | `127.0.0.1:8084` | 实验模块服务（课程） |
| `/stu/module/` | `127.0.0.1:8084` | 实验模块服务（模块） |
| `/api/images/` | `127.0.0.1:8086` | 图片服务 |
| `/api/docker/` | `127.0.0.1:8010` | AI Agent（Docker 管理） |
| `/api/docker/vnc/` | `127.0.0.1:8010` | AI Agent（noVNC WebSocket） |
| `/api/agent/` | `127.0.0.1:8010` | AI Agent（聊天） |
| `/api/chat` | `127.0.0.1:8010` | AI Agent（SSE 流式） |
| `/api/profile/` | `127.0.0.1:8010` | AI Agent（画像数据） |
| `/api/teacher/` | `127.0.0.1:8010` | AI Agent（教师端） |
| `/targets/sqli/` | `127.0.0.1:8091` | SQL 注入靶场 |
| `/targets/xss/` | `127.0.0.1:8092` | XSS 靶场 |
| `/targets/csrf/` | `127.0.0.1:8093` | CSRF 靶场 |
| `/targets/cmd/` | `127.0.0.1:8090` | 命令注入靶场 |
| `/targets/upload/` | `127.0.0.1:8094` | 文件上传靶场 |
| `/targets/dir/` | `127.0.0.1:8095` | 目录遍历靶场 |
| `/targets/stack/` | `127.0.0.1:8096` | 栈溢出靶场 |
| `/targets/protocol/` | `127.0.0.1:8896` | 协议分析靶场 |

---

## 12. 验证部署

### 12.1 服务健康检查

```bash
echo "=== 服务健康检查 ==="

echo "1. MySQL："
docker exec seclab-mysql mysqladmin ping -uroot-phan0.521 --silent 2>/dev/null \
    && echo "  ✓ 运行中" || echo "  ✗ 未运行"

echo "2. user-service (8083)："
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8083/stu/login 2>/dev/null \
    | xargs -I{} echo "  HTTP {}"

echo "3. experiment-module-service (8084)："
curl -s http://127.0.0.1:8084/course/overview-list 2>/dev/null | head -c 200

echo ""
echo "4. image-service (8086)："
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8086/api/images/files/ 2>/dev/null \
    | xargs -I{} echo "  HTTP {}"

echo "5. ai-agent-service (8010)："
curl -s http://127.0.0.1:8010/health 2>/dev/null || echo "  无 /health 端点"
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8010/docs 2>/dev/null \
    | xargs -I{} echo "  /docs HTTP {}"

echo "6. Nginx (8088)："
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8088/ 2>/dev/null \
    | xargs -I{} echo "  HTTP {}"

echo "7. 靶场容器："
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E 'lab|sec-code'

echo "=== 检查完成 ==="
```

### 12.2 浏览器验证

1. **访问前端**：浏览器打开 `http://<服务器IP>:8088/`
2. **登录**：使用 `admin` / `123456`
3. **进入实验模块**：点击课程 → 模块 → 开始挑战
4. **启动靶机**：点击「启动靶机环境」，应看到靶机在线
5. **启动操作环境**：点击「启动操作环境」，应看到 noVNC 桌面
6. **教师端**：登录后访问教师端，应能看到课程列表和学生数据

### 12.3 API 接口验证

```bash
# 登录测试
curl -X POST http://127.0.0.1:8088/stu/login \
    -H "Content-Type: application/json" \
    -d '{"userStudentNumber":"admin","userPassword":"123456"}'

# 应返回包含 token 的 JSON

# 课程列表
curl http://127.0.0.1:8088/course/overview-list

# AI Agent 健康检查
curl http://127.0.0.1:8088/api/docker/list

# 靶场状态
curl http://127.0.0.1:8088/api/docker/target-status/sqli
```

---

## 13. 日常运维

### 13.1 启动/停止所有服务

```bash
# 启动所有服务
cd /opt/seclab
bash deploy/scripts/start-all-services.sh

# 停止所有服务
bash deploy/scripts/stop-all-services.sh

# 停止并连同 MySQL 一起停止
STOP_MYSQL=true bash deploy/scripts/stop-all-services.sh
```

### 13.2 查看日志

```bash
# 后端服务日志
tail -f /opt/seclab/logs/user-service.log
tail -f /opt/seclab/logs/experiment-module-service.log
tail -f /opt/seclab/logs/image-service.log
tail -f /opt/seclab/logs/ai-agent-service.log

# systemd 方式
sudo journalctl -u seclab-user-service -f
sudo journalctl -u seclab-experiment-module-service -f
sudo journalctl -u seclab-ai-agent -f

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# MySQL 日志
docker logs -f seclab-mysql

# 靶场容器日志
docker logs -f sqli-lab-web-1
docker logs -f stack-overflow-lab-web-1
```

### 13.3 重启单个服务

```bash
# 重启 user-service（脚本方式）
PID=$(cat /opt/seclab/logs/user-service.pid)
kill $PID
cd /opt/seclab/seclab-backend/user-service
nohup ./gradlew bootRun > /opt/seclab/logs/user-service.log 2>&1 &
echo $! > /opt/seclab/logs/user-service.pid

# 重启 ai-agent-service（systemd 方式）
sudo systemctl restart seclab-ai-agent

# 重启单个靶场
cd /opt/seclab/seclab-backend/sqli-lab
docker compose restart
```

### 13.4 更新代码后重新部署

```bash
cd /opt/seclab

# 1. 停止服务
bash deploy/scripts/stop-all-services.sh

# 2. 更新代码（如使用 git）
git pull

# 3. 重新构建后端
cd seclab-backend
./gradlew :user-service:bootJar :experiment-module-service:bootJar :image-service:bootJar -x test

# 4. 重新构建前端
cd /opt/seclab/SecLab-FrontEnd-2
npm run build

# 5. 重新导入数据库（如有 SQL 变更）
bash /opt/seclab/deploy/scripts/bootstrap-mysql.sh

# 6. 重启服务
bash /opt/seclab/deploy/scripts/start-all-services.sh

# 7. 重载 nginx（如有配置变更）
sudo nginx -s reload
```

---

## 14. 常见问题排查

### 14.1 `bash: ./script.sh: /bin/bash^M: bad interpreter`

**原因**：shell 脚本含有 Windows CRLF 换行符。

**解决**：
```bash
sudo apt install -y dos2unix
find /opt/seclab -name "*.sh" -exec dos2unix {} \;
```

### 14.2 靶场容器启动失败：`exec /start.sh: no such file or directory`

**原因**：靶场目录下的 `start.sh` 脚本含有 CRLF 换行符。

**解决**：
```bash
# 转换所有靶场的 shell 脚本
find /opt/seclab/seclab-backend -name "*.sh" -exec dos2unix {} \;

# 重新构建容器
cd /opt/seclab/seclab-backend/stack-overflow-lab
docker compose down
docker compose build --no-cache
docker compose up -d
```

### 14.3 user-service 启动失败：`Unknown column 'created_by'`

**原因**：`course` 表缺少 `created_by` 列。

**解决**：
```bash
docker exec -i seclab-mysql mysql -uroot -phan0.521 userservice <<'SQL'
ALTER TABLE `course` ADD COLUMN `created_by` BIGINT NULL AFTER `course_status`;
ALTER TABLE `course` ADD INDEX `idx_course_creator_status` (`created_by`, `course_status`);
SQL
```

### 14.4 教师端 500 错误：`course/overview-list`

**原因**：数据库缺少教师表或种子数据。

**解决**：
```bash
# 重新执行 bootstrap
bash /opt/seclab/deploy/scripts/bootstrap-mysql.sh

# 或手动导入缺失的表
docker exec -i seclab-mysql mysql -uroot -phan0.521 \
    < /opt/seclab/database/sql/teacher_teaching_class.sql
docker exec -i seclab-mysql mysql -uroot -phan0.521 \
    < /opt/seclab/database/sql/seed_teacher_showcase.sql
```

### 14.5 Gradle 构建失败：`Could not find Java 17`

**原因**：`gradle.properties` 中的 JDK 路径是 Windows 格式。

**解决**：
```bash
echo "org.gradle.java.installations.paths=/usr/lib/jvm/java-17-openjdk-amd64" \
    > /opt/seclab/seclab-backend/gradle.properties
```

### 14.6 前端访问后端 404

**原因**：前端 `.env.production` 未配置或 nginx 路由缺失。

**解决**：
```bash
# 1. 确认 .env.production 存在
cat /opt/seclab/SecLab-FrontEnd-2/.env.production

# 2. 重新构建前端
cd /opt/seclab/SecLab-FrontEnd-2
npm run build

# 3. 检查 nginx 配置
sudo nginx -t
sudo nginx -s reload
```

### 14.7 noVNC 连接失败

**原因**：nginx WebSocket 代理配置缺失或 ai-agent-service 未启动。

**解决**：
```bash
# 1. 检查 ai-agent-service
curl http://127.0.0.1:8010/health

# 2. 检查 nginx WebSocket 配置
grep -A5 'api/docker/vnc' /etc/nginx/sites-enabled/seclab
# 应包含 proxy_http_version 1.1 和 Upgrade/Connection 头

# 3. 重载 nginx
sudo nginx -s reload
```

### 14.8 Docker 容器无法访问宿主机服务

**原因**：容器内 `localhost` 指向容器自身，不是宿主机。

**解决**：靶场的 `docker-compose.yml` 中已配置 `host.docker.internal`，如仍有问题：

```bash
# 检查容器是否能访问宿主机
docker exec -it sqli-lab-web-1 ping host.docker.internal

# 如果不通，在 docker-compose.yml 中添加
# extra_hosts:
#   - "host.docker.internal:host-gateway"
```

### 14.9 磁盘空间不足

```bash
# 检查磁盘
df -h

# 清理 Docker 无用镜像和容器
docker system prune -a --volumes

# 清理 Gradle 缓存
rm -rf /opt/seclab/seclab-backend/.gradle
rm -rf /opt/seclab/seclab-backend/*/.gradle

# 清理 npm 缓存
rm -rf /opt/seclab/SecLab-FrontEnd-2/node_modules
npm cache clean --force
```

### 14.10 端口被占用

```bash
# 查看端口占用
ss -tlnp | grep -E '8083|8084|8086|8010|3306|8088'

# 杀掉占用进程
fuser -k 8083/tcp

# 或修改服务端口（在 application.yml 中）
```

---

---

## 15. 从旧版升级（已部署过旧版本）

如果服务器上已部署过旧版本，推荐使用 **"备份 → 替换 → 迁移"** 策略，不需要从零开始。

### 15.1 升级前检查

```bash
# SSH 登录服务器，检查旧版状态
echo "=== 旧版状态检查 ==="

# 1. 旧代码目录
ls -la /opt/seclab/SecLab/ 2>/dev/null && echo "✓ 旧代码存在" || echo "✗ 旧代码不存在"

# 2. MySQL 容器
docker ps -a --format '{{.Names}} {{.Status}}' | grep -i mysql

# 3. MySQL 数据卷
ls -la /opt/seclab/data/mysql/ 2>/dev/null | head -3

# 4. 运行中的服务
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'lab|sec-code|seclab'
systemctl list-units --type=service | grep seclab

# 5. Nginx
ls /etc/nginx/sites-enabled/seclab 2>/dev/null && echo "✓ Nginx 配置存在"

# 6. 检查旧版 MySQL 密码（如不确定，试常见的）
docker exec seclab-mysql mysqladmin ping -uroot -phan0.521 --silent 2>/dev/null \
    && echo "MySQL 密码: han0.521" \
    || echo "MySQL 密码不是 han0.521，需要确认"
```

### 15.2 一键升级（推荐）

#### 步骤 1：在 Windows 上打包新代码

```powershell
cd D:\SecLab

# 打包（排除 node_modules/build/.gradle 等大目录）
tar -czf SecLab-deploy.tar.gz `
    --exclude='SecLab/node_modules' `
    --exclude='SecLab/SecLab-FrontEnd-2/node_modules' `
    --exclude='SecLab/seclab-backend/node_modules' `
    --exclude='SecLab/SecLab-FrontEnd-2/dist' `
    --exclude='SecLab/build' `
    --exclude='SecLab/seclab-backend/build' `
    --exclude='SecLab/seclab-backend/*/build' `
    --exclude='SecLab/.gradle' `
    --exclude='SecLab/seclab-backend/.gradle' `
    --exclude='SecLab/seclab-backend/*/.gradle' `
    --exclude='SecLab/seclab-backend/ai-agent-service/venv' `
    --exclude='SecLab/seclab-backend/ai-agent-service/__pycache__' `
    --exclude='SecLab/**/*.log' `
    SecLab

# 上传到服务器
scp SecLab-deploy.tar.gz root@<服务器IP>:/tmp/
```

#### 步骤 2：在服务器上执行升级脚本

```bash
# 执行升级脚本（自动完成备份→停服务→替换代码→迁移数据库→重建→启动）
bash /opt/seclab/SecLab/deploy/scripts/update-from-old.sh /tmp/SecLab-deploy.tar.gz

# 如果旧版路径不在 /opt/seclab/SecLab，指定路径：
# OLD_PROJECT_DIR=/your/old/path bash deploy/scripts/update-from-old.sh /tmp/SecLab-deploy.tar.gz
```

升级脚本会自动执行：

| 步骤 | 操作 | 安全保证 |
|------|------|----------|
| 1 | mysqldump 备份所有数据库 | 备份到 `/opt/seclab/backup/<时间戳>/` |
| 2 | 备份旧 `.env` 和 nginx 配置 | 不丢失 DIFY_API_KEY 等配置 |
| 3 | 停止所有旧服务（systemd + 进程 + 容器） | — |
| 4 | 旧代码重命名为 `.old`，解压新代码 | 旧代码完整保留，可回滚 |
| 5 | 迁移 `.env` 到新代码，修复 Gradle JDK 路径 | DIFY_API_KEY 自动迁移 |
| 6 | 运行 `bootstrap-mysql.sh`（幂等） | 只补缺表/缺列，不删现有数据 |
| 7 | 重新构建后端 JAR + 前端 + noVNC 镜像 | — |
| 8 | 更新 nginx/systemd 配置，启动所有服务 | — |

### 15.3 手动升级（如需更细粒度控制）

如果一键脚本不适用，可手动分步执行：

```bash
# ── 变量 ──
OLD_DIR="/opt/seclab/SecLab"
NEW_TAR="/tmp/SecLab-deploy.tar.gz"
TS=$(date +%Y%m%d_%H%M%S)
MYSQL_PW="han0.521"

# ── 1. 备份 MySQL ──
mkdir -p /opt/seclab/backup/$TS
docker exec seclab-mysql mysqldump -uroot -p$MYSQL_PW \
    --databases userservice seclab_profile imagedb \
    --single-transaction --routines --triggers \
    > /opt/seclab/backup/$TS/mysql-backup.sql

# ── 2. 备份旧 .env ──
cp $OLD_DIR/seclab-backend/ai-agent-service/.env /opt/seclab/backup/$TS/ai-agent.env 2>/dev/null
cp /etc/nginx/sites-enabled/seclab /opt/seclab/backup/$TS/nginx.conf 2>/dev/null

# ── 3. 停止旧服务 ──
sudo systemctl stop seclab-ai-agent seclab-user-service seclab-experiment-module 2>/dev/null
pkill -f 'bootRun|main.py|docker-api-server' 2>/dev/null
for lab in sqli-lab xss-lab csrf-lab file-upload-lab directory-traversal-lab command-inject stack-overflow-lab protocol-analysis-lab; do
    cd $OLD_DIR/seclab-backend/$lab 2>/dev/null && docker compose down 2>/dev/null
done

# ── 4. 替换代码 ──
cd /opt/seclab
mv SecLab SecLab.old
mkdir SecLab
tar -xzf $NEW_TAR --strip-components=1 -C SecLab
find SecLab -name "*.sh" -exec dos2unix {} \;
echo "org.gradle.java.installations.paths=/usr/lib/jvm/java-17-openjdk-amd64" > SecLab/seclab-backend/gradle.properties

# ── 5. 迁移 .env ──
cp /opt/seclab/backup/$TS/ai-agent.env SecLab/seclab-backend/ai-agent-service/.env

# ── 6. 数据库迁移（幂等，只补缺） ──
cd /opt/seclab/SecLab
bash deploy/scripts/bootstrap-mysql.sh

# ── 7. 重新构建 ──
cd seclab-backend && chmod +x gradlew
./gradlew :user-service:bootJar :experiment-module-service:bootJar :image-service:bootJar -x test
cd ../SecLab-FrontEnd-2 && npm install && npm run build
cd ../seclab-backend/operation-image && docker build -t seclab-op-web-tools:1.0 .

# ── 8. 更新 nginx + 启动 ──
cd /opt/seclab/SecLab
sudo cp deploy/nginx/seclab.conf /etc/nginx/sites-available/seclab
sudo nginx -t && sudo systemctl reload nginx
bash deploy/scripts/start-all-services.sh
```

### 15.4 验证升级

```bash
# 1. 检查前端
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8088/
# 应返回 200

# 2. 登录测试
curl -s -X POST http://127.0.0.1:8088/stu/login \
    -H "Content-Type: application/json" \
    -d '{"userStudentNumber":"admin","userPassword":"123456"}' | head -c 200
# 应返回 token

# 3. 检查新靶场（旧版可能没有）
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8096/  # 栈溢出
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8896/  # 协议分析

# 4. 检查教师端
curl -s http://127.0.0.1:8088/course/overview-list | head -c 200

# 5. 检查数据库数据是否完整
docker exec seclab-mysql mysql -uroot -phan0.521 userservice \
    -e "SELECT COUNT(*) AS users FROM user;"
# 用户数应与升级前一致（或更多，因为 bootstrap 补了 admin 账号）
```

### 15.5 回滚（如升级失败）

```bash
# 1. 停止新服务
bash /opt/seclab/SecLab/deploy/scripts/stop-all-services.sh
STOP_MYSQL=true bash /opt/seclab/SecLab/deploy/scripts/stop-all-services.sh

# 2. 恢复旧代码
cd /opt/seclab
mv SecLab SecLab.failed     # 保留失败的新代码供排查
mv SecLab.old SecLab        # 恢复旧代码

# 3. 恢复 MySQL（如数据被破坏）
docker exec -i seclab-mysql mysql -uroot -phan0.521 \
    < /opt/seclab/backup/<时间戳>/mysql-backup.sql

# 4. 恢复旧 nginx 配置
sudo cp /opt/seclab/backup/<时间戳>/nginx.conf /etc/nginx/sites-enabled/seclab
sudo nginx -s reload

# 5. 启动旧服务
cd /opt/seclab/SecLab
# 使用旧版的启动方式（.bat 已不可用，用旧版的 docker/systemd 启动）
```

### 15.6 清理旧代码

确认新版本运行稳定 **至少 24 小时** 后，可清理旧代码和备份：

```bash
# 删除旧代码目录
rm -rf /opt/seclab/SecLab.old

# 删除失败的新代码（如已回滚）
rm -rf /opt/seclab/SecLab.failed

# 清理旧备份（保留最近 2 次）
ls -dt /opt/seclab/backup/*/ | tail -n +3 | xargs rm -rf

# 清理 Docker 无用镜像
docker image prune -a
```

### 15.7 旧版常见差异处理

| 旧版情况 | 处理方式 |
|----------|----------|
| MySQL 密码不是 `han0.521` | `MYSQL_ROOT_PASSWORD=你的密码 bash update-from-old.sh ...` |
| 旧版没有 ai-agent-service | 脚本会从 `.env.example` 创建 `.env`，需手动填 `DIFY_API_KEY` |
| 旧版用 Docker 镜像跑 Java 服务 | 脚本会用 Gradle bootRun 启动，旧 Docker 镜像可忽略 |
| 旧版 MySQL 不是 Docker 容器 | 需手动 mysqldump，然后导入到新的 Docker MySQL |
| 旧版代码在别的路径 | `OLD_PROJECT_DIR=/your/path bash update-from-old.sh ...` |
| 旧版没有 nginx，直接访问端口 | 新版必须用 nginx，按文档第 11 章配置 |

---

## 附录 A：完整部署速查命令

```bash
# === 服务器环境准备 ===
sudo apt update && sudo apt install -y \
    openjdk-17-jdk python3 python3-venv nodejs npm \
    nginx docker.io docker-compose-plugin dos2unix
sudo usermod -aG docker $USER  # 然后重新登录

# === 上传解压 ===
# (在 Windows 上) scp D:\SecLab\SecLab-deploy.tar.gz user@server:/tmp/
sudo mkdir -p /opt/seclab && sudo chown $USER:$USER /opt/seclab
cd /opt/seclab && tar -xzf /tmp/SecLab-deploy.tar.gz --strip-components=1
find . -name "*.sh" -exec dos2unix {} \;
echo "org.gradle.java.installations.paths=/usr/lib/jvm/java-17-openjdk-amd64" > seclab-backend/gradle.properties

# === 数据库 ===
bash deploy/scripts/bootstrap-mysql.sh

# === AI Agent 配置 ===
cd seclab-backend/ai-agent-service
cp .env.example .env && vim .env  # 填入 DIFY_API_KEY
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate
cd /opt/seclab

# === 构建后端 ===
cd seclab-backend && chmod +x gradlew
./gradlew :user-service:bootJar :experiment-module-service:bootJar :image-service:bootJar -x test
cd ../..

# === 构建前端 ===
cd SecLab-FrontEnd-2 && npm install && npm run build && cd ..

# === 构建 noVNC 镜像 ===
cd seclab-backend/operation-image && docker build -t seclab-op-web-tools:1.0 . && cd ../..

# === 启动所有服务 ===
bash deploy/scripts/start-all-services.sh

# === 配置 Nginx ===
sudo cp deploy/nginx/seclab.conf /etc/nginx/sites-available/seclab
sudo ln -sfn /etc/nginx/sites-available/seclab /etc/nginx/sites-enabled/seclab
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# === 验证 ===
curl http://127.0.0.1:8088/
curl -X POST http://127.0.0.1:8088/stu/login -H "Content-Type: application/json" -d '{"userStudentNumber":"admin","userPassword":"123456"}'
```

---

## 附录 B：部署文件清单

| 文件 | 用途 |
|------|------|
| `deploy/scripts/start-all-services.sh` | Linux 一键启动所有服务 |
| `deploy/scripts/stop-all-services.sh` | Linux 一键停止所有服务 |
| `deploy/scripts/bootstrap-mysql.sh` | MySQL 容器创建 + 数据库导入 + 验证 |
| `deploy/scripts/deploy-all.sh` | 全自动部署（含 systemd + nginx 安装） |
| `deploy/nginx/seclab.conf` | Nginx 反向代理配置 |
| `deploy/systemd/seclab-*.service` | systemd 服务单元（4 个服务） |
| `SecLab-FrontEnd-2/.env.production` | 前端生产环境变量（API 地址使用相对路径） |
| `database/sql/*.sql` | 数据库主初始化脚本 |
| `shujuku/*.sql` | 数据库细粒度建表和种子数据 |

---

**文档版本**：2026-07-26
**适用项目**：SecLab 网络安全漏洞综合实验平台
