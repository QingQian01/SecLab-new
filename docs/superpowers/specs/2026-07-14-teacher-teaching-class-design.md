# 教师端教学班真实化改造设计

## 目标

将当前以测试班级、抽象画像分和自动 AI 套话为主的教师端，改造成符合 SecLab 实验教学流程的教师工作台。

教师自主创建按学期使用的教学班，批量导入学生，为教学班选择多门可跨学期复用的课程，并查看学生端实时产生的训练题、作答和实验数据。AI 只作为辅助亮点：教师手动点击后才分析当前班级数据，系统只保留最新分析结果。

## 已确认的业务规则

1. 系统没有单独管理员，教师自行创建和管理教学班。
2. 教学班按学年、学期使用；课程是长期资源，可被不同学期、不同教学班重复选择。
3. 一个教学班可以关联多门课程，教师大约每两周讲授一门课程。
4. 教师可以选择已有课程，也可以在课程资源页单独创建新课程。
5. 教师通过 Excel 导入学生名单，最少包含学号、姓名、行政班。
6. 不存在的学生账号由系统自动创建，账号为学号，初始密码为 `123456`；首次登录不强制修改。
7. 已存在账号只加入教学班，不覆盖密码和个人资料；重复导入不得重复创建账号或成员关系。
8. 学生端 AI 生成题及作答结果直接存入现有训练数据，教师端实时查询同一份数据，不建立复制或推送任务。
9. 教师可以把有代表性的训练题标记为“典型题”，该标记不影响学生端题目状态。
10. 班级 AI 分析只在教师点击“开始分析”后运行。系统保存当前最新分析，再次分析时更新，不保留历史快照。
11. AI 失败时不在前端拼接规则套话；页面保留上一次成功结果并给出明确错误。

## 信息架构

教师端主导航调整为：

- 教学工作台
- 教学班
- 课程资源
- 个性化训练记录

学生管理进入具体教学班，不再作为全局入口；模块和实验管理进入课程详情，不再与课程并列展示。

### 教学工作台

工作台展示当前学期的真实业务状态：教学班数量、学生人数、课程安排进度、近期训练情况、实验异常和最新班级 AI 分析。快捷操作包含创建教学班、导入学生和安排课程。

不再把“画像均分”作为核心指标，也不再显示“高分学生”排行榜。页面优先回答教师实际问题：当前讲到哪里、哪些学生尚未开始、哪些实验反复失败、学生最近生成了哪些训练题。

### 教学班列表与详情

教学班卡片显示教学班名称、学年学期、学生人数、已选课程数、当前课程和最近学习活动。测试班、演示班和无学生脏记录不进入正式数据集。

教学班详情包含：

- 基本信息与归档状态
- 学生名单导入、导入预检和成员列表
- 已选课程及教学顺序
- 当前课程与计划起止日期
- 学生实验与训练概览
- 个性化训练题聚合
- 班级 AI 分析入口与最新结果

### 课程资源

课程是独立、可复用的资源。教师可新建、编辑和选择课程；课程下维护模块、实验及必要教学说明。教学班只引用课程，不复制课程主体数据，也不携带往届学生学习记录。

### 个性化训练记录

该页面不是审核流程。教师可以按教学班、课程、知识点、学生、答题结果和时间筛选学生端已生成的训练题，并查看生成原因、题干、答案、解析、学生作答和得分。

教师可以标记或取消“典型题”。班级聚合视图统计各知识点涉及学生数、题目数、作答数和错误情况，并从现有题目中展示代表题，不重新生成题目。

## 数据模型

保留现有用户、课程、模块、实验和训练相关表，新增以下表。

### 现有 `user` 表角色字段

现有系统通过 `is_admin` 或旧班级 `admin_id` 反推教师身份，无法支持“教师在尚未创建教学班时自主开班”。因此在 `user` 表增加 `user_role` 字段，取值为 `STUDENT`、`TEACHER` 或 `ADMIN`，默认 `STUDENT`。本项目默认数据只创建教师和学生，不要求存在管理员账号；旧 `is_admin` 字段仅保留兼容读取，后续鉴权统一以 `user_role` 为准。

