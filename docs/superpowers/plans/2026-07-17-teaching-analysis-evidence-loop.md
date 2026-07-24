# Teaching Analysis Evidence Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an evidence-traceable cybersecurity teaching analysis workflow with working Dify analysis, complete student profiles, risk heatmaps, experiment replay, and teacher intervention follow-up.

**Architecture:** Extend the existing FastAPI AI agent service with focused read-model and intervention repositories. Reuse the existing profile and training pipelines; add only intervention persistence. Split the Vue teaching analysis page into small components and keep all secrets in an ignored runtime `.env`.

**Tech Stack:** Python 3/FastAPI/PyMySQL/unittest, MySQL 9, Vue 3/TypeScript/Vite/Vitest, Dify Chat API.

## Global Constraints

- Do not commit `.env`, Dify keys, database passwords, tokens, or raw container output.
- Every teacher endpoint must validate teacher ownership of the class and student membership.
- Every new database object must be present in both the main initialization SQL and a focused `shujuku` migration.
- Use TDD: add and run the failing test before each production change.
- Preserve previous successful AI analysis when a refresh fails.
- Keep the current teacher visual language and scrolling behavior.

---

### Task 1: Runtime AI Configuration and Error Fidelity

**Files:**
- Runtime create (ignored): `seclab-backend/ai-agent-service/.env`
- Modify: `seclab-backend/ai-agent-service/config.py`
- Modify: `seclab-backend/ai-agent-service/main.py`
- Modify: `SecLab-FrontEnd-2/src/api.ts`
- Test: `seclab-backend/ai-agent-service/test_teacher_api_errors.py`

**Interfaces:**
- Produces `GET /health/ai-analysis` returning `{configured, providerReachable, message}` without secrets.
- Preserves server-provided `detail` for status 503 and 504 in `getApiErrorMessage`.

- [ ] Add failing backend tests for configured, missing, and unreachable Dify states.
- [ ] Run `python -m unittest test_teacher_api_errors.py -v` and confirm the new tests fail because the health route is missing.
- [ ] Copy only Dify runtime values from `D:/SecLab/seclab-backend/ai-agent-service/.env` into the ignored current `.env`; keep current MySQL/service values from `.env.example`.
- [ ] Implement the non-secret AI configuration health response and distinct provider errors.
- [ ] Add a frontend error-message unit test that expects the 503 response detail.
- [ ] Run the focused Python test, frontend unit test, and a live authenticated Dify smoke request.

### Task 2: Class Profile Rebuild and Test Evidence Backfill

**Files:**
- Create: `seclab-backend/ai-agent-service/teacher_profile_service.py`
- Modify: `seclab-backend/ai-agent-service/main.py`
- Create: `seclab-backend/ai-agent-service/test_teacher_profile_service.py`
- Create: `shujuku/seed-teacher-learning-evidence.sql`

**Interfaces:**
- Produces `rebuild_teaching_class_profiles(class_id: int, teacher_id: int) -> dict`.
- Produces `POST /api/teacher/teaching-classes/{class_id}/profiles/rebuild` with `{studentCount, rebuiltCount, failedCount, failures}`.

- [ ] Write failing tests proving only owned-class members are rebuilt and one student failure does not abort the batch.
- [ ] Run the test and confirm failure due to the missing service.
- [ ] Implement the batch service around `rebuild_student_profile`.
- [ ] Add the authenticated route and error mapping.
- [ ] Add idempotent showcase evidence for the 32 imported students, including command failures, hint/AI interactions, retries, and successes with `source='showcase-seed'`.
- [ ] Apply the seed, rebuild all 32 profiles, and verify a membership join returns 32 matching profiles.

### Task 3: Capability Evidence and Learning Replay Read Models

**Files:**
- Create: `seclab-backend/ai-agent-service/teacher_learning_insight_repository.py`
- Create: `seclab-backend/ai-agent-service/test_teacher_learning_insight_repository.py`
- Modify: `seclab-backend/ai-agent-service/main.py`

**Interfaces:**
- `get_capability_evidence(teacher_id, class_id, student_id) -> dict`
- `get_learning_replay(teacher_id, class_id, student_id, limit=100) -> dict`
- Evidence keys: `knowledge_mastery`, `troubleshooting`, `autonomy`, `ai_collaboration`, `engagement`.
- Timeline event kinds: `LAB_START`, `COMMAND`, `ERROR`, `HINT`, `AI`, `ATTEMPT`, `SUCCESS`.

- [ ] Write failing tests for chronological ordering, retry-outcome detection, evidence dimension mapping, and secret redaction.
- [ ] Run the focused test and confirm failures occur because the repository is missing.
- [ ] Implement normalized evidence queries over existing event, command, error, completion, and attempt tables.
- [ ] Add teacher-scoped GET routes and validate the JSON contract.
- [ ] Run repository and API tests.

### Task 4: Knowledge Risk Map

**Files:**
- Modify: `seclab-backend/ai-agent-service/teacher_learning_insight_repository.py`
- Modify: `seclab-backend/ai-agent-service/test_teacher_learning_insight_repository.py`
- Modify: `seclab-backend/ai-agent-service/main.py`

**Interfaces:**
- `get_class_risk_map(teacher_id, class_id) -> dict`
- Each item returns course/order, knowledge point, attempted/incorrect students, incorrect rate, risk level, affected students, and representative questions.

