# Tasks — oc-visual-test-runner

Implementation roadmap. **Do not skip ahead** without updating this file and `docs/DECISIONS.md`.

Status categories: **Todo**, **In Progress**, **Done**, **Blocked**.

## Current Priority

**Phase 0 — Convert starter kit into oc-visual-test-runner scaffold**

Documentation and project-context only. No runtime code, no API calls, no Playwright, no Gemini, no browser adapter.

| Status | Task |
|---|---|
| In Progress | Rewrite README, SKILL, AGENTS, START_HERE, docs/, rules for oc-visual-test-runner |
| Todo | Mark Phase 0 Done after VERIFY.md checks pass |

**Exit criteria:** All context files describe the real project; agents can read docs and know what to build next; git diff contains only scaffold/context files.

---

## Backlog

### Phase 1 — Browser visual runner for figma/web

| Status | Task |
|---|---|
| Todo | Create `scripts/ux_testing.py` CLI entry |
| Todo | Define target config parsing |
| Todo | Implement shared browser platform adapter |
| Todo | Implement core visual agent loop |
| Todo | Integrate VLM (Gemini) for action decisions |
| Todo | Implement action schema and executor |
| Todo | Write trace/result output (`action_trace.json`, `ux_result.json`, screenshots, `.webm`) |
| Todo | Decide package layout; record in DECISIONS.md |
| Todo | Add `requirements.txt` when stack chosen |

**Exit criteria:** End-to-end run against one Figma prototype URL and one web URL with full output contract.

---

### Phase 1.5 — Cursor marker + hover observation loop

| Status | Task |
|---|---|
| Todo | Visual cursor marker overlay on observation frames |
| Todo | Hover-before-click observation step |
| Todo | VLM reacts to hover/visual feedback in loop |

**Exit criteria:** Trace shows hover/marker steps; documented in VERIFY.md.

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

**Exit criteria:** Report generated alongside `ux_result.json`; no legacy report system.

---

### Phase 4 — OpenClaw skill integration

| Status | Task |
|---|---|
| Todo | Skill entrypoint matching SKILL.md contract |
| Todo | OpenClaw manifest or registration docs |
| Todo | End-to-end skill invocation test |

**Exit criteria:** OpenClaw invokes runner and consumes output files.

---

### Phase 5 — Android/Windows adapter design

| Status | Task |
|---|---|
| Todo | Design Android platform adapter interface |
| Todo | Design Windows platform adapter interface |
| Todo | Extend target config and SKILL.md for new targets |

**Exit criteria:** Adapter design documented; no implementation required.

---

### Phase 6 — Android/Windows implementation exploration

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
| — | — | — |

## Explicitly Not Doing

- Migrating legacy `figma_runner.py`, `web_runner.py`, patch/backup/report code
- Figma API resolver or node/layer matching
- DOM-selector-first automation
- Treating failed clicks as automatic UX issues
- Runtime implementation during Phase 0
