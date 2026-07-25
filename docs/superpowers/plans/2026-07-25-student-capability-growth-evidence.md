# Student Capability Growth Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add student and teacher capability-growth views whose scores, trends, behavior metrics, samples, and evidence come only from authenticated real database APIs.

**Architecture:** Extend the existing FastAPI AI agent service with a focused growth domain module and repository. Harden profile rebuild provenance so only production learning events can create growth-eligible snapshots, then expose student-self and teacher-owned-class endpoints. Add one reusable Vue component that consumes the typed API response in both student and teacher surfaces.

**Tech Stack:** Python 3, FastAPI, PyMySQL, unittest, Vue 3, TypeScript, Vite, Vitest, Chart.js.

## Global Constraints

- Never import or call `SecLab-FrontEnd-2/src/mock/profileFallback.ts` from the growth feature.
- Exclude source values containing `showcase-seed`, `static-fallback`, `mock`, `demo`, `test`, or `seed` from growth scores, metrics, samples, and evidence.
- Return an honest empty or insufficient-evidence state when production data is unavailable.
- Every metric must include sample counts and traceable source record identifiers.
- Students may read only their own growth data; teachers may read only members of teaching classes they own.
- Do not add frontend dependencies; reuse Chart.js.
- Follow TDD: add and run a failing test before each production change.
- Do not add a new database table.

---

### Task 1: Production-Data Provenance for Profile Snapshots

**Files:**
- Modify: `seclab-backend/ai-agent-service/profile_repository.py`
- Create: `seclab-backend/ai-agent-service/test_profile_data_provenance.py`

**Interfaces:**
- Produces `CALCULATION_VERSION = "capability-growth-v1"`.
- Produces `is_production_source(value: Any) -> bool`.
- Produces `build_data_provenance(source_counts: dict[str, int], eligible_record_count: int, excluded_record_count: int, unverifiable_record_count: int) -> dict[str, Any]`.
- Produces `is_growth_eligible_snapshot(snapshot: dict[str, Any]) -> bool`.
- Changes `rebuild_student_profile(user_id)` so `profile_summary_json.data_provenance` records `mode`, `calculationVersion`, eligible/excluded counts, and source types.

- [ ] **Step 1: Write failing provenance tests**

```python
class ProfileDataProvenanceTest(unittest.TestCase):
    def test_rejects_nonproduction_sources_case_insensitively(self):
        for value in ("showcase-seed", "STATIC-FALLBACK", "mock-profile", "demo", "pytest-seed"):
            self.assertFalse(profile_repository.is_production_source(value))

    def test_accepts_runtime_sources(self):
        for value in ("api", "hook", "ai-agent-service", "course_question", "personalized_training"):
            self.assertTrue(profile_repository.is_production_source(value))

    def test_snapshot_requires_production_provenance_and_real_records(self):
        eligible = {
            "profile_summary_json": {
                "data_provenance": {
                    "mode": "production_events",
                    "calculationVersion": "capability-growth-v1",
                    "eligibleRecordCount": 4,
                    "excludedRecordCount": 0,
                    "unverifiableRecordCount": 0,
                }
            }
        }
        self.assertTrue(profile_repository.is_growth_eligible_snapshot(eligible))
        eligible["profile_summary_json"]["data_provenance"]["eligibleRecordCount"] = 0
        self.assertFalse(profile_repository.is_growth_eligible_snapshot(eligible))
        eligible["profile_summary_json"]["data_provenance"]["eligibleRecordCount"] = 4
        eligible["profile_summary_json"]["data_provenance"]["excludedRecordCount"] = 1
        self.assertFalse(profile_repository.is_growth_eligible_snapshot(eligible))
        self.assertFalse(profile_repository.is_growth_eligible_snapshot({"profile_summary_json": {}}))
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
cd seclab-backend/ai-agent-service
python -m unittest test_profile_data_provenance.py -v
```

Expected: failures because the provenance helpers do not exist.

- [ ] **Step 3: Add minimal provenance helpers**

Implement a normalized deny-token check:

```python
CALCULATION_VERSION = "capability-growth-v1"
NON_PRODUCTION_SOURCE_TOKENS = ("showcase-seed", "static-fallback", "mock", "demo", "test", "seed")

def is_production_source(value: Any) -> bool:
    normalized = str(value or "").strip().lower()
    return bool(normalized) and not any(token in normalized for token in NON_PRODUCTION_SOURCE_TOKENS)
```

