# SecLab 平台 2核2GB 云服务器优化部署方案

## Context

用户需要将 SecLab 平台部署到阿里云 ECS（2核 vCPU / 2GB RAM / Ubuntu 22.04 / 3Mbps 带宽）。PVE 部署指南推荐 4核8GB，直接全量部署会导致 OOM 崩溃。需裁剪非核心服务、优化内存配置、靶场改为按需启动，以支持单用户教学演示。

目标服务器：`47.97.154.90`，SSH `root/Lab123456`。

## 裁剪决策

| 保留 | 移除 | 理由 |
|------|------|------|
| MySQL、user-service、experiment-module-service、ai-agent-service、Nginx、noVNC | image-service | 头像上传非核心，省 ~300MB |
| | eureka、gateway | 前端 .env.production 用相对路径，Nginx 直连后端，省 ~600MB |
| | sec-code | 安全代码容器非核心，省 ~50MB |
| | 8个靶场常驻 | 改为按需启动，省 ~800MB |

## 内存预算（2GB + 2GB Swap）

| 组件 | 稳态 | 峰值（noVNC+1靶场） |
|------|------|-----|
| 系统+Docker daemon | 350MB | 350MB |
| MySQL 8.0 | 430MB | 430MB |
| user-service (-Xmx256m) | 300MB | 300MB |
| experiment-module-service (-Xmx256m) | 300MB | 300MB |
| ai-agent-service | 120MB | 120MB |
| Nginx | 20MB | 20MB |
| 1个靶场（按需） | 0 | 150MB |
| noVNC（按需） | 0 | 250MB |
| **合计** | **~1.52GB** | **~1.92GB** |

稳态留约 500MB 余量，峰值靠 2GB swap 缓冲。

## 实施步骤

### 步骤 1：本地打包项目（Windows）

在 Windows 上打包源码（不构建 JAR，JAR 在服务器上构建）：

```powershell
cd D:\SecLab
tar -czf SecLab-deploy.tar.gz \
    --exclude='SecLab/node_modules' \
    --exclude='SecLab/SecLab-FrontEnd-2/node_modules' \
    --exclude='SecLab/SecLab-FrontEnd-2/dist' \
    --exclude='SecLab/seclab-backend/build' \
    --exclude='SecLab/seclab-backend/*/build' \
    --exclude='SecLab/seclab-backend/.gradle' \
    --exclude='SecLab/seclab-backend/*/.gradle' \
    --exclude='SecLab/seclab-backend/ai-agent-service/venv' \
    --exclude='SecLab/**/*.log' \
    --exclude='SecLab/.trae' \
    --exclude='SecLab/.vscode' \
    SecLab
```

上传到新服务器：
```powershell
D:\PuTTY\pscp.exe -pw Lab123456 SecLab-deploy.tar.gz root@47.97.154.90:/tmp/
```

### 步骤 2：服务器环境准备

**修改文件：`deploy/scripts/bootstrap-mysql.sh`** — MySQL 启动命令追加内存优化参数：
- `--innodb-buffer-pool-size=256M`
- `--max-connections=50`
- `--performance-schema=OFF`
- `--skip-name-resolve`
- `--memory=512m`

**修改文件：`deploy/systemd/seclab-user-service.service`** — 添加 JVM 参数和内存限制：
```
ExecStart=... java -Xms128m -Xmx256m -XX:MaxMetaspaceSize=128m -XX:+UseSerialGC -XX:+ExitOnOutOfMemoryError -Dspring.jmx.enabled=false -jar .../user-service/build/libs/*.jar
MemoryMax=400M
```

**修改文件：`deploy/systemd/seclab-experiment-module.service`** — 同上 JVM 参数。

**修改文件：`deploy/systemd/seclab-ai-agent.service`** — 添加 Dify Key、MySQL 环境变量、`--workers 1`、`MemoryMax=200M`。

**删除文件：`deploy/systemd/seclab-image-service.service`** — 不部署此服务。

**修改文件：`deploy/nginx/seclab.conf`** — 删除 `/api/images/` 代理段（image-service 已移除）。

### 步骤 3：服务器执行部署

SSH 到服务器后按顺序执行：