- [ ] Add failing tests for high/medium/low thresholds and low-sample protection.
- [ ] Implement risk aggregation using teaching schedule plus generated-question attempts.
- [ ] Add the class-scoped route and run tests.

### Task 5: Intervention Persistence and Teacher APIs

**Files:**
- Modify: `database/sql/init_seclab_profile.sql`
- Create: `shujuku/teacher_intervention.sql`
- Create: `seclab-backend/ai-agent-service/teacher_intervention_repository.py`
- Create: `seclab-backend/ai-agent-service/test_teacher_intervention_repository.py`
- Modify: `seclab-backend/ai-agent-service/main.py`

**Interfaces:**
- `create_intervention(...)`, `list_interventions(...)`, `get_intervention(...)`, `update_intervention_status(...)`, `refresh_intervention_metrics(...)`.
- Supported types: `FOCUS_GROUP`, `TARGETED_PRACTICE`, `LESSON_EXAMPLE`.

- [ ] Add the three idempotent table definitions and indexes to both SQL locations.
- [ ] Write failing repository tests for ownership, membership, idempotent question links, baseline capture, and delta calculation.
- [ ] Implement repository methods in transactions.
- [ ] Add GET/POST/PATCH/refresh routes with Pydantic validation.
- [ ] Apply SQL and run repository/API tests.

### Task 6: Student Assignment Consumption

**Files:**
- Modify: `seclab-backend/ai-agent-service/teacher_intervention_repository.py`
- Modify: `seclab-backend/ai-agent-service/training_session_service.py`
- Modify: `seclab-backend/ai-agent-service/main.py`
- Modify: `seclab-backend/ai-agent-service/test_teacher_intervention_repository.py`

**Interfaces:**
- `GET /api/students/{student_id}/teacher-assignments`
- `POST /api/students/{student_id}/teacher-assignments/{intervention_id}/start`
- Starting creates/reuses a training session with `source_type='teacher_assignment'` and `interventionId` in context.

- [ ] Write failing tests that reject another student, prevent duplicate starts, and preserve intervention context.
- [ ] Implement student-scoped assignment listing and start behavior by reusing the current question-set generator.
- [ ] Mark completion from existing submissions and expose completion to teacher metrics.
- [ ] Run training and intervention tests.

### Task 7: Frontend API Contracts and Component Test Harness

**Files:**
- Modify: `SecLab-FrontEnd-2/package.json`
- Modify: `SecLab-FrontEnd-2/package-lock.json`
- Modify: `SecLab-FrontEnd-2/src/api.ts`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/analysisPresentation.ts`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/__tests__/analysisPresentation.spec.ts`

**Interfaces:**
- Typed API functions for profile rebuild, evidence, replay, risk map, interventions, and student assignments.
- Pure helpers for risk colors, event labels, score states, and error copy.

- [ ] Add Vitest and the `test:unit` script.
- [ ] Write failing tests for presentation helpers and the 503 detail behavior.
- [ ] Implement types, API functions, and helpers.
- [ ] Run `npm run test:unit` and `npm run vue-tsc`.

### Task 8: Teacher Analysis UI

**Files:**
- Modify: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/index.vue`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/components/CapabilityEvidencePanel.vue`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/components/LearningReplayTimeline.vue`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/components/KnowledgeRiskHeatmap.vue`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/components/TeachingActionPanel.vue`

**Interfaces:**
- Score cards emit `select-dimension`.
- Risk cells emit `select-risk` and `create-action`.
- Action panel emits `created`, `status-changed`, and `refreshed`.

- [ ] Add the AI configuration state and one-click class profile refresh.
- [ ] Display overall plus all five dimensions, including AI collaboration.
- [ ] Add expandable capability evidence and replay with loading/empty/error states.
- [ ] Add risk heatmap with affected-student and representative-question details.
- [ ] Add intervention creation and follow-up comparison without changing the page’s established visual language.
- [ ] Run unit tests, type checking, and production build.

### Task 9: Student Assignment UI

**Files:**
- Create: `SecLab-FrontEnd-2/src/pages/User/Profile/TeacherAssignments.vue`
- Modify: `SecLab-FrontEnd-2/src/pages/User/Profile/index.vue`
- Modify: `SecLab-FrontEnd-2/src/api.ts`

**Interfaces:**
- Component loads the current student’s teacher assignments and emits `started(trainingSessionId)`.

- [ ] Add the assignment section to the existing profile page.
- [ ] Start/continue assigned training through the existing training view.
- [ ] Show due date, teacher reason, status, and completion.
- [ ] Run frontend tests, type checking, and build.

### Task 10: End-to-End Verification and Repository Sync

**Files:**
- Modify only files required by defects discovered during verification.

- [ ] Run all AI service unittests.
- [ ] Run `npm run test:unit`, `npm run vue-tsc`, and `npm run build`.
- [ ] Restart the AI service with the ignored `.env` and verify health.
- [ ] Authenticate as teacher and verify 32 profile rebuilds, Dify analysis, evidence, replay, risk map, and intervention APIs.
- [ ] Authenticate as a seeded student and verify assignment start/completion.
- [ ] Verify no secret is tracked with `git status`, `git check-ignore`, and a staged-content scan.
- [ ] Commit in focused units, push `main`, and report commit hashes plus remaining runtime dependencies.

