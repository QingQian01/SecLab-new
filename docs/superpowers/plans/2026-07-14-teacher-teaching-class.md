# Teacher Teaching Class Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a realistic teacher workspace where teachers create semester teaching classes, import students, arrange reusable courses, inspect student AI-generated training records, collect representative questions, and manually run evidence-backed class analysis.

**Architecture:** Store teacher identity and teaching-class membership in `userservice`; keep reusable shared course/module resources in the existing catalog tables; keep generated questions, attempts, typical-question marks, and the latest AI analysis in `seclab_profile`. Every teacher can read all teaching classes and shared courses, while mutations require the teaching-class owner or course creator. The frontend reads student-generated content directly from the backend and invokes class AI analysis only after an explicit owner action.

**Tech Stack:** Vue 3, TypeScript, Vite, Tailwind CSS/DaisyUI, Kotlin 1.9, Spring Boot, Spring Data JPA, Apache POI, FastAPI, PyMySQL, MySQL 8, Python `unittest`.

## Global Constraints

- Teachers create their own teaching classes; no administrator workflow is required.
- Every teacher can view every teaching class and its learning data; only the class owner can mutate class data or run class AI analysis.
- One teaching class can arrange many reusable courses in a defined order.
- Every teacher can view and select every shared course; only the course creator can edit or delete it.
- Excel import uses `学号｜姓名｜行政班`; missing accounts are created with password `123456` and no forced password change.
- Generated questions and attempts are read from the existing student-side records; do not copy them into a teacher-only feed.
- “典型题” is a teacher-owned mark and never changes student visibility or question delivery.
- AI analysis runs only after the teacher clicks “开始分析”, keeps only the latest successful result, and never falls back to frontend-generated advice.
- SQL master changes go into `数据库文件/`; the current runtime copies in `database/sql/` must remain synchronized while that mirror exists.
- Preserve unrelated staged and unstaged changes. Each commit stages only the files named by its task.
- Do not introduce a new frontend state framework or a new backend service.

---

## File Map

### Database

- Create `数据库文件/teacher_teaching_class.sql`: canonical role, teaching-class, course-arrangement, import-batch, typical-question, and latest-analysis schema.
- Modify `database/sql/user-service-local-init.sql`: runtime `userservice` schema mirror, teacher seed role, and course creator field.
- Modify `database/sql/init_seclab_profile.sql`: runtime `seclab_profile` schema mirror.
- Create `数据库文件/teacher_realistic_data_reset.sql`: preview-first cleanup transaction.
- Create `数据库文件/seed_realistic_teacher_data.sql`: realistic post-cleanup dataset.
- Modify `database/sql/teacher-scope-test-seed.sql`: keep authorization-only fixtures clearly isolated from default data.

### User service

- Create `entity/UserRole.kt`: stable role enum.
- Modify `entity/UserEntity.kt`: persist `user_role`.
- Create `service/CurrentUserService.kt`: token-to-active-user and teacher authorization boundary.
- Modify `service/UserService.kt`: return roles from `user_role`, create imported students as `STUDENT`.
- Create `entity/TeachingClassEntity.kt`, `TeachingClassStudentEntity.kt`, `TeachingClassCourseEntity.kt`, `TeachingClassImportBatchEntity.kt`.
- Create `repository/TeachingClassRepositories.kt`.
- Create `dto/TeachingClassDtos.kt`.
- Create `service/TeacherTeachingClassService.kt`: global reads plus owner-only class mutations.
- Create `service/TeachingClassImportService.kt`: Excel preview/confirm.
- Create `controller/TeacherTeachingClassController.kt`.
- Modify `build.gradle.kts`: add Apache POI only.
- Create focused tests under `src/test/kotlin/me/myot233/seclab/userservice/`.

### Experiment-module service

- Modify `service/CatalogAuthService.kt`: authorize explicit `TEACHER` accounts and expose the current teacher ID.
- Modify `entity/CourseEntity.kt`, `dto/CatalogDtos.kt`, `repository/CourseRepository.kt`, `service/CatalogQueryService.kt`, and `controller/CourseController.kt`: persist `createdBy`, allow global reads, and enforce creator-only edits/deletes.
- Create `src/test/kotlin/me/myot233/seclab/experimentmoduleservice/service/CatalogAuthServiceTest.kt`.

### AI agent service

- Modify `teacher_repository.py`: global teaching-class reads, question feed, aggregates, and personal typical marks.
- Create `teacher_analysis_repository.py`: latest-analysis persistence and atomic run state.
- Modify `teacher_ai_analysis_service.py`: evidence input, manual execution, and latest-result replacement.
- Modify `teacher_ai_prompts.py`: require evidence and representative existing question IDs.
- Modify `main.py`: new teaching-class question and manual-analysis endpoints.
- Extend the existing `test_teacher_*.py` files and create `test_teacher_analysis_repository.py`.

### Frontend

- Create `src/types/teacher.ts` and `src/api/teacher.ts`; keep compatibility re-exports in `src/api.ts`.
- Create `src/layout/Teacher/index.vue` and `src/layout/Teacher/Nav.vue`.
- Create `src/pages/Teacher/Dashboard/index.vue`.
- Create `src/pages/Teacher/TeachingClasses/index.vue`.
- Create `src/pages/Teacher/TeachingClassDetail/index.vue`.
- Create `src/pages/Teacher/TrainingRecords/index.vue`.
- Modify `src/pages/Admin/Courses/index.vue` and its create page so the user-facing feature is “课程资源” and teacher authorization is respected.
- Modify `src/router/router.ts` and `src/auth.ts` for `/teacher` routes and `/admin` compatibility redirects.

---

### Task 1: Add the canonical database schema

**Files:**
- Create: `数据库文件/teacher_teaching_class.sql`
- Modify: `database/sql/user-service-local-init.sql`
- Modify: `database/sql/init_seclab_profile.sql`

