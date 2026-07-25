# Student Solve History And Training Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用真实持久化数据提供可展开的课程题与专项训练作答记录，并让推荐训练题生成在固定时间内成功或明确失败。

**Architecture:** 后端画像仓储分别读取课程题快照、生成题作答和 Flag 记录，归一化为同一 DTO；前端使用独立的 `SolveHistoryPanel` 组件完成筛选与展开。训练题服务并发生成各题，并在服务层与 HTTP 客户端层设置一致的超时边界。

**Tech Stack:** Python 3、FastAPI、PyMySQL、asyncio、Vue 3、TypeScript、Vitest、Vite。

## Global Constraints

- 只读取和展示真实数据库记录，不增加 mock、fallback 或种子数据。
- 历史记录缺失题干时必须明确显示缺失，不得根据题号推测内容。
- 推荐训练题整组服务端超时 45 秒，前端超时 50 秒。
- 课程题、专项训练题和 Flag 的来源必须在响应中可区分。

---

### Task 1: 完整作答记录数据契约

**Files:**
- Modify: `seclab-backend/ai-agent-service/profile_dashboard_repository.py`
- Test: `seclab-backend/ai-agent-service/test_profile_dashboard_repository.py`

**Interfaces:**
- Consumes: `question_submission.question_snapshot_json`、`generated_question_attempt`、`generated_question`
- Produces: `solveRecords: list[dict]`，每项包含详情字段与 `contentAvailable`

- [ ] **Step 1: Write the failing tests**

创建游标桩，分别返回一条带快照的课程题和一条错误的生成题。断言课程题标题来自真实题干、选项和答案被解析；断言生成题错题被包含并带有题干、学生答案、标准答案和解析；断言缺失快照时 `contentAvailable` 为 `False`。

- [ ] **Step 2: Run tests to verify RED**

Run: `python -m unittest test_profile_dashboard_repository.py -v`

Expected: FAIL，因为现有 DTO 只有 `experiment/module/time/result/score`，且不查询生成题作答。

- [ ] **Step 3: Implement minimal normalization**

增加安全 JSON 解析与答案格式化函数；扩展 `_question_records` 查询快照、答案、题型和耗时；新增 `_generated_question_records`；让 `_solve_records` 合并三种真实来源并返回统一字段。

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python -m unittest test_profile_dashboard_repository.py -v`

Expected: PASS。

### Task 2: 新提交保存题目快照

**Files:**
- Modify: `seclab-backend/ai-agent-service/question_repository.py`
- Modify: `database/sql/init_seclab_profile.sql`
- Test: `seclab-backend/ai-agent-service/test_question_repository_snapshot.py`

**Interfaces:**
- Consumes: `save_question_submission(data)` 中的 `question_snapshot` 或 `question`
- Produces: `question_submission.question_snapshot_json`

- [ ] **Step 1: Write the failing test**

断言保存参数包含真实题目快照 JSON，并且 schema 升级会在缺少字段时添加 `question_snapshot_json`。

- [ ] **Step 2: Run tests to verify RED**

Run: `python -m unittest test_question_repository_snapshot.py -v`

Expected: FAIL，因为当前插入 SQL 不包含快照字段。

- [ ] **Step 3: Implement schema and persistence**

在建表 SQL、兼容升级函数和插入 SQL中加入可空 JSON 字段；同步主初始化 SQL。

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python -m unittest test_question_repository_snapshot.py -v`

Expected: PASS。

### Task 3: 训练题生成受控超时

**Files:**
- Modify: `seclab-backend/ai-agent-service/training_session_service.py`
- Test: `seclab-backend/ai-agent-service/test_training_session_service.py`

**Interfaces:**
- Consumes: `generate_question_with_llm(...)`
- Produces: `generate_training_question_set_batch(data)`；超时抛出 `TrainingSessionServiceError(code="QUESTION_SET_GENERATION_TIMEOUT", status_code=504)`

- [ ] **Step 1: Write the failing tests**

用可控异步生成器证明多个题位并发开始；模拟永不完成的生成器，断言整组超时转换为稳定错误码；断言少量失败但至少 4 道合格题时返回部分题组。

- [ ] **Step 2: Run tests to verify RED**