Parse string or object `profile_summary_json` in `is_growth_eligible_snapshot` and require `mode == "production_events"`, the current calculation version, and a positive eligible count.

- [ ] **Step 4: Add real-source counting to profile rebuild**

Add a focused `_collect_data_provenance(cursor, user_id)` query set that counts:

- `learning_event.source`;
- `container_command_event.source`;
- `error_event.source`;
- `question_submission.question_source`;
- `training_session.source_type` joined to `generated_question_attempt`;
- `ai_conversation.source`.

Classify rows with `is_production_source`. Write the result under `summary["data_provenance"]`. Set `mode = "production_events"` only when the same scoring window contains at least one eligible record and both `excludedRecordCount` and `unverifiableRecordCount` are zero. Otherwise use `mixed_or_insufficient_data`; keep that snapshot available for legacy current-profile screens but never use it in a growth comparison. This conservative rule prevents existing score queries from being declared trustworthy when their input set contains seed or unverifiable records.

- [ ] **Step 5: Run focused and existing profile tests**

```powershell
python -m unittest test_profile_data_provenance.py test_teacher_profile_service.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add seclab-backend/ai-agent-service/profile_repository.py seclab-backend/ai-agent-service/test_profile_data_provenance.py
git commit -m "feat: record real profile data provenance"
```

---

### Task 2: Growth Domain Calculations

**Files:**
- Create: `seclab-backend/ai-agent-service/capability_growth_service.py`
- Create: `seclab-backend/ai-agent-service/test_capability_growth_service.py`

**Interfaces:**
- `select_growth_snapshots(snapshots: Iterable[dict[str, Any]]) -> tuple[Optional[dict[str, Any]], Optional[dict[str, Any]], list[dict[str, Any]]]`
- `split_comparable_windows(rows: Iterable[dict[str, Any]], bucket_key: Callable[[dict[str, Any]], Hashable], window_size: int = 3) -> list[dict[str, Any]]`
- `confidence_for_samples(baseline_count: int, current_count: int, consistent: bool = False) -> str`
- `compare_rate_metric(...) -> dict[str, Any]`
- `compare_duration_metric(...) -> dict[str, Any]`
- `build_capability_growth(...) -> dict[str, Any]`

- [ ] **Step 1: Write failing snapshot, window, and confidence tests**

Cover these behaviors with real dictionaries rather than mocks:

```python
def test_selects_first_and_latest_eligible_snapshots_only():
    baseline, current, history = growth.select_growth_snapshots([
        snapshot("legacy", 55, day=1, eligible=False),
        snapshot("first-real", 61, day=2, eligible=True),
        snapshot("latest-real", 74, day=5, eligible=True),
    ])
    assert baseline["snapshot_id"] == "first-real"
    assert current["snapshot_id"] == "latest-real"
    assert [item["snapshot_id"] for item in history] == ["first-real", "latest-real"]

def test_windows_never_share_the_same_task():
    comparisons = growth.split_comparable_windows(rows, bucket_key=lambda row: row["bucket"])
    assert set(comparisons[0]["baselineIds"]).isdisjoint(comparisons[0]["currentIds"])

def test_two_samples_are_emerging_and_three_are_moderate():
    assert growth.confidence_for_samples(2, 2) == "emerging"
    assert growth.confidence_for_samples(3, 3) == "moderate"
```

- [ ] **Step 2: Run focused tests and verify RED**

```powershell
python -m unittest test_capability_growth_service.py -v
```

Expected: import failure because the module does not exist.

- [ ] **Step 3: Implement snapshot and window selection**

Use `profile_repository.is_growth_eligible_snapshot`, chronological sorting, non-overlapping first/last windows, and a minimum of two samples on each side.

- [ ] **Step 4: Add failing metric-direction tests**

