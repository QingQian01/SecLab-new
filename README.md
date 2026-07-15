# SecLab

SecLab 是网络安全实验平台，核心包含前端、后端微服务、AI 辅助服务、靶场源码和数据库初始化脚本。

## 核心目录

- `SecLab-FrontEnd-2/`：Vue 3 前端工程。
- `seclab-backend/`：后端微服务、AI 服务、Docker 配置和靶场源码。
- `database/sql/`：主数据库初始化脚本。
- `STARTUP.md`：本地启动简要命令。
- `AGENTS.md`：仓库协作规范。

## 常用命令

前端：

```powershell
cd SecLab-FrontEnd-2
npm install
npm run dev
```

后端：

```powershell
cd seclab-backend
.\gradlew.bat build
```

AI 辅助服务：

```powershell
cd seclab-backend/ai-agent-service
pip install -r requirements.txt
python main.py
```

Docker 靶场：

```powershell
cd seclab-backend
docker compose up -d
```

## 数据库

主初始化脚本：

- `database/sql/init_seclab_db.sql`
- `database/sql/init_seclab_profile.sql`

靶场初始化脚本保留在各靶场目录内，例如 `seclab-backend/sqli-lab/init.sql`。
