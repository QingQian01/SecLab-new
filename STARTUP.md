# SecLab 启动

## 1. 启动 Docker Desktop

打开 Docker Desktop，等待左下角图标变成绿色（Running）。

## 2. 启动后端

```powershell
cd seclab-backend
.\start-all-services.bat
```

## 3. 启动前端

```powershell
cd SecLab-FrontEnd-2
npm run dev
```

若前端报错 `crypto$2.getRandomValues is not a function`，说明 Node.js 版本过低，先切换：

```powershell
nvm use 23.10.0
```

再重新执行 `npm run dev`。

## 4. 打开浏览器

访问 http://localhost:5173/

## 停止服务

1. 关闭后端脚本弹出的所有 cmd 窗口（user-service、experiment-module-service、Docker API、AI Agent）。

2. 停止所有 Docker 容器：

```powershell
docker stop $(docker ps -q)
```
