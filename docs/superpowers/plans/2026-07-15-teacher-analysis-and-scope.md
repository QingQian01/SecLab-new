# Teacher Analysis and Owned Scope Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restrict every teacher-facing class, student, generated-question, and analysis query to the current teacher's own teaching classes, and add one left-navigation page named “教学分析” for manual class and student analysis.

**Architecture:** The user service is authoritative for teaching-class ownership and membership. The AI service derives scope directly from `userservice.teaching_class` and `teaching_class_student`, persists only the latest class/student analysis, and never trusts client-supplied teacher IDs. The Vue teacher app consumes these scoped APIs and keeps the shared course catalog as the sole cross-teacher resource.

**Tech Stack:** Vue 3, TypeScript, Vite, Kotlin, Spring Boot, Spring Data JPA, Python, FastAPI, MySQL.

## Global Constraints

- Visible navigation copy is exactly “教学分析”; no “特色”, “创新中心”, or “AI 中心” suffix.
- Teachers see only their own teaching classes and the students, generated questions, and analyses inside them.
- The course catalog remains globally readable; only the course creator may edit or delete a course.
- Class and student analysis are manually triggered and keep only the latest successful result.
- Provider failure must not create a fake analysis and must preserve the previous success.
- Do not add scheduled analysis jobs or new learning-event types.

---

### Task 1: Scope the user-service teaching-class APIs

**Files:**
- Modify: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/repository/TeachingClassRepositories.kt`
- Modify: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/service/TeacherTeachingClassService.kt`
- Modify: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/service/TeachingClassImportService.kt`
- Modify: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/controller/TeacherTeachingClassController.kt`
- Test: `seclab-backend/user-service/src/test/kotlin/me/myot233/seclab/userservice/service/TeacherTeachingClassServiceTest.kt`
- Test: `seclab-backend/user-service/src/test/kotlin/me/myot233/seclab/userservice/service/TeachingClassImportServiceTest.kt`

**Interfaces:**
- Produces: `listOwned(teacherId: Long): List<TeachingClassResponse>`.
- Produces: `requireOwner(teacherId: Long, teachingClassId: Long): TeachingClassEntity` as the read/write authorization boundary.
- Changes: `listStudents(teacherId: Long, teachingClassId: Long)` and `listCourses(teacherId: Long, teachingClassId: Long)`.

- [ ] Add failing tests proving teacher A cannot list, detail, read students, or read course arrangements from teacher B's teaching class.
- [ ] Run `gradlew.bat test --tests "*TeacherTeachingClassServiceTest" --tests "*TeachingClassImportServiceTest"` and confirm the new assertions fail.
- [ ] Add repository query `findAllByTeacherIdOrderByUpdatedAtDesc`, replace global reads with owner-scoped reads, and pass current teacher ID through the controller read endpoints.
- [ ] Run the focused tests and confirm they pass.

### Task 2: Scope AI-service authentication and generated-question data

**Files:**
- Modify: `seclab-backend/ai-agent-service/main.py`
- Modify: `seclab-backend/ai-agent-service/teacher_repository.py`
- Modify: `seclab-backend/ai-agent-service/test_teacher_api_errors.py`
- Modify: `seclab-backend/ai-agent-service/test_teacher_repository_helpers.py`

**Interfaces:**
- Produces auth context field `owned_teaching_class_ids: list[int]` loaded from `userservice.teaching_class.teacher_id`.
- Produces `require_owned_teaching_class(teacher_id: int, teaching_class_id: int)`.
- Changes generated-question queries to require `tc.teacher_id = current_user.user_id`.

- [ ] Add failing tests for owned teaching-class IDs, cross-teacher generated-question access, cross-teacher summaries, and direct student-profile access.
- [ ] Run `python -m unittest test_teacher_api_errors.py test_teacher_repository_helpers.py` from the AI service directory and confirm failure.
- [ ] Load owned teaching-class IDs in `_load_teacher_auth_context`, apply ownership predicates to list/detail/summary queries, and authorize students through `teaching_class_student` membership.
- [ ] Pass `current_user` into summary and latest-analysis endpoints instead of using unscoped repository calls.
- [ ] Run the focused tests and confirm they pass.

### Task 3: Persist latest student analysis without fallback

