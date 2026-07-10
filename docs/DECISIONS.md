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

### 2026-07-01 — Phase 3 persona report (trace synthesis + optional Gemini)

**Status:** Accepted

**Context:**
Phase 3 needs a minimal user-facing report from trace data, written from the participant persona perspective, without auto-classifying UX defects from click verification.

**Decision:**
- Output file: **`persona_report.md`** (first-person narrative sections + reviewer appendix).
- **A (always):** Trace synthesis from `action_trace.json` + `ux_result.json` — persona setup/outcome/journey/friction/evidence/reviewer notes.
- **B (optional):** Gemini polish via `--persona-report-gemini` or `PERSONA_REPORT_GEMINI=1`; skipped for `--use-stub`; fallback to A on API failure.
- `ux_result.json` gains `artifacts.persona_report` and `report.synthesis` (`trace_only`, `trace+gemini`, `gemini_failed_fallback`).
- Optional findings only under explicit criteria; verification `interaction_hint` stays telemetry-only.
- stderr: `SELECTED_PERSONA_REPORT=trace` or `trace+gemini`.

**Reasoning:**
Persona voice matches product intent; trace synthesis keeps stub/offline runs usable; optional Gemini improves readability without blocking the runner.

**Consequences:**
- New module: `scripts/core/report.py`
- Phase 4 formal `ux_report.md` / `index.html` remain separate deliverables

---

### 2026-07-03 — Phase 4 formal reports and Skill-ready ux_result.json

**Status:** Accepted

**Context:**
OpenClaw needs primary user-facing report paths and a structured summary block in `ux_result.json` without reviving legacy report systems.

**Decision:**
- Generate **`ux_report.md`** (reviewer-facing) and **`index.html`** (primary HTML report) on every run from trace + `ux_result.json`.
- HTML embeds step/hover screenshots and optional recording; Markdown uses image links.
- Add **`skill`** block to `ux_result.json`: `return_summary`, `primary_report`, `markdown_report`, `persona_report`, `result_json`, `action_trace`, `evidence`.
- stderr prints `SELECTED_FORMAL_REPORT=enabled`.
- Content aligns with `SKILL.md`: setup, journey, verification summary, findings/classification, evidence, recommendations.

**Reasoning:**
Phase 3 `persona_report.md` stays first-person; Phase 4 reports are reviewer-facing and Skill-ready. Trace-derived only — no extra VLM call.

**Consequences:**
- New module: `scripts/core/formal_report.py`
- Phase 4.5 adds public publish + `report_url`; Phase 5 wires OpenClaw/Feishu to return that URL

---

### 2026-07-06 — Phase 5.5 visual click grounding (structural)

**Status:** Accepted — **G1 + G2 implemented**; **UVG (5.5b) accepted, not implemented** — G1+G2 failed Tier 2 scenario A

**Context:**
Figma E2E on cloud VM confirmed the visual agent loop works end-to-end, but clicks often miss controls. Screenshots show the red cursor marker beside list items (e.g. left of **English**) while the persona intent is correct. Playwright executes the coordinates returned by the VLM; Figma viewport scaling is **not** a separate coordinate space — the failure is **VLM visual grounding**, not runner mapping.

**Decision:**
- **Keep** visual-first architecture (screenshot → VLM action → browser click). No Figma API or DOM-selector-first primary path.
- **G1 — Normalized coordinates:** VLM outputs **0–1000** grid; runner maps to viewport pixels at execution boundary. Replaces raw pixel coordinates in prompts and trace (with schema/version update at implementation).
- **G2 — Hover as alignment:** Phase 1.5 hover loop remains but hover phase must **align** the marker on the target before `click_current` — for **text, icon-only, icon+label, and button** controls on the **point-click path only** (`click` with coordinates → hover → `click_current`). Scroll, `type`, `wait`, and other actions do not use G2. Off-target blank-area clicks are forbidden by prompt policy on that path.
- **G3 / UVG L1 — ROI refine:** **Mandatory** on every coordinate `click` under UVG (Phase 5.5b); not optional after Tier 2 failure.
- **G4 / UVG L3 — Dedicated grounding model:** After L1+L2 measured; optional fallback.
- Primary plan document: `docs/GROUNDING.md`.

**Reasoning:**
Prompt-only tweaks do not fix systematic coordinate estimation errors. Normalized coords address a long-standing PRD open question; hover alignment uses existing loop structure for a second visual correction pass without new adapters.

**Consequences:**
- Phase 5.5 tasks in `docs/TASKS.md`; verification in `docs/VERIFY.md` (when implemented).
- `SKILL.md` action protocol will update when G1 ships (breaking change to coordinate semantics — document in VERIFY).
- Phase 5 OpenClaw delivery may proceed in parallel; click quality expected to improve after 5.5.

