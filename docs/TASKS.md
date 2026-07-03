# Tasks — oc-visual-test-runner

Implementation roadmap. **Do not skip ahead** without updating this file and `docs/DECISIONS.md`.

Status categories: **Todo**, **In Progress**, **Done**, **Blocked**.

## Current Priority

**Phase 5 — OpenClaw / Feishu-style Skill delivery**

| Status | Task |
|---|---|
| Todo | Wire runner into OpenClaw Skill invocation path |
| Todo | Map NL user input → structured runner input |
| Todo | Return concise summary + report/evidence links to user |
| Todo | End-to-end Skill invocation test with report/evidence links |

**Exit criteria:** User asks in natural language; OpenClaw invokes runner and returns concise summary plus report/recording/result paths.

---

## Phase 4 (Complete)

**Formal reports and Skill-ready result JSON — implemented 2026-07-03**

| Status | Task |
|---|---|
| Done | Generate formal `ux_report.md` |
| Done | Generate formal `index.html` (main human-readable report) |
| Done | Improve `ux_result.json` schema for OpenClaw Skill integration |
| Done | Align report content with `SKILL.md` (journey, findings, classification, evidence) |

**Exit criteria (met in code):** `ux_report.md` and `index.html` generated on every run; `ux_result.json` includes `skill` block and formal report artifact paths. See `docs/VERIFY.md` Phase 4.

---

## Phase 3 (Complete)

**Minimal persona report output — implemented 2026-07-01**

| Status | Task |
|---|---|
| Done | Generate minimal human-readable report from trace |
| Done | Optional UX finding tags with explicit criteria |
| Done | Document report schema in DECISIONS.md |
| Done | Optional Gemini persona report synthesis (`--persona-report-gemini`) |

**Exit criteria (met in code):** `persona_report.md` generated alongside `ux_result.json`; trace synthesis (A) always runs; optional Gemini polish (B) when enabled. See `docs/VERIFY.md` Phase 3.

**E2E verification (2026-07-03):** Cloud runner Gemini run with `PERSONA_REPORT_GEMINI=1` — `trace+gemini` confirmed. See `docs/VERIFY.md` Phase 3 verification record.

---

## Phase 2 (Complete)

**Post-click verification and retry logic — implemented 2026-07-01**

| Status | Task |
|---|---|
| Done | Detect whether click produced visible change |
| Done | Bounded retry policy |
| Done | Classify click miss vs UI no-response (not auto UX issue) |

**Exit criteria (met in code):** Trace records `verification` on click/`click_current` executions with outcomes, retry attempts, and telemetry-only `interaction_hint`. See `docs/VERIFY.md` Phase 2.

---

## Phase 1.5 (Complete)

**Cursor marker + hover observation loop — implemented 2026-07-01**

| Status | Task |
|---|---|
| Done | Visual cursor marker overlay on observation frames |
| Done | Hover-before-click observation step |
| Done | VLM reacts to hover/visual feedback in loop |

**Exit criteria (met in code):** Trace records `hover` blocks and `-hover` screenshots; hover-phase VLM may return `click_current` / adjust / `wait` / `done` / `blocked`. Gemini E2E re-verification on cloud runner recommended — see `docs/VERIFY.md` Phase 1.5.

---

## Phase 1 (Complete)

**Browser visual runner for `figma` / `web` — verified 2026-07-01**

| Status | Task |
|---|---|
| Done | Create `scripts/ux_testing.py` CLI entry |
| Done | Define target config parsing |
| Done | Implement shared browser platform adapter (URL open + screenshot + visual actions) |
| Done | Implement core visual agent loop |
| Done | Integrate VLM (Gemini via `google-genai`) for action decisions |
| Done | Implement action schema and executor (browser visual actions) |
| Done | Write trace/result output (`action_trace.json`, `ux_result.json`, screenshots, `.webm`) |
| Done | Decide package layout; record in DECISIONS.md |
| Done | Print `SELECTED_TARGET`, `SELECTED_ADAPTER`, `SELECTED_RUNNER` metadata for OpenClaw |
| Done | Add `requirements.txt` when stack chosen |

**Phase 1 output:** `ux_result.json`, `action_trace.json`, `ux_test_recording.webm`, `screenshots/` only.

**Exit criteria (met):** End-to-end Gemini runs against one web URL and one Figma prototype URL with the Phase 1 output contract. See `docs/VERIFY.md` — Phase 1 verification record.

**Verification environment:** Primary E2E runs on a **cloud runner** (US, direct access to `generativelanguage.googleapis.com`). Local Windows dev validated browser path via `--use-stub`; Gemini E2E requires VPN or the cloud runner.

**Known limitations (Phase 1):**

- Default VLM: `gemini-2.5-flash` (`google-genai`); `gemini-2.0-flash` shut down 2026-06-01
- Gemini API may return **503 UNAVAILABLE** under high demand — re-run; not classified as UX issue
- Figma loads with `domcontentloaded` + fixed post-load wait (not `networkidle`)
- Formal HTML/Markdown reports generated from Phase 4 onward (`ux_report.md`, `index.html`)

---

## Backlog

### Phase 1.5 — Cursor marker + hover observation loop

Moved to **Current Priority** above — implementation complete; E2E verification pending on cloud runner.

---

### Phase 2 — Post-click verification and retry logic

Moved to **Phase 2 (Complete)** above.

---

### Phase 3 — Minimal report output

Moved to **Phase 3 (Complete)** above.

### Phase 4 — Formal reports and Skill-ready result JSON

Moved to **Phase 4 (Complete)** above.

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
| 2026-07-01 | Phase 1.5 — Cursor marker + hover observation loop | DOM marker, hover screenshots, dual-phase VLM on click; stub smoke in VERIFY.md |
| 2026-07-01 | Phase 1 — Browser visual runner for figma/web | E2E on cloud runner: web `max_steps`@10; figma 4 steps + 503; see VERIFY.md |
| 2026-06-24 | Phase 0 — Convert starter kit into oc-visual-test-runner scaffold | VERIFY.md checks passed; docs/rules/SKILL aligned to project name and architecture |

## Explicitly Not Doing

- Migrating legacy `figma_runner.py`, `web_runner.py`, patch/backup/report code
- Figma API resolver or node/layer matching
- DOM-selector-first automation
- Treating failed clicks as automatic UX issues
- Runtime implementation during Phase 0