**Files:**
- Modify: `数据库文件/teacher_teaching_class.sql`
- Modify: `database/sql/init_seclab_profile.sql`
- Modify: `database/sql/init_seclab_db.sql`
- Modify: `database/sql/test_teacher_teaching_class_schema.py`
- Modify: `seclab-backend/ai-agent-service/teacher_analysis_repository.py`
- Modify: `seclab-backend/ai-agent-service/teacher_ai_analysis_service.py`
- Modify: `seclab-backend/ai-agent-service/main.py`
- Modify: `seclab-backend/ai-agent-service/test_teacher_analysis_repository.py`
- Modify: `seclab-backend/ai-agent-service/test_teacher_ai_analysis_service.py`

**Interfaces:**
- Adds table `teacher_student_analysis` keyed by `(teacher_id, teaching_class_id, student_id)` with status, latest analysis JSON, evidence stats, cutoff, error, generated and attempt timestamps.
- Adds GET/POST `/api/teacher/teaching-classes/{class_id}/students/{student_id}/ai-analysis`.
- Produces `get_latest_student_analysis(...)` and `run_manual_student_analysis(...)`.

- [ ] Add schema assertions and repository tests for IDLE, RUNNING conflict, successful replacement, and failed-refresh preservation.
- [ ] Add service tests proving question/evidence scope is the selected student and that provider failure raises a controlled error rather than returning `rule_fallback`.
- [ ] Run schema and AI tests to confirm failure.
- [ ] Implement the table, latest-result repository, ownership/membership validation, evidence collection, GET/POST endpoints, and `409/422/503` mapping.
- [ ] Run the schema and AI tests and confirm they pass.

### Task 4: Add the code-native “教学分析” page

**Files:**
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/index.vue`
- Modify: `SecLab-FrontEnd-2/src/api.ts`
- Modify: `SecLab-FrontEnd-2/src/router/router.ts`
- Modify: `SecLab-FrontEnd-2/src/layout/Teacher/index.vue`
- Reuse: `SecLab-FrontEnd-2/src/pages/Teacher/teacher-page.css`

**Interfaces:**
- Adds route `/teacher/analysis`.
- Adds API functions `getTeachingClassStudentAnalysis(classId, studentId)` and `startTeachingClassStudentAnalysis(classId, studentId)`.
- Consumes existing owned teaching-class list, student list, generated-question summary, class latest analysis, and class manual analysis APIs.

- [ ] Add the navigation item exactly as “教学分析” between “教学班” and “生成题记录”, with no badge or suffix.
- [ ] Build the page with owned-class selector and two tabs: “班级分析” and “学生分析”.
- [ ] In the class tab, render latest result, evidence-linked common problems, manual start/retry, empty/error/running states.
- [ ] In the student tab, render searchable class members, evidence summary, latest individual result, manual start/retry, empty/error/running states.
- [ ] Run `npm run vue-tsc` and fix all type errors.

### Task 5: Simplify teaching overview and keep analysis in one place

**Files:**
- Modify: `SecLab-FrontEnd-2/src/pages/Teacher/Overview/index.vue`

**Interfaces:**
- Links to `/teacher/analysis?classId={id}`.
- Keeps only a short latest-analysis summary on the overview.

- [ ] Replace the full class-analysis problem list and trigger button with a concise latest-result summary and “进入教学分析” link.
- [ ] Preserve student counts, course arrangement, recent activity, loading, empty, and error states.
- [ ] Run `npm run vue-tsc`.

### Task 6: Verify isolation, copy, build, and responsive layout

**Files:**
- Update tests from Tasks 1–3 only when verification exposes a missing regression.
- Keep browser screenshots under `docs/design/` only when they are final review artifacts.

**Interfaces:**
- Verifies current-teacher scope from token through SQL predicate and rendered filters.

- [ ] Run `gradlew.bat build --console=plain` in `user-service`.
- [ ] Run `python -m unittest discover -s seclab-backend/ai-agent-service -p 'test_teacher*.py'`.
- [ ] Run `python database/sql/test_teacher_teaching_class_schema.py`.
- [ ] Run `npm run vue-tsc` and `npm run build` in the frontend.
- [ ] Browser-test desktop and mobile with two teacher identities and verify no cross-teacher class/student/question identifiers appear.
- [ ] Search the new teacher UI for prohibited copy: `特色`, `创新中心`, `AI 中心`, `管理员端`, and review-workflow terms.
- [ ] Inspect the accepted teacher dashboard concept and final browser screenshot with `view_image`; record layout, copy, typography, palette, spacing, and responsive comparison.