---

### 2026-07-07 — G1 normalized coordinate mapping (implemented)

**Status:** Accepted (implemented)

**Context:** Phase 5.5 G1 replaces raw viewport pixels in VLM I/O with a 0–1000 grid.

**Decision:**
- VLM `x` / `y` on `move_to` and `click` are **integers 0–1000** inclusive (`coordinate_space`: `norm_1000`).
- Runner maps at execution: `x_px = round(x / 1000 * (viewport_width - 1))` (same for `y`).
- `move_by_delta` remains **pixel offsets** (not normalized).
- `action_trace.json` `schema_version` **2**; step actions record `x`, `y`, `x_px`, `y_px`, `coordinate_space`.
- Module: `scripts/core/coordinates.py`; mapping used in `scripts/core/executor.py` and trace writers.

**Reasoning:** Bounded integer grid improves VLM pointing; pixel mapping stays at adapter boundary; trace retains both spaces for audit.

**Consequences:** Breaking change for VLM prompts (no pixel coords > 1000). Stub smoke uses norm `(500, 500)` for viewport center. G2 hover alignment implemented — see G2 decision below.

---

### 2026-07-07 — G2 hover alignment phase (implemented)

**Status:** Accepted (implemented)

**Context:** G1 normalized coordinates; clicks still missed when VLM confirmed at wrong marker position. G2 makes hover an **alignment** step, not confirm-only.

**Decision:**
- **Prompts:** Observe `click` rules target control center (text / icon / composite / button). Hover phase forbids `click_current` when marker is off-target; requires `move_to` / `move_by_delta` to align first. Observe phase must not use `click_current`.
- **Sub-loop:** Up to `MAX_HOVER_ALIGNMENT_PASSES` (3) reposition passes after initial `move_to`; each pass captures a hover screenshot (`step-NNN-hover.png`, then `-hover-2`, …).
- **Optional VLM fields:** `target_kind` (`text`|`icon`|`composite`|`button`); `alignment` on `click_current` (`aligned`|`adjusted`|`clicked_off_target`).
- **Trace:** `hover.alignment`, `hover.alignment_passes`, `hover.target_kind`, optional `hover.adjustments` for earlier passes.

**Reasoning:** Prompt-only G2 insufficient when single hover pass executes `move_to` without re-capture; sub-loop matches structural plan in `docs/GROUNDING.md`.

**Consequences:** Figma/web regression scenarios A–C in `docs/GROUNDING.md` / `docs/VERIFY.md` for manual validation. Tier 2 scenario A (`grounding-A-test-1`) **failed** — superseded by **UVG** decision below.

---

### 2026-07-08 — UVG universal visual grounding stack (accepted, not implemented)

**Status:** Accepted — **UVG L1+L2 implemented (2026-07-08)**; Tier 2 re-validation pending; L3 if needed

**Context:** G1+G2 shipped; formal regression on Figma language list still shows large norm errors and `max_steps` exhaustion from observe-only `move_to` loops. Root cause is **single-shot full-viewport VLM coordinate estimation**, not runner mapping. Per-UI hacks (e.g. list row index) are out of scope.

**Decision:**
- **UVG** — one mandatory pipeline for **all** coordinate `click` paths (text, icon, composite, button):
  - **L1 — ROI refine:** crop ~25% viewport centered on coarse point; second VLM norm in crop → global coords (**mandatory**, not optional G3).
  - **L2 — Convergence hover:** multi-pass hover until `aligned` or `blocked`; hover budget **separate from** `max_steps`; no alignment via repeated observe `move_to`.
  - **L3 — Spatial model:** bbox / dedicated pointing — only after L1+L2 measured; requires separate DECISIONS for dependency.
- **Sign-off:** Tier 2 fixtures A–C each ≥2/3 final-hover on target; see `docs/GROUNDING.md` UVG sign-off table.
- Primary plan: `docs/GROUNDING.md` (UVG section).

**Reasoning:** Format (G1) and alignment policy (G2) do not remove estimation variance; universal fix requires smaller reference frame (L1) + closed-loop convergence (L2).

**Consequences:** Phase 5.5b tasks in `docs/TASKS.md`; G3 reframed as mandatory L1; G4 as optional L3. **Implementation:** `scripts/core/refine.py`, loop integration, `grounding: uvg` in trace.

---

### 2026-07-03 — Phase 5 OpenClaw integration scope

**Status:** Accepted (planned — not implemented)

**Context:**
Phase 4.5 provides public `skill.report_url` on the cloud VM. Phase 5 connects OpenClaw + Feishu so users trigger runs in natural language and receive summary + clickable report links.

