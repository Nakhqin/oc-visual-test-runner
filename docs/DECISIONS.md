# Decisions

Record meaningful product and engineering decisions here.

---

### 2026-06-24 — Adopt universal visual agent runner architecture

**Status:** Accepted

**Context:**
The project needs one orchestration model that works across Figma prototypes, websites, and future platforms.

**Decision:**
Organize the runner around a **universal visual agent loop**: target config → platform adapter → observation frame → VLM action decision → action execution → feedback observation → trace/result output.

**Reasoning:**
Single loop reduces duplication; new targets add adapters, not new runners.

**Consequences:**
- CLI entry at `scripts/ux_testing.py` orchestrates the loop (Phase 1).
- Android/Windows plug in as future adapters.

---

### 2026-06-24 — Use shared browser adapter for figma and web

**Status:** Accepted

**Context:**
Phase 1 targets are Figma prototype URLs and web URLs. Both render in a browser surface.

**Decision:**
Implement one **browser platform adapter** serving both `figma` and `web` targets. Target type affects navigation/wait behavior only.

**Reasoning:**
Avoids duplicate automation stacks; Figma prototypes are exercised as browser pages.

**Consequences:**
- No separate Figma runner vs web runner in Phase 1.
- Figma-specific quirks handled in adapter config, not a second codebase path.

---

### 2026-06-24 — Treat Android and Windows as future adapters

**Status:** Accepted

**Context:**
Mobile and desktop native surfaces require different capture and input mechanisms.

**Decision:**
Document `android` and `windows` as **planned future adapter targets**. Design in Phase 5; implementation exploration in Phase 6. Do not implement in Phase 0–1.

**Reasoning:**
Keeps Phase 1 focused on browser-based validation of the visual agent loop.

**Consequences:**
SKILL.md and docs list android/windows as planned only.
Phase 5 produces design docs; Phase 6 produces spikes.

---

### 2026-06-24 — Use low-frequency observation frames before full real-time streaming

**Status:** Accepted

**Context:**
Continuous video streaming to the VLM would increase cost and complexity.

**Decision:**
Capture **observation frames at loop cadence** (screenshot per step) before investing in full real-time streaming.

**Reasoning:**
Sufficient for persona walkthroughs in Phase 1; simpler to implement and debug.

**Consequences:**
Transient UI feedback may be missed until Phase 1.5 hover loop or higher capture rates.
Screen recording (`ux_test_recording.webm`) provides human review, not per-frame VLM input initially.

---

### 2026-06-24 — Require cursor marker and hover observation in Phase 1.5

**Status:** Accepted

**Context:**
Coordinate-only clicks without visible cursor feedback reduce VLM spatial reasoning quality.

**Decision:**
Phase 1.5 adds a **cursor marker overlay** and **hover-before-click observation** in the agent loop.

**Reasoning:**
Improves persona simulation fidelity and action explainability.

**Consequences:**
Phase 1 may ship without hover loop; Phase 1.5 is a required follow-up, not optional polish.
Trace should record hover/marker steps when enabled.

**Implementation (2026-07-01):** Red DOM cursor marker on all observation frames; `click` intents trigger `step-NNN-hover.png` and a second VLM call (`phase=hover`) before `click_current` or adjust/wait/block. See `scripts/core/hover.py`, `scripts/core/loop.py`, `docs/VERIFY.md` Phase 1.5.

---

### 2026-07-01 — Phase 2 post-click verification (telemetry only)

**Status:** Accepted

**Context:**
After click actions, the runner must detect visible UI change, retry bounded times when unchanged, and distinguish automation telemetry from UX findings.

**Decision:**
- After `click` / `click_current`, capture **marker-free** before/after screenshots and compare URL + image diff ratio (Pillow).
- Default **1 retry** (`CLICK_VERIFY_MAX_RETRIES=1` → up to 2 attempts total).
- Record `verification` on execution payloads in `action_trace.json` with `outcome`, `attempts`, `retry_count`, and optional `interaction_hint`.
- `interaction_hint` values (`possible_click_miss`, `possible_ui_no_response`, `inconclusive_no_visible_change`) are **telemetry only** — never promoted to `ux_result.json` classifications automatically.

