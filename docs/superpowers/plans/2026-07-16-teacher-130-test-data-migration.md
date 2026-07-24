# Teacher 130-Person Test Data Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Safely add the supplied 130-person teacher test dataset to the current databases without deleting existing accounts or history, then make the migration reproducible from the repository.

**Architecture:** Keep schema migration, seed data, static safety tests, live migration orchestration, and operator documentation as separate units. The seed uses stable student numbers and the `teacher-demo-20260716-` prefix as ownership boundaries; existing student primary keys are preserved through upserts, while the PowerShell runner enforces preflight checks, backups, import ordering, and post-import verification.

**Tech Stack:** MySQL 9.6 SQL, Python 3 `unittest`, PowerShell 7/Windows PowerShell, Git.

## Global Constraints

- Import directly into the current `userservice` and `seclab_profile` databases so the data is visible in the existing application.
- Preserve all existing non-dataset data and preserve the `user_id` values of the 32 existing students in the managed number range.
- Never execute `reset_and_seed_teacher_demo.sql` or `seed_teacher_showcase.sql` during this migration.
- Never commit database backups, logs, credentials, or MySQL data-directory files.
- Back up both target databases before any database mutation.
- The migration must be repeatable without increasing managed row counts.
- Do not print or place database passwords on command lines.

---

### Task 1: Add the seed safety contract

**Files:**
- Create: `database/sql/test_teacher_130_data_seed.py`
- Test: `database/sql/test_teacher_130_data_seed.py`

**Interfaces:**
- Consumes: repository path and the planned `database/sql/seed_teacher_130_data.sql` file.
- Produces: a static regression suite that defines destructive-statement, identity, row-count, transaction, and idempotency requirements.

- [ ] **Step 1: Write the failing static test**

Create a `unittest.TestCase` that loads the seed as UTF-8 and asserts all of the following:

```python
STUDENT_NUMBERS = set(re.findall(r"202321040(?:5\d{2}|6[0-2]\d|630)", sql))
self.assertEqual(130, len(STUDENT_NUMBERS))
self.assertNotRegex(sql, re.compile(r"DELETE\s+FROM\s+`userservice`\.`user`", re.I))
self.assertNotRegex(sql, re.compile(r"\b(?:TRUNCATE|DROP\s+TABLE(?!\s+IF\s+EXISTS\s+`demo_))\b", re.I))
self.assertIn("teacher-demo-20260716-%", sql)
self.assertIn("ON DUPLICATE KEY UPDATE", sql)
self.assertIn("START TRANSACTION", sql)
self.assertIn("COMMIT", sql)
self.assertIn("T20260001", sql)
```

Also assert that every persistent `DELETE` targets only a `teacher-demo-20260716-%` identifier, and that temporary-table drops are restricted to `demo_students` and `demo_question_templates`.

- [ ] **Step 2: Run the test and confirm the red state**

Run:

```powershell
python database/sql/test_teacher_130_data_seed.py
```

Expected: FAIL because `database/sql/seed_teacher_130_data.sql` does not exist.

- [ ] **Step 3: Commit the test contract**

```powershell
git add database/sql/test_teacher_130_data_seed.py
git commit -m "test: define teacher 130 data seed safety"
```

### Task 2: Build the safe, idempotent 130-person seed

**Files:**
- Create: `database/sql/seed_teacher_130_data.sql`
- Test: `database/sql/test_teacher_130_data_seed.py`

**Interfaces:**
- Consumes: `seed_teacher_130_data.sql` from the supplied archive, existing `userservice`/`seclab_profile` schemas, course IDs 1 through 8.
- Produces: one transactional seed that owns only the 130-number range and `teacher-demo-20260716-*` records while preserving existing primary keys.

- [ ] **Step 1: Extract the supplied seed into a staging directory**

Use `tar -xf` with the archive path and extract only `数据库文件/seed_teacher_130_data.sql` into a workspace staging directory. Copy that file to `database/sql/seed_teacher_130_data.sql`; do not add the archive or staging directory to Git.

- [ ] **Step 2: Remove destructive account and relationship replacement**

Delete this statement entirely:

```sql
DELETE FROM `userservice`.`user`
WHERE `user_student_number` BETWEEN '202321040501' AND '202321040630';
```

Delete the unconditional teaching-class course replacement:

```sql
DELETE FROM `userservice`.`teaching_class_course`
WHERE `teaching_class_id` = @teaching_class_id;
```

Keep only deletes whose predicates contain `teacher-demo-20260716-%`.

- [ ] **Step 3: Make teacher and student identities idempotent**

Before resolving `@teacher_id`, insert the missing `T20260001` test teacher using the same user columns and password representation already used by the supplied demo SQL. Finish with:

```sql
ON DUPLICATE KEY UPDATE
  `user_role` = 'TEACHER',
  `is_deleted` = 0;
