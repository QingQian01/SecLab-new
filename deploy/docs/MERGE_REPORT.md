# SecLab 双版本合并报告

## 合并方向

以同事项目 `D:\Seclab\SecLab (2)\SecLab` 为底，合并用户项目 `e:\Project\SecLab\SeclabSecond\Seclab` 的 noVNC 操作环境能力。原始同事目录和原始用户目录均未覆盖，本次结果落在 `D:\Seclab\SecLab-Merged`。

## 同事版本的主要变化

- 精简顶层目录：移除了原项目里的 `.claude/`、`tmp-*`、`数据库文件/`、`项目容器文件/`、`同事修改的部分/` 等开发/历史目录，数据库脚本集中到 `shujuku/`，另保留 `database/`。
- 保留并增强事件上报相关代码：`ai-agent-service/main.py`、多个 repository、前端 `useLabState.ts`、`Module/index.vue` 里有实验事件收集、结束实验上报、路由离开保护。
- 新增演示数据：`seed-demo-scoreboard-data.sql`、`seed-demo-teacher-data.sql`。
- 修改图片服务配置：前端 `IMAGE_SERVICE_BASE_URL` 指向 `8086`。
- 退化点：同事版本删除了 `ModuleOverView.vue` 的开始实验跳转；操作环境仍是旧 iframe 占位，没有 noVNC。

## 本次合并写入的用户功能

- 后端：
  - 合入 `operation_env.py`、`operation_session_repository.py`。
  - `main.py` 新增 `/api/docker/operation/start`、`/stop`、`/status/{session_id}`、`WS /api/docker/vnc/{session_id}`。
  - startup 启动 operation session 清理循环。
- 前端：
  - 合入 `VNCViewer.vue`。
  - `vite.config.ts` 将 `/api/docker` 代理到 `8010` 并开启 `ws:true`，同时设置 `build.target: esnext`。
  - `Module/index.vue` 的操作环境改为创建 per-user operation 容器，并通过 noVNC 连接。
  - 显示操作环境内部靶机访问地址，例如 `http://command-inject-web-1/index.html`。
- 操作机镜像：
  - 合入 `seclab-backend/operation-image/`，包含 XFCE/TigerVNC/noVNC 所需工具和 6 类实验壁纸。
- 数据库：
  - 合入 `shujuku/operation-session.sql`。

## 冲突处理

- 实验事件上报：保留同事版本。
- 结束实验：保留同事事件上报流程，但不再 stop 共享靶机，只 stop 当前用户的 operation 容器。
- 靶机容器名：保留同事版本 `CONTAINER_NAMES`，和 noVNC 后端映射一致。
- 命令注入 URL：修为 `index.html`，避免旧 `index.php` 404。
- 注册头像：头像上传失败只提示，不阻断 `/stu/register`。
- 模块详情：`getModuleDetail` 改为请求 experiment-module-service `8084`；若接口不可用，继续 fallback 本地实验数据。
- 开始实验按钮：恢复 `ModuleOverView.vue` 的 `router.push('/user/module/:id')`。

## 本次新增部署产物

- `deploy/systemd/seclab-ai-agent.service`
- `deploy/systemd/seclab-user-service.service`
- `deploy/systemd/seclab-experiment-module.service`
- `deploy/nginx/seclab.conf`
- `deploy/scripts/bootstrap-mysql.sh`
- `deploy/scripts/deploy-all.sh`
- `deploy/scripts/verify-local.sh`
- `deploy/docs/SERVER_DEPLOYMENT.md`

## 剩余风险

- 当前 `experiment-module-service` 没有完整 `/course/module/detail` 详情端点，前端依赖本地 fallback 数据保证能进实验。后续若要完全去 mock，需要补课程/模块/任务点/题目详情接口和数据库表。
- Linux 脚本需要在真实服务器上按实际用户名、IP、防火墙、Node 版本调整。
- `image-service` 虽然目录存在，但需要确认服务器上是否真的能构建和运行；本次注册流程已绕开头像上传失败阻断。
- `deploy/scripts/bootstrap-mysql.sh` 为幂等导入脚本，刻意不导入会 `DROP TABLE` 的旧 dump；若要完整恢复旧数据库快照，需要先人工备份再导入。
- 前端生产构建默认使用相对 API 路径，由 nginx 转发到本机服务；开发环境仍默认使用 `localhost` 端口。
