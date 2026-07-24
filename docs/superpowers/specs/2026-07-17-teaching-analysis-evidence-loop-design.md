# 教学分析证据闭环设计

## 目标

把当前“汇总数字 + 手动 AI 评语”升级为网络安全教学专用的证据分析闭环：教师能从能力分数追溯到实验、命令、错误、求助与重试证据；能查看班级知识点风险；能创建教学干预并向学生下发专项训练；系统在到期后自动计算干预前后变化。

## 设计选择

采用现有 `ai-agent-service` 内增量扩展方案，不新增微服务。读取型洞察从现有事件表即时聚合，教学干预使用独立关系表持久化。前端保留当前教学分析页面结构，并把大块功能拆成独立 Vue 组件。

没有采用独立分析微服务或数据仓库：当前班级规模和数据量不需要额外基础设施，拆服务会增加部署、鉴权和数据一致性成本。

## 数据链路

1. `learning_event`、`container_command_event`、`error_event`、`challenge_completion_event`、`generated_question_attempt` 保存原始学习证据。
2. `student_profile_snapshot` 保存规则模型计算的五维画像：知识掌握、排障能力、自主探索、AI 协同、学习投入。
3. 教师端只读取自己拥有的教学班。证据接口先校验教师、教学班和学生三者关系。
4. 点击 AI 分析时，将画像、近期作答和个人学习信号发送到 Dify；成功结果保存到 `teacher_student_analysis` 或 `teacher_class_analysis`。
5. 教学干预创建时冻结基线指标；读取干预详情时按当前数据计算最新指标和变化量。达到 `due_at` 后显示“可评估”，不依赖额外定时任务。

## 功能设计

### 画像补齐与 AI 配置

- 从已有 SecLab 本地配置安全复制 Dify URL 和密钥到当前服务的 git 忽略 `.env`。
- 新增教师班级画像重建接口，为教学班成员逐个调用现有规则画像构建器。
- 当前导入的 32 名测试学生补充可追溯的实验命令、错误、求助和成功重试数据，再使用真实评分逻辑生成画像，不直接写死分数。
- 前端保留服务端 503 的业务错误文案，不再把 AI 不可用误报成“数据加载失败”。

### 能力证据

每个维度返回分数、计算说明和证据条目。证据条目包含发生时间、实验上下文、结果、脱敏命令、错误类别、提示次数和后续是否成功。命令中的 token、password、cookie 等敏感值必须脱敏。

### 安全实验学习回放

把不同事件表统一成时间线：实验开始、命令执行、错误、提示/AI 求助、题目作答、Flag 或实验完成。按 `lab_session_id` 优先关联；测试数据缺少会话时，使用学生、模块、任务和时间窗口关联。

### 知识点风险热力图

按教学安排和知识点聚合生成题、作答、错误人数和错误率，风险等级为高、中、低。展开项返回受影响学生和代表性题目。高风险判定优先看错误人数，其次看错误率，避免少量样本造成夸大。

### 教学行动闭环

- `FOCUS_GROUP`：创建重点辅导小组。
- `TARGETED_PRACTICE`：为学生下发知识点专项训练。
- `LESSON_EXAMPLE`：将代表性题目标记为下节课案例。
- 学生画像页显示老师布置的训练；开始后复用现有训练题生成和作答链路，并把 `intervention_id` 写入训练上下文。
- 干预详情展示基线、当前值、变化量、完成率和到期状态。

## 数据库

新增三张表：

- `teacher_intervention`：干预主记录，主键 `intervention_id`；关键索引 `(teaching_class_id, status, due_at)`。
- `teacher_intervention_student`：干预学生和基线/随访快照，联合主键 `(intervention_id, student_id)`。
- `teacher_intervention_question`：干预关联题目及用途，联合主键 `(intervention_id, generated_question_id, usage_type)`。

所有表在 `database/sql/init_seclab_profile.sql` 和 `shujuku/teacher_intervention.sql` 同步维护。

## API

- `POST /api/teacher/teaching-classes/{class_id}/profiles/rebuild`
- `GET /api/teacher/teaching-classes/{class_id}/students/{student_id}/capability-evidence`
- `GET /api/teacher/teaching-classes/{class_id}/students/{student_id}/learning-replay`
- `GET /api/teacher/teaching-classes/{class_id}/risk-map`
- `GET|POST /api/teacher/teaching-classes/{class_id}/interventions`
- `GET|PATCH /api/teacher/teaching-classes/{class_id}/interventions/{intervention_id}`
- `POST /api/teacher/teaching-classes/{class_id}/interventions/{intervention_id}/refresh`
- `GET /api/students/{student_id}/teacher-assignments`
- `POST /api/students/{student_id}/teacher-assignments/{intervention_id}/start`

## 页面结构

班级分析增加知识点风险热力图和教学行动区。学生分析增加六项指标（综合 + 五维）、能力证据抽屉、安全实验回放时间线和“创建教学行动”入口。学生画像页增加“老师布置的专项训练”。

## 错误与安全

- Dify 未配置、超时、上游异常分别返回可识别的 503/504 文案。
- 已有成功分析在刷新失败时继续保留。
- 所有教师接口执行教学班所有权校验，所有学生接口校验本人身份。
- 命令和错误原文在响应前截断、脱敏；不返回完整容器输出。
- `.env`、密钥和令牌不提交仓库。

## 验收标准

- 当前网络安全232班的 32 名学生均有最新画像，王子睿页面不再显示横线。
- Dify 配置有效时可成功生成学生分析；不可用时页面明确显示 AI 服务状态。
- 点击任一能力分数可以看到至少一条可追溯证据。
- 王子睿能看到包含失败、求助、修改和成功的实验回放。
- 班级风险图至少展示 SQL 注入、XSS、文件上传等知识点，并能展开学生和题目。
- 教师能创建教学行动，学生能看到并启动专项训练，教师能看到完成率和前后变化。

