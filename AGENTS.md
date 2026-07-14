# SecLab-1 仓库协作规范

本文档是 SecLab-1 仓库级开发指引。所有后续代码、数据库、接口、靶场、人物画像相关修改，都应优先遵守本文档。

## 仓库结构

- `SecLab-FrontEnd-2/`：前端工程，基于 Vue 3、Vite、TypeScript、Tailwind CSS。
- `SecLab-FrontEnd-2/src/`：前端核心源码，包含路由、页面、组件、类型、API 封装和实验数据。
- `SecLab-FrontEnd-2/public/`：前端静态图片资源，保留头像、课程封面、默认图和 logo；`public/video/` 不进入源码仓库。
- `seclab/seclab/`：后端与靶场主目录，包含微服务工程、AI 辅助服务、Docker/Gradle 配置和靶场源码。
- `seclab/seclab/gateway/`：网关服务配置与工程目录。
- `seclab/seclab/eureka/`：服务注册中心配置与工程目录。
- `seclab/seclab/user-service/`：用户服务目录，和用户资料、班级、人物画像基础数据强相关。
- `seclab/seclab/experiment-module-service/`：课程、模块、实验相关服务目录。
- `seclab/seclab/image-service/`：图片、头像、课程图等资源服务目录。
- `seclab/seclab/docker-service/`：靶场容器管理相关服务目录。
- `seclab/seclab/ai-agent-service/`：AI 辅助与实验事件分析服务，后续人物画像、学习过程分析可复用这里的事件分析能力。
- `数据库文件/`：数据库结构和初始化脚本的主副本，包含用户、课程、模块、实验等相关 SQL。
- `seclab/seclab/sqli-lab/`、`xss-lab/`、`csrf-lab/`、`file-upload-lab/`、`directory-traversal-lab/`、`command-inject/`：主要靶机场景源码目录。
- `项目容器文件/`：历史/重复的靶场容器文件快照，默认不作为主开发目录；优先维护 `seclab/seclab/` 下的靶场源码。
- `SecLab系统部署说明文档.md`：系统部署说明。


前端：

```powershell
cd SecLab-FrontEnd-2
npm install
npm run dev
npm run build
npm run preview
npm run vue-tsc
```

后端 Gradle 主工程：

```powershell
cd seclab/seclab
.\gradlew.bat build
.\gradlew.bat :gateway:build
.\gradlew.bat :eureka:build
.\gradlew.bat :user-service:build
.\gradlew.bat :experiment-module-service:build
.\gradlew.bat :docker-service:build
.\gradlew.bat :image-service:build
```

AI 辅助服务：

```powershell
cd seclab/seclab/ai-agent-service
pip install -r requirements.txt
python main.py
```

Docker/靶场相关：

```powershell
cd seclab/seclab
docker compose up -d

cd seclab/seclab/sqli-lab
docker compose up -d
```

具体靶场启动命令以对应目录下的 `docker-compose.yml`、`Dockerfile` 和项目部署文档为准。

数据库：

- 优先维护 `数据库文件/` 下 SQL。
- 新增或修改表结构时，同步更新初始化脚本和必要说明。
- 不要只改代码而遗漏建表、字段、索引、默认数据或迁移说明。

## 开发原则

- 所有开发优先做“小步可回滚修改”：每次只解决一个明确问题，避免把重构、功能、样式、数据结构改动混在一起。
- 修改前先理解现有调用链、数据库表、接口入参/出参和前端页面状态，不凭猜测大范围重写。
- 不允许擅自删除现有可用接口、路由、字段、组件、脚本或靶场入口；确需废弃时，先说明替代方案和兼容影响。
- 不允许跳过数据库建表、接口定义、日志埋点、错误处理。涉及功能闭环时，数据库、后端接口、前端调用、日志与错误返回都要同时考虑。
- 新增代码必须可维护：命名清晰、边界明确、职责单一，复杂逻辑加必要注释；不要写只有当前作者能看懂的临时代码。
- 优先沿用仓库现有技术栈和目录风格，不随意引入新框架、新全局状态方案或新的服务拆分方式。
- `.env`、密钥、令牌、运行时上传文件、构建产物、依赖目录和大视频文件不得提交。

## 任务完成说明要求

每完成一个任务，必须在回复中说明：

- 改了哪些文件。
- 为什么这样改。
- 如何验证，包含执行过的命令、观察到的结果，或未能验证的原因。
- 是否涉及数据库结构、接口定义、事件类型、日志埋点、错误处理。
- 是否有剩余风险或需要用户确认的事项。

## 数据库与接口约束

- 所有新表、字段、索引、接口、事件类型都要先定义清楚再实现。
- 新表应说明用途、主键、外键或关联字段、关键索引、必要默认值。
- 新接口应说明 URL、方法、请求参数、响应结构、错误码或错误消息。
- 新事件类型应说明触发时机、事件字段、落库位置、幂等或重复上报处理方式。
- 数据库修改要优先落在 `数据库文件/`，并和前后端字段命名保持可追踪映射。
- 不要在前端硬编码替代真实接口，除非明确是临时 mock，并在任务说明中标出后续替换点。

## 人物画像开发约束

涉及人物画像、学习画像、班级画像或行为分析时，优先级如下：

1. 先保证事件采集真实可用。
2. 再保证事件可靠落库，可查询、可追溯、可排错。
3. 再定义画像所需的基础指标、统计口径和事件类型。
4. 最后再实现画像算法、评分模型、可视化或 AI 总结。

人物画像相关开发不得直接从前端静态假数据跳到算法展示。必须先明确：

- 采集哪些事件，例如登录、进入课程、打开模块、启动靶场、提交答案、请求提示、完成实验、查看解析等。
- 每类事件的字段，例如用户 ID、课程 ID、模块 ID、靶场容器 ID、时间戳、结果、耗时、分数、来源页面、错误信息。
- 事件如何进入后端，落到哪张表，如何处理失败重试和重复事件。
- 画像指标如何从事件表计算，哪些是实时统计，哪些是离线统计。
- 前端展示的数据来自哪个接口，是否有加载、空数据、错误状态。

## 靶场与安全实验约束

- 靶场源码优先维护 `seclab/seclab/` 下对应场景目录。
- 修改靶场时，保留可运行的 `Dockerfile`、`docker-compose.yml`、`init.sql` 和必要的 `web/`、`files/`、`conf/` 文件。
- 不要删除已有实验入口、flag 校验、初始化账号或教学提示，除非明确说明替代实现。
- 涉及容器启动、日志分析、AI 提示时，要关注 `docker-service`、`ai-agent-service` 与前端调用之间的契约。

## 提交与验证

- 提交前运行和本次修改相关的最小验证命令。
- 前端改动优先运行 `npm run vue-tsc` 和必要时 `npm run build`。
- 后端配置或服务改动优先运行对应 Gradle 子项目构建。
- SQL 改动至少检查语法、表名、字段名和接口字段映射。
- 靶场改动至少检查对应 Docker 配置和启动路径。
- 每次提交保持主题清晰，提交信息能表达本次改动目的。