```python
def test_faster_time_is_not_improvement_when_success_rate_falls():
    metric = growth.compare_duration_metric(
        key="answer_time",
        label="有效作答时间",
        baseline_values=[90, 100, 110],
        current_values=[50, 60, 70],
        baseline_quality=0.90,
        current_quality=0.60,
        source_rows=source_rows,
    )
    assert metric["direction"] == "declined"
    assert "正确率下降" in metric["explanation"]

def test_duration_uses_median_and_reports_traceable_sources():
    metric = growth.compare_duration_metric(
        key="recovery_time",
        label="遇错后恢复时间",
        baseline_values=[600, 660, 3600],
        current_values=[360, 420, 480],
        baseline_quality=0.70,
        current_quality=0.80,
        source_rows=source_rows,
    )
    assert metric["baselineValue"] == 660
    assert metric["currentValue"] == 420
    assert metric["sourceRecordIds"]
```

- [ ] **Step 5: Run tests, implement rate/duration comparisons, and rerun**

Duration improvement requires non-decreasing paired quality. Use `statistics.median`; return `None` changes for insufficient samples. Keep source types and record IDs in every metric.

- [ ] **Step 6: Add and implement response assembly tests**

Test:

- no eligible snapshot;
- one eligible snapshot;
- baseline/current dimension deltas;
- history limited to eight chronological snapshots;
- five dimensions always returned;
- messages never invent evidence.

- [ ] **Step 7: Run all growth-domain tests**

```powershell
python -m unittest test_capability_growth_service.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add seclab-backend/ai-agent-service/capability_growth_service.py seclab-backend/ai-agent-service/test_capability_growth_service.py
git commit -m "feat: calculate traceable capability growth"
```

---

### Task 3: Real Database Repository and Authenticated APIs

**Files:**
- Create: `seclab-backend/ai-agent-service/capability_growth_repository.py`
- Create: `seclab-backend/ai-agent-service/test_capability_growth_repository.py`
- Modify: `seclab-backend/ai-agent-service/main.py`

**Interfaces:**
- `get_student_capability_growth(student_id: int, teaching_class_id: Optional[int] = None) -> dict[str, Any]`
- `get_teacher_student_capability_growth(teacher_id: int, class_id: int, student_id: int) -> dict[str, Any]`
- `GET /api/students/{student_id}/capability-growth?teachingClassId={id}`
- `GET /api/teacher/teaching-classes/{class_id}/students/{student_id}/capability-growth`

- [ ] **Step 1: Write failing repository tests**

Use a fake cursor only at the database boundary and assert returned behavior:

- only snapshots from the requested teaching class are loaded;
- question rows join attempts to `generated_question`, `training_session`, and real source type;
- experiment rows include commands, errors, completions, and their source IDs;
- non-production rows are excluded and counted;
- no title-based difficulty or knowledge-point guessing occurs.

- [ ] **Step 2: Run repository tests and verify RED**

```powershell
python -m unittest test_capability_growth_repository.py -v
```

Expected: import failure because the repository does not exist.

- [ ] **Step 3: Implement real queries**

Query:

- `student_profile_snapshot` by `user_id`, `class_id`, and chronological order;
- generated attempts joined to `generated_question` and `training_session`, selecting attempt ID, knowledge point, type, difficulty, correctness, score, cost time, and submission time;
- course questions from `question_submission` when knowledge point and question type are present;
- `lab_session`, `container_command_event`, `error_event`, `challenge_completion_event`, and `ai_conversation/ai_message` by student and class.

Do not synthesize missing labels. Pass raw rows to the growth service and return its result.

- [ ] **Step 4: Add authenticated route tests**

Test with FastAPI dependency overrides:

- a student can read their own data;
- a student gets 403 for another student;
- a teacher route invokes `require_student_in_owned_teaching_class`;
- a teacher outside the class receives the existing repository error mapping.

- [ ] **Step 5: Implement routes**

Student route must use `Depends(require_authenticated_user)` and `_require_student_self`. Teacher route must use `Depends(require_teacher_user)` and pass the authenticated teacher ID to the repository.

- [ ] **Step 6: Run focused backend tests**

```powershell
python -m unittest test_capability_growth_service.py test_capability_growth_repository.py test_profile_data_provenance.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add seclab-backend/ai-agent-service/capability_growth_repository.py seclab-backend/ai-agent-service/test_capability_growth_repository.py seclab-backend/ai-agent-service/main.py
git commit -m "feat: expose authenticated capability growth APIs"
```

---

### Task 4: Frontend API Contract and Presentation Helpers