**Reasoning:**
Cursor marker would invalidate observation-frame diffs; marker-free verify snapshots isolate page content change. Bounded retry reduces flaky single-shot misses without infinite loops.

**Consequences:**
- New dependency: `Pillow` for screenshot diff
- Verify snapshots under `screenshots/verify/`
- stderr prints `SELECTED_POST_CLICK_VERIFY=enabled`
- Env tuning: `CLICK_VERIFY_MAX_RETRIES`, `CLICK_VERIFY_POST_WAIT_MS`, `CLICK_VERIFY_IMAGE_DIFF_RATIO_THRESHOLD`

---

### 2026-06-24 — Failed clicks must not automatically be classified as UX issues

**Status:** Accepted

**Context:**
Click failures may stem from prototype limits, automation limits, wrong targets, or no visible response—not necessarily bad UX.

**Decision:**
Failed clicks are **runner telemetry**. UX findings require explicit persona reasoning or verified criteria—never automatic promotion from click failure alone.

**Reasoning:**
Separates automation reliability from product UX quality.

**Consequences:**
Classification schema uses distinct categories (UX issue, prototype limitation, automation limitation, etc.) per `SKILL.md`.
Phase 2 verification informs but does not auto-tag UX defects.

---

### 2026-06-24 — Phase 1 package layout and CLI defaults

**Status:** Accepted

**Context:**
Phase 1 needs a stable entrypoint and config model before browser adapter and agent loop land.

**Decision:**
- CLI entry: `scripts/ux_testing.py`
- Config module: `scripts/core/config.py` with `TargetConfig` dataclass
- Future loop/writers under `scripts/core/`; platform adapters under `scripts/adapters/` (next slices)
- CLI defaults: `max_steps=10`, `timeout_seconds=180` (aligned with `.env.example`)
- Phase 1 dependencies in `requirements.txt`: Playwright + `google-genai` (migrated from deprecated `google-generativeai`)

**Reasoning:**
Keeps the first vertical slice small: validate inputs and `--help` before Playwright/Gemini wiring.

**Consequences:**
- `python3 ./scripts/ux_testing.py --help` is the first runtime verification step
- Full runs remain blocked until browser adapter and visual agent loop ship

---

### 2026-06-24 — Browser adapter first slice: open URL and capture frame

**Status:** Accepted

**Context:**
Phase 1 needs a shared browser surface for `figma` and `web` before the visual agent loop and VLM integration.

**Decision:**
- Implement `scripts/adapters/browser.py` with `BrowserPlatformAdapter`
- Use Playwright Chromium, headless, default viewport 1280×900
- `figma` navigation waits for `networkidle`; `web` uses `domcontentloaded`
- First slice: open URL, capture `screenshots/step-000.png`, print `SELECTED_*` metadata from CLI
- Recording, click/scroll actions, and trace writers follow in later Phase 1 tasks

**Consequences:**
- CLI exits 0 after initial capture; agent loop still returns a not-implemented message on stderr
- Full Phase 1 exit criteria still require loop, VLM, and complete output contract

---

### 2026-06-24 — Phase 1 JSON artifact schema v1

**Status:** Accepted

**Context:**
OpenClaw needs structured `ux_result.json` and `action_trace.json` before the full visual agent loop exists.

**Decision:**
- Add `scripts/core/writers.py` with schema version `"1"`
- `action_trace.json` records initial observation step with screenshot ref and page URL
- `ux_result.json` uses `terminal_state: blocked` until the agent loop can continue the walkthrough
- `classifications` remains empty on this slice — no UX issue inferred from capture-only runs
- `artifacts.recording` is `null` until `.webm` capture lands

**Consequences:**
- CLI writes both JSON files after initial browser capture
- Schema may evolve in Phase 4 when Skill integration hardens `ux_result.json`

---

### 2026-06-24 — Visual agent loop skeleton with stub decision maker

**Status:** Accepted

**Context:**
Phase 1 needs the observe → decide → record loop before Gemini integration.

