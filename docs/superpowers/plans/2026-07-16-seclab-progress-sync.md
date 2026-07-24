# SecLab Progress Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Import the verified functional progress from `D:\SecLab` into the Git repository while preserving the target repository's `seclab-backend` layout and cleanup decisions.

**Architecture:** Treat `D:\SecLab` as a read-only implementation source and `D:\Seclab-team\SecLab-Team` as the only write target. Import by vertical slice—database, Kotlin services, Python analysis service, frontend, then documentation—using exact path mappings and focused regression tests instead of mirroring directories.

**Tech Stack:** Vue 3, Vite, TypeScript, Kotlin, Spring Boot, Gradle, Python, unittest, MySQL SQL, Git.

## Global Constraints

- Preserve the target `seclab-backend` directory; map source `seclab\seclab` paths into it.
- Use `apply_patch` for every text edit; copy a source binary only after hashing it, and use `git mv` only for a hash-proven binary rename.
- Do not import dependencies, builds, caches, logs, `.env` files, secrets, uploads, output reports, or one-off repair scripts.
- Preserve target-only files unless they are verified mojibake duplicates of correctly named source assets.
- Keep demo and authorization-test data in standalone SQL files, not in production initialization data.
- Do not weaken backend authorization or replace real APIs with frontend mocks.
- Commit each task independently after its focused verification passes.

---

## File Structure

- `database/sql/`: canonical schema, service-local initialization, standalone demo data, and schema assertions.
- `seclab-backend/user-service/`: teacher identity, teaching-class ownership, import, membership, and course arrangement.
- `seclab-backend/experiment-module-service/`: shared course visibility and creator-only mutation rules.
- `seclab-backend/ai-agent-service/`: teacher-scoped generated-question data and latest-only class/student analysis.
- `SecLab-FrontEnd-2/src/layout/Teacher/`: teacher navigation shell.
- `SecLab-FrontEnd-2/src/pages/Teacher/`: overview, teaching classes, teaching analysis, generated questions, and course library.
- `docs/superpowers/`: imported source specifications/plans plus this sync record.

### Task 1: Import and adapt the canonical teaching schema

**Files:**
- Create: `database/sql/teacher_teaching_class.sql`
- Create: `database/sql/reset_and_seed_teacher_demo.sql`
- Create: `database/sql/seed_teacher_showcase.sql`
- Create: `database/sql/test_teacher_teaching_class_schema.py`
- Modify: `database/sql/init_seclab_db.sql`
- Modify: `database/sql/init_seclab_profile.sql`
- Modify: `database/sql/user-service-local-init.sql`
- Modify: `database/sql/experiment-module-service-local-init.sql`

**Interfaces:**
- Consumes: source SQL from `D:\SecLab\数据库文件` and `D:\SecLab\database\sql`.
- Produces: `user_role`, `created_by`, `teaching_class`, `teaching_class_student`, `teaching_class_course`, `teaching_class_import_batch`, `teacher_typical_question`, `teacher_class_analysis`, and `teacher_student_analysis` structures used by later tasks.

- [ ] **Step 1: Add the schema assertion with the target canonical path**

Import `D:\SecLab\database\sql\test_teacher_teaching_class_schema.py`, then change its canonical path to:

```python
ROOT = Path(__file__).resolve().parents[2]
CANONICAL_SCHEMA = ROOT / "database" / "sql" / "teacher_teaching_class.sql"
```

- [ ] **Step 2: Run the schema assertion and record the expected baseline failure**

Run: `python database/sql/test_teacher_teaching_class_schema.py`

Expected before schema import: FAIL because `database/sql/teacher_teaching_class.sql` is missing or required fields/tables are absent.

- [ ] **Step 3: Import the canonical and runtime SQL using exact source content**

Use `apply_patch` to import these source artifacts, changing only the destination path and references to the removed `数据库文件` directory:

```text
D:\SecLab\数据库文件\teacher_teaching_class.sql
  -> database/sql/teacher_teaching_class.sql
D:\SecLab\数据库文件\reset_and_seed_teacher_demo.sql
  -> database/sql/reset_and_seed_teacher_demo.sql
D:\SecLab\数据库文件\seed_teacher_showcase.sql
  -> database/sql/seed_teacher_showcase.sql
D:\SecLab\database\sql\init_seclab_db.sql
  -> database/sql/init_seclab_db.sql
D:\SecLab\database\sql\init_seclab_profile.sql
  -> database/sql/init_seclab_profile.sql
D:\SecLab\database\sql\user-service-local-init.sql
  -> database/sql/user-service-local-init.sql
D:\SecLab\database\sql\experiment-module-service-local-init.sql
  -> database/sql/experiment-module-service-local-init.sql
```

- [ ] **Step 4: Verify schema mirrors and isolation of demo data**

Run: `python database/sql/test_teacher_teaching_class_schema.py`

Expected: all tests PASS. Confirm the two demo scripts remain standalone and are not sourced automatically by production initialization.

- [ ] **Step 5: Commit the database slice**

```powershell
git add database/sql
git commit -m "feat: sync teacher teaching schema"
```

### Task 2: Import teacher identity and teaching-class ownership