**Files:**
- Modify: `SecLab-FrontEnd-2/src/api.ts`
- Create: `SecLab-FrontEnd-2/src/components/capabilityGrowthPresentation.ts`
- Create: `SecLab-FrontEnd-2/src/components/__tests__/capabilityGrowthPresentation.spec.ts`

**Interfaces:**
- Types `CapabilityGrowthResponse`, `CapabilityGrowthDimension`, `CapabilityGrowthMetric`, `CapabilityGrowthEvidence`, `CapabilityGrowthConfidence`.
- `getStudentCapabilityGrowth(studentId: number, teachingClassId?: number | null)`.
- `getTeacherStudentCapabilityGrowth(classId: number, studentId: number)`.
- Presentation helpers `formatGrowthDelta`, `formatGrowthMetricValue`, `confidencePresentation`, and `growthTone`.

- [ ] **Step 1: Write failing presentation tests**

```typescript
it('formats positive, negative and unavailable deltas honestly', () => {
  expect(formatGrowthDelta(12.4)).toBe('↑ 12.4')
  expect(formatGrowthDelta(-3)).toBe('↓ 3.0')
  expect(formatGrowthDelta(null)).toBe('尚无对比')
})

it('formats seconds as human-readable time without changing raw values', () => {
  expect(formatGrowthMetricValue(420, 'seconds')).toBe('7分钟')
})

it('maps insufficient confidence to evidence-insufficient copy', () => {
  expect(confidencePresentation('insufficient').label).toBe('证据不足')
})
```

- [ ] **Step 2: Run the test and verify RED**

```powershell
cd SecLab-FrontEnd-2
npm test -- src/components/__tests__/capabilityGrowthPresentation.spec.ts
```

Expected: import failure because the helper does not exist.

- [ ] **Step 3: Implement helpers and typed API functions**

Use the existing agent authorization config. Do not provide fallback response objects in catch blocks; let callers render an error or empty state.

- [ ] **Step 4: Run focused test and type check**

```powershell
npm test -- src/components/__tests__/capabilityGrowthPresentation.spec.ts
npm run vue-tsc
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add SecLab-FrontEnd-2/src/api.ts SecLab-FrontEnd-2/src/components/capabilityGrowthPresentation.ts SecLab-FrontEnd-2/src/components/__tests__/capabilityGrowthPresentation.spec.ts
git commit -m "feat: add capability growth frontend contract"
```

---

### Task 5: Reusable Capability Growth Panel

**Files:**
- Create: `SecLab-FrontEnd-2/src/components/CapabilityGrowthPanel.vue`
- Create: `SecLab-FrontEnd-2/src/components/__tests__/CapabilityGrowthPanel.spec.ts`

**Interfaces:**
- Props: `{ data: CapabilityGrowthResponse | null; loading?: boolean; error?: string; teacherMode?: boolean }`.
- Emits: `retry`.
- Renders comprehensive delta, five dimensions, history chart, metrics, evidence, samples, provenance, and empty/error states.

- [ ] **Step 1: Write failing component tests**

Render with `createSSRApp` and `@vue/server-renderer`, matching the repository's existing component-test pattern, and assert:

- baseline, current, and delta are visible;
- the initially selected dimension displays its metrics and evidence;
- sample counts and confidence labels are visible;
- one-snapshot mode says “尚未形成成长对比”;
- null data says “暂无真实成长数据”;
- error state emits `retry`;
- strings such as `mock-`, `static-fallback`, and hardcoded example scores do not appear.

- [ ] **Step 2: Run component test and verify RED**

```powershell
npm test -- src/components/__tests__/CapabilityGrowthPanel.spec.ts
```

Expected: import failure because the component does not exist.

- [ ] **Step 3: Implement the panel**

Use:

- a summary card with `起点 → 当前`;
- five keyboard-accessible dimension buttons;
- a Chart.js line chart capped at eight snapshots;
- metric rows with baseline/current values, sample counts, confidence, and explanation;
- evidence rows with type, timestamp, and source ID;
- a provenance footer containing calculation version, eligible/excluded counts, and last computed time.

Destroy the Chart.js instance on unmount and rebuild only when history changes.

- [ ] **Step 4: Run component tests and type check**

