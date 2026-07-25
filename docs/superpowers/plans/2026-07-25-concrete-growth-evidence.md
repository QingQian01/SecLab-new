# Concrete Capability Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make each recent capability evidence record state exactly what the student accessed or asked and expose its traceable source details.

**Architecture:** Enrich the existing capability-growth repository queries without adding tables, pass optional evidence fields through the existing response, and render each evidence item as an expandable native disclosure in the shared Vue panel.

**Tech Stack:** Python 3, PyMySQL, FastAPI, unittest, Vue 3, TypeScript, Vitest, Playwright.

## Global Constraints

- Use only fields read from production tables; never synthesize evidence.
- Keep the existing authorization boundaries unchanged.
- Historical missing values render honestly as unavailable.
- Follow red-green TDD for repository and component behavior.
- Restore the current main frontend on `127.0.0.1:5173`.

---

### Task 1: Enrich backend evidence

**Files:**
- Modify: `seclab-backend/ai-agent-service/test_capability_growth_repository.py`
- Modify: `seclab-backend/ai-agent-service/capability_growth_repository.py`

**Interfaces:**
- `build_lab_evidence(rows) -> list[dict[str, Any]]`
- `build_ai_evidence(rows) -> list[dict[str, Any]]`
- Existing `CapabilityGrowthEvidenceDto` response gains optional real-source fields.

- [ ] Add failing tests that require the SQL lab title, target URL, duration, event count, identifiers, and actual AI message text.
- [ ] Run the focused tests and confirm failures are caused by the missing enrichment.
- [ ] Extend the production queries and evidence builders with the minimal required fields.
- [ ] Run the repository and service tests until green.

### Task 2: Render inspectable evidence

**Files:**
- Modify: `SecLab-FrontEnd-2/src/api.ts`
- Modify: `SecLab-FrontEnd-2/src/components/__tests__/CapabilityGrowthPanel.spec.ts`
- Modify: `SecLab-FrontEnd-2/src/components/CapabilityGrowthPanel.vue`

**Interfaces:**
- `CapabilityGrowthEvidenceDto` exposes the optional backend fields.
- Each `.evidence-row` is a `<details>` disclosure whose `<summary>` contains the concrete list view and whose body contains trace fields.

- [ ] Add a failing SSR test requiring the concrete SQL lab summary and expandable source details while rejecting the generic fallback sentence.
- [ ] Run the focused Vitest file and confirm RED.
- [ ] Add the typed fields and minimal disclosure rendering.
- [ ] Run focused tests and the frontend build until green.

### Task 3: Runtime and browser verification

**Files:**
- No committed artifacts.

- [ ] Restart the FastAPI service on `8011` so the enriched query is live.
- [ ] Confirm `5173` is served from the main checkout with acceptance API configuration.
- [ ] Open `/#/user/profile` as 姜理想, select the learning-engagement dimension, expand a real evidence record, and verify the real SQL module, URL, timing, source IDs, and absence of console/framework errors.
- [ ] Save screenshots outside the repository and report the remaining historical-data limitations.