```

Finish the 130-student insert with updates to display/profile columns only. Do not assign `user_id` in the update clause:

```sql
ON DUPLICATE KEY UPDATE
  `user_name` = VALUES(`user_name`),
  `user_gender` = VALUES(`user_gender`),
  `user_academy` = VALUES(`user_academy`),
  `class_id_class_id` = VALUES(`class_id_class_id`),
  `user_role` = 'STUDENT',
  `is_deleted` = 0;
```

Resolve `@teacher_id`, `@admin_class_id`, and `@teaching_class_id` after their prerequisite rows exist.

- [ ] **Step 4: Make class relationships idempotent**

Retain the teaching-class upsert, reselect `@teaching_class_id` after it, retain student membership upsert, and finish the eight course rows with:

```sql
ON DUPLICATE KEY UPDATE
  `teaching_order` = VALUES(`teaching_order`),
  `planned_start_date` = VALUES(`planned_start_date`),
  `planned_end_date` = VALUES(`planned_end_date`),
  `updated_at` = VALUES(`updated_at`);
```

- [ ] **Step 5: Run the static test and confirm green**

```powershell
python database/sql/test_teacher_130_data_seed.py
```

Expected: all seed safety tests PASS.

- [ ] **Step 6: Commit the safe dataset**

```powershell
git add database/sql/seed_teacher_130_data.sql
git commit -m "feat: add safe teacher 130 test dataset"
```

### Task 3: Add live verification and migration orchestration

**Files:**
- Create: `database/sql/verify_teacher_130_data.sql`
- Create: `database/sql/migrate_teacher_130_test_data.ps1`
- Modify: `database/sql/test_teacher_130_data_seed.py`

**Interfaces:**
- Consumes: MySQL client directory, `MYSQL_USER` and `MYSQL_PWD`, canonical schema SQL, and safe seed SQL.
- Produces: timestamped backups outside Git, ordered migration execution, and machine-checkable postconditions.

- [ ] **Step 1: Extend the failing static contract for the runner**

Assert that the runner references all required artifacts and operations:

```python
self.assertIn("mysqldump", runner)
self.assertIn("teacher_teaching_class.sql", runner)
self.assertIn("seed_teacher_130_data.sql", runner)
self.assertIn("verify_teacher_130_data.sql", runner)
self.assertIn("MYSQL_PWD", runner)
self.assertNotRegex(runner, re.compile(r"--password=", re.I))
```

Run the test and expect FAIL because the runner and verifier do not exist.

- [ ] **Step 2: Create the verification SQL**

Return named values for these exact postconditions:

```sql
SELECT 'managed_students', COUNT(*)
FROM `userservice`.`user`
WHERE `user_student_number` BETWEEN '202321040501' AND '202321040630';

SELECT 'managed_teachers', COUNT(*)
FROM `userservice`.`user`
WHERE `user_student_number` = 'T20260001'
  AND `user_role` = 'TEACHER';