**Files:**
- Modify: `seclab-backend/user-service/build.gradle.kts`
- Modify: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/entity/UserEntity.kt`
- Modify: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/repository/UserRepository.kt`
- Modify: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/service/UserService.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/entity/UserRole.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/entity/TeachingClassEntity.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/entity/TeachingClassStudentEntity.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/entity/TeachingClassCourseEntity.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/entity/TeachingClassImportBatchEntity.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/dto/TeachingClassDtos.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/repository/TeachingClassRepositories.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/service/CurrentUserService.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/service/TeacherTeachingClassService.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/service/TeachingClassImportService.kt`
- Create: `seclab-backend/user-service/src/main/kotlin/me/myot233/seclab/userservice/controller/TeacherTeachingClassController.kt`
- Create: `seclab-backend/user-service/src/test/kotlin/me/myot233/seclab/userservice/service/CurrentUserServiceTest.kt`
- Create: `seclab-backend/user-service/src/test/kotlin/me/myot233/seclab/userservice/service/TeacherTeachingClassServiceTest.kt`
- Create: `seclab-backend/user-service/src/test/kotlin/me/myot233/seclab/userservice/service/TeachingClassImportServiceTest.kt`
- Create: `seclab-backend/user-service/src/test/kotlin/me/myot233/seclab/userservice/service/TeachingClassCourseServiceTest.kt`

**Interfaces:**
- Consumes: Task 1 schema and the existing JWT/authentication context.
- Produces: teacher-scoped `/api/teacher/teaching-classes` CRUD, import, member, and course-arrangement APIs.

- [ ] **Step 1: Import the focused tests before production code**

Use `apply_patch` with exact content from the four matching source test files under `D:\SecLab\seclab\seclab\user-service\src\test`. Keep package names unchanged.

- [ ] **Step 2: Run the tests and verify the missing implementation baseline**

Run from `seclab-backend/user-service`:

```powershell
.\gradlew.bat test --tests "*CurrentUserServiceTest" --tests "*TeacherTeachingClassServiceTest" --tests "*TeachingClassImportServiceTest" --tests "*TeachingClassCourseServiceTest" --console=plain
```

Expected before production import: compilation failure for missing teacher-class types.

- [ ] **Step 3: Import entities, DTOs, repositories, services, controller, and dependency changes**

For every file listed in this task, use the exact corresponding source implementation under `D:\SecLab\seclab\seclab\user-service`, mapped into `seclab-backend/user-service`. Preserve the target's path layout and normalize text files to UTF-8.

- [ ] **Step 4: Verify owner-scoped reads, writes, import idempotency, and course ordering**

Run the focused Gradle command from Step 2.

Expected: PASS, including cross-teacher denial, duplicate-import idempotency, and course arrangement validation.

- [ ] **Step 5: Commit the user-service slice**

```powershell
git add seclab-backend/user-service
git commit -m "feat: sync teacher teaching classes"
```

### Task 3: Import shared-course creator permissions

**Files:**
- Modify: `seclab-backend/experiment-module-service/src/main/kotlin/me/myot233/seclab/experimentmoduleservice/controller/CourseController.kt`
- Modify: `seclab-backend/experiment-module-service/src/main/kotlin/me/myot233/seclab/experimentmoduleservice/dto/CatalogDtos.kt`
- Modify: `seclab-backend/experiment-module-service/src/main/kotlin/me/myot233/seclab/experimentmoduleservice/entity/CourseEntity.kt`
- Modify: `seclab-backend/experiment-module-service/src/main/kotlin/me/myot233/seclab/experimentmoduleservice/service/CatalogAuthService.kt`
- Modify: `seclab-backend/experiment-module-service/src/main/kotlin/me/myot233/seclab/experimentmoduleservice/service/CatalogQueryService.kt`
- Create: `seclab-backend/experiment-module-service/src/test/kotlin/me/myot233/seclab/experimentmoduleservice/service/CatalogAuthServiceTest.kt`
- Create: `seclab-backend/experiment-module-service/src/test/kotlin/me/myot233/seclab/experimentmoduleservice/service/CoursePermissionTest.kt`

**Interfaces:**
- Consumes: `course.created_by` from Task 1 and current-user headers/token context.
- Produces: globally readable courses with creator-only update/delete semantics.

- [ ] **Step 1: Import the two permission tests**

Use exact source content from `D:\SecLab\seclab\seclab\experiment-module-service\src\test`.

- [ ] **Step 2: Run tests and confirm the permission baseline fails**

Run from `seclab-backend/experiment-module-service`:

```powershell
.\gradlew.bat test --tests "*CatalogAuthServiceTest" --tests "*CoursePermissionTest" --console=plain
```

Expected before implementation import: FAIL because creator-aware authorization is absent.

- [ ] **Step 3: Import the five production changes**

Use `apply_patch` with exact source content from the corresponding source paths. Do not import unrelated Gradle wrapper, IDE, or build-output differences.

- [ ] **Step 4: Run focused tests and module build**

Run the command from Step 2, then run `.\gradlew.bat build --console=plain`.

Expected: PASS.

- [ ] **Step 5: Commit the course-permission slice**

```powershell
git add seclab-backend/experiment-module-service
git commit -m "feat: sync shared course permissions"
```

### Task 4: Import teacher-scoped AI analysis

**Files:**
- Create: `seclab-backend/ai-agent-service/teacher_analysis_repository.py`
- Create: `seclab-backend/ai-agent-service/test_teacher_analysis_repository.py`
- Modify: `seclab-backend/ai-agent-service/main.py`
- Modify: `seclab-backend/ai-agent-service/teacher_repository.py`
- Modify: `seclab-backend/ai-agent-service/teacher_ai_analysis_service.py`
- Modify: `seclab-backend/ai-agent-service/teacher_ai_prompts.py`
- Modify: `seclab-backend/ai-agent-service/test_teacher_ai_analysis_service.py`
- Modify: `seclab-backend/ai-agent-service/test_teacher_api_errors.py`
- Modify: `seclab-backend/ai-agent-service/test_teacher_repository_helpers.py`

**Interfaces:**
- Consumes: teacher/class/student membership from Tasks 1–2 and existing training/event repositories.
- Produces: teacher-scoped generated-question queries and latest-only class/student analysis APIs with controlled errors.

- [ ] **Step 1: Import repository and service tests first**

Use `apply_patch` with the exact five matching `test_teacher*.py` files from `D:\SecLab\seclab\seclab\ai-agent-service`.

- [ ] **Step 2: Run the teacher test suite and record failures**

Run from `seclab-backend/ai-agent-service`:

```powershell
python -m unittest test_teacher_analysis_repository.py test_teacher_ai_analysis_service.py test_teacher_api_errors.py test_teacher_repository_helpers.py
```

Expected before implementation import: failures for the missing repository and new analysis/scope behavior.

- [ ] **Step 3: Import the repository, HTTP integration, analysis service, prompts, and query changes**

Use the exact source implementations from `D:\SecLab\seclab\seclab\ai-agent-service`. Preserve target `.env.example` and dependency policy; do not copy secrets or local environment files.

- [ ] **Step 4: Verify tests and Python syntax**

```powershell
python -m unittest test_teacher_analysis_repository.py test_teacher_ai_analysis_service.py test_teacher_api_errors.py test_teacher_repository_helpers.py
python -m py_compile main.py teacher_repository.py teacher_analysis_repository.py teacher_ai_analysis_service.py teacher_ai_prompts.py
```

Expected: PASS with no syntax errors.

- [ ] **Step 5: Commit the AI-service slice**

```powershell
git add seclab-backend/ai-agent-service
git commit -m "feat: sync teacher analysis service"
```

### Task 5: Import typed teacher frontend and navigation

**Files:**
- Create: `SecLab-FrontEnd-2/src/layout/Teacher/index.vue`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/teacher-page.css`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/Overview/index.vue`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingClasses/index.vue`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/index.vue`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/GeneratedQuestions/index.vue`
- Create: `SecLab-FrontEnd-2/src/pages/Teacher/CourseLibrary/index.vue`
- Create: `SecLab-FrontEnd-2/public/templates/教学班学生导入模板.xlsx`
- Create: `SecLab-FrontEnd-2/scripts/teacher-api-response-regression.mjs`
- Modify: `SecLab-FrontEnd-2/src/api.ts`
- Modify: `SecLab-FrontEnd-2/src/auth.ts`
- Modify: `SecLab-FrontEnd-2/src/App.vue`
- Modify: `SecLab-FrontEnd-2/src/router/router.ts`
- Modify: `SecLab-FrontEnd-2/src/types/course.ts`