**Decision:**
- **Deployment:** OpenClaw Skill and runner run on the **same VM** (`170.106.175.128`); OpenClaw invokes `scripts/ux_testing.py` via **local subprocess**.
- **NL → structured input:** **OpenClaw main agent** extracts Skill fields per `SKILL.md` — **not** a parser in this repo.
- **Feishu:** Use the **existing OpenClaw Feishu channel** for user-facing replies.
- **User reply:** Built from `ux_result.json` (`skill.return_summary`, `skill.report_url`, terminal fields) — not raw stderr/trace.
- **`run_id`:** OpenClaw should pass `--run-id` correlated to Feishu context when possible (e.g. message id).
- **Publish:** OpenClaw subprocess must inherit `UX_REPORT_PUBLIC_DIR` and `UX_REPORT_PUBLIC_BASE_URL`; Phase 5 does not re-implement publish.

**Reasoning:**
Keeps runner focused on visual testing; orchestration and NL live in OpenClaw where Feishu channel already exists. Same-VM avoids remote exec complexity.

**Consequences:**
- Primary plan: `docs/OPENCLAW_INTEGRATION.md`
- Phase 5 split: 5.1 integration contract (this repo), 5.2 OpenClaw wiring, 5.3 Feishu E2E verification
- Optional runner helpers: `format_skill_reply.py`, `skill.recording_url`, `invoke_runner.sh` — **implemented** (5.1)
- PRD open question on NL ownership resolved: OpenClaw layer

---

### 2026-07-03 — Phase 4.5 public report publish (runner-only)

**Status:** Accepted (implemented 2026-07-03)

**Context:**
Phase 4 writes `index.html` under local `output_dir` (e.g. `/tmp/...`). Users need a **public HTTP URL** to open the report in a browser **before** OpenClaw/Feishu integration. Publishing must copy the **entire** output directory so relative screenshot/recording paths work.

**Decision:**
- **Optional publish** when **both** env vars are set:
  - `UX_REPORT_PUBLIC_DIR` — e.g. `/var/www/ux-reports`
  - `UX_REPORT_PUBLIC_BASE_URL` — e.g. `http://170.106.175.128:8080` (no trailing slash)
- **`run_id`:** optional CLI `--run-id` or env `RUN_ID`; if omitted, runner generates `{UTC_timestamp}-{short_uuid}` (e.g. `20260703-154812-a1b2c3d4`).
- **`publish()`:** atomically copy full run `output_dir` → `$UX_REPORT_PUBLIC_DIR/<run_id>/`.
- **`ux_result.json` → `skill`:** add `report_url` (`{BASE_URL}/{run_id}/index.html`) and `report_base_url` (`{BASE_URL}/{run_id}/`). Omit when publish env not set.
- **stderr:** `report_url=...`, `run_id=...`, `SELECTED_REPORT_PUBLISH=enabled|disabled`.
- **Static host is ops, not runner:** e.g. `python3 -m http.server 8080 --bind 0.0.0.0 --directory /var/www/ux-reports` or nginx. Document in `docs/VERIFY.md`.

**Reasoning:**
Separates report generation (Phase 4) from public delivery. OpenClaw Phase 5 only reads `skill.report_url` — no duplicate publish logic.

**Consequences:**
- Implemented in `scripts/core/publish.py`; wired from `scripts/core/loop.py` and `scripts/ux_testing.py`
- Security/retention (HTTP, no auth, disk cleanup) documented; HTTPS/auth out of scope for 4.5
- Publish requires **both** env vars; setting only one disables publish with a stderr warning
- Reusing the same `run_id` replaces the prior published directory (no merge)
- Phase 5 exit criteria updated to use public `report_url` in user/Feishu reply

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

## 2026-07-08 — Scenario A fixture: setup flow goal (not “Select English”)

**Status:** Accepted

**Context:**
Tier 2 grounding regression initially used goal `Select English.` on the language list — a micro-goal for text-row click testing. Product scope (`docs/PRD.md`, `SKILL.md`) is **first-time tablet setup to home screen**. A Chinese persona with goal “select English” is unrealistic; persona + goal must align so the VLM exercises the real setup path.

**Decision:**
- Scenario A fixture goal: **`Complete the first-time tablet setup: set a 4-digit lock screen PIN, enable the Tianxi intelligent agent (天喜智能体), including recording the wake word, and reach the home screen (desktop).`**
- Scenario A persona: **cautious first-time Chinese tablet user** (expects Chinese UI).
- Pass criteria: `terminal_state: done` on desktop in ≥2/3 runs; trace shows **简体中文**, **4-digit PIN**, **Tianxi + wake word**; per-step hover on stated target.
- Env: `FIGMA_SETUP_PROTO_URL` (primary); `FIGMA_LANGUAGE_LIST_URL` retained as alias for same proto URL.