导入名单自动创建的账号固定写入 `STUDENT`，教师种子账号明确写入 `TEACHER`。`user_role` 建普通索引，所有教师接口必须校验当前账号为启用状态且角色为 `TEACHER`。

### `teaching_class`

用途：保存教师按学期创建的教学班。

关键字段：

- `teaching_class_id`：主键
- `class_name`：教师填写的教学班名称，如“网络安全 232 班”
- `academic_year`：学年，如 `2026-2027`
- `semester`：学期枚举，建议 `1`、`2`
- `teacher_id`：创建并负责该教学班的教师用户 ID
- `start_date`、`end_date`：教学周期
- `status`：`ACTIVE` 或 `ARCHIVED`
- `created_at`、`updated_at`

索引与约束：按 `teacher_id + status`、`academic_year + semester` 建索引；同一教师、同一学年学期下教学班名称唯一。

### `teaching_class_student`

用途：保存学生与教学班的多对多成员关系。

关键字段：

- `teaching_class_id`
- `student_id`
- `joined_at`
- `source`：本期固定为 `EXCEL_IMPORT`

联合主键或唯一索引为 `teaching_class_id + student_id`，保证重复导入幂等。

### `teaching_class_course`

用途：保存教学班选择的可复用课程及教学安排。

关键字段：

- `teaching_class_course_id`：主键
- `teaching_class_id`
- `course_id`
- `teaching_order`：教学顺序
- `planned_start_date`、`planned_end_date`
- `created_at`、`updated_at`

同一教学班和课程唯一；按 `teaching_class_id + teaching_order` 建索引。

### `teaching_class_import_batch`

用途：保存 Excel 导入预检结果，保证“预检后确认”和重复确认幂等。

关键字段：

- `import_batch_id`：UUID 主键
- `teaching_class_id`、`teacher_id`
- `file_sha256`：上传文件摘要
- `preview_json`：新增账号、已有账号、重复行和错误行
- `status`：`PREVIEWED`、`CONFIRMED` 或 `EXPIRED`
- `expires_at`、`created_at`、`confirmed_at`

同一批次只允许确认一次；过期批次返回 409，教师不能确认其他教师创建的批次。

### `teacher_typical_question`

用途：保存教师对学生端 AI 生成题的个人典型题标记。

关键字段：

- `teacher_id`
- `generated_question_id`
- `created_at`

联合唯一索引为 `teacher_id + generated_question_id`。标记只属于教师端，不修改生成题审核状态或学生端可见性。

### `teacher_class_analysis`

用途：保存每个教学班当前最新一次成功的 AI 分析。

关键字段：

- `teaching_class_id`：主键或唯一关联
- `requested_by`：触发分析的教师 ID
- `data_cutoff_at`：本次分析读取数据的截止时间
- `analysis_json`：共性问题、代表题、证据和教学建议
- `source_stats_json`：可追溯的统计摘要
- `analysis_status`：`IDLE`、`RUNNING` 或 `READY`
- `last_attempt_at`、`last_error_message`
- `generated_at`、`updated_at`

开始分析时原子地切换为 `RUNNING`，用于拒绝重复请求。再次成功分析时更新该教学班记录；失败时恢复可重试状态并保留已有成功结果，同时记录对教师可读的最近错误。

## 接口设计

所有教师接口从登录令牌获取教师身份，不接受前端传入任意 `teacherId` 绕过范围。

### 教学班

- `GET /api/teacher/teaching-classes`
- `POST /api/teacher/teaching-classes`
- `GET /api/teacher/teaching-classes/{id}`
- `PUT /api/teacher/teaching-classes/{id}`
- `POST /api/teacher/teaching-classes/{id}/archive`

只有创建教师可访问。请求校验教学班名称、学年学期和日期范围；不存在返回 404，越权返回 403，名称冲突返回 409。

### 学生导入