**Interfaces:**
- Consumes: APIs from Tasks 2–4.
- Produces: teacher navigation and responsive pages for overview, classes, analysis, generated questions, and courses.

- [ ] **Step 1: Import the API response regression script and run the baseline**

Use exact source content for `scripts/teacher-api-response-regression.mjs`.

Run from `SecLab-FrontEnd-2`: `node scripts/teacher-api-response-regression.mjs`

Expected before frontend API import: FAIL for missing or mismatched teacher API response handling.

- [ ] **Step 2: Import shared contracts, auth, routing, and application-shell changes**

Use `apply_patch` with exact content from the five corresponding files in `D:\SecLab\SecLab-FrontEnd-2`. Verify teacher routes point to `src/pages/Teacher`, not legacy admin pages.

- [ ] **Step 3: Import the seven teacher UI files and Excel template**

Use exact source content for all Vue/CSS files. Import and verify the XLSX template byte-for-byte:

```powershell
$source = 'D:\SecLab\SecLab-FrontEnd-2\public\templates\教学班学生导入模板.xlsx'
$target = 'D:\Seclab-team\SecLab-Team\SecLab-FrontEnd-2\public\templates\教学班学生导入模板.xlsx'
Copy-Item -LiteralPath $source -Destination $target
if ((Get-FileHash -LiteralPath $source).Hash -ne (Get-FileHash -LiteralPath $target).Hash) { throw 'XLSX hash mismatch' }
```

- [ ] **Step 4: Run frontend regression, type checking, and build**

```powershell
node scripts/teacher-api-response-regression.mjs
npm run vue-tsc
npm run build
```

Expected: all commands succeed. Existing non-blocking Browserslist, `/pattern.svg`, or chunk-size warnings may remain, but no new type/build error is allowed.

- [ ] **Step 5: Commit the teacher frontend slice**

```powershell
git add SecLab-FrontEnd-2/src SecLab-FrontEnd-2/scripts SecLab-FrontEnd-2/public/templates
git commit -m "feat: sync teacher frontend workspace"
```

### Task 6: Repair mojibake course asset names

**Files:**
- Create: the 12 correctly named PNG files under `SecLab-FrontEnd-2/public/` from `D:\SecLab\SecLab-FrontEnd-2\public`.
- Delete: the 12 mojibake-named PNG duplicates currently under `SecLab-FrontEnd-2/public/`.

**Interfaces:**
- Consumes: course image paths referenced by frontend course data.
- Produces: stable UTF-8 Chinese asset names with no duplicate payloads.

