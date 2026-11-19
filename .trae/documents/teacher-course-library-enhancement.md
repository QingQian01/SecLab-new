# 教师端课程库增强 + 测试数据整合 + 实验包上传登记

## Context（背景）

当前教师端课程库（`src/pages/Teacher/CourseLibrary/index.vue`）只是基础 CRUD：课程卡片只显示名称/描述/难度/状态，**看不到课程内的实验模块**，也**不能在点击课程时直观编辑信息或切换发布**——与学生端看到的课程内容（封面/标签/模块列表）脱节。

同时：
- `testsql/` 下 4 个测试数据脚本互相冲突（班级名不一致、学生号段重叠、硬编码 ID），且引用了不存在的 module 4-6，无法直接使用。
- 教师无法上传自定义实验包；`stack-overflow-lab` 这类靶场只能由开发人员手工部署。

目标：按风险从小到大分三阶段交付——① 课程库前端对齐学生端并支持编辑/发布；② 整合修复测试数据入库；③ 实验包 zip 上传 + 元数据登记（不做自动构建/启动，用户已确认范围）。

---

## Phase 1：教师端课程库对齐学生端 + 点击编辑/发布（纯前端）

**范围：仅前端，零 DB / 零接口改动。** 所有需要的接口 `api.ts` 已封装。