**Interfaces:**
- Produces: `user.user_role`, `course.created_by`, `teaching_class`, `teaching_class_student`, `teaching_class_course`, `teaching_class_import_batch`, `teacher_typical_question`, and `teacher_class_analysis`.
- Consumed by: every later backend task.

- [ ] **Step 1: Write the schema assertions before the migration**

Create an executable verification block at the bottom of the canonical SQL file:

```sql
SELECT COUNT(*) = 1 AS has_user_role
FROM information_schema.columns
WHERE table_schema = 'userservice' AND table_name = 'user' AND column_name = 'user_role';

SELECT COUNT(*) = 1 AS has_course_creator
FROM information_schema.columns
WHERE table_schema = 'userservice' AND table_name = 'course' AND column_name = 'created_by';

SELECT COUNT(*) = 4 AS has_teaching_tables
FROM information_schema.tables
WHERE table_schema = 'userservice'
  AND table_name IN ('teaching_class', 'teaching_class_student', 'teaching_class_course', 'teaching_class_import_batch');

SELECT COUNT(*) = 2 AS has_profile_tables
FROM information_schema.tables
WHERE table_schema = 'seclab_profile'
  AND table_name IN ('teacher_typical_question', 'teacher_class_analysis');
```

- [ ] **Step 2: Run the assertions against a fresh MySQL container and verify failure**

Run:

```powershell
docker run --rm -d --name seclab-schema-check -e MYSQL_ROOT_PASSWORD=check -p 33306:3306 mysql:8.4
docker exec seclab-schema-check mysqladmin ping -uroot -pcheck --wait=30
Get-Content -Raw database/sql/user-service-local-init.sql | docker exec -i seclab-schema-check mysql -uroot -pcheck
Get-Content -Raw database/sql/init_seclab_profile.sql | docker exec -i seclab-schema-check mysql -uroot -pcheck
```

Expected: the new assertions cannot pass because the tables, `user_role`, and `course.created_by` do not exist yet.

- [ ] **Step 3: Implement the schema with exact constraints**

Use the following role and teaching-class definitions in the canonical file and mirror them into the runtime scripts:

```sql
ALTER TABLE `userservice`.`user`
  ADD COLUMN `user_role` VARCHAR(16) NOT NULL DEFAULT 'STUDENT' AFTER `is_admin`,
  ADD KEY `idx_user_role_deleted` (`user_role`, `is_deleted`);

UPDATE `userservice`.`user`
SET `user_role` = CASE
  WHEN COALESCE(`is_admin` + 0, 0) = 1 THEN 'TEACHER'
  WHEN EXISTS (
    SELECT 1 FROM `userservice`.`class` c
    WHERE c.admin_id = `user`.user_id AND COALESCE(c.is_end, 0) = 0
  ) THEN 'TEACHER'
  ELSE 'STUDENT'
END;

ALTER TABLE `userservice`.`course`
  ADD COLUMN `created_by` BIGINT NULL AFTER `instructor`,
  ADD KEY `idx_course_creator_status` (`created_by`, `course_status`),
  ADD CONSTRAINT `fk_course_creator` FOREIGN KEY (`created_by`) REFERENCES `userservice`.`user` (`user_id`);

CREATE TABLE `userservice`.`teaching_class` (
  `teaching_class_id` BIGINT NOT NULL AUTO_INCREMENT,
  `class_name` VARCHAR(120) NOT NULL,
  `academic_year` VARCHAR(9) NOT NULL,
  `semester` TINYINT NOT NULL,
  `teacher_id` BIGINT NOT NULL,
  `start_date` DATE NULL,
  `end_date` DATE NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`teaching_class_id`),
  UNIQUE KEY `uk_teacher_term_class_name` (`teacher_id`, `academic_year`, `semester`, `class_name`),
  KEY `idx_teaching_class_teacher_status` (`teacher_id`, `status`),
  CONSTRAINT `fk_teaching_class_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `userservice`.`user` (`user_id`),
  CONSTRAINT `chk_teaching_class_semester` CHECK (`semester` IN (1, 2)),
  CONSTRAINT `chk_teaching_class_status` CHECK (`status` IN ('ACTIVE', 'ARCHIVED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

Define membership with `PRIMARY KEY (teaching_class_id, student_id)`, course arrangement with `UNIQUE (teaching_class_id, course_id)` and `UNIQUE (teaching_class_id, teaching_order)`, and import batches with UUID `CHAR(36)`, `preview_json JSON`, status checks, and expiry timestamps. Define profile tables exactly as specified in the design document.

- [ ] **Step 4: Apply the migration twice in the fresh container**

Run the canonical SQL twice, then run the three assertions.

Expected: both migration executions succeed; all four assertions return `1`; no duplicate index or column error occurs. Use `information_schema` guards around additions that MySQL cannot repeat directly.

- [ ] **Step 5: Commit the schema foundation**

```powershell
git add -- '数据库文件/teacher_teaching_class.sql' 'database/sql/user-service-local-init.sql' 'database/sql/init_seclab_profile.sql'
git commit -m "feat(db): add teacher teaching class schema"
```

---

### Task 2: Make teacher identity explicit

**Files:**
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/entity/UserRole.kt`
- Modify: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/entity/UserEntity.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/service/CurrentUserService.kt`
- Modify: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/service/UserService.kt`
- Modify: `seclab-backend/experiment-module-service/src/main/kotlin/me/myot233/seclab/experimentmoduleservice/service/CatalogAuthService.kt`
- Test: `seclab-backend/user-service/src/test/kotlin/me/myot233/seclab/userservice/service/CurrentUserServiceTest.kt`
- Test: `seclab-backend/experiment-module-service/src/test/kotlin/me/myot233/seclab/experimentmoduleservice/service/CatalogAuthServiceTest.kt`

**Interfaces:**
- Produces: `CurrentUserService.requireTeacher(token, authorization): UserEntity`.
- Produces: login/profile role values `teacher` and `student` from `user_role`.
- Consumed by: teaching-class controllers and course mutations.

- [ ] **Step 1: Write failing role tests**

```kotlin
@Test
fun `teacher role can create teaching classes before owning a class`() {
    val teacher = UserEntity(userId = 9, userStudentNumber = "teacher01", userRole = UserRole.TEACHER)
    whenever(jwtTokenService.parse("token")).thenReturn(TokenPayload(9, "teacher01"))
    whenever(userRepository.findById(9)).thenReturn(Optional.of(teacher))

    assertEquals(9, currentUserService.requireTeacher("token", null).userId)
}

@Test
fun `student role is rejected from teacher endpoints`() {
    val student = UserEntity(userId = 10, userStudentNumber = "20260001", userRole = UserRole.STUDENT)
    whenever(jwtTokenService.parse("token")).thenReturn(TokenPayload(10, "20260001"))
    whenever(userRepository.findById(10)).thenReturn(Optional.of(student))

    val error = assertThrows<ApiException> { currentUserService.requireTeacher("token", null) }
    assertEquals(403, error.status)
}
```

- [ ] **Step 2: Run the tests and verify failure**

Run: `cd seclab/seclab; .\gradlew.bat :user-service:test --tests "*CurrentUserServiceTest"`

Expected: FAIL because `UserRole`, `userRole`, and `CurrentUserService` do not exist.

- [ ] **Step 3: Implement role persistence and authorization**

```kotlin
enum class UserRole { STUDENT, TEACHER, ADMIN }

@field:Enumerated(EnumType.STRING)
@field:Column(name = "user_role", nullable = false, length = 16)
open var userRole: UserRole = UserRole.STUDENT
```

`CurrentUserService.requireTeacher` must resolve the bearer/query token through `JwtTokenService`, load an active user, and accept only `TEACHER`. Keep `ADMIN` readable for compatibility but do not route it into the teacher workspace.

Update imported and registered users to `STUDENT`; update seeded teacher accounts to `TEACHER`. Update `CatalogAuthService` to query `user_role` and require `TEACHER` instead of inferring ownership through legacy `class.admin_id`.

- [ ] **Step 4: Run both service test suites**

Run:

```powershell
cd seclab/seclab
.\gradlew.bat :user-service:test
.\gradlew.bat :experiment-module-service:test
```

Expected: PASS; teacher access works without an existing legacy class, student access returns 403.

- [ ] **Step 5: Commit explicit roles**

```powershell
git add -- seclab-backend/user-service/src seclab-backend/experiment-module-service/src
git commit -m "feat(auth): add explicit teacher role"
```

---

### Task 3: Implement globally visible teaching classes with owner-only mutations

**Files:**
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/entity/TeachingClassEntity.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/entity/TeachingClassStudentEntity.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/entity/TeachingClassCourseEntity.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/entity/TeachingClassImportBatchEntity.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/repository/TeachingClassRepositories.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/dto/TeachingClassDtos.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/service/TeacherTeachingClassService.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/controller/TeacherTeachingClassController.kt`
- Test: `seclab-backend/user-service/src/test/kotlin/me/myot233/seclab/userservice/service/TeacherTeachingClassServiceTest.kt`

**Interfaces:**
- Produces: global `list` and `detail`, plus owner-checked `create`, `update`, and `archive`.
- Produces: REST endpoints under `/api/teacher/teaching-classes`.
- Consumed by: import, course arrangement, AI scope, and frontend tasks.

- [ ] **Step 1: Write failing visibility, ownership, and validation tests**

```kotlin
@Test
fun `teacher lists classes owned by every teacher`() {
    whenever(repository.findAllByOrderByUpdatedAtDesc()).thenReturn(listOf(ownedClass, otherTeacherClass))
    val result = service.listAll()
    assertEquals(listOf(101L, 102L), result.map { it.teachingClassId })
}

@Test
fun `teacher cannot update another teachers class`() {
    whenever(repository.findById(102)).thenReturn(Optional.of(otherTeacherClass))
    val error = assertThrows<ApiException> { service.update(7, 102, validRequest) }
    assertEquals(403, error.status)
}

@Test
fun `end date cannot precede start date`() {
    val request = TeachingClassSaveRequest("网络安全232班", "2026-2027", 1, LocalDate.parse("2026-09-01"), LocalDate.parse("2026-08-31"))
    assertThrows<ApiException> { service.create(7, request) }
}
```

- [ ] **Step 2: Run the test and verify failure**

Run: `cd seclab/seclab; .\gradlew.bat :user-service:test --tests "*TeacherTeachingClassServiceTest"`

Expected: FAIL because teaching-class types and service are absent.

- [ ] **Step 3: Implement focused entities and DTOs**

Expose this stable request contract:

```kotlin
data class TeachingClassSaveRequest(
    @field:NotBlank val className: String,
    @field:Pattern(regexp = "\\d{4}-\\d{4}") val academicYear: String,
    @field:Min(1) @field:Max(2) val semester: Int,
    val startDate: LocalDate?,
    val endDate: LocalDate?,
)
```

Return `teachingClassId`, normalized name, term, dates, status, `studentCount`, `courseCount`, `currentCourse`, and `lastActiveAt`. Put mapping code in the service rather than the controller.

- [ ] **Step 4: Implement endpoints and error mapping**

Use token-derived teacher ID for writes. `listAll` and `detail` return classes owned by any active teacher. Creation writes the current teacher as `teacherId`; update and archive return 403 when the current teacher is not the owner. Return 404 for missing ID, 409 for the unique name/term conflict, and 400 for invalid dates. Archive by setting `ARCHIVED`; never delete a teaching class with learning data.

- [ ] **Step 5: Run service tests and build**

Run:

```powershell
cd seclab/seclab
.\gradlew.bat :user-service:test
.\gradlew.bat :user-service:build
```

Expected: PASS and BUILD SUCCESSFUL.

- [ ] **Step 6: Commit the teaching-class vertical slice**

```powershell
git add -- seclab-backend/user-service/src
git commit -m "feat(teacher): add teaching class management"
```

---

### Task 4: Add Excel student import with preview and idempotent confirmation

**Files:**
- Modify: `seclab-backend/user-service/build.gradle.kts`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/service/TeachingClassImportService.kt`
- Modify: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/controller/TeacherTeachingClassController.kt`
- Modify: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/dto/TeachingClassDtos.kt`
- Test: `seclab-backend/user-service/src/test/kotlin/me/myot233/seclab/userservice/service/TeachingClassImportServiceTest.kt`
- Create: `SecLab-FrontEnd-2/public/templates/教学班学生导入模板.xlsx`

**Interfaces:**
- Consumes: `TeacherTeachingClassService.requireVisibleClass(classId)` for reads and `requireManagedClass(teacherId, classId)` for mutations.
- Produces: preview response `{batchId, newAccounts, existingAccounts, duplicateRows, errorRows, expiresAt}`.
- Produces: confirm response `{createdAccountCount, addedMemberCount, skippedMemberCount}`.

- [ ] **Step 1: Write failing parser and idempotency tests**

```kotlin
@Test
fun `preview classifies new existing duplicate and invalid rows`() {
    val preview = service.preview(teacherId = 7, teachingClassId = 101, bytes = workbookBytes(
        listOf("20260001", "张晨", "网安232班"),
        listOf("20260001", "张晨", "网安232班"),
        listOf("bad-number-too-long", "", "网安232班"),
    ))
    assertEquals(1, preview.newAccounts.size)
    assertEquals(1, preview.duplicateRows.size)
    assertEquals(1, preview.errorRows.size)
}

@Test
fun `confirming one batch twice does not create duplicate members`() {
    val first = service.confirm(7, batchId)
    val second = service.confirm(7, batchId)
    assertEquals(first, second)
    verify(userRepository, times(1)).saveAll(any())
}
```

- [ ] **Step 2: Run the test and verify failure**

Run: `cd seclab/seclab; .\gradlew.bat :user-service:test --tests "*TeachingClassImportServiceTest"`

Expected: FAIL because the import service is absent.

- [ ] **Step 3: Add only the required Excel dependency**

```kotlin
implementation("org.apache.poi:poi-ooxml:5.3.0")
```

Accept `.xlsx` up to 2 MB and 500 rows. Require the first row headers `学号`, `姓名`, `行政班`. Reject formulas, blank student numbers, names over 80 characters, and student numbers over 13 characters.

- [ ] **Step 4: Implement preview persistence**

Normalize cell values as text, de-duplicate by student number, query existing users in one repository call, and save the full preview JSON with a 30-minute expiry. Do not write users or memberships during preview.

- [ ] **Step 5: Implement transactional confirmation**

Within one transaction, lock the batch, validate `PREVIEWED`, create missing users with encoded `123456`, `userRole = STUDENT`, and the imported administrative class label, then insert teaching-class memberships with `insert ignore` or existence checks. Mark the batch `CONFIRMED` and return the stored result on repeat confirmation.

Add `GET /api/teacher/teaching-classes/{id}/students` and `DELETE /api/teacher/teaching-classes/{id}/students/{studentId}` in the same service boundary. Any teacher can list students. Only the class owner can preview/confirm imports or remove a member. Listing returns student ID, student number, name, administrative class, joined time, and recent activity. Removal deletes only the teaching-class membership; it never deletes the student account or learning history.

- [ ] **Step 6: Generate the real template and run tests**

Create the workbook with a single sheet named `学生名单`, the required headers, and one clearly marked example row. Run:

```powershell
cd seclab/seclab
.\gradlew.bat :user-service:test --tests "*TeachingClassImportServiceTest"
.\gradlew.bat :user-service:build
```

Expected: PASS; malformed workbooks produce 400; expired/confirmed batch conflicts produce 409.

- [ ] **Step 7: Commit student import**

```powershell
git add -- seclab-backend/user-service SecLab-FrontEnd-2/public/templates
git commit -m "feat(teacher): import teaching class students"
```

---

### Task 5: Arrange reusable courses inside a teaching class

**Files:**
- Modify: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/service/TeacherTeachingClassService.kt`
- Modify: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/controller/TeacherTeachingClassController.kt`
- Modify: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/dto/TeachingClassDtos.kt`
- Test: `seclab-backend/user-service/src/test/kotlin/me/myot233/seclab/userservice/service/TeachingClassCourseServiceTest.kt`
- Modify: `seclab-backend/experiment-module-service/src/main/kotlin/me/myot233/seclab/experimentmoduleservice/entity/CourseEntity.kt`
- Modify: `seclab-backend/experiment-module-service/src/main/kotlin/me/myot233/seclab/experimentmoduleservice/dto/CatalogDtos.kt`
- Modify: `seclab-backend/experiment-module-service/src/main/kotlin/me/myot233/seclab/experimentmoduleservice/repository/CourseRepository.kt`
- Modify: `seclab-backend/experiment-module-service/src/main/kotlin/me/myot233/seclab/experimentmoduleservice/service/CatalogQueryService.kt`
- Modify: `seclab-backend/experiment-module-service/src/main/kotlin/me/myot233/seclab/experimentmoduleservice/controller/CourseController.kt`
- Test: `seclab-backend/experiment-module-service/src/test/kotlin/me/myot233/seclab/experimentmoduleservice/service/CoursePermissionTest.kt`

**Interfaces:**
- Produces: `GET /api/teacher/teaching-classes/{id}/courses`.
- Produces: `PUT /api/teacher/teaching-classes/{id}/courses` with ordered items.
- Consumed by: teaching-class details, dashboards, and AI course filters.

- [ ] **Step 1: Write failing course arrangement tests**

```kotlin
@Test
fun `one teaching class accepts multiple reusable courses in order`() {
    val request = TeachingClassCourseUpdateRequest(listOf(
        TeachingClassCourseItemRequest(1, 1, LocalDate.parse("2026-09-01"), LocalDate.parse("2026-09-14")),
        TeachingClassCourseItemRequest(2, 2, LocalDate.parse("2026-09-15"), LocalDate.parse("2026-09-28")),
    ))
    val result = service.replaceCourses(teacherId = 7, teachingClassId = 101, request)
    assertEquals(listOf(1, 2), result.map { it.courseId })
}
```

Define the request DTOs with the same names used by the test:

```kotlin
data class TeachingClassCourseItemRequest(
    val courseId: Long,
    val teachingOrder: Int,
    val plannedStartDate: LocalDate?,
    val plannedEndDate: LocalDate?,
)

data class TeachingClassCourseUpdateRequest(
    val items: List<TeachingClassCourseItemRequest>,
)
```

- [ ] **Step 2: Run and verify failure**

Run: `cd seclab/seclab; .\gradlew.bat :user-service:test --tests "*TeachingClassCourseServiceTest"`

Expected: FAIL because `replaceCourses` is absent.

- [ ] **Step 3: Implement replacement semantics**

Validate teaching-class ownership, course existence, unique course IDs, contiguous `teachingOrder` beginning at 1, and planned dates within the teaching-class dates. Any shared course can be selected regardless of creator. Replace the arrangement in one transaction without modifying course rows or historical student activity.

- [ ] **Step 4: Verify course creation remains teacher-accessible**

Add catalog tests proving all teachers can list and select all courses, only `createdBy` can update/delete a course, and a `STUDENT` gets 403 from mutations. Course creation writes the token teacher ID to `created_by`. Historical rows with null `created_by` are readable/selectable but cannot be edited until explicitly assigned. No course copy is created when a teaching class selects one.

- [ ] **Step 5: Run both service builds and commit**

```powershell
cd seclab/seclab
.\gradlew.bat :user-service:build
.\gradlew.bat :experiment-module-service:build
git add -- user-service/src experiment-module-service/src
git commit -m "feat(teacher): arrange reusable class courses"
```

Expected: both builds succeed.

---

### Task 6: Replace generated-question review with a live teaching record

**Files:**
- Modify: `seclab-backend/ai-agent-service/teacher_repository.py`
- Modify: `seclab-backend/ai-agent-service/main.py`
- Modify: `seclab-backend/ai-agent-service/test_teacher_repository_helpers.py`
- Modify: `seclab-backend/ai-agent-service/test_teacher_api_errors.py`

**Interfaces:**
- Consumes: `userservice.teaching_class_student` and `userservice.teaching_class_course`.
- Produces: filtered generated-question records, details, aggregate summary, and typical-question mutation.
- Consumed by: frontend training-record page and manual class analysis.

- [ ] **Step 1: Write failing repository tests**

```python
def test_generated_questions_can_be_filtered_by_any_visible_teaching_class(self):
    result = list_generated_questions_for_teacher(
        current_user={"user_id": 7, "role": "teacher"},
        teaching_class_id=101,
        course_id=2,
        answer_result="incorrect",
        typical_only=False,
    )
    self.assertTrue(all(item["teachingClassId"] == 101 for item in result["items"]))

def test_marking_typical_does_not_update_review_status(self):
    mark_generated_question_typical(7, "gq-1")
    self.assertEqual("PENDING_REVIEW", self.read_raw_review_status("gq-1"))
```

- [ ] **Step 2: Run and verify failure**

Run: `cd seclab-backend/ai-agent-service; python -m unittest test_teacher_repository_helpers.py test_teacher_api_errors.py -v`

Expected: FAIL because teaching-class filters and typical functions are absent.

- [ ] **Step 3: Implement the live record query**

Return `generatedQuestionId`, student, teaching class, course, knowledge point, question type, difficulty, title, stem, generation reason, standard answer, explanation, latest attempt, attempt count, generated time, and `isTypical`. Filters are `teachingClassId`, `courseId`, `knowledgePointId`, `studentId`, `answerResult`, `typicalOnly`, `dateFrom`, and `dateTo`.

Delete the teacher-facing review mutation and review-status filter from the endpoint contract. Keep underlying legacy JSON untouched for backward compatibility.

- [ ] **Step 4: Implement summary and typical endpoints**

Add:

```text
GET    /api/teacher/generated-questions/{generated_question_id}
PUT    /api/teacher/generated-questions/{generated_question_id}/typical
DELETE /api/teacher/generated-questions/{generated_question_id}/typical
GET    /api/teacher/teaching-classes/{teaching_class_id}/generated-question-summary
```

Summary rows include knowledge point, involved student count, generated question count, attempted count, incorrect count, incorrect rate, and representative existing question IDs.

- [ ] **Step 5: Run the AI service tests and commit**

```powershell
cd seclab-backend/ai-agent-service
python -m unittest discover -p "test_teacher_*.py" -v
git add -- teacher_repository.py main.py test_teacher_repository_helpers.py test_teacher_api_errors.py
git commit -m "feat(teacher): expose student training records"
```

Expected: PASS; every teacher can read questions from every teaching class, student callers return 403, and a missing question returns 404.

---

### Task 7: Implement manual latest-only class AI analysis

**Files:**
- Create: `seclab-backend/ai-agent-service/teacher_analysis_repository.py`
- Modify: `seclab-backend/ai-agent-service/teacher_ai_analysis_service.py`
- Modify: `seclab-backend/ai-agent-service/teacher_ai_prompts.py`
- Modify: `seclab-backend/ai-agent-service/main.py`
- Create: `seclab-backend/ai-agent-service/test_teacher_analysis_repository.py`
- Modify: `seclab-backend/ai-agent-service/test_teacher_ai_analysis_service.py`

**Interfaces:**
- Produces: `GET /api/teacher/teaching-classes/{id}/ai-analysis`.
- Produces: `POST /api/teacher/teaching-classes/{id}/ai-analysis`.
- Guarantees: no automatic invocation, one active run per class, last successful result retained on failure.

- [ ] **Step 1: Write failing state and evidence tests**

```python
def test_begin_analysis_rejects_second_running_request(self):
    repository.begin(101, requested_by=7, data_cutoff_at=self.cutoff)
    with self.assertRaises(AnalysisAlreadyRunningError):
        repository.begin(101, requested_by=7, data_cutoff_at=self.cutoff)

def test_failed_refresh_keeps_previous_successful_analysis(self):
    repository.save_success(101, 7, self.cutoff, {"overallComment": "旧结果"}, {"studentCount": 20})
    repository.begin(101, 7, self.new_cutoff)
    repository.save_failure(101, "AI 服务暂不可用")
    self.assertEqual("旧结果", repository.get_latest(101)["analysis"]["overallComment"])
```

- [ ] **Step 2: Run and verify failure**

Run: `cd seclab-backend/ai-agent-service; python -m unittest test_teacher_analysis_repository.py test_teacher_ai_analysis_service.py -v`

Expected: FAIL because repository state functions are absent.

- [ ] **Step 3: Implement current evidence collection**

Collect current teaching-class membership, arranged courses, experiment starts/completions/failures, hint requests, generated questions, attempts, repeated incorrect knowledge points, and representative existing question IDs. Return 422 when there are no students or no learning/training evidence.

- [ ] **Step 4: Tighten the AI contract**

Require JSON with this stable shape:

```json
{
  "overallComment": "本班当前最需要处理的问题",
  "commonProblems": [
    {
      "title": "引号闭合判断反复出错",
      "evidence": "涉及 11 名学生、19 次错误作答",
      "studentCount": 11,
      "questionIds": ["gq-1024"],
      "teacherAction": "下次课先复盘闭合判断，再安排 10 分钟随堂练习"
    }
  ]
}
```

Reject model output whose question IDs are not in the evidence set. Do not generate a local rule fallback.

- [ ] **Step 5: Implement latest-only persistence and HTTP errors**

`GET` allows any teacher to read the selected class analysis. `POST` checks that the current teacher owns the class, atomically begins, invokes analysis, stores success, and releases state on failure. A non-owner POST returns 403. `GET` returns `null` analysis when never run, plus `analysisStatus`, `generatedAt`, `dataCutoffAt`, and `lastErrorMessage`. Map already running to 409, data shortage to 422, and provider failure to 503.

- [ ] **Step 6: Run all teacher AI tests and commit**

```powershell
cd seclab-backend/ai-agent-service
python -m unittest discover -p "test_teacher_*.py" -v
git add -- teacher_analysis_repository.py teacher_ai_analysis_service.py teacher_ai_prompts.py main.py test_teacher_analysis_repository.py test_teacher_ai_analysis_service.py
git commit -m "feat(ai): add manual class teaching analysis"
```

Expected: PASS; no test expects automatic analysis or history snapshots.

---

### Task 8: Add typed frontend contracts and teacher-only navigation

**Files:**
- Create: `SecLab-FrontEnd-2/src/types/teacher.ts`
- Create: `SecLab-FrontEnd-2/src/api/teacher.ts`
- Modify: `SecLab-FrontEnd-2/src/api.ts`
- Create: `SecLab-FrontEnd-2/src/layout/Teacher/index.vue`
- Create: `SecLab-FrontEnd-2/src/layout/Teacher/Nav.vue`
- Modify: `SecLab-FrontEnd-2/src/router/router.ts`
- Modify: `SecLab-FrontEnd-2/src/auth.ts`

**Interfaces:**
- Consumes: Tasks 3-7 REST contracts.
- Produces: typed client functions and `/teacher` route shell.
- Consumed by: all new teacher pages.

- [ ] **Step 1: Define exact DTOs before page code**

```ts
export interface TeachingClassSummary {
  teachingClassId: number
  className: string
  academicYear: string
  semester: 1 | 2
  status: 'ACTIVE' | 'ARCHIVED'
  studentCount: number
  courseCount: number
  currentCourse: { courseId: number; courseName: string } | null
  lastActiveAt: string | null
}

export interface TeacherClassAnalysis {
  analysisStatus: 'IDLE' | 'RUNNING' | 'READY'
  generatedAt: string | null
  dataCutoffAt: string | null
  lastErrorMessage: string | null
  analysis: null | {
    overallComment: string
    commonProblems: Array<{
      title: string
      evidence: string
      studentCount: number
      questionIds: string[]
      teacherAction: string
    }>
  }
}
```

- [ ] **Step 2: Implement a focused teacher API module**

Expose named functions for teaching-class CRUD, import preview/confirm, class courses, generated-question list/detail/summary, typical mark/unmark, and class analysis get/run. Use `Authorization: Bearer` from the existing auth helper and `getApiErrorMessage` for server messages.

- [ ] **Step 3: Add teacher routes and compatibility redirects**

Use `/teacher/dashboard`, `/teacher/classes`, `/teacher/classes/:id`, `/teacher/training-records`, and `/teacher/courses`. Redirect legacy teacher visits from `/admin/*` to the matching teacher route; students remain blocked. Do not show global users or module management in teacher navigation.

- [ ] **Step 4: Run type checking before page implementation**

Run: `cd SecLab-FrontEnd-2; npm run vue-tsc`

Expected: PASS with the new DTOs and route shell; no page uses `any` for teacher contracts.

- [ ] **Step 5: Commit frontend contracts**

```powershell
git add -- SecLab-FrontEnd-2/src/types/teacher.ts SecLab-FrontEnd-2/src/api/teacher.ts SecLab-FrontEnd-2/src/api.ts SecLab-FrontEnd-2/src/layout/Teacher SecLab-FrontEnd-2/src/router/router.ts SecLab-FrontEnd-2/src/auth.ts
git commit -m "feat(frontend): add teacher workspace contracts"
```

---

### Task 9: Build teaching-class list, detail, import, and course arrangement UI

**Files:**
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingClasses/index.vue`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingClassDetail/index.vue`
- Modify: `SecLab-FrontEnd-2/src/pages/Admin/Courses/index.vue`
- Modify: `SecLab-FrontEnd-2/src/pages/Admin/Courses/create/create.vue`

**Interfaces:**
- Consumes: teaching-class, import, course catalog, and arrangement APIs.
- Produces: teacher workflow from class creation through course sequencing.

- [ ] **Step 1: Build the list around real term data**

Show a term selector, active/archived tabs, and cards with class name, responsible teacher, term, student count, course progress, current course, and recent activity. Use “创建教学班” as the primary action. Empty state text is “还没有本学期教学班” with a create action; never render test cards.

- [ ] **Step 2: Add the create/edit form**

Fields are class name, academic year, semester, start date, and end date. Display 409 name conflicts inline. For a non-owner, hide or disable edit/import/course-arrangement/archive/analysis actions and display “仅负责人可修改”. Archive requires a confirmation explaining that students and learning records remain available.

- [ ] **Step 3: Add Excel preview and confirmation**

The import dialog has four visible result groups: new accounts, existing accounts, duplicate rows, and errors. Disable confirmation whenever `errorRows.length > 0`. On success display created accounts, added members, skipped members, and the initial-password rule `123456`.

- [ ] **Step 4: Add ordered course arrangement**

Allow selection from existing courses, ordering with up/down controls, and setting planned start/end dates. A class can contain many courses. Link “新建课程” to the existing course creation page, then return to the class detail without automatically selecting the new course.

- [ ] **Step 5: Verify responsive and error states**

Run:

```powershell
cd SecLab-FrontEnd-2
npm run vue-tsc
npm run build
```

Expected: PASS; list works at 375 px and desktop widths; loading, empty, 403, 409, and network error states are visible.

- [ ] **Step 6: Commit teaching-class UI**

```powershell
git add -- SecLab-FrontEnd-2/src/pages/Teacher/TeachingClasses SecLab-FrontEnd-2/src/pages/Teacher/TeachingClassDetail SecLab-FrontEnd-2/src/pages/Admin/Courses
git commit -m "feat(frontend): add teaching class workflow"
```

---

### Task 10: Build live training records, typical questions, dashboard, and manual analysis UI

**Files:**
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TrainingRecords/index.vue`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/Dashboard/index.vue`
- Modify or retire route usage: `SecLab-FrontEnd-2/src/pages/Admin/GeneratedQuestions/index.vue`
- Modify or retire route usage: `SecLab-FrontEnd-2/src/pages/Admin/ClassProfile/index.vue`
- Modify or retire route usage: `SecLab-FrontEnd-2/src/pages/Admin/DashBoard/index.vue`

**Interfaces:**
- Consumes: live generated-question list/summary, typical marks, teaching-class current stats, and manual AI analysis.
- Produces: the complete teacher-facing analysis experience.

- [ ] **Step 1: Replace review language with training-record language**

Filters are teaching class, course, knowledge point, student, answer result, date range, and typical-only. Remove “待审核、通过、驳回、需要修改” labels and controls. Detail shows generation reason, question, answer, explanation, student response, score, and attempt time.

- [ ] **Step 2: Implement typical-question interaction**

Use “标记为典型题” and “取消典型题”. Update only after the API succeeds; on failure retain the prior state and show the backend message. A dedicated typical-only filter is sufficient; do not add a new top-level collection page.

- [ ] **Step 3: Build the teacher dashboard around current work**

Show current-term teaching classes, student count, current/next course, course progress, recent generated questions, repeated failures, and shortcuts for class creation, import, and course arrangement. Remove profile average, high-score ranking, and automatic AI request on mount.

- [ ] **Step 4: Implement the explicit analysis state machine**

Before first analysis, show explanatory copy and a “开始分析” button. While running, disable the button and show progress. For READY, show overall comment, evidence-backed common problems, representative question links, generated time, and data cutoff. “重新分析” calls POST only after a teacher click. On 503, keep the previous result on screen and show the error above it.

- [ ] **Step 5: Run frontend verification**

Run:

```powershell
cd SecLab-FrontEnd-2
npm run vue-tsc
npm run build
```

Expected: PASS; opening dashboard does not issue an AI-analysis POST; training records appear after a normal GET refresh.

- [ ] **Step 6: Commit the teacher experience**

```powershell
git add -- SecLab-FrontEnd-2/src/pages/Teacher SecLab-FrontEnd-2/src/pages/Admin/GeneratedQuestions/index.vue SecLab-FrontEnd-2/src/pages/Admin/ClassProfile/index.vue SecLab-FrontEnd-2/src/pages/Admin/DashBoard/index.vue
git commit -m "feat(frontend): add teacher training insights"
```

---

### Task 11: Remove polluted demo data and seed a realistic teaching scenario

**Files:**
- Create: `数据库文件/teacher_realistic_data_reset.sql`
- Create: `数据库文件/seed_realistic_teacher_data.sql`
- Modify: `database/sql/teacher-scope-test-seed.sql`

**Interfaces:**
- Produces: clean default data without acceptance users, permission-test classes, demo classes, or malformed class names.
- Consumed by: final end-to-end verification and project demonstration.

- [ ] **Step 1: Write the preview section before destructive statements**

```sql
SELECT 'student_users' AS category, COUNT(*) AS affected
FROM `userservice`.`user` WHERE `user_role` = 'STUDENT'
UNION ALL
SELECT 'legacy_classes', COUNT(*) FROM `userservice`.`class`
UNION ALL
SELECT 'profile_snapshots', COUNT(*) FROM `seclab_profile`.`student_profile_snapshot`
UNION ALL
SELECT 'generated_questions', COUNT(*) FROM `seclab_profile`.`generated_question`
UNION ALL
SELECT 'learning_events', COUNT(*) FROM `seclab_profile`.`learning_event`;
```

Require the operator to save this output and take a database backup before executing the transaction section.

- [ ] **Step 2: Implement foreign-key-safe cleanup**

Delete child records before parents inside an explicit transaction. Preserve `userservice.course`, module/course links, experiment resources, images, and users with `user_role = 'TEACHER'`. Delete teacher analysis and typical marks before generated questions. Do not use `DROP DATABASE` or `TRUNCATE`.

- [ ] **Step 3: Seed a small realistic dataset**

Create two teachers, two active teaching classes with different owners in the current term, 8-12 students per class, shared courses created by different teachers and arranged in two-week blocks, and coherent learning events/generated questions/attempts that support at least two common problems. Use normal Chinese names and student numbers; avoid words such as “演示、测试、验收、权限、未命名”.

- [ ] **Step 4: Keep authorization fixtures isolated**

Retain `teacher-scope-test-seed.sql` for automated permission checks only. Add a header stating it is not part of default initialization, and ensure startup scripts do not load it automatically.

- [ ] **Step 5: Verify cleanup and seed in the disposable MySQL container**

Run schema initialization, seed, cleanup, and seed again. Expected: no FK errors; two teaching classes exist; all displayed names pass the prohibited-word check; courses remain intact after cleanup.

- [ ] **Step 6: Commit data cleanup separately**

```powershell
git add -- '数据库文件/teacher_realistic_data_reset.sql' '数据库文件/seed_realistic_teacher_data.sql' 'database/sql/teacher-scope-test-seed.sql'
git commit -m "chore(db): replace polluted teacher demo data"
```

Do not run the cleanup against the user's working database until the saved preview counts and backup location have been reviewed.

---

### Task 12: Run end-to-end contract and regression verification

**Files:**
- Modify: `SecLab系统部署说明文档.md`
- Modify: `seclab-backend/ai-agent-service/test_teacher_api_errors.py`
- Create: `docs/teacher-workspace-verification.md`

**Interfaces:**
- Verifies: database, authentication, global visibility, owner-only mutations, shared-course creator permissions, import, course arrangement, live training records, typical marks, and manual analysis.

- [ ] **Step 1: Add API contract tests for the complete teacher journey**

Cover these exact cases: teacher A creates a class; teacher B can read it but gets 403 when changing its students, courses, analysis, or archive state; teacher B can select teacher A's course but gets 403 when editing/deleting it; a student gets 403; preview with an invalid row cannot confirm; valid import creates accounts with encoded `123456`; repeated import is idempotent; a class accepts multiple shared courses; a generated question becomes visible without a copy operation; a typical mark is teacher-specific; AI POST runs only when the owner calls it; failed refresh retains previous analysis.

- [ ] **Step 2: Run all focused verification commands**

```powershell
cd D:\SecLab\SecLab-FrontEnd-2
npm run vue-tsc
npm run build

cd D:\Seclab-team\SecLab-Team\seclab-backend
.\gradlew.bat :user-service:test
.\gradlew.bat :user-service:build
.\gradlew.bat :experiment-module-service:test
.\gradlew.bat :experiment-module-service:build

cd D:\Seclab-team\SecLab-Team\seclab-backend\ai-agent-service
python -m unittest discover -p "test_teacher_*.py" -v
```

Expected: all commands exit 0.

- [ ] **Step 3: Perform the browser smoke test**

Start the documented local services, log in as the seeded teacher, create a temporary teaching class, import the workbook, arrange three courses, verify a student-generated question appears in training records, mark it typical, open the class analysis empty state, click “开始分析”, and verify the latest result displays evidence and a representative question link.

- [ ] **Step 4: Document observed results and known limits**

Record command output summaries, tested account role, tested teaching class, API error cases, and the fact that no scheduler/history/push system exists. Include the cleanup preview and backup prerequisite.

- [ ] **Step 5: Commit documentation and final regression coverage**

```powershell
git add -- SecLab系统部署说明文档.md seclab-backend/ai-agent-service/test_teacher_api_errors.py docs/teacher-workspace-verification.md
git commit -m "docs: verify teacher teaching workflow"
```

---

## Completion Checklist

- [ ] Database schema, runtime mirrors, indexes, defaults, and migrations are synchronized.
- [ ] Teacher identity no longer depends on legacy class ownership.
- [ ] Every teacher can read every teaching class; class mutations and AI refresh are owner-only.
- [ ] Every teacher can use every course; course edit/delete operations are creator-only.
- [ ] Teaching class CRUD, import, course arrangement, and permission errors are tested.
- [ ] Generated questions are live records rather than an approval queue.
- [ ] Typical-question marking is teacher-specific and non-destructive.
- [ ] AI analysis is manual, evidence-backed, latest-only, and preserves the last success on failure.
- [ ] Teacher navigation contains no global user-management or standalone module-management entry.
- [ ] Polluted default student/class/analysis data is removed only after preview and backup.
- [ ] Frontend type check/build, Gradle service tests/builds, Python tests, and browser smoke test pass.
