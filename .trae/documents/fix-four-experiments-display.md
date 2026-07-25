# 让四个实验在课程页正常显示的修复方案

## Context（背景）

用户已引入两个靶场（`seclab-backend/stack-overflow-lab`、`seclab-backend/protocol-analysis-lab`）和两张封面图（`cover-heap-overflow.png`、`cover-format-string.png`），但前端课程页 `pages/User/Courses` 没有显示"栈溢出、协议分析、堆溢出、格式化字符串"这四个实验。

### 根因

1. **课程列表页** `pages/User/Courses/index.vue` 的 `mergeCourseSummariesWithPresentation`（[catalogPresentation.ts:287](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/mock/catalogPresentation.ts)）只遍历 `PRESENTATION_COURSE_SEEDS`（12 门，id 1-12），后端返回的新课程会被忽略。
2. **实验详情数据** `data/index.js` 的 `AllExperiments`（[index.js:436](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/data/index.js)）只有 13 个实验（id 1-13），`StackOverflowExperiment.js`（id 15）从未被 import 接入。
3. 协议分析、堆溢出、格式化字符串**没有实验数据 JS 文件**。
4. **课程详情页** `pages/User/Course/index.vue` 用硬编码 `allCourses` 数组（[index.vue:86](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/pages/User/Course/index.vue)），未含四门课。
5. **数据库** `database/sql/init_seclab_db.sql` 的 `course`/`module`/`module_course` 表只有 3 条种子，无新实验记录。

### id 对齐关系（关键）

模块点击跳 `/user/module/${id}` → `Module/index.vue` 与 `api.ts:getModuleDetail` 都调用 `findExperimentById(id)`（[api.ts:3105](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/api.ts)）。因此**模块 id 必须等于 `AllExperiments` 的 experiment id**，否则 fallback 到 SQL 注入实验。

## id 规划

避开现有 `PRESENTATION_MODULE_SEEDS` 的 id 14（"第三方框架漏洞"，遗留无对应实验数据），新实验统一用 id 15-18。`StackOverflowExperiment.js` 原 id 即 15，无需修改。

| 实验 | 课程 id (PRESENTATION_COURSE_SEEDS) | 模块/实验 id (AllExperiments & PRESENTATION_MODULE_SEEDS) | 封面图 |
|------|------|------|------|
| 栈溢出 | 13 | 15 | /cover-stack-overflow.png |
| 协议分析 | 14 | 16 | /13.png（用户后续补图） |
| 堆溢出 | 15 | 17 | /cover-heap-overflow.png |
| 格式化字符串 | 16 | 18 | /cover-format-string.png |

课程-模块关联（`PRESENTATION_MODULE_SEEDS.courseId`）：模块 15→课程 13、16→14、17→15、18→16。

## 修复方案（分层）

### 第一层：前端课程列表种子

文件：[SecLab-FrontEnd-2/src/mock/catalogPresentation.ts](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/mock/catalogPresentation.ts)

- `PRESENTATION_COURSE_SEEDS` 末尾追加 4 门课程种子（id 13-16），字段对齐现有结构（name/description/difficulty/type/category/cover/videoUrl/tags）。type 用 `system`（二进制/协议类归系统安全），category 用"系统安全"或"网络安全"。
- `PRESENTATION_MODULE_SEEDS` 末尾追加 4 个模块种子（id 15-18，courseId 对应 13-16），字段对齐现有结构。

### 第二层：前端课程详情页硬编码

文件：[SecLab-FrontEnd-2/src/pages/User/Course/index.vue](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/pages/User/Course/index.vue)

- `allCourses` 数组追加 4 门课程对象，每门含 `modules` 数组（moduleId 用 15-18，与 AllExperiments 对齐），保证点击模块能进入正确实验详情。

### 第三层：前端实验数据（完整教学级）

参照 `StackOverflowExperiment.js` 结构（4 taskPoints + 详细 document 教学文档 + questions 题目，约 16KB/个）。

