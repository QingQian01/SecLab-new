# Generated Question Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the deformed audit-status badge and view button with stable, single-line, accessible controls while preserving the existing row expansion behavior.

**Architecture:** Keep the change local to the existing generated-question page. Add one pure status-to-class mapping function and render Heroicons inside the existing toggle button; no data flow, API, or component boundary changes are needed.

**Tech Stack:** Vue 3, TypeScript, Tailwind CSS 3, DaisyUI 4, `@heroicons/vue` v1, Vite.

## Global Constraints

- Modify only `SecLab-FrontEnd-2/src/pages/Admin/GeneratedQuestions/index.vue`.
- Preserve all table fields, API calls, routes, expanded content, and current uncommitted request-race protection.
- Add no dependency and make no database, API, event, logging, or error-handling changes.
- Keep every status badge and action button on one line.

---

### Task 1: Stabilize and restyle the audit controls

**Files:**
- Modify: `SecLab-FrontEnd-2/src/pages/Admin/GeneratedQuestions/index.vue`
- Test: existing project type checking, production build, and rendered interaction check

**Interfaces:**
- Consumes: `item.reviewStatus: string`, `expandedId: Ref<string | null>`, and `item.generatedQuestionId: string`.
- Produces: `statusClasses(value: string): string`; unchanged row-toggle behavior; accessible `aria-expanded` state.

- [ ] **Step 1: Record the current static failure evidence**

Run:

```powershell
Select-String -Path src/pages/Admin/GeneratedQuestions/index.vue -Pattern 'badge badge-outline|btn btn-primary btn-xs'
```

Expected: both old control class strings are present and neither guarantees a minimum width or `whitespace-nowrap`.

- [ ] **Step 2: Add icon imports and the status style mapping**

Add the import:

```ts
import { ChevronUpIcon, EyeIcon } from '@heroicons/vue/outline'
```

Add the pure mapping next to `statusLabel`:

```ts
function statusClasses(value: string) {
  const normalized = String(value || '').toUpperCase()
  if (normalized === 'APPROVED') return 'border-emerald-200 bg-emerald-50 text-emerald-700'
  if (normalized === 'REJECTED') return 'border-rose-200 bg-rose-50 text-rose-700'
  if (normalized === 'NEEDS_REVISION') return 'border-orange-200 bg-orange-50 text-orange-700'
  return 'border-amber-200 bg-amber-50 text-amber-700'
}
```

- [ ] **Step 3: Replace the two deformed controls**

Render the review state with stable geometry:

```vue
<span
  class="inline-flex h-7 min-w-[4.5rem] items-center justify-center whitespace-nowrap rounded-full border px-2.5 text-xs font-medium"
  :class="statusClasses(item.reviewStatus)"
>
  {{ statusLabel(item.reviewStatus) }}
</span>
```

Render the existing row toggle as a light outlined action:

```vue
<button
  type="button"
  class="inline-flex h-8 min-w-[4.75rem] items-center justify-center gap-1.5 whitespace-nowrap rounded-lg border border-primary/30 bg-base-100 px-2.5 text-xs font-medium text-primary shadow-sm transition hover:border-primary/50 hover:bg-primary/5 focus:outline-none focus:ring-2 focus:ring-primary/30"
  :aria-expanded="expandedId === item.generatedQuestionId"
  @click="expandedId = expandedId === item.generatedQuestionId ? null : item.generatedQuestionId"
>
  <ChevronUpIcon v-if="expandedId === item.generatedQuestionId" class="h-4 w-4 shrink-0" aria-hidden="true" />
  <EyeIcon v-else class="h-4 w-4 shrink-0" aria-hidden="true" />
  {{ expandedId === item.generatedQuestionId ? '收起' : '查看' }}
</button>
```

- [ ] **Step 4: Run static verification**

Run:

```powershell
npm run vue-tsc
npm run build
```

Expected: both commands exit with code 0; the build emits the production bundle without Vue or TypeScript errors.

- [ ] **Step 5: Run rendered verification**

Start the existing Vite app, open the generated-question admin route, and verify:

1. Page identity and meaningful table content render without a framework error overlay.
2. Relevant console errors are absent.
3. Status pills remain single-line at desktop and a narrower viewport.
4. Clicking “查看” expands the matching row and changes the control to “收起”.
5. Clicking “收起” closes the row and restores “查看”.

- [ ] **Step 6: Review the focused diff**

Run:

```powershell
git diff --check -- src/pages/Admin/GeneratedQuestions/index.vue
git diff -- src/pages/Admin/GeneratedQuestions/index.vue
```

Expected: no whitespace errors; the diff contains only the icon import, status class mapping, and the two control templates in addition to the user’s pre-existing edits.
