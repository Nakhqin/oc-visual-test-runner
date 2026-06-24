# Tasks — oc-visual-test-runner

Implementation roadmap. **Do not skip ahead** without updating this file and `docs/DECISIONS.md`.

Status categories: **Todo**, **In Progress**, **Done**, **Blocked**.

## Current Priority

**Phase 1 — Browser visual runner for figma/web**

| Status | Task |
|---|---|
| Done | Create `scripts/ux_testing.py` CLI entry |
| Done | Define target config parsing |
| In Progress | Implement shared browser platform adapter (initial URL open + screenshot capture) |
| Todo | Implement core visual agent loop |
| Todo | Integrate VLM (Gemini) for action decisions |
| Todo | Implement action schema and executor |
| Todo | Write trace/result output (`action_trace.json`, `ux_result.json`, screenshots, `.webm`) |
| Done | Decide package layout; record in DECISIONS.md |
| Done | Print `SELECTED_TARGET`, `SELECTED_ADAPTER`, `SELECTED_RUNNER` metadata for OpenClaw |
| Done | Add `requirements.txt` when stack chosen |

**Phase 1 output:** `ux_result.json`, `action_trace.json`, `ux_test_recording.webm`, `screenshots/` only.

**Exit criteria:** End-to-end run against one Figma prototype URL and one web URL with Phase 1 output contract.

---

## Backlog

### Phase 1.5 — Cursor marker + hover observation loop

| Status | Task |
|---|---|
| Todo | Visual cursor marker overlay on observation frames |
| Todo | Hover-before-click observation step |
| Todo | VLM reacts to hover/visual feedback in loop |

**Exit criteria:** Trace shows hover/marker steps; VLM can decide click / adjust / wait / block after hover feedback; documented in VERIFY.md.

---

### Phase 2 — Post-click verification and retry logic

| Status | Task |
|---|---|
| Todo | Detect whether click produced visible change |
| Todo | Bounded retry policy |
| Todo | Classify click miss vs UI no-response (not auto UX issue) |

**Exit criteria:** Verification outcomes recorded in trace; retries bounded and logged.

---

### Phase 3 — Minimal report output

| Status | Task |
|---|---|
| Todo | Generate minimal human-readable report from trace |
| Todo | Optional UX finding tags with explicit criteria |
| Todo | Document report schema in DECISIONS.md |

**Exit criteria:** Minimal user-facing report generated alongside `ux_result.json`; no legacy report system.

---

### Phase 4 — Formal reports and Skill-ready result JSON

| Status | Task |
|---|---|
| Todo | Generate formal `ux_report.md` |
| Todo | Generate formal `index.html` (main human-readable report) |
| Todo | Improve `ux_result.json` schema for OpenClaw Skill integration |
| Todo | Align report content with `SKILL.md` (journey, findings, classification, evidence) |

**Exit criteria:** User-facing report paths (`index.html`, `ux_report.md`) populated; OpenClaw can build user-facing return from artifacts.

---

### Phase 5 — OpenClaw / Feishu-style Skill delivery

| Status | Task |
|---|---|
| Todo | Skill entrypoint matching SKILL.md contract |
| Todo | NL → structured input conversion in OpenClaw layer |
| Todo | User-facing summary template (not raw logs) |
| Todo | End-to-end Skill invocation test with report/evidence links |
| Todo | OpenClaw manifest or registration docs |

**Exit criteria:** User asks in natural language; OpenClaw invokes runner and returns concise summary plus report/recording/result paths.

---

### Phase 6 — Android/Windows adapter design

| Status | Task |
|---|---|
| Todo | Design Android platform adapter interface |
| Todo | Design Windows platform adapter interface |
| Todo | Extend target config and SKILL.md for new targets |

**Exit criteria:** Adapter design documented; no implementation required.

---

### Phase 7 — Android/Windows implementation exploration

| Status | Task |
|---|---|
| Todo | Spike Android visual control adapter |
| Todo | Spike Windows visual control adapter |
| Todo | Validate same trace/result output contract |

**Exit criteria:** At least one scenario per platform documented with findings.

---

## Blocked

| Task | Blocker | Next Step |
|---|---|---|
| — | — | — |

## Done

| Date | Task | Notes |
|---|---|---|
| 2026-06-24 | Phase 0 — Convert starter kit into oc-visual-test-runner scaffold | VERIFY.md checks passed; docs/rules/SKILL aligned to project name and architecture |

## Explicitly Not Doing

- Migrating legacy `figma_runner.py`, `web_runner.py`, patch/backup/report code
- Figma API resolver or node/layer matching
- DOM-selector-first automation
- Treating failed clicks as automatic UX issues
- Runtime implementation during Phase 0