文件：
- [SecLab-FrontEnd-2/src/data/StackOverflowExperiment.js](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/data/StackOverflowExperiment.js)：id 保持 15，无需改。
- **新建** `SecLab-FrontEnd-2/src/data/ProtocolAnalysisExperiment.js`（id 16）：基于 `protocol-analysis-lab` 靶场，taskPoints 主题：①协议分析基础与 Wireshark 使用 ②HTTP 协议深度分析 ③TCP/UDP 协议分析（三次握手/四次挥手）④协议安全：明文嗅探与 HTTPS/TLS。
- **新建** `SecLab-FrontEnd-2/src/data/HeapOverflowExperiment.js`（id 17）：taskPoints 主题：①堆基础与 glibc malloc 机制（chunk/fastbin/smallbin）②堆溢出原理与漏洞程序编写 ③unlink 利用与 fastbin attack ④实战 exp 编写与 getshell。
- **新建** `SecLab-FrontEnd-2/src/data/FormatStringExperiment.js`（id 18）：taskPoints 主题：①printf 与格式化字符串漏洞原理 ②栈上任意地址泄露（%p/%x 泄露 canary/libc）③任意地址写入（%n）④实战 exp：泄露与劫持控制流。
- [SecLab-FrontEnd-2/src/data/index.js](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/data/index.js)：import 4 个实验，追加到 `AllExperiments`（id 15-18），更新 `ExperimentTypes` 常量与注释。
- [SecLab-FrontEnd-2/src/data/index.d.ts](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/data/index.d.ts)：补充 4 个新实验的 `ExperimentType` 声明与 `ExperimentTypes` 字段。

### 第四层：数据库主初始化脚本

文件：[database/sql/init_seclab_db.sql](file:///d:/SecLab/SecLab/database/sql/init_seclab_db.sql)

- `course` 表 `INSERT IGNORE` 追加 4 条（id 13-16），字段对齐现有（cost_time/course_description/difficulty/image_url/instructor/course_name/schedule/course_status/tags/type）。image_url 用封面图文件名。
- `module` 表 `INSERT IGNORE` 追加 4 条（id 15-18），字段对齐现有（module_id/difficulty/image_id/introduction/module_name/task_points/type）。task_points 用 `'[]'`，image_id 给一个合理值（沿用现有 101/102/103 风格或引用已有 image 记录）。
- `module_course` 表 `INSERT IGNORE` 追加 4 条关联：(15,13),(16,14),(17,15),(18,16)。

注：`shujuku/` 下两库（userservice / experimentmoduleservice）种子与前端不一致，本次不同步，后续单独整理（用户确认）。

## 验证

1. **前端类型检查**：`cd SecLab-FrontEnd-2; npm run vue-tsc` 应无错误。
2. **前端运行**：`npm run dev`，访问 `/user/courses` 确认四门课卡片显示（封面、名称、难度、标签）。
3. **课程详情**：点击四门课进入 `/user/course/13|14|15|16`，确认模块列表显示。
4. **实验详情**：点击模块进入 `/user/module/15|16|17|18`，确认 taskPoints、document、questions 正确加载（非 fallback 到 SQL 注入）。控制台应打印"找到ID为N的实验: <对应名称>"。
5. **SQL 语法**：检查 `init_seclab_db.sql` 新增 INSERT 语句的字段数、值数、引号、表名正确。

## 风险与说明

1. **协议分析封面图**：`public/13.png` 当前不存在（public 下仅 1-12.png），用户后续补图，期间课程卡片显示破图。
2. **shujuku/ 两库种子未同步**：与 `database/sql/init_seclab_db.sql` 不一致，后续单独整理。
3. **新建实验数据内容**：基于标准 PWN/协议分析教学知识编写，需专业校对；靶场实际 flag/端口以靶场 `docker-compose.yml` 为准（协议分析 web 端口 8896）。
4. **遗留问题**：`PRESENTATION_MODULE_SEEDS` id 14"第三方框架漏洞"在 `AllExperiments` 无对应实验，点击仍 fallback 到 SQL 注入——这是本次范围外的遗留 bug，不处理。
5. **课程详情页硬编码**：`allCourses` 与 `PRESENTATION_COURSE_SEEDS` 重复维护，是现有架构债务，本次保持风格不重构。