Run: `python -m unittest test_training_session_service.py -v`

Expected: FAIL，因为当前实现逐题串行且没有整组超时。

- [ ] **Step 3: Implement bounded concurrent generation**

使用 `asyncio.gather` 启动目标题位任务，在每个任务内部保留两次质量重试；外层 `asyncio.wait_for(..., 45)`；超时取消任务并抛出 504 错误。

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python -m unittest test_training_session_service.py -v`

Expected: PASS。

### Task 4: 可展开的解题记录组件

**Files:**
- Create: `SecLab-FrontEnd-2/src/pages/User/Profile/SolveHistoryPanel.vue`
- Create: `SecLab-FrontEnd-2/src/pages/User/Profile/SolveHistoryPanel.spec.ts`
- Modify: `SecLab-FrontEnd-2/src/api.ts`
- Modify: `SecLab-FrontEnd-2/src/pages/User/Profile/index.vue`

**Interfaces:**
- Consumes: `ProfileDashboardSolveRecord[]`
- Produces: 全部/错题/正确筛选、可展开详情和真实空状态

- [ ] **Step 1: Write the failing component tests**

提供一条正确课程题、一条错误专项训练题与一条缺快照历史记录。断言真实题干和错题数量可见，详情包含本人答案、正确答案、解析，缺失快照提示诚实呈现。

- [ ] **Step 2: Run tests to verify RED**

Run: `npm test -- SolveHistoryPanel.spec.ts`

Expected: FAIL，因为组件尚不存在。

- [ ] **Step 3: Implement the component and DTO**

扩展 TypeScript DTO；组件使用按钮筛选和原生 `details/summary` 展开内容；在画像页替换静态表格。

- [ ] **Step 4: Run tests to verify GREEN**

Run: `npm test -- SolveHistoryPanel.spec.ts`

Expected: PASS。

### Task 5: 训练生成进度与前端超时

**Files:**
- Modify: `SecLab-FrontEnd-2/src/api.ts`
- Modify: `SecLab-FrontEnd-2/src/pages/User/Profile/index.vue`
- Test: `SecLab-FrontEnd-2/src/pages/User/Profile/trainingReadiness.spec.ts`

**Interfaces:**
- Consumes: `generateTrainingQuestionSet(payload, timeoutMs?)`
- Produces: 已等待秒数、预计时长说明、超时错误文案和可重试按钮

- [ ] **Step 1: Write the failing presentation test**

断言 0–29 秒显示“正在生成真实训练题”，30 秒后显示“模型仍在准备”，超时错误码显示“准备超时，请重试”。

- [ ] **Step 2: Run tests to verify RED**

Run: `npm test -- trainingReadiness.spec.ts`

Expected: FAIL，因为当前只有固定加载文字。

- [ ] **Step 3: Implement timed state**

记录开始时间，每秒更新等待秒数；API 使用 50 秒 Axios 超时；在 finally 中清理定时器；补充 `QUESTION_SET_GENERATION_TIMEOUT` 和 Axios 超时提示。

- [ ] **Step 4: Run tests to verify GREEN**

Run: `npm test -- trainingReadiness.spec.ts`

Expected: PASS。

### Task 6: 集成与真实账号验收

**Files:**
- Verify only

**Interfaces:**
- Consumes: 运行中的 AI 服务、用户服务和 Vite 应用
- Produces: 姜理想账号可直接查看的页面

- [ ] **Step 1: Run backend suite**

Run: `python -m unittest discover -p "test_*.py" -v`

Expected: 全部通过。

- [ ] **Step 2: Run frontend suite and build**

Run: `npm test`

Run: `npm run vue-tsc`

Run: `npm run build`

Expected: 全部通过。

- [ ] **Step 3: Restart AI service and verify live API**

请求 `/api/profile/295/dashboard`，断言返回两条真实 SQL 注入题、`contentAvailable=true`、错题数为 0。

- [ ] **Step 4: Browser acceptance**

打开 `http://127.0.0.1:5174/#/user/profile`，进入姜理想账号画像页，点击一条记录的“查看详情”，验证题干、选项、本人答案和正确答案可见；检查控制台无相关错误并保存验收截图。
