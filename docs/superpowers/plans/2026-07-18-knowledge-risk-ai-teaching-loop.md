# Knowledge Risk AI Teaching Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the teacher knowledge-risk heatmap with an experiment-scoped, independently clickable risk pie chart and complete the evidence → AI analysis → teacher review → targeted assignment → student attempt → outcome feedback loop.

**Architecture:** Keep the existing Vue teacher analysis page, FastAPI AI service, generated-question attempt model, and teacher-intervention/student-assignment flow. Add pure presentation helpers and focused Vue components, extend the knowledge-risk query with experiment-scoped details, persist the latest knowledge analysis and independently reviewed exercise drafts, and snapshot approved exercises into existing targeted interventions so students answer exactly what teachers approved.

**Tech Stack:** Vue 3, TypeScript, Vite, Vitest, Chart.js 4, FastAPI, Python unittest, PyMySQL, MySQL 8.

## Global Constraints

- Teacher-visible selected units are called “实验”; existing backend `courseId`/`courseName` fields are not renamed.
- Pie size is `knowledge point incorrect count / all incorrect counts in the selected experiment`.
- Color is based on the point's own incorrect rate: red `>= 60%`, orange `40%–59%`, yellow `20%–39%`, green `< 20%`.
- Every knowledge point is a separate slice even when adjacent points share a color; same-color points are never merged.
- Zero-error points appear as individually clickable green “掌握良好” items rather than fake non-zero slices.
- AI analysis is manually triggered, source-grounded, preserves the latest success on refresh failure, and never returns a fabricated fallback.
- AI exercises are independently editable and reviewable; only `APPROVED` exercises can be issued.
- Issued exercise content is an immutable snapshot; student start must not regenerate different AI questions.
- All teacher APIs derive teacher identity from authentication and enforce class ownership; students see only their own assignments.
- Database declarations must be updated in both `database/sql/` and `shujuku/`; runtime schema guards are compatibility only.

---

### Task 1: Lock the risk-pie calculation and experiment copy with frontend tests

**Files:**
- Modify: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/__tests__/analysisPresentation.spec.ts`
- Modify: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/analysisPresentation.ts`
- Modify: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/components/CourseAnalysisPanel.vue`
- Modify: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/components/CourseQuestionRecords.vue`
- Modify: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/index.vue`

**Interfaces:**
- Produces: `buildKnowledgeRiskPie(items, selectedCourseId): { slices, mastered, totalIncorrect }`.
- Produces: `KnowledgeRiskPieSlice` with `key`, `item`, `sharePercent`, `incorrectRatePercent`, `tone`, and `color`.
- Produces: `getRiskPresentation()` with four tones: `high`, `medium`, `attention`, `good`.

- [ ] **Step 1: Add failing presentation tests**

Add tests proving two yellow points remain two slices, shares use incorrect counts and sum to 100, zero-error points move to `mastered`, and the four threshold boundaries map to red/orange/yellow/green.

```ts
it('keeps same-colour knowledge points as independent slices', () => {
  const result = buildKnowledgeRiskPie([
    risk({ knowledgePointId: 1, incorrectCount: 2, attemptedCount: 8, incorrectRate: .25 }),
    risk({ knowledgePointId: 2, incorrectCount: 3, attemptedCount: 10, incorrectRate: .30 }),
  ], 7)
  expect(result.slices).toHaveLength(2)
  expect(result.slices.map((item) => item.tone)).toEqual(['attention', 'attention'])
  expect(result.slices.map((item) => item.sharePercent)).toEqual([40, 60])
})
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `npm test -- src/pages/Teacher/TeachingAnalysis/__tests__/analysisPresentation.spec.ts`

Expected: FAIL because `buildKnowledgeRiskPie` and the four-tone presentation do not exist.

- [ ] **Step 3: Implement the pure calculation**

Filter by `courseId === selectedCourseId`, retain one output record per input knowledge point, calculate each share from `incorrectCount`, and use stable colors `#c9483c`, `#e98c3d`, `#e7b23c`, `#3e9b65`.

- [ ] **Step 4: Replace teacher-visible “课程” copy with “实验” copy**

Update headings, button labels, empty states, summaries, and errors in the three Vue files. Keep internal variables and API field names unchanged.

- [ ] **Step 5: Run the focused test and type check**

Run: `npm test -- src/pages/Teacher/TeachingAnalysis/__tests__/analysisPresentation.spec.ts`

Expected: PASS.

Run: `npm run vue-tsc`

Expected: exit 0.

- [ ] **Step 6: Commit**

Commit message: `feat: define experiment knowledge risk presentation`

---

### Task 2: Make knowledge-risk evidence experiment-scoped and detailed