```

Add equivalent named queries for 130 class memberships, 8 course relationships, and zero orphan rows across teaching-class and prefixed profile data.

- [ ] **Step 3: Create the fail-fast PowerShell runner**

The runner must:

1. Resolve `mysql.exe` and `mysqldump.exe` from `-MySqlBin`.
2. Require `MYSQL_USER` and `MYSQL_PWD` without printing either value.
3. Run read-only preflight queries for schemas, base tables, admin class, and courses 1 through 8.
4. Create a timestamped backup directory outside the Git worktree.
5. Dump `userservice` and `seclab_profile`; stop if either command exits nonzero or creates an empty file.
6. Capture the current `user_id` values for the 32 existing managed students.
7. Execute `teacher_teaching_class.sql`, then `seed_teacher_130_data.sql`, stopping on the first nonzero exit code.
8. Execute `verify_teacher_130_data.sql`, assert exact expected values, and assert captured student IDs remain unchanged.
9. Print only backup paths, verification values, and a final success line.

- [ ] **Step 4: Run static tests**

```powershell
python database/sql/test_teacher_130_data_seed.py
python database/sql/test_teacher_teaching_class_schema.py
```

Expected: both suites PASS.

- [ ] **Step 5: Commit orchestration and verification**

```powershell
git add database/sql/migrate_teacher_130_test_data.ps1 database/sql/verify_teacher_130_data.sql database/sql/test_teacher_130_data_seed.py
git commit -m "feat: automate safe teacher test data migration"
```

### Task 4: Document operator usage and recovery

**Files:**
- Create: `database/sql/README-teacher-130-test-data.md`

**Interfaces:**
- Consumes: the runner parameters and generated backup paths.
- Produces: a collaborator-facing runbook for prerequisites, execution, verification, repeat execution, and two-database restore.

- [ ] **Step 1: Write the runbook**

Document the exact environment and invocation without embedding a password:

```powershell
$env:MYSQL_USER = 'seclab_app'
$env:MYSQL_PWD = Read-Host 'MySQL password'
./database/sql/migrate_teacher_130_test_data.ps1 `
  -MySqlBin 'C:\Program Files\MySQL\MySQL Server 9.6\bin' `
  -BackupRoot 'D:\Seclab-backups'
Remove-Item Env:MYSQL_PWD
```

Explain that successful verification requires 130 managed students, one managed teacher, 130 memberships, eight course mappings, zero orphans, and stable pre-existing user IDs. Include restore commands for both generated SQL dumps and state explicitly that restore replaces live data and should only be used after stopping application services.

- [ ] **Step 2: Check the runbook for secrets and repository-relative paths**

```powershell
Select-String -Path database/sql/README-teacher-130-test-data.md -Pattern 'seclab123|--password='
```

Expected: no matches.

- [ ] **Step 3: Commit the runbook**

```powershell
git add database/sql/README-teacher-130-test-data.md
git commit -m "docs: add teacher test data migration runbook"
```

### Task 5: Back up, migrate, verify, and publish

**Files:**
- Modify only if verification exposes a defect: files introduced in Tasks 1 through 4.
- Do not add: backup dumps, staging extraction, credentials, or runtime logs.

**Interfaces:**
- Consumes: approved migration artifacts and application credentials already configured locally.
- Produces: migrated live databases and a pushed reproducible repository state.

- [ ] **Step 1: Confirm clean repository and tool availability**

Run `git status --short`, locate `mysql.exe`/`mysqldump.exe`, and verify the MySQL service is running. Expected: clean tracked worktree and both clients available.

- [ ] **Step 2: Load credentials without displaying them and run migration**

Read the existing application username/password defaults into process environment variables without printing them, then invoke the runner with `D:\Seclab-backups` as backup root. Expected: two nonempty dumps and `MIGRATION VERIFIED`.

- [ ] **Step 3: Prove idempotency**

Run the migration a second time. Expected: verification values are unchanged, existing managed student IDs remain stable, and no managed count increases.

- [ ] **Step 4: Run full regression checks**

```powershell
python database/sql/test_teacher_130_data_seed.py
python database/sql/test_teacher_teaching_class_schema.py
cd seclab-backend/user-service
.\gradlew.bat test
cd ..\experiment-module-service
.\gradlew.bat test
```

Run the existing AI teacher tests and frontend teacher API regression from their documented package directories. Expected: all tests PASS.

- [ ] **Step 5: Audit repository contents and commit any verification fixes**

Use `git status --short --untracked-files=all` and confirm that no `.sql` dump, credential file, staging directory, or log is tracked. If fixes were required, commit only the migration artifacts with a focused message.

- [ ] **Step 6: Push and verify remote visibility**

```powershell
git push origin main
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

Expected: local HEAD and remote `main` hashes match.