- [ ] **Step 1: Prove each source asset matches one target mojibake asset by SHA-256**

Run a PowerShell hash comparison over the 12 source PNGs and 12 target-only PNGs.

Expected: a one-to-one hash match for every pair before renaming.

- [ ] **Step 2: Rename verified binary assets and verify references**

For each one-to-one hash match, run `git mv -- <mojibake-target-path> <correct-Chinese-target-path>`. Do not copy a second payload. Search `SecLab-FrontEnd-2/src` for all 12 image references and confirm every referenced file exists.

- [ ] **Step 3: Re-run the frontend build**

Run from `SecLab-FrontEnd-2`: `npm run build`

Expected: PASS with no missing course-image error.

- [ ] **Step 4: Commit the asset repair**

```powershell
git add SecLab-FrontEnd-2/public
git commit -m "fix: restore readable course asset names"
```

### Task 7: Restore implementation documentation without generated outputs

**Files:**
- Create: `docs/superpowers/specs/2026-07-13-generated-question-controls-design.md`
- Create: `docs/superpowers/specs/2026-07-14-teacher-teaching-class-design.md`
- Create: `docs/superpowers/specs/2026-07-15-teacher-analysis-and-scope-design.md`
- Create: `docs/superpowers/plans/2026-07-13-generated-question-controls.md`
- Create: `docs/superpowers/plans/2026-07-14-teacher-teaching-class.md`
- Create: `docs/superpowers/plans/2026-07-15-teacher-analysis-and-scope.md`

**Interfaces:**
- Consumes: source design history under `D:\SecLab\docs\superpowers`.
- Produces: repository-local rationale and implementation history using the target backend path.

- [ ] **Step 1: Import the six Markdown files**

Use exact source content, then replace repository path references:

```text
seclab-backend/ -> seclab-backend/
D:\SecLab\seclab\seclab -> D:\Seclab-team\SecLab-Team\seclab-backend
```

- [ ] **Step 2: Verify no removed output directory or obsolete backend path remains**

Search the six imported files for `outputs/`, `seclab-backend/`, and `D:\SecLab\seclab\seclab`.

Expected: no obsolete implementation path; historical prose may mention source context only when explicitly labelled as historical.

- [ ] **Step 3: Commit restored documentation**

```powershell
git add docs/superpowers
git commit -m "docs: restore SecLab feature history"
```

### Task 8: Run full synchronization verification

**Files:**
- Modify only if verification reveals an integration defect in a file imported by Tasks 1–7.

**Interfaces:**
- Consumes: all prior task outputs.
- Produces: a clean, tested Git worktree containing only approved progress.

- [ ] **Step 1: Run repository hygiene checks**

```powershell
git diff --check origin/main..HEAD
git status --short
git ls-files | Select-String -Pattern '(^|/)(node_modules|dist|build|bin|\.gradle|__pycache__|outputs)(/|$)|(^|/)\.env$|\.log$'
```

Expected: no patch errors, no unexpected worktree changes, and no forbidden new tracked artifacts.

- [ ] **Step 2: Run all automated verification**

```powershell
python database/sql/test_teacher_teaching_class_schema.py
cd seclab-backend/user-service
.\gradlew.bat test --console=plain
cd ..\experiment-module-service
.\gradlew.bat test --console=plain
cd ..\ai-agent-service
python -m unittest discover -p "test_teacher*.py"
cd ..\..\SecLab-FrontEnd-2
node scripts/teacher-api-response-regression.mjs
npm run vue-tsc
npm run build
```

Expected: PASS, except external-service checks explicitly documented as unavailable.

- [ ] **Step 3: Compare approved source and target deltas**

Re-run normalized hash comparison for the approved file set. Expected differences are limited to target path adaptations, canonical SQL path changes, documentation path changes, and line-ending normalization.

- [ ] **Step 4: Review the final Git diff and commit any verification-only correction**

If verification required a correction, stage only the affected imported file and commit with a focused `fix:` message. Otherwise create no empty commit.

- [ ] **Step 5: Record handoff results**

Report changed files by subsystem, every command executed and its result, database/interface/event/log/error-handling impact, external checks not run, and remaining risks.