**Files:**
- Modify: `seclab-backend/ai-agent-service/test_teacher_learning_insight_repository.py`
- Modify: `seclab-backend/ai-agent-service/teacher_learning_insight_repository.py`
- Modify: `seclab-backend/ai-agent-service/main.py`
- Modify: `SecLab-FrontEnd-2/src/api.ts`

**Interfaces:**
- Changes: `get_knowledge_risk_map(teacher_id, class_id, course_id=None)` filters the selected experiment before aggregation.
- Produces: `get_knowledge_risk_detail(teacher_id, class_id, course_id, knowledge_point_id)`.
- Adds GET `/api/teacher/teaching-classes/{class_id}/experiments/{course_id}/knowledge-risks`.
- Adds GET `/api/teacher/teaching-classes/{class_id}/experiments/{course_id}/knowledge-risks/{knowledge_point_id}`.

- [ ] **Step 1: Add failing repository tests**

Test experiment filtering, distinct affected students, common wrong-answer grouping, representative answer/standard-answer pairs, pagination metadata, and ownership enforcement.

- [ ] **Step 2: Run the focused Python test and verify RED**

Run: `python -m unittest test_teacher_learning_insight_repository.py`

Expected: FAIL because the scoped functions and detail serializer are missing.

- [ ] **Step 3: Implement scoped query and deterministic detail**

The list response keeps `KnowledgeRiskItemDto`; add `errorShare`, `unansweredStudentCount`, and stable `riskLevel` values `high|medium|attention|good`. The detail response includes `commonMistakes`, `affectedStudents`, `representativeAttempts`, and `pagination` without using AI for names or counts.

- [ ] **Step 4: Add authenticated FastAPI routes and TypeScript DTOs**

Route handlers call `require_owned_teaching_class`, validate experiment membership, map `PermissionError` to 403 and `KeyError` to 404, and never accept a teacher ID from query/body.

- [ ] **Step 5: Run tests**

Run: `python -m unittest test_teacher_learning_insight_repository.py test_teacher_api_errors.py`

Expected: PASS.

- [ ] **Step 6: Commit**

Commit message: `feat: expose experiment knowledge risk details`

---

### Task 3: Persist source-grounded knowledge-point AI analyses and reviewable exercises

**Files:**
- Create: `database/sql/teacher_knowledge_analysis.sql`
- Create: `shujuku/teacher_knowledge_analysis.sql`
- Modify: `database/sql/init_seclab_profile.sql`
- Create: `database/sql/test_teacher_knowledge_analysis_schema.py`
- Create: `seclab-backend/ai-agent-service/teacher_knowledge_analysis_service.py`
- Create: `seclab-backend/ai-agent-service/test_teacher_knowledge_analysis_service.py`
- Modify: `seclab-backend/ai-agent-service/main.py`

**Interfaces:**
- Produces tables `teacher_knowledge_analysis` and `teacher_knowledge_exercise`.
- Produces service methods `get_analysis`, `run_analysis`, `update_exercise`, `regenerate_exercise`, and `review_exercise`.
- Adds GET/POST `/api/teacher/teaching-classes/{class_id}/experiments/{course_id}/knowledge-points/{knowledge_point_id}/ai-analysis`.
- Adds PATCH/POST endpoints below `/.../ai-analysis/exercises/{exercise_id}` for edit, regenerate, and review.

- [ ] **Step 1: Add failing schema tests**

Assert composite ownership/scope keys, `analysis_status`, JSON evidence/output fields, exercise review state, version, reviewer, review time, and indexes.

- [ ] **Step 2: Add failing service tests**

Cover evidence scoping, `RUNNING` conflict, structured output validation, latest-success preservation on provider failure, three exercise roles, independent review, edit-after-approval returning to `PENDING_REVIEW`, and cross-teacher rejection.

- [ ] **Step 3: Run schema and service tests and verify RED**

Run: `python database/sql/test_teacher_knowledge_analysis_schema.py`

Run: `python -m unittest test_teacher_knowledge_analysis_service.py`

Expected: both fail because schema and service are missing.

- [ ] **Step 4: Add the declared schema**

Use a unique analysis key `(teacher_id, teaching_class_id, course_id, knowledge_point_id)` and exercise foreign key to analysis. Store latest successful result separately from last error so a failed refresh does not remove the previous result.

- [ ] **Step 5: Implement the service with dependency injection**

`run_analysis` receives a provider callable in tests, validates `overallConclusion`, `commonMistakes`, `teachingAdvice`, and exactly three exercises with roles `FOUNDATION`, `CONSOLIDATION`, `TRANSFER`, then persists success atomically. Provider failure persists only attempt status/error and raises a controlled unavailable exception.

- [ ] **Step 6: Add authenticated routes and error mappings**

Map running conflict to 409, insufficient evidence to 422, provider failure to 503, authorization to 403, missing resources to 404, and invalid review transition to 400.

