# Real Learning Loop Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Make the SQL experiment, student profile, teacher analysis, knowledge-risk chart, AI analysis, and targeted assignment flow use one coherent set of real local learning records and fail with actionable behavior instead of 500/blank states.

**Architecture:** Keep the existing Vue 3 front end, Kotlin user/experiment services, FastAPI teacher-analysis service, and MySQL schema. Repair compatibility migrations, connect student registration and experiment records to teaching-class scope, read both legacy/static-experiment submissions and generated attempts in teacher analytics, expose real catalog endpoints, and make all knowledge points independently clickable chart sectors whose colors are derived from their own error rates.

**Tech Stack:** Vue 3, TypeScript, Vitest, Chart.js, Kotlin, Spring Boot, JUnit, FastAPI, Python unittest, PyMySQL, MySQL 8, Playwright.

## Global Constraints

- Teacher-visible selected units are called “实验”; internal `courseId` field names remain unchanged.
- All counts, affected students, mistakes, and chart weights come from persisted local records.
- Each knowledge point is a separate chart sector even when multiple points share the same color.
- Risk thresholds remain red `>= 60%`, orange `40%–59%`, yellow `20%–39%`, green `< 20%`.
- Teacher assignment and student assignment APIs derive identity from authentication and enforce class membership.
- Schema declarations in `database/sql/` and `shujuku/` stay consistent with runtime compatibility guards.
- Every behavioral change starts with a failing focused test and finishes with focused plus regression verification.

---

### Task 1: Repair intervention schema compatibility and assignment APIs

**Files:**
- Modify: `seclab-backend/ai-agent-service/test_teacher_intervention_repository.py`
- Modify: `seclab-backend/ai-agent-service/teacher_intervention_repository.py`
- Modify as required: `database/sql/teacher_learning_insight.sql`
- Modify as required: `shujuku/teacher_learning_insight.sql`
- Modify as required: `database/sql/init_seclab_profile.sql`

- [ ] Add a failing test proving runtime schema setup never emits MySQL-incompatible `ADD COLUMN IF NOT EXISTS`.
- [ ] Implement an `information_schema.columns` guard followed by a plain `ALTER TABLE ... ADD COLUMN` only when missing.
- [ ] Run `python -m unittest test_teacher_intervention_repository.py` and verify the teacher/student assignment paths no longer return 500.

### Task 2: Connect new students and experiment submissions to teacher analytics

**Files:**
- Modify: `seclab-backend/user-service/src/test/kotlin/com/seclab/user/service/UserServiceTest.kt`
- Modify: `seclab-backend/user-service/src/main/kotlin/com/seclab/user/service/UserService.kt`
- Modify as required: teaching-class repository/entity files in `seclab-backend/user-service/src/main/kotlin/`
- Modify: `seclab-backend/ai-agent-service/test_teacher_learning_insight_repository.py`
- Modify: `seclab-backend/ai-agent-service/teacher_learning_insight_repository.py`

- [ ] Add failing tests for registration-to-teaching-class membership when the administrative class matches an active teaching class.
- [ ] Add failing repository tests proving `question_submission` records contribute to selected-experiment risk counts and affected-student detail alongside `generated_question_attempt`.
- [ ] Implement idempotent membership creation and a normalized analytics union with deduplication.
- [ ] Run focused Kotlin and Python tests.

### Task 3: Fix real experiment catalog, detail routing, and completion metrics

**Files:**
- Modify/add tests under `seclab-backend/experiment-module-service/src/test/kotlin/`
- Modify experiment catalog controller/service/DTO files under `seclab-backend/experiment-module-service/src/main/kotlin/`
- Modify/add tests under `SecLab-FrontEnd-2/src/pages/User/Modules/`
- Modify: `SecLab-FrontEnd-2/src/pages/User/Modules/index.vue`
- Modify: `SecLab-FrontEnd-2/src/components/ModuleOverView.vue`
- Modify: `SecLab-FrontEnd-2/src/api.ts`
- Modify profile repository tests and `seclab-backend/ai-agent-service/profile_dashboard_repository.py`

- [ ] Add failing tests for module list loading, start navigation, correct service base URL, module detail response, and completion-event aggregation.
- [ ] Replace the hard-coded module catalog with the experiment service response and explicit loading/error states.
- [ ] Add/use a real module detail endpoint and remove the wrong user-service request path.
- [ ] Count distinct completed experiments from persisted completion events.
- [ ] Run focused front-end, Kotlin, and Python tests.

### Task 4: Render every knowledge point as an independent red/orange/yellow/green sector

**Files:**
- Modify: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/__tests__/analysisPresentation.spec.ts`
- Modify: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/__tests__/KnowledgeRiskPieChart.spec.ts`
- Modify: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/analysisPresentation.ts`
- Modify: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/components/KnowledgeRiskPieChart.vue`

- [ ] Add failing tests proving green points are real clickable sectors and two same-color points remain separate sectors.
- [ ] Derive sector weight from persisted response volume while deriving color from each point's error rate.
- [ ] Keep click/keyboard detail access for every sector and remove redundant explanatory copy.
- [ ] Run focused Vitest and Vue type checks.

### Task 5: Make knowledge-point AI analysis resilient and informative

**Files:**
- Modify: `seclab-backend/ai-agent-service/test_teacher_knowledge_analysis_service.py`
- Modify: `seclab-backend/ai-agent-service/teacher_knowledge_analysis_service.py`
- Modify related API error tests and front-end panel tests as required.

- [ ] Add failing tests for bare provider timeout, retry behavior, preserved latest success, and non-empty failure status.
- [ ] Add a bounded retry and a stable timeout error while keeping the latest successful analysis visible.
- [ ] Ensure the UI offers retry without showing a blank/system-error-only panel.
- [ ] Run focused service/API/front-end tests.

### Task 6: Verify the teacher-to-student targeted practice loop

**Files:**
- Modify only where failing evidence identifies a remaining defect.
- Add regression tests beside the affected repository/component.

- [ ] Create or reuse a local teacher, register a new student, and confirm automatic class membership.
- [ ] Submit a deliberate mix of correct and incorrect SQL experiment answers through the student UI/API.
- [ ] Confirm student profile completion, teacher risk sectors/details, AI analysis state, teacher-issued assignment, student assignment visibility, and student submission all update persisted records.

### Task 7: Full verification and handoff

- [ ] Run all affected Python suites.
- [ ] Run affected Gradle service tests.
- [ ] Run front-end Vitest, Vue type check, and production build.
- [ ] Run a real rendered Playwright regression for student and teacher flows and capture evidence.
- [ ] Review `git diff`, schema changes, API/event/log impacts, and document any remaining external-provider limitation.