1. **安装基础环境**：`apt install -y openjdk-21-jdk-headless python3 python3-venv nginx docker.io docker-compose-plugin dos2unix`
2. **创建 2GB swap**：`fallocate -l 2G /swapfile && mkswap /swapfile && swapon /swapfile`
3. **解压项目**到 `/opt/seclab/SecLab`
4. **修复换行符**：`find /opt/seclab -name "*.sh" -exec dos2unix {} \;`
5. **修正 Gradle JDK 路径**：`echo 'org.gradle.java.installations.paths=/usr/lib/jvm/java-21-openjdk-amd64' > seclab-backend/gradle.properties`
6. **启动 MySQL**：`bash deploy/scripts/bootstrap-mysql.sh`（使用优化后的配置）
7. **构建 JAR**（有 swap 兜底）：`cd seclab-backend && ./gradlew :user-service:bootJar :experiment-module-service:bootJar -x test`
8. **构建前端**：`cd SecLab-FrontEnd-2 && npm install && npm run build`
9. **创建 Python venv**：`cd ai-agent-service && python3 -m venv venv && venv/bin/pip install -r requirements.txt`
10. **构建靶场镜像并创建容器**（创建后立即 stop）：
    ```bash
    for lab in sqli-lab xss-lab csrf-lab file-upload-lab directory-traversal-lab command-inject stack-overflow-lab protocol-analysis-lab; do
        cd $lab && docker compose up -d --build && docker compose stop && cd ..
    done
    ```
11. **构建 noVNC 镜像**：`cd operation-image && docker build -t seclab-op-web-tools:1.0 .`
12. **安装 systemd 服务**：复制 3 个 .service 文件（user-service, experiment-module, ai-agent），`systemctl daemon-reload && systemctl enable --now ...`
13. **配置 Nginx**：复制 seclab.conf，`nginx -t && systemctl restart nginx`
14. **开放安全组**：阿里云控制台放行 8088/TCP

### 步骤 4：数据库导入

1. `bootstrap-mysql.sh` 自动导入主初始化脚本 + admin 账号 + showcase 数据
2. 导入演示数据：`docker exec -i seclab-mysql mysql -uroot-phan0.521 < database/sql/reset_and_seed_teacher_demo.sql`
3. **不导入** `seed_teacher_130_data.sql`（班级名不一致，130 学生对单用户演示无必要）

### 步骤 5：验证

```bash
# 服务健康
systemctl status seclab-user-service seclab-experiment-module-service seclab-ai-agent
curl -s http://127.0.0.1:8010/health/ai-analysis
curl -s -X POST http://127.0.0.1:8088/stu/login -H "Content-Type: application/json" -d '{"userStudentNumber":"admin","userPassword":"123456"}'

# 内存检查
free -h
docker stats --no-stream

# 浏览器访问 http://47.97.154.90:8088/
```

## 关键修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `deploy/scripts/bootstrap-mysql.sh` | MySQL docker run 追加内存优化参数 |
| `deploy/systemd/seclab-user-service.service` | JVM 参数 -Xmx256m + MemoryMax=400M |
| `deploy/systemd/seclab-experiment-module.service` | JVM 参数 -Xmx256m + MemoryMax=400M |
| `deploy/systemd/seclab-ai-agent.service` | Dify Key + MySQL 环境变量 + --workers 1 + MemoryMax=200M |
| `deploy/nginx/seclab.conf` | 删除 /api/images/ 代理段 |

## 风险与注意事项

1. **JDK 21 要求**：`build.gradle.kts` 声明 `JavaLanguageVersion.of(21)`，服务器必须装 `openjdk-21-jdk`，不是 17
2. **image-service 移除后**：头像上传返回 404，不影响教学演示主链路
3. **含 MySQL 5.7 的靶场**（sqli/csrf/upload/protocol）：每个多占 ~200MB，教学时只同时开 1 个
4. **3Mbps 带宽**：首次拉取 Docker 镜像（mysql:8.0/5.7, debian 等）约 1-2GB，耗时较长
5. **构建期内存**：Gradle 构建峰值约 1.5GB，需先创建 swap 再构建
6. **构建后清理**：构建完成后清理 Gradle 缓存 `rm -rf ~/.gradle seclab-backend/.gradle` 释放磁盘
