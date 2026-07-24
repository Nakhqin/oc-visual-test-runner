# Tasks — oc-visual-test-runner

Implementation roadmap. **Do not skip ahead** without updating this file and `docs/DECISIONS.md`.

Status categories: **Todo**, **In Progress**, **Done**, **Blocked**.

## Current Priority

**Phase 5 — OpenClaw / Feishu Skill delivery**

Primary plan: **`docs/OPENCLAW_INTEGRATION.md`**

**Confirmed (2026-07-03):** Same VM deployment (`170.106.175.128`); NL extraction in OpenClaw main agent; existing Feishu channel.

### Phase 5.1 — Integration contract (this repo)

| Status | Task |
|---|---|
| Done | Phase 5 plan doc: `docs/OPENCLAW_INTEGRATION.md` |
| Done | Feishu reply helper: `scripts/format_skill_reply.py` + `scripts/core/skill_return.py` |
| Done | OpenClaw invoke wrapper: `scripts/openclaw/invoke_runner.sh` |
| Done | Agent prompt: `docs/openclaw/AGENT_PROMPT.md` |
| Done | `skill.recording_url` + `skill.result_json_url` when publish enabled |
| Done | Link plan doc from `README.md` and `AGENTS.md` |

### Phase 5.2 — OpenClaw wiring (OpenClaw side, same VM) — in progress

| Status | Task |
|---|---|
| Todo | Sync `docs/openclaw/OPENCLAW_SKILL.md` (YAML frontmatter `name: oc-visual-test-runner`) → `~/.openclaw/skills/oc-visual-test-runner/SKILL.md` |
| Todo | Confirm `openclaw skills list` shows **`oc-visual-test-runner` ✓ ready** (not legacy `ux_test_runner`) |
| Todo | Agent bash: one exec — `.venv` PATH + `./scripts/openclaw/invoke_runner.sh` (stdout = Feishu reply; Hard rules in OPENCLAW_SKILL.md) |
| Todo | Optional pathway smoke (`--use-stub`) before first NL |
| Todo | NL extraction + missing-field clarifying question in Feishu |
| Todo | Prefer disable legacy `ux-test-skill` during 5.3; confirm `tools.allow` includes `exec` |

**Do not** paste `AGENT_PROMPT.md` into Agent Instructions — OpenClaw injects skill `SKILL.md` automatically. Legacy `ux_test_runner` is a different skill; do not use it for Phase 5.

### Phase 5.3 — E2E verification

| Status | Task |
|---|---|
| Todo | Feishu NL → run (Gemini) → reply with clickable `report_url` |
| Todo | Verify `blocked` / `max_steps` still produce readable Feishu summary |
| Todo | Document failure modes in `docs/VERIFY.md` Phase 5 |
| Todo | OpenClaw manifest path recorded (OpenClaw config; note in integration doc) |

**Exit criteria:** User asks in natural language via Feishu; OpenClaw on the VM invokes runner and returns concise summary plus **public `report_url`** and evidence links.

**Non-goals (Phase 5):** Re-implementing publish (Phase 4.5); Feishu SDK in this repo; NL parser in this repo.

---

## Next Priority (after Phase 5.3)

**Phase 5.5 — Visual click grounding (G1 + G2 foundation)**

Primary plan: **`docs/GROUNDING.md`**

**Phase 5.5b — UVG (Universal Visual Grounding)** — **current implementation priority** after G1+G2 formal regression failed scenario A.

| Status | Task |
|---|---|
| Done | G1: Normalized 0–1000 coordinate protocol + pixel mapping + tests |
| Done | G2: Hover alignment prompts + multi-pass sub-loop + trace metadata |
| Done | Trace: `schema_version` 2; norm + pixel; hover `alignment` / `adjustments` |
| Blocked | Tier 2 regression B–C — fixture URLs **TBD** |
| Done | Tier 2 **Scenario A** — ≥2/3 pass (`grounding-A-setup-1` + additional runs, 2026-07-09) |
| Done | **UVG L2'** — convergence hover (`MAX_HOVER_ALIGNMENT_PASSES=5`; `blocked` on exhaust) |
| Done | **UVG L1** — mandatory ROI refine (`scripts/core/refine.py`) on every coordinate `click` |
| Todo | Tier 2 scenarios **B–C**; full Phase 5.5 sign-off when B–C pass |
| Todo | **UVG L3** — spatial / bbox model only if L1+L2 below bar |

**Exit criteria (UVG):** Tier 2 **A** done (2026-07-09); **B–C** each ≥2/3 final-hover on target; no off-target `click_current`; no `max_steps` wasted on alignment. See **`docs/GROUNDING.md`** UVG sign-off table.

**Non-goals:** Per-UI row hacks; Figma API; DOM-selector-first; L3 before L1+L2 measured.

---

## Phase 4.5 (Complete)

**Public report publish (no OpenClaw required) — implemented 2026-07-03**

| Status | Task |
|---|---|
| Done | `run_id` resolution (optional `--run-id` / `RUN_ID`; default auto-generated slug) |
| Done | `publish()` copy full `output_dir` → `UX_REPORT_PUBLIC_DIR/<run_id>/` |
| Done | Write `skill.report_url` and `skill.report_base_url` in `ux_result.json` when publish env is set |
| Done | stderr `report_url=...` and publish metadata |
| Done | Document ops: static host (`http.server` or nginx) + security/retention notes in `docs/VERIFY.md` |

**Exit criteria (met in code):** With `UX_REPORT_PUBLIC_DIR` and `UX_REPORT_PUBLIC_BASE_URL` set, a run publishes artifacts and `report_url` is written to `ux_result.json`. Without publish env, run completes with `SELECTED_REPORT_PUBLISH=disabled`. See `docs/VERIFY.md` Phase 4.5.

---

## Phase 5 (Next)

Moved to **Current Priority** above. See **`docs/OPENCLAW_INTEGRATION.md`**.

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

**E2E verification (2026-07-03):** Cloud runner Gemini run — `SELECTED_FORMAL_REPORT=enabled`, `ux_report.md` + `index.html` generated. Public URL publish deferred to Phase 4.5. See `docs/VERIFY.md` Phase 4 verification record.

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
- Formal HTML/Markdown reports generated from Phase 4 onward (`ux_report.md`, `index.html`); public URL publish is Phase 4.5

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

### Phase 4.5 — Public report publish

Moved to **Current Priority** above.

---

### Phase 5 — OpenClaw / Feishu Skill delivery

Moved to **Current Priority** above. Plan: **`docs/OPENCLAW_INTEGRATION.md`**. Consumes `skill.report_url` from Phase 4.5; does not implement publish.

---

### Phase 5.5 — Visual click grounding (G1 + G2 + UVG)

Moved to **Next Priority (after Phase 5.3)** above. Plan: **`docs/GROUNDING.md`**. Formal regression: **`docs/fixtures/GROUNDING_REGRESSION.md`**. **UVG (5.5b)** is current work after Tier 2 scenario A failure.

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