### 复用的现有接口与类型（`src/api.ts`）
- `getTeacherCourseList()` / `getTeacherCourseDetail(id)` / `createTeacherCourse` / `updateTeacherCourse` / `deleteTeacherCourse`
- `getCourseModules(courseId)` — 课程内实验列表（[api.ts:2294](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/api.ts#L2294)）
- `addCourseModule(courseId, moduleId)` / `removeCourseModule(courseId, moduleId)`（[api.ts:2301-2316](file:///d:/SecLab/SecLab/SecLab-FrontEnd-2/src/api.ts#L2301-L2316)）
- `getTeacherLabList()` — 全部实验池，用于添加到课程
- 类型：`AdminCourse`、`AdminExperiment`、`TeacherCourseMutationPayload`、`TeacherLabMutationPayload`

### 改动文件
- `src/pages/Teacher/CourseLibrary/index.vue`（主改动）
- 新增 `src/pages/Teacher/CourseLibrary/components/CourseDetailDrawer.vue`（课程详情/编辑抽屉，沿用 `teacher-page.css` 风格）

### 具体改动
1. **课程卡片信息对齐学生端**：在现有卡片上补充封面图（`course.cover`）、标签（`course.tags`）、实验数（`course.experimentCount`），与学生端 `CourseOverView` 展示字段一致。
2. **点击卡片 → 打开详情/编辑抽屉**（替代当前只有"编辑"按钮弹 modal 的方式）：
   - 编辑表单：name / description / difficulty / category / tags / cover / status
   - **发布开关**：`status` 在 `published ↔ draft` 间快捷切换（`archived` 保留在下拉），切换即调 `updateTeacherCourse`。
   - **课程内实验列表**：抽屉内调 `getCourseModules(courseId)` 渲染实验列表，每项可"移除"（`removeCourseModule`）。
   - **添加实验**：从 `getTeacherLabList()` 实验池中选择并"加入课程"（`addCourseModule`）。
3. 保留现有"创建课程""删除"能力；创建仍用 modal，编辑改为抽屉以容纳实验管理。

### 验证
- `npm run vue-tsc`（类型检查，必须无错）
- `npm run dev` 手动：登录教师 → 课程库 → 点课程卡片 → 编辑信息 → 切换发布 → 添加/移除实验 → 刷新确认持久化

---

## Phase 2：测试数据整合修复入库

**范围：DB 种子脚本整合，由用户在演示库执行。** 会清空 STUDENT 账号及学习数据。

### 现状冲突点（需修复）
- 班级名：`reset_and_seed` 用 '网络空间安全232班'，`seed_teacher_130` 查 '网络安全232班'（不匹配会得 NULL）
- 学生号段重叠：8 / 32 / 130 三套都从 202321040501 起；130 是超集
- 硬编码 ID：`showcase` 硬编码 `teaching_class_id=1 / teacher_id=1 / admin_class_id=3`
- **数据缺口**：130 脚本引用 module_id 1-6（`MOD(seq-1,6)+1`），但 `experiment-module-service-local-init.sql` 只插了 module 1-3

### 改动文件
- 新增 `shujuku/seed_teacher_demo.sql`（合并 4 个 `testsql/` 脚本为单一可重复执行脚本）
- 新增 `shujuku/seed_teacher_demo.README.md`（前置依赖 + 执行步骤 + 影响范围说明）
- 新增 `shujuku/seed_teacher_demo_modules.sql`（补 module 4-6 + module_course 关联，对齐 course 5-8，让教师端课程库有更丰富的实验可展示）

### 整合策略
1. 统一班级名为 '网络空间安全232班'，`@admin_class_id`/`@teacher_id`/`@teaching_class_id` **全部用 SELECT 查询赋值**，不硬编码。
2. 采用 130 学生数据集（丢弃 8/32 冲突版本），教师账号 `T20260001`（密码 123456，MD5 `e10adc...`）。
3. **修复 module 缺口**：补建 module 4-6（目录遍历/命令注入/CSRF 综合实验），并补 `module_course` 关联到 course 5/6/7/8，使每门课都有实验（直接支撑 Phase 1 展示）。
4. 幂等：`training_session`/`generated_question`/`learning_event` 等按前缀 `teacher-demo-*` 先 DELETE 再插；`user`/`teaching_class` 用 `ON DUPLICATE KEY UPDATE`。
5. 事务包裹 + 末尾 SELECT 校验计数（130 学生 / 170 题 / 390 事件）。
6. 前置依赖文档：需先执行 `database/sql/user-service-local-init.sql`、`database/sql/experiment-module-service-local-init.sql`、`database/sql/init_seclab_profile.sql`。

### 验证
- SQL 语法自检（关键字/表名/字段名与现有 schema 对齐）
- 用户在演示库执行后，登录教师端（T20260001）确认：教学班有 130 学生、教学分析有数据、课程库每门课有实验

---

## Phase 3：实验包 zip 上传 + 元数据登记（不自动构建/启动）

**范围：后端新接口 + 新表 + 前端上传 UI。** 按用户确认的"仅上传+元数据登记"档位，**不做** docker build / 动态白名单 / 自动启动。

### DB（experiment-module-service，即 `userservice` 库）
- 新表 `lab_package`：
  - `id` BIGINT PK AUTO_INCREMENT
  - `module_id` INT NULL（关联 `module.module_id`，ON DELETE SET NULL）
  - `lab_key` VARCHAR(64) NOT NULL UNIQUE（如 `stack-overflow`）
  - `image_name` VARCHAR(255) NULL（预期镜像名，如 `stack-overflow-lab-web:latest`）
  - `host_port` INT NULL（预期宿主端口）
  - `flag` VARCHAR(255) NULL
  - `package_path` VARCHAR(512) NOT NULL（zip 落盘相对路径）
  - `uploaded_by` BIGINT NULL
  - `status` VARCHAR(32) DEFAULT 'UPLOADED'（UPLOADED / BUILT / REGISTERED，本期只到 UPLOADED）
  - `created_at` / `updated_at` DATETIME
  - KEY `idx_lab_package_module` (`module_id`)、KEY `idx_lab_package_uploader` (`uploaded_by`)
- 建表脚本落 `database/sql/experiment-module-service-local-init.sql`（追加）+ `shujuku/lab_package.sql`（细粒度）。

### 后端（experiment-module-service，Kotlin）
- 新增 `LabPackageController`：`POST /lab-package/upload`（`MultipartFile` zip + 表单字段 lab_key/image_name/host_port/flag/moduleName/moduleDescription）
  - 鉴权 `catalogAuthService.requireTeacherOrAdmin`
  - 校验：zip 大小/扩展名、lab_key 唯一、基本路径穿越防护
  - 存盘到配置目录 `${lab-package.storage-dir}`（`application.yml` 新增，默认 `./lab-packages/`）
  - 若提供 moduleName → 调 `createModule` 建 module 并关联；否则仅登记 lab_package
  - 返回 `LabPackageDto`
- 新增 `LabPackageService` / `LabPackageDto` / `LabPackageRepository`，沿用现有 `ApiResponse` 包装。
- 网关 `gateway/application.yml` 已通过 StripPrefix 路由 experiment-module-service，无需改路由。

### 前端（CourseLibrary 创建课程流程）
- `src/pages/Teacher/CourseLibrary/index.vue` 创建课程 modal 增加"上传实验包（可选）"区块：
  - `<input type="file" accept=".zip">` + lab_key/镜像名/端口/flag 表单
  - 提交时 `FormData` 调 `uploadLabPackage`（新增 `api.ts` 封装）
- `src/api.ts` 新增 `uploadLabPackage(payload)` → `POST /lab-package/upload`（multipart）

### 验证
- `.\gradlew.bat :experiment-module-service:build` 通过
- 前端上传一个 zip（可用 `stack-overflow-lab` 打包）→ 检查 `lab-packages/` 落盘 + `lab_package` 表记录 + module 已创建
- 在 Phase 1 的课程详情抽屉里能看到新 module

### 明确不做（后续任务）
- 不调 `docker build`，不修改 `LabAllowlist` 硬编码白名单，不自动启动容器。`lab_package.status` 停在 `UPLOADED`，构建/注册/启动留作后续迭代。

---

## 总体风险与说明
- **Phase 1**：纯前端，零接口/DB 改动，可独立交付回滚。
- **Phase 2**：仅改 DB 种子脚本（新增文件），不动表结构；会清空 STUDENT 数据，仅在演示/开发库执行。
- **Phase 3**：新增表 + 新增接口，不改动现有 course/module 表结构与现有接口；上传不触发构建，无 docker build 安全风险。
- 三个阶段互不依赖，可分别提交；按 1→3→2 顺序交付（注：此处的"3"指 Phase 顺序，即 Phase1→Phase2→Phase3）。