- [ ] **Step 7: Run tests**

Run: `python database/sql/test_teacher_knowledge_analysis_schema.py`

Run: `python -m unittest test_teacher_knowledge_analysis_service.py test_teacher_api_errors.py`

Expected: PASS.

- [ ] **Step 8: Commit**

Commit message: `feat: add reviewed knowledge point ai analysis`

---

### Task 4: Snapshot approved exercises into targeted interventions

**Files:**
- Modify: `database/sql/teacher_learning_insight.sql`
- Modify: `shujuku/teacher_learning_insight.sql`
- Modify: `database/sql/init_seclab_profile.sql`
- Modify: `seclab-backend/ai-agent-service/test_teacher_intervention_repository.py`
- Modify: `seclab-backend/ai-agent-service/teacher_intervention_repository.py`
- Modify: `seclab-backend/ai-agent-service/main.py`

**Interfaces:**
- Extends `teacher_intervention` with `course_id`.
- Adds `teacher_intervention_exercise_snapshot` keyed by intervention and source exercise.
- Extends `create_intervention(..., course_id, approved_exercise_ids)`.
- Produces `create_assignment_training_session_from_snapshots(student_id, intervention_id)`.

- [ ] **Step 1: Add failing intervention tests**

Cover rejection of unapproved/cross-scope exercises, immutable JSON snapshot creation, default affected-student membership validation, idempotent student start, and exact snapshot-to-generated-question conversion.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m unittest test_teacher_intervention_repository.py`

Expected: FAIL because approved exercise snapshot support is missing.

- [ ] **Step 3: Update declared schema and repository**

Copy question type, stem, options, answer, explanation, difficulty, knowledge point, source exercise ID and source version into the snapshot table in the same transaction as intervention creation.

- [ ] **Step 4: Replace start-time AI generation for reviewed assignments**

If snapshots exist, create/reuse the student's training session and insert generated questions from snapshots. Keep the existing generation path only for legacy interventions without snapshots.

- [ ] **Step 5: Run intervention and API tests**

Run: `python -m unittest test_teacher_intervention_repository.py test_teacher_api_errors.py`

Expected: PASS.

- [ ] **Step 6: Commit**

Commit message: `feat: issue approved exercises as immutable assignments`

---

### Task 5: Replace the heatmap with an accessible independent-slice pie and detail drawer

**Files:**
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/components/KnowledgeRiskPieChart.vue`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/components/KnowledgeRiskDetailDrawer.vue`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/__tests__/KnowledgeRiskPieChart.spec.ts`
- Modify: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/index.vue`
- Modify: `SecLab-FrontEnd-2/src/api.ts`
- Delete: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/components/KnowledgeRiskHeatmap.vue`

**Interfaces:**
- Pie emits `select(item)` for every slice and mastered item.
- Drawer consumes `classId`, `courseId`, and selected `KnowledgeRiskItemDto` and lazy-loads the deterministic detail.

- [ ] **Step 1: Add failing component tests**

Mount with two yellow points and assert two independently labelled/keyboard-clickable elements, separate white borders, distinct selection events, a four-color legend, and separately clickable zero-error green items.

- [ ] **Step 2: Run the focused component test and verify RED**

Run: `npm test -- src/pages/Teacher/TeachingAnalysis/__tests__/KnowledgeRiskPieChart.spec.ts`

Expected: FAIL because the component does not exist.

- [ ] **Step 3: Implement with Chart.js doughnut segments**

Register only required Chart.js primitives. Supply one dataset entry per knowledge point, `borderColor: '#fff'`, `borderWidth: 3`, `spacing: 2`, stable unique keys, keyboard-equivalent adjacent list buttons, tooltips showing both percentages, and no dataset-level grouping by color.

- [ ] **Step 4: Implement detail drawer**

Render metrics, common mistakes, representative wrong/standard-answer pairs, searchable paginated affected students, attempt history, loading/error/empty states, focus trap, Escape close, and focus restoration.

- [ ] **Step 5: Replace heatmap integration**

Pass only current experiment data, remove the cross-experiment supplement wording, retain selected-risk integration with teaching actions, and open the drawer on slice/list click.

- [ ] **Step 6: Run frontend tests and type check**

Run: `npm test -- src/pages/Teacher/TeachingAnalysis/__tests__/analysisPresentation.spec.ts src/pages/Teacher/TeachingAnalysis/__tests__/KnowledgeRiskPieChart.spec.ts`

Run: `npm run vue-tsc`

Expected: PASS and exit 0.

- [ ] **Step 7: Commit**

Commit message: `feat: render interactive knowledge risk pie`

---

### Task 6: Add teacher AI analysis, exercise review, and issue UI

