# Concrete Capability Evidence Design

## Goal

Replace generic capability-growth evidence labels with concrete, inspectable facts from the existing production event tables.

## Data contract

Each growth evidence item keeps the shared `kind`, `title`, `detail`, `occurredAt`, `sourceId`, and `sourceType` fields and may additionally return:

- `labSessionId`, `courseId`, `moduleId`, `taskId`
- `moduleName`, `status`, `startedAt`, `endedAt`, `durationSeconds`
- `targetUrl`, `containerName`, `eventCount`, `eventTypes`
- `conversationId`, `messageContent`

The lab-session query obtains these values from `lab_session`, real `learning_event` rows, and the existing module catalogue. The AI evidence query obtains the actual student message from `ai_message`. Missing historical fields stay absent and are rendered as unavailable; they are never replaced by invented copy.

## User experience

The evidence list shows a concrete one-line summary such as:

`SQL注入基础实验 · 已结束`

`访问 http://localhost:8091/index.php · 持续 2分10秒 · 记录 2 条事件`

Each item is a native expandable disclosure. Its detail view exposes the source record ID and all available real fields so a student or teacher can verify exactly which activity supports the capability result.

AI evidence uses the actual question text as the title/summary and exposes the conversation and message identifiers.

## Error and privacy rules

- Only evidence already authorized by the existing student-self or teacher-owned-class endpoint is returned.
- Empty values are labeled `未记录`; no mock or fallback evidence is generated.
- Target URLs are displayed as recorded text and are not auto-opened from the evidence panel.
- Message content is limited to the student's own submitted text already stored by the platform.

## Verification

- Repository tests prove lab and AI evidence preserve real source fields.
- Component tests prove concrete summaries and expandable details render while generic fallback copy does not.
- Browser QA uses the 姜理想 account through the restored `5173` entry and expands a real SQL-injection lab session.
