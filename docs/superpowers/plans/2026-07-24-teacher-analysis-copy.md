# Teacher Analysis Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove template-like AI wording from the class experiment analysis panel and retain only teacher-useful experiment statistics.

**Architecture:** The Vue component will render deterministic copy from the existing `summary` and `knowledgeFindings` numeric fields instead of displaying generated prose. The backend fallback will stop producing unused teaching slogans so the API response also stays clean.

**Tech Stack:** Vue 3, TypeScript, Vitest, Python `unittest`

## Global Constraints

- Do not change analysis API paths, response shapes, or statistical calculations.
- Do not display “教学动作”“建议下一步”“重点关注” or cross-course implementation explanations.
- Keep knowledge-point name, accuracy, remaining incorrect-question count, and affected-student count.

---

### Task 1: Lock the teacher-facing copy contract

**Files:**
- Modify: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/__tests__/analysisPresentation.spec.ts`
- Test: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/__tests__/analysisPresentation.spec.ts`

**Interfaces:**
- Consumes: `CourseAnalysisPanel.vue` source text.
- Produces: a regression contract for visible labels and removed template phrases.

- [ ] **Step 1: Write the failing test**

Add a source-contract test asserting that the component contains `更新分析`, `答题情况`, `仍有`, and `名学生`, and does not contain `教学动作`, `建议下一步`, `重点关注`, `teacherAction`, `teachingSuggestions`, or `overallComment`.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/pages/Teacher/TeachingAnalysis/__tests__/analysisPresentation.spec.ts`

Expected: FAIL because the current component renders the removed fields and labels.

- [ ] **Step 3: Keep the failing test for Task 2**

No production code changes are made in this task.

### Task 2: Simplify the analysis panel

**Files:**
- Modify: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/components/CourseAnalysisPanel.vue`
- Test: `SecLab-FrontEnd-2/src/pages/Teacher/TeachingAnalysis/__tests__/analysisPresentation.spec.ts`

**Interfaces:**
- Consumes: `TeacherCourseAnalysisDto.analysis.summary` and `knowledgeFindings`.
- Produces: deterministic teacher-facing experiment statistics.

- [ ] **Step 1: Render a factual summary**

Replace generated `overallComment` with:

```vue
本实验共 {{ summary.questionCount }} 道题，已作答 {{ summary.attemptCount }} 次，正确率 {{ accuracy }}%。
```

- [ ] **Step 2: Render factual knowledge-point details**

Replace generated `evidence` and `teacherAction` with:

```vue
仍有 {{ item.incorrectQuestionCount }} 道题答错，涉及 {{ item.affectedStudentCount }} 名学生。
```

- [ ] **Step 3: Remove template sections**

Remove the “教学动作” line and the entire “建议下一步” list. Rename the button to “更新分析” and the empty state to “暂无分析结果”.

- [ ] **Step 4: Run the frontend test**

Run: `npm test -- src/pages/Teacher/TeachingAnalysis/__tests__/analysisPresentation.spec.ts`

Expected: PASS.

### Task 3: Clean the backend fallback payload

**Files:**
- Modify: `seclab-backend/ai-agent-service/test_teacher_course_analysis_service.py`
- Modify: `seclab-backend/ai-agent-service/teacher_course_analysis_service.py`
- Test: `seclab-backend/ai-agent-service/test_teacher_course_analysis_service.py`

**Interfaces:**
- Consumes: `build_course_analysis_fallback(items, scope, course)`.
- Produces: the same response keys without canned teaching slogans.

- [ ] **Step 1: Write the failing backend test**

Assert that fallback `overallComment` does not contain `重点关注`, every finding omits `teacherAction`, and `teachingSuggestions` is empty.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest test_teacher_course_analysis_service.py`

Expected: FAIL on the old fallback phrases.

- [ ] **Step 3: Remove canned fallback prose**

Keep the factual overall count and finding evidence, omit `teacherAction`, and return an empty `teachingSuggestions` array.

- [ ] **Step 4: Run the backend test**

Run: `python -m unittest test_teacher_course_analysis_service.py`

Expected: PASS.

### Task 4: Build and rendered verification

**Files:**
- No production files created.

**Interfaces:**
- Consumes: running frontend and local teacher account.
- Produces: screenshot and console/network evidence outside the repository.

- [ ] **Step 1: Run focused tests and build**

Run:

```powershell
npm test -- src/pages/Teacher/TeachingAnalysis/__tests__/analysisPresentation.spec.ts
npm run build
python -m unittest test_teacher_course_analysis_service.py
```

Expected: all commands exit 0.

- [ ] **Step 2: Restart the AI service**

Restart port 8010 so the updated fallback code is active.

- [ ] **Step 3: Validate the rendered page**

Use Playwright with the existing Chrome installation. Open the teacher analysis page, select a class and experiment with records, update the analysis, then assert:

- no old labels or template explanations;
- factual summary and knowledge-point statistics are visible;
- no relevant console errors or failed analysis requests.

- [ ] **Step 4: Open the verified page in Chrome**

Open the tested route for user acceptance.