**Files:**
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/components/KnowledgeAiAnalysisPanel.vue`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/components/KnowledgeExerciseReview.vue`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/components/IssuePersonalizedPracticeDialog.vue`
- Modify: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/components/KnowledgeRiskDetailDrawer.vue`
- Modify: `SecLab-FrontEnd-2/src/api.ts`

**Interfaces:**
- Adds DTO/API wrappers for analysis GET/POST, exercise PATCH/regenerate/review, and approved-exercise intervention creation.
- Review emits updated exercise; issue dialog emits created intervention.

- [ ] **Step 1: Add failing interaction tests**

Cover manual analysis trigger, previous-success display beside refresh error, independent exercise review, edit resetting approval, disabled issue action with no approved exercises, default affected students, all-class/custom selection, and due-date validation.

- [ ] **Step 2: Run tests and verify RED**

Run: `npm test -- src/pages/Teacher/TeachingAnalysis/__tests__`

Expected: FAIL for missing components/interactions.

- [ ] **Step 3: Implement source-grounded analysis panel and review cards**

Render conclusion, common mistakes, teaching advice, three exercise roles, editable fields, per-exercise status, review comments, regenerate control, and explicit provider/error states.

- [ ] **Step 4: Implement issue dialog**

Require at least one approved exercise and one student. Default to affected students, allow all/custom, collect title/description/due date, then call the extended intervention API with `courseId` and `approvedExerciseIds`.

- [ ] **Step 5: Run tests, type check, and build**

Run: `npm test -- src/pages/Teacher/TeachingAnalysis/__tests__`

Run: `npm run vue-tsc`

Run: `npm run build`

Expected: all pass.

- [ ] **Step 6: Commit**

Commit message: `feat: review and issue knowledge point exercises`

---

### Task 7: Complete the student personal-center assignment experience

**Files:**
- Modify: `SecLab-FrontEnd-2/src/pages/User/Profile/TeacherAssignments.vue`
- Modify: `SecLab-FrontEnd-2/src/api.ts`
- Modify: `seclab-backend/ai-agent-service/teacher_intervention_repository.py`
- Modify: `seclab-backend/ai-agent-service/main.py`
- Test: `seclab-backend/ai-agent-service/test_teacher_intervention_repository.py`

**Interfaces:**
- Student assignment DTO adds `courseName`, `questionCount`, `estimatedMinutes`, `isOverdue`, and result summary.
- Existing start endpoint returns the exact snapshot-backed training session.

- [ ] **Step 1: Add failing assignment serialization tests**

Assert pending/in-progress/completed/overdue presentation data, experiment and knowledge-point labels, exact exercise count, and result summary isolation by student.

- [ ] **Step 2: Run backend test and verify RED**

Run: `python -m unittest test_teacher_intervention_repository.py`

Expected: FAIL for missing assignment fields.

- [ ] **Step 3: Implement assignment DTO and personal-center cards**

Use heading “老师布置的个性化练习”; show teacher, experiment, knowledge point, deadline, instructions, count, status and start/continue/result action. Keep the existing training route and authenticated student ID checks.

- [ ] **Step 4: Run backend and frontend verification**

Run: `python -m unittest test_teacher_intervention_repository.py test_teacher_api_errors.py`

Run: `npm run vue-tsc`

Run: `npm run build`

Expected: all pass.

- [ ] **Step 5: Commit**

Commit message: `feat: show personalized teacher practice to students`

---

### Task 8: Verify the complete teacher-student loop

**Files:**
- Modify only tests or focused implementation files if verification exposes a reproducible defect.

**Interfaces:**
- Verifies one teacher-owned class and student from risk evidence through outcome refresh.

- [ ] **Step 1: Run all focused backend checks**

Run: `python -m unittest discover -s seclab-backend/ai-agent-service -p 'test_teacher*.py'`

Run: `python database/sql/test_teacher_knowledge_analysis_schema.py`

Expected: all pass.

- [ ] **Step 2: Run all frontend checks**

Run: `npm test`

Run: `npm run vue-tsc`

Run: `npm run build`

Expected: all pass.

- [ ] **Step 3: Run browser verification**

Verify desktop and mobile: experiment copy, multiple same-color independent slices, zero-error list, slice/detail navigation, deterministic evidence, AI refresh failure preservation, edit/review transitions, approved-only issue, student personal-center task, exact approved questions, submission, and teacher completion/result refresh.

- [ ] **Step 4: Run permission and source scans**

Confirm no teacher ID is trusted from client input; no unapproved exercise can be issued; no student can query another student's assignment; and the demo answer exists only in the seed SQL/data response path, not frontend hardcoded UI.

- [ ] **Step 5: Review diff and commit verification fixes**

Run: `git diff --check`

Commit message when fixes were required: `fix: close knowledge teaching loop verification gaps`