**Reasoning:**
Goal drives task completion; persona drives realistic choices. Grounding is still verified per click (hover screenshots + trace), but acceptance is tied to the PRD setup scenario, not a forced English pick.

**Consequences:**
- `docs/fixtures/GROUNDING_REGRESSION.md`, `docs/GROUNDING.md`, `docs/VERIFY.md` updated.
- Prior runs with `Select English.` (e.g. `grounding-A-uvg-1`) are UVG pipeline references only — not formal Scenario A sign-off.

---

## 2026-07-09 — UVG L2 convergence: stall detection + adjusted click

**Status:** Accepted

**Context:**
Real-web runs (e.g. Lenovo `web-lenovo-gaming-1`) could `blocked` after 6 hover passes when VLM kept issuing tiny `move_to` adjustments on small composite chips without ever `click_current`. Prompt-only strict center alignment was insufficient.

**Decision:**
- Hover prompt includes **alignment pass** / **max passes** and convergence rules (prefer `click_current` with `adjusted` after pass 2+ when marker overlaps target).
- Runner **`should_force_hover_click`**: on **final pass** or when **stall/oscillation** detected (≥3 micro-moves), coerce `move_to` → `click_current` with `alignment: adjusted`.
- `blocked` after hover exhaust reserved for truly off-target final state — not endless micro-nudge failure.

**Consequences:**
- `scripts/core/hover.py`, `loop.py`, `vlm.py`; tests in `.tmp/test_hover_alignment.py`.

---

## 2026-07-10 — OpenClaw skill install: SKILL.md frontmatter only (not Agent Instructions)

**Status:** Accepted

**Context:**
Phase 5.2 docs previously said to paste `AGENT_PROMPT.md` into OpenClaw Agent Instructions. OpenClaw 2026.4.x loads skills from directories containing `SKILL.md` with YAML frontmatter (`name`, `description`); the markdown body is injected automatically. A copy without frontmatter at `~/.openclaw/skills/oc-visual-test-runner/` did not appear in `openclaw skills list`. Legacy `ux_test_runner` (`ux-test-skill/`) is a **different** skill and must not be conflated with `oc-visual-test-runner`.

**Decision:**
- Canonical installable skill: `docs/openclaw/OPENCLAW_SKILL.md` with frontmatter `name: oc-visual-test-runner`.
- Install path: `~/.openclaw/skills/oc-visual-test-runner/SKILL.md`.
- `AGENT_PROMPT.md` is reference-only — do not paste into Agent Instructions.
- Phase 5 verification uses **`oc-visual-test-runner` only**, not `ux_test_runner`.

**Consequences:**
- Operators: `cp` skill file → `openclaw skills list | grep oc-visual` → Feishu `/new` or gateway restart → NL E2E.
- Docs: `OPENCLAW_INTEGRATION.md`, `TASKS.md`, `VERIFY.md`, `AGENT_PROMPT.md` updated.

---

## 2026-07-10 — Feishu reply: Status / Summary / Full report + language match

**Status:** Accepted

**Context:**
Operators want a short Feishu reply after each run: completion vs blocked (with reason), test summary, and full report link. Replies must follow the user’s language (Chinese vs English).

**Decision:**
- `format_feishu_reply` emits **Status** (+ **Reason** for blocked/stop), **Summary**, **Full report** (optional Recording).
- Language auto-detects CJK in `goal`/`persona` (override `--lang zh|en`).
- OpenClaw Agent must send formatter stdout unchanged.

**Consequences:**
- `scripts/core/skill_return.py`, `format_skill_reply.py`, `SKILL.md`, OpenClaw skill docs updated.
- Summary body text still comes from run artifacts (may remain English if VLM wrote English); chrome/labels are localized.

---

## 2026-07-10 — Harden OpenClaw SKILL.md against legacy tool confusion

**Status:** Accepted

**Context:**
Feishu Agent often acknowledged UX test requests without running `invoke_runner.sh`, or invoked legacy `ux_test_runner` / `--report-file` flows (ascii codec JSON errors) while SSH runs succeeded. OpenClaw `tools.allow` needed `exec`; project `.venv` must be used (system python3 lacks playwright site-packages when not via venv).

**Decision:**
- Strengthen `docs/openclaw/OPENCLAW_SKILL.md` with **Hard rules**, canonical exec block (venv PATH + UTF-8 + publish env), and ban on `ux_test_runner` / `--report-file`.
- `invoke_runner.sh` **refuses** fallback to system `python3` if `.venv/bin/python3` is missing.
- Operators should temporarily disable `ux-test-skill` during Phase 5.3 validation.

**Consequences:**
- After `cp` skill + gateway restart / `/new`, Feishu diag must create `/tmp/ux_<run_id>`.
- Skill text is still advisory to the LLM; disabling the legacy skill remains recommended.

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