- `POST /api/teacher/teaching-classes/{id}/students/import/preview`
- `POST /api/teacher/teaching-classes/{id}/students/import/confirm`
- `GET /api/teacher/teaching-classes/{id}/students`
- `DELETE /api/teacher/teaching-classes/{id}/students/{studentId}`

预检结果返回新增账号、已有账号、重复行和错误行。确认接口使用一次性导入批次 ID，事务内创建账号并加入教学班；重复确认保持幂等。

### 教学班课程

- `GET /api/teacher/teaching-classes/{id}/courses`
- `PUT /api/teacher/teaching-classes/{id}/courses`

更新接口一次提交课程顺序和计划日期，验证课程存在、无重复、日期在教学班周期内。

### 训练记录与典型题

- `GET /api/teacher/generated-questions`
- `GET /api/teacher/generated-questions/{id}`
- `PUT /api/teacher/generated-questions/{id}/typical`
- `DELETE /api/teacher/generated-questions/{id}/typical`
- `GET /api/teacher/teaching-classes/{id}/generated-question-summary`

列表和汇总只读取当前教师教学班成员产生的数据。移除现有审核状态筛选和审核操作，增加教学班、课程、知识点、学生、答题结果及典型题筛选。

### 班级 AI 分析

- `GET /api/teacher/teaching-classes/{id}/ai-analysis`
- `POST /api/teacher/teaching-classes/{id}/ai-analysis`

`GET` 返回当前最新结果或空状态。`POST` 在教师点击后读取当前数据并生成分析；返回 409 表示已有分析正在执行，422 表示数据不足，503 表示 AI 服务暂不可用。成功结果包含数据截止时间、统计证据、共性问题、代表题 ID 和教学建议。

## AI 分析边界

AI 输入仅使用当前教师教学班内的聚合统计、脱敏学生标识、训练题与作答摘要、实验事件摘要。建议必须引用可追溯的数据或题目 ID。

AI 不负责自动给学生发题、不替代教师评分、不自动修改课程安排、不自动执行班级分析，也不在失败时输出固定套话。

## 数据清理与真实演示数据

数据清理单独执行，保留课程、模块、实验资源和 `user_role = 'TEACHER'` 的教师账号，清除污染的学生账号、旧班级、画像快照、训练记录、生成题作答及学习事件。清理脚本必须先列出影响数量，显式事务执行，并提供回滚或备份说明。

随后创建少量结构一致的演示数据：一个教师、两个本学期教学班、每班若干学生、多门复用课程，以及能够支撑训练题汇总和班级分析的实验事件、生成题与作答记录。测试或权限验证数据放入独立测试脚本，不进入默认初始化数据。

## 错误处理与空状态

- 无教学班：引导创建教学班。
- 无学生：引导下载模板并导入名单。
- 无课程：引导先到课程资源创建课程。
- 无训练记录：明确说明尚无学生训练数据。
- AI 数据不足：显示所缺数据，不生成建议。
- AI 请求失败：保留已有成功结果并允许重试。
- 导入部分错误：预检阶段阻止确认，提供逐行错误信息。
- 所有越权访问由后端拒绝，前端只显示当前教师可用入口。

## 非目标

本期不实现管理员端、正式教务排课、教室与课次管理、消息队列推送、定时 AI 分析、分析历史快照、学生首次登录强制改密，以及将典型题重新下发给学生。

## 验收标准

1. 教师可以创建本学期教学班并只能看到自己的教学班。
2. 教师可以预检并确认 Excel 名单，自动创建学生账号，重复导入不产生重复数据。
3. 一个教学班可以按顺序关联多门已有课程，课程可被多个教学班复用。
4. 教师可以创建新课程，并在教学班中选用。
5. 学生端生成题和作答后，教师端刷新即可看到相同真实记录。
6. 教师可以标记典型题，且不影响学生端题目状态。
7. 教师点击后才启动班级 AI 分析；结果包含数据依据，只保留最新成功结果。
8. 默认数据中不出现验收用户、权限测试班、演示班和错误班名。
9. 页面具备加载、空数据、错误和越权状态。
10. 前端类型检查、相关后端测试、SQL 检查和最小服务构建通过。