**Decision:**
- Add `scripts/core/loop.py` to orchestrate browser capture, decision, and artifact writes
- Add `scripts/core/actions.py` for minimal `Action` types and terminal detection
- Add `scripts/core/decision.py` with `StubDecisionMaker` returning `blocked` until VLM lands
- Refactor `scripts/core/writers.py` to `TraceBuilder` + `write_loop_artifacts`
- Stub-blocked runs classify as `automation limitation` (runner cannot decide persona actions yet)
- Action execution and feedback observation remain `null` until executor ships

**Consequences:**
- CLI runs full loop skeleton and writes updated trace/result JSON
- Next slice: swap `StubDecisionMaker` for Gemini client and add action executor

---

### 2026-06-24 — Gemini VLM decision maker

**Status:** Accepted

**Context:**
Phase 1 needs persona-based action decisions from observation frames.

**Decision:**
- Add `scripts/core/vlm.py` with `GeminiDecisionMaker` using `google-generativeai`
- Default model: `gemini-2.0-flash` (override via `GEMINI_MODEL`)
- API key from `GOOGLE_API_KEY`; fallback to `StubDecisionMaker` when unset
- CLI flag `--use-stub` forces stub for local testing
- VLM returns JSON actions per `SKILL.md`; parse failures become `blocked` with system-runtime classification
- Persona-driven `blocked`/`done` from Gemini do not auto-map to UX issue classifications
- Action execution in browser remains TODO — non-terminal actions advance the loop without executing

**Consequences:**
- CLI prints `SELECTED_DECISION_MAKER=gemini|stub` on stderr
- Next slice: action executor in browser adapter

---

### 2026-06-25 — Browser action executor for visual agent loop

**Status:** Accepted

**Context:**
Gemini can return non-terminal actions, but the loop previously recorded `execution: null` without acting.

**Decision:**
- Add `scripts/core/executor.py` to map `Action` → browser adapter calls
- Extend `BrowserPlatformAdapter` with `move_to`, `click`, `scroll`, `type`, `wait`, cursor tracking
- Loop executes non-terminal actions, records `execution` in trace, pauses briefly for UI feedback
- Execution failures are logged in trace — not auto-classified as UX issues
- Terminal actions (`done`, `blocked`) skip execution

**Consequences:**
- Multi-step runs can progress when VLM returns click/scroll/wait actions
- `.webm` recording and post-click verification remain future work

---

### 2026-06-25 — Playwright screen recording to ux_test_recording.webm

**Status:** Accepted

**Context:**
Phase 1 output contract requires `ux_test_recording.webm` for human review and OpenClaw evidence links.

**Decision:**
- Enable Playwright `record_video_dir` on browser context during visual agent loop runs
- Finalize recording on context close and move to `output_dir/ux_test_recording.webm`
- Set `artifacts.recording` in `ux_result.json` when file exists
- CLI prints `recording=` path on stderr

**Consequences:**
- Phase 1 JSON + screenshot + recording output contract is complete
- Recording quality and codec settings may be tuned later in DECISIONS if needed

---

### 2026-07-01 — Migrate Gemini client to google-genai and update default model

**Status:** Accepted

**Context:**
Google shut down `gemini-2.0-flash` on 2026-06-01. The deprecated `google-generativeai` package is EOL. Cloud E2E runs returned 404 for the old model id; Figma navigation often timed out waiting for `networkidle`.

**Decision:**
- Replace `google-generativeai` with `google-genai` in `scripts/core/vlm.py`
- Default model: `gemini-2.5-flash` (override via `GEMINI_MODEL`)
- Per-request HTTP timeout via `GEMINI_REQUEST_TIMEOUT_SECONDS` (default 90)
- Figma opens with `domcontentloaded` plus a fixed post-load wait; drop `networkidle` for figma

**Reasoning:**
Restores Gemini E2E on current API models; avoids indefinite VLM hangs; fixes Figma prototype loads in headless cloud runners.

**Consequences:**
- `requirements.txt` and `.env.example` updated
- `docs/VERIFY.md` troubleshooting reflects new model ids and Figma load behavior

---

## Decision Template

### YYYY-MM-DD — Decision Title

**Status:** Proposed / Accepted / Rejected / Superseded

**Context:**
...

**Decision:**
...

**Reasoning:**
...

**Consequences:**
...

---