```powershell
npm test -- src/components/__tests__/CapabilityGrowthPanel.spec.ts
npm run vue-tsc
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add SecLab-FrontEnd-2/src/components/CapabilityGrowthPanel.vue SecLab-FrontEnd-2/src/components/__tests__/CapabilityGrowthPanel.spec.ts
git commit -m "feat: render traceable capability growth"
```

---

### Task 6: Student and Teacher Page Integration

**Files:**
- Modify: `SecLab-FrontEnd-2/src/pages/User/Profile/index.vue`
- Modify: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/index.vue`
- Modify: `SecLab-FrontEnd-2/src/pages/User/Profile/TeacherAssignments.spec.ts`
- Modify: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/__tests__/analysisPresentation.spec.ts`

**Interfaces:**
- Student page loads `getStudentCapabilityGrowth(currentUserId, currentClassId)`.
- Teacher student view loads `getTeacherStudentCapabilityGrowth(selectedClassId, selectedStudentId)`.
- Both pass the untouched API response into `CapabilityGrowthPanel`.

- [ ] **Step 1: Add failing integration tests**

Assert:

- the student profile requests growth only after a real user ID is resolved;
- class ID is passed when available;
- the teacher page refreshes growth when selected student or class changes;
- failed refresh preserves the last successful growth response and shows an error;
- neither page imports `profileFallback`.

- [ ] **Step 2: Run focused tests and verify RED**

```powershell
npm test -- src/pages/User/Profile/TeacherAssignments.spec.ts src/pages/Teacher/TeachingAnalysis/__tests__/analysisPresentation.spec.ts
```

Expected: failures because the growth loaders and panel are absent.

- [ ] **Step 3: Integrate student page**

Add growth state, load/error/retry functions, and place the panel after the current overview stats and before teacher assignments. Do not alter existing profile, diagnosis, or training behavior.

- [ ] **Step 4: Integrate teacher page**

Add growth state to the existing student-data loading sequence. Place the panel before current capability evidence so the order is:

1. growth change;
2. current score evidence;
3. learning replay.

- [ ] **Step 5: Run frontend verification**

```powershell
npm test
npm run vue-tsc
npm run build
```

Expected: PASS with no new warnings.

- [ ] **Step 6: Commit**

```powershell
git add SecLab-FrontEnd-2/src/pages/User/Profile/index.vue SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/index.vue SecLab-FrontEnd-2/src/pages/User/Profile/TeacherAssignments.spec.ts SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/__tests__/analysisPresentation.spec.ts
git commit -m "feat: show capability growth to students and teachers"
```

---

### Task 7: Real-Data End-to-End Verification

**Files:**
- Modify only files required by defects found during verification.

**Interfaces:**
- Student and teacher endpoints return the same calculation version and student/class result.
- Response provenance maps to database record IDs.
- UI contains no fallback or seeded values.

- [ ] **Step 1: Run backend regression tests**

```powershell
cd seclab-backend/ai-agent-service
python -m unittest discover -p "test_*.py" -v
```

- [ ] **Step 2: Run frontend regression tests**

```powershell
cd SecLab-FrontEnd-2
npm test
npm run vue-tsc
npm run build
```

- [ ] **Step 3: Verify real database provenance**

With the configured local services:

1. use a real student account to answer a generated or course question;
2. perform a real experiment action that writes a command, error, or completion event;
3. rebuild the student profile;
4. query the related rows by returned record IDs;
5. call the student growth endpoint with that student's token;
6. call the teacher growth endpoint with the owning teacher's token;
7. confirm both responses agree on snapshot IDs, metrics, samples, and calculation version.

- [ ] **Step 4: Verify honest empty state**

Use a student whose database rows are exclusively seed/demo sources. Confirm both endpoints return insufficient real data and both pages show “暂无真实成长数据” or “证据不足”, with no demonstration values.

- [ ] **Step 5: Scan for forbidden fallback use**

```powershell
Get-ChildItem SecLab-FrontEnd-2/src -Recurse -File |
  Select-String -Pattern 'profileFallback|static-fallback|showcase-seed|mock-profile'
```

Accept occurrences only in explicitly isolated mock/demo files and tests; no growth production file may match.

- [ ] **Step 6: Inspect repository state and commit verification fixes**

```powershell
git diff --check
git status --short
```

Commit only focused defect fixes produced by verification.
