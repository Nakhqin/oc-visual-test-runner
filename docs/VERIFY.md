# Verification — oc-visual-test-runner

How to verify changes at each project stage.

## Phase 0 — Documentation Scaffold (Complete)

No runtime to execute. Verify documentation and scope only.

### Automated Checks

```bash
# From repo root — confirm key files exist
ls README.md SKILL.md AGENTS.md START_HERE.md docs/PRD.md docs/ARCHITECTURE.md docs/TASKS.md docs/DECISIONS.md docs/VERIFY.md docs/CONTEXT.md
```

```bash
# Confirm no runtime implementation directories were created
# (these should not exist in Phase 0 unless already present before conversion)
test ! -d scripts/core && test ! -d scripts/adapters && test ! -d scripts/targets && echo "OK: no impl dirs"
```

```bash
# Confirm starter-kit naming is gone (should return no matches)
grep -r "nana-cursor-starter" README.md SKILL.md AGENTS.md docs/ 2>/dev/null || echo "OK: no starter-kit name"
grep -r "starter kit" README.md SKILL.md docs/ 2>/dev/null || echo "OK: no starter-kit reference"
```

### Manual Checklist

- [x] Starter-kit naming has been fully replaced with oc-visual-test-runner
- [x] `README.md` describes project name, Phase 1 targets (`figma`, `web`), planned targets (`android`, `windows`), architecture, CLI shape, output contract, Phase 0 non-goals
- [x] `SKILL.md` exists and describes skill contract: inputs, outputs, action protocol, classifications
- [x] `docs/` files are no longer TODO placeholders — they reflect the real project
- [x] No runtime implementation files were created (`scripts/ux_testing.py`, `scripts/core/`, adapters, etc.)
- [x] No secrets were added — `.env.example` has placeholders only
- [x] Git diff only includes scaffold/context files (docs, rules, README, SKILL, AGENTS, START_HERE, `.env.example`, `.gitignore`, `.cursorignore`)

### Definition of Done (Phase 0)

- All checklist items pass
- `docs/TASKS.md` Phase 0 marked Done
- Summary includes changed files, verification, risks, open questions

---

## Phase 1 — Browser Visual Runner (Complete)

Verified **2026-07-01** on a cloud runner with direct Gemini API access. Phase 1.5 is current — see `docs/TASKS.md`.

Phase 1 is **not Done** until you complete the [End-to-End Verification Checklist](#phase-1-end-to-end-verification-checklist) below on **one Figma prototype URL** and **one web URL** with the full output contract.

### One-Time Setup

From repo root:

```bash
python3 -m venv .venv
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
# Edit .env — set GOOGLE_API_KEY locally; never commit .env
```

**macOS / Linux:**

```bash
source .venv/bin/activate
pip install -r requirements.txt
python3 -m playwright install chromium
cp .env.example .env
# Set GOOGLE_API_KEY in .env — never commit .env
```

Optional in `.env`:

```text
GEMINI_MODEL=gemini-2.5-flash
GEMINI_REQUEST_TIMEOUT_SECONDS=90
URL=
PERSONA=
GOAL=
OUTPUT_DIR=/tmp/ux_report_output
```

### Quick Sanity Check (optional, no API key)

Confirms CLI, browser, JSON, and recording without calling Gemini:

```bash
python3 ./scripts/ux_testing.py --use-stub \
  --target web \
  --url "https://example.com" \
  --persona "first-time visitor" \
  --goal "view homepage" \
  --output-dir /tmp/ux_report_output
```

**Windows:** `--output-dir` can be `C:\temp\ux_report_output` or `/tmp/ux_report_output` (both work on many setups).

Expect stderr:

```text
SELECTED_DECISION_MAKER=stub
SELECTED_TARGET=web
SELECTED_ADAPTER=browser
SELECTED_RUNNER=visual_agent
terminal_state=blocked
```

Expect files:

```bash
ls /tmp/ux_report_output/ux_result.json
ls /tmp/ux_report_output/action_trace.json
ls /tmp/ux_report_output/ux_test_recording.webm
ls /tmp/ux_report_output/screenshots/step-000.png
```

---

### Phase 1 End-to-End Verification Checklist

Use this checklist to close Phase 1. Run **both** targets with **Gemini** (not `--use-stub`). Replace placeholders with your real URLs and scenarios.

#### Before you start

- [x] `python3 ./scripts/ux_testing.py --help` succeeds
- [x] `GOOGLE_API_KEY` is set in `.env` or your shell (never commit the key)
- [x] You have a **Figma prototype URL** (share link that opens the prototype in browser)
- [x] You have a **live website URL** to test
- [x] Output directories are empty or new for each run (avoid mixing artifacts)

**Recommended verification setup:** Run Gemini E2E on a host that can reach `generativelanguage.googleapis.com:443` (e.g. US cloud runner). Local stub runs (`--use-stub`) validate Playwright without Gemini. If local Gemini times out on 443, use the cloud runner — do not treat that as a runner defect.

#### Test A — Web target (Gemini)

Pick a real page and a persona scenario, for example a pricing page walkthrough.

**macOS / Linux:**

```bash
export GOOGLE_API_KEY="your-key-here"   # or rely on .env if your shell loads it

WEB_URL="https://example.com"
WEB_PERSONA="A first-time visitor who has never seen this product before."
WEB_GOAL="Understand what the product does and try to find pricing information."
WEB_OUTPUT="/tmp/ux_report_web"

python3 ./scripts/ux_testing.py \
  --target web \
  --url "$WEB_URL" \
  --persona "$WEB_PERSONA" \
  --goal "$WEB_GOAL" \
  --output-dir "$WEB_OUTPUT" \
  --max-steps 10 \
  --timeout-seconds 180
```

**Windows (PowerShell):**

```powershell
$env:GOOGLE_API_KEY = "your-key-here"

$WEB_URL = "https://example.com"
$WEB_PERSONA = "A first-time visitor who has never seen this product before."
$WEB_GOAL = "Understand what the product does and try to find pricing information."
$WEB_OUTPUT = "C:\temp\ux_report_web"

python scripts/ux_testing.py `
  --target web `
  --url $WEB_URL `
  --persona $WEB_PERSONA `
  --goal $WEB_GOAL `
  --output-dir $WEB_OUTPUT `
  --max-steps 10 `
  --timeout-seconds 180
```

**After Test A, confirm:**

- [ ] stderr shows `SELECTED_DECISION_MAKER=gemini`
- [ ] stderr shows `SELECTED_TARGET=web`, `SELECTED_ADAPTER=browser`, `SELECTED_RUNNER=visual_agent`
- [ ] Exit code is `0` (or document failure if non-zero)
- [ ] `ux_result.json` exists with `terminal_state` (`done`, `blocked`, `max_steps`, or `timeout`)
- [ ] `action_trace.json` has one or more steps with `observation`, `decision`, and `decision.source` = `gemini`
- [ ] `screenshots/` contains `step-000.png` (and more if multi-step)
- [ ] `ux_test_recording.webm` exists and plays
- [ ] `ux_result.json` → `artifacts.recording` is `ux_test_recording.webm`
- [ ] Open `action_trace.json`: non-terminal steps should have `execution` with `success` / `page_url_after` when Gemini returned click/scroll/wait
- [ ] Failed or blocked runs do **not** automatically tag `classifications` as UX issue without persona evidence

**Inspect web run (optional):**

```bash
python3 -c "import json; r=json.load(open('/tmp/ux_report_web/ux_result.json')); print(r['terminal_state'], r.get('classifications'))"
python3 -c "import json; t=json.load(open('/tmp/ux_report_web/action_trace.json')); print(len(t['steps']), t['steps'][0]['decision']['source'])"
```

---

#### Test B — Figma target (Gemini)

Use a **prototype** URL (often `figma.com/proto/...` or `figma.com/design/...` with prototype mode).

**macOS / Linux:**

```bash
FIGMA_URL="https://www.figma.com/proto/your-prototype-link"
FIGMA_PERSONA="A cautious first-time Chinese tablet user who is not familiar with this device. They normally read Chinese and expect the device to use Chinese."
FIGMA_GOAL="Complete the first-time tablet setup: set a 4-digit lock screen PIN, enable the Tianxi intelligent agent (天喜智能体), including recording the wake word, and reach the home screen (desktop)."
FIGMA_OUTPUT="/tmp/ux_report_figma"

python3 ./scripts/ux_testing.py \
  --target figma \
  --url "$FIGMA_URL" \
  --persona "$FIGMA_PERSONA" \
  --goal "$FIGMA_GOAL" \
  --output-dir "$FIGMA_OUTPUT" \
  --max-steps 10 \
  --timeout-seconds 180
```

**Windows (PowerShell):**

```powershell
$FIGMA_URL = "https://www.figma.com/proto/your-prototype-link"
$FIGMA_PERSONA = "A cautious first-time Chinese tablet user who is not familiar with this device. They normally read Chinese and expect the device to use Chinese."
$FIGMA_GOAL = "Complete the first-time tablet setup: set a 4-digit lock screen PIN, enable the Tianxi intelligent agent (天喜智能体), including recording the wake word, and reach the home screen (desktop)."
$FIGMA_OUTPUT = "C:\temp\ux_report_figma"

python scripts/ux_testing.py `
  --target figma `
  --url $FIGMA_URL `
  --persona $FIGMA_PERSONA `
  --goal $FIGMA_GOAL `
  --output-dir $FIGMA_OUTPUT `
  --max-steps 10 `
  --timeout-seconds 180
```

**After Test B, confirm:** (same checklist as Test A, plus Figma-specific notes)

- [ ] Prototype loaded in headless browser (check `screenshots/step-000.png` — not blank/error page)
- [ ] If Figma shows login wall or cookie gate, record as **blocked** / limitation in trace — do not treat as confirmed UX defect
- [ ] Clicks in trace use coordinates only (no Figma node IDs or CSS selectors in `action_trace.json`)

**Inspect Figma run (optional):**

```bash
python3 -c "import json; r=json.load(open('/tmp/ux_report_figma/ux_result.json')); print(r['terminal_state'], r.get('classifications'))"
```

---

#### Phase 1 Definition of Done

Phase 1 marked **Done** in `docs/TASKS.md` on **2026-07-01** when:

- [x] Test A (web + Gemini) checklist complete
- [x] Test B (figma + Gemini) checklist complete
- [x] Both runs produced: `ux_result.json`, `action_trace.json`, `ux_test_recording.webm`, `screenshots/`
- [x] No secrets committed (`.env` stays local)
- [x] Known limitations documented (see verification record below)

#### Phase 1 verification record (2026-07-01)

| Run | Target | Host | Terminal state | Steps | Notes |
|---|---|---|---|---:|---|
| Stub | web (Lenovo) | Local Windows | `blocked` (stub) | 1 | Browser + artifacts OK |
| Stub | figma (proto) | Local Windows | `blocked` (stub) | 1 | Prototype screenshot OK |
| Gemini | web (Lenovo) | Cloud runner (US) | `max_steps` | 10 | Multi-step; `decision.source=gemini` |
| Gemini | figma (proto) | Cloud runner (US) | `blocked` (503) | 5 | Steps 0–3: wait + clicks executed; step 4: Gemini **503 UNAVAILABLE** (transient API demand) |

**Documented limitations:**

- Local dev (CN): `generativelanguage.googleapis.com:443` may be blocked — use cloud runner or VPN for Gemini E2E
- `gemini-2.0-flash` retired 2026-06-01 — use `gemini-2.5-flash` (default in repo)
- Gemini **503** during peak demand — re-run; classified as `system-runtime issue`, not UX defect
- Figma: public `figma.com/proto/...` links; adapter uses `domcontentloaded` + 3s wait (not `networkidle`)

**Not required for Phase 1:**

- `ux_report.md` / `index.html` (Phase 4)
- OpenClaw end-to-end Skill delivery (Phase 5)

---

## Phase 1.5 — Hover Observation Loop

Implemented in the runner. stderr prints `SELECTED_HOVER_LOOP=enabled`.

### Behavior

1. Every observation screenshot overlays a **red circular cursor marker** at the tracked pointer.
2. When the VLM returns **`click` with coordinates**, the runner:
   - moves the pointer to `(x, y)`;
   - captures **`step-NNN-hover.png`**;
   - asks the VLM again (hover phase) to choose **`click_current`**, adjust, **`wait`**, **`done`**, or **`blocked`**.
3. `action_trace.json` records a **`hover`** object on click-intent steps with hover observation, decision, and execution.

### Quick stub check (no Gemini)

```bash
python3 ./scripts/ux_testing.py \
  --target web \
  --url "https://example.com" \
  --persona "visitor" \
  --goal "hover loop smoke" \
  --output-dir /tmp/ux_hover_stub \
  --max-steps 2 \
  --use-stub
```

**Confirm:**

- [ ] stderr shows `SELECTED_HOVER_LOOP=enabled`
- [ ] `screenshots/step-000.png` and `screenshots/step-000-hover.png` exist
- [ ] `action_trace.json` step 0 has `"phase": "observe"` and a `"hover"` block with `"phase": "hover"`
- [ ] Hover decision allows `click_current`, `move_to`, `move_by_delta`, `wait`, `done`, `blocked` only

### Gemini E2E (cloud runner)

Re-run web or figma with Gemini (no `--use-stub`). On steps where the VLM returns `click`, confirm the trace includes a `hover` block and hover screenshot.

---

## Phase 2 — Post-Click Verification

Implemented in the runner. stderr prints `SELECTED_POST_CLICK_VERIFY=enabled`.

### Behavior

1. After **`click`** or **`click_current`**, the runner captures marker-free before/after screenshots under `screenshots/verify/`.
2. Compares **URL change** and **image diff ratio** (default threshold `0.01`).
3. On **`no_visible_change`**, retries up to **`CLICK_VERIFY_MAX_RETRIES`** (default `1` → 2 total attempts).
4. Records **`verification`** on the execution object with `outcome`, `attempts`, `retry_count`, and optional **`interaction_hint`** (telemetry only — not auto UX classification).

### Verification outcomes

| `outcome` | Meaning |
|---|---|
| `visible_change` | URL changed or image diff ≥ threshold |
| `no_visible_change` | Click succeeded but page appears unchanged |
| `execution_failed` | Browser action failed |
| `not_applicable` | Non-click action (scroll, wait, move, etc.) |

### Interaction hints (telemetry only)

| `interaction_hint` | When |
|---|---|
| `possible_click_miss` | No change and diff ratio exactly `0` |
| `possible_ui_no_response` | No change after retries exhausted, with sub-threshold diff |
| `inconclusive_no_visible_change` | No change on first attempt, retry may follow |

### Quick stub check (no Gemini)

```bash
python3 ./scripts/ux_testing.py \
  --target web \
  --url "https://example.com" \
  --persona "visitor" \
  --goal "post-click verify smoke" \
  --output-dir /tmp/ux_verify_stub \
  --max-steps 2 \
  --use-stub
```

**Confirm:**

- [ ] stderr shows `SELECTED_POST_CLICK_VERIFY=enabled`
- [ ] `action_trace.json` step 0 `hover.execution.verification.applied` is `true`
- [ ] `verification.outcome` is recorded (`visible_change` or `no_visible_change`)
- [ ] `screenshots/verify/step-000-attempt-*-{before,after}.png` exist when click runs
- [ ] `ux_result.json` **does not** gain automatic UX classifications from verification alone

### Env tuning (optional)

| Variable | Default | Purpose |
|---|---|---|
| `CLICK_VERIFY_MAX_RETRIES` | `1` | Extra attempts after `no_visible_change` |
| `CLICK_VERIFY_POST_WAIT_MS` | `500` | Wait before after screenshot |
| `CLICK_VERIFY_IMAGE_DIFF_RATIO_THRESHOLD` | `0.01` | Fraction of changed pixels for `visible_change` |

---

## Phase 3 — Persona Report

Implemented in the runner. stderr prints `SELECTED_PERSONA_REPORT=trace` (or `trace+gemini` when Gemini polish is enabled).

### Behavior

1. Every run writes **`persona_report.md`** — first-person sections from trace + reviewer appendix.
2. **Trace synthesis (A)** always runs (works with `--use-stub`).
3. **Gemini polish (B)** when `--persona-report-gemini` or `PERSONA_REPORT_GEMINI=1` and Gemini decision maker is active; falls back to A on failure.
4. `ux_result.json` includes `artifacts.persona_report` and `report.synthesis`.

### Quick stub check (no Gemini)

```bash
python3 ./scripts/ux_testing.py \
  --target web \
  --url "https://example.com" \
  --persona "first-time visitor" \
  --goal "persona report smoke" \
  --output-dir /tmp/ux_persona_stub \
  --max-steps 2 \
  --use-stub
```

**Confirm:**

- [x] stderr shows `SELECTED_PERSONA_REPORT=trace` (stub) or `trace+gemini` (Gemini)
- [x] `persona_report.md` exists with persona setup, journey, friction, evidence, reviewer notes
- [x] `ux_result.json` has `artifacts.persona_report` and `report.synthesis`
- [x] Optional findings do not appear from verification telemetry alone

#### Phase 3 verification record (2026-07-03)

| Run | Target | Host | Terminal state | Report synthesis | Notes |
|---|---|---|---|---|
| Stub | web (example.com) | Local Windows | `blocked` (stub) | `trace_only` | persona_report.md OK |
| Gemini | web (example.com) | Cloud runner (US) | `max_steps` | `trace+gemini` | `SELECTED_DECISION_MAKER=gemini`; 2 steps |

---

### Optional Gemini polish (cloud runner)

```bash
export PERSONA_REPORT_GEMINI=1
python3 ./scripts/ux_testing.py \
  --target web \
  --url "https://example.com" \
  --persona "first-time visitor" \
  --goal "persona report gemini" \
  --output-dir /tmp/ux_persona_gemini \
  --max-steps 5
```

**Confirm:** `report.synthesis=trace+gemini` (or `gemini_failed_fallback` with A content preserved).

---

## Phase 4 — Formal Reports

Implemented in the runner. stderr prints `SELECTED_FORMAL_REPORT=enabled`.

### Behavior

1. Every run writes **`ux_report.md`** (reviewer-facing Markdown) and **`index.html`** (primary HTML report with embedded screenshots).
2. `ux_result.json` gains `artifacts.ux_report`, `artifacts.index_html`, and a **`skill`** block for OpenClaw integration.
3. Reports include setup, journey timeline, verification summary, findings, evidence, and recommendations per `SKILL.md`.

### Quick stub check (no Gemini)

```bash
python3 ./scripts/ux_testing.py \
  --target web \
  --url "https://example.com" \
  --persona "first-time visitor" \
  --goal "formal report smoke" \
  --output-dir /tmp/ux_formal_stub \
  --max-steps 2 \
  --use-stub
```

**Confirm:**

- [ ] stderr shows `SELECTED_FORMAL_REPORT=enabled`
- [ ] `ux_report.md` and `index.html` exist
- [ ] `index.html` renders step screenshots inline
- [ ] `ux_result.json` has `skill.primary_report=index.html` and `skill.return_summary`

#### Phase 4 verification record (2026-07-03)

| Run | Target | Host | Terminal state | Notes |
|---|---|---|---|---|
| Stub | web (example.com) | Local Windows | `blocked` (stub) | `ux_report.md` + `index.html` OK |
| Gemini | web (example.com) | Cloud runner (US) | `max_steps` | Full formal report + `trace+gemini` persona report; **no public URL yet** (Phase 4.5) |

---

## Phase 4.5 — Public Report Publish (Current)

**Implemented in runner.** See `docs/DECISIONS.md` and `scripts/core/publish.py`.

### Intended behavior

1. After Phase 4 artifacts are written, **`publish()`** copies the full `output_dir` to `$UX_REPORT_PUBLIC_DIR/<run_id>/` when publish env is configured.
2. **`run_id`:** optional `--run-id` / `RUN_ID`; default auto-generated `{timestamp}-{short_uuid}`.
3. **`ux_result.json`:** `skill.report_url`, `skill.report_base_url`.
4. **Static host (ops):** separate long-running service, e.g.:

```bash
export UX_REPORT_PUBLIC_DIR=/var/www/ux-reports
export UX_REPORT_PUBLIC_BASE_URL=http://170.106.175.128:8080

python3 -m http.server 8080 \
  --bind 0.0.0.0 \
  --directory /var/www/ux-reports
```

4. **Public URL pattern:** `{UX_REPORT_PUBLIC_BASE_URL}/{run_id}/index.html`

### Planned verification (after implementation)

```bash
export UX_REPORT_PUBLIC_DIR=/var/www/ux-reports
export UX_REPORT_PUBLIC_BASE_URL=http://<public-ip>:8080

python3 ./scripts/ux_testing.py \
  --target web \
  --url "https://example.com" \
  --persona "first-time visitor" \
  --goal "publish smoke" \
  --output-dir /tmp/ux_publish_smoke \
  --max-steps 2
```

**Confirm:**

- [ ] stderr shows `SELECTED_REPORT_PUBLISH=enabled` and `report_url=http://.../<run_id>/index.html`
- [ ] `/var/www/ux-reports/<run_id>/index.html` exists with `screenshots/`
- [ ] Opening `report_url` in a browser (public network) renders screenshots and recording
- [ ] Without publish env, run completes with `SELECTED_REPORT_PUBLISH=disabled` and no `report_url`

**Ops notes:** Open security group port for the static host; plan retention/cleanup for `/var/www/ux-reports/`; MVP uses HTTP without auth.

**Gotchas:**

- Both `UX_REPORT_PUBLIC_DIR` and `UX_REPORT_PUBLIC_BASE_URL` are required; if only one is set, publish is disabled (stderr warning).
- Reusing the same `run_id` overwrites the existing published directory.

---

## Phase 5 — OpenClaw / Feishu Skill Delivery (Current)

**Not implemented end-to-end yet.** Plan: `docs/OPENCLAW_INTEGRATION.md`. Phase 4.5 publish on VM `170.106.175.128` verified.

### Prerequisites (same VM)

- OpenClaw installed with **Feishu channel** enabled
- Runner repo + `.venv` + Playwright Chromium
- Publish env + static host on `:8080` (see Phase 4.5)
- `GOOGLE_API_KEY` for Gemini runs (no `--use-stub` for E2E)

### Phase 5.2 MVP — pathway smoke (optional, before NL)

Optional internal check — not a Phase 5 milestone. See `docs/OPENCLAW_INTEGRATION.md` **Repo helpers**.

### Phase 5.2 — pathway smoke (optional, ~5 min)

```bash
chmod +x ./scripts/openclaw/invoke_runner.sh
./scripts/openclaw/invoke_runner.sh pathway-smoke-001 web https://example.com \
  "first-time visitor" "pathway smoke" 2 --use-stub
```

**Confirm:** stdout is Feishu-ready text (Status / Summary / Full report with clickable URL).

### Phase 5.3 — Feishu NL E2E

Install skill only: sync `docs/openclaw/OPENCLAW_SKILL.md` → `~/.openclaw/skills/oc-visual-test-runner/SKILL.md`, then confirm `openclaw skills list` shows **`oc-visual-test-runner` ✓ ready**. Agent must **exec once**: venv PATH + `./scripts/openclaw/invoke_runner.sh` (stdout = Feishu reply). Do **not** use legacy `ux_test_runner` / `--report-file`. Prefer temporarily disabling `~/.openclaw/skills/ux-test-skill`. `tools.allow` must include `exec`. OpenClaw exec timeout must exceed runner `--timeout-seconds` + buffer. After Feishu run, `/tmp/ux_<run_id>` must exist.

**Example Feishu input:**

> 用 first-time visitor 测一下 https://example.com ，看看首页主要信息是否清楚。

Or explicit: `/oc-visual-test-runner` with the same request.

**Confirm:**

- [ ] OpenClaw extracts `target`, `url`, `persona`, `goal` without runner-side NL parser
- [ ] Agent actually execs (not verbal-only); `/tmp/ux_<run_id>` exists
- [ ] `--run-id` correlates to Feishu context when configured
- [ ] Feishu reply is **invoke_runner.sh stdout** (Status/Summary/Full report, or 状态/测试摘要/完整报告) — **one message**, no interim “Executing…”
- [ ] `terminal_state=blocked` or `max_steps` still returns readable summary + report link
- [ ] Runner failure (exit `1`/`2`) produces short Feishu error via `format_skill_reply.py --error`, not legacy JSON/`--report-file` errors

**Failure checks:**

- [ ] Missing publish env → Feishu warns no public link (or ops-only local path)
- [ ] Missing `GOOGLE_API_KEY` → clear error (stub not used for E2E)

---

### Troubleshooting

| Symptom | Likely cause | What to try |
|---|---|---|
| `SELECTED_DECISION_MAKER=stub` | No `GOOGLE_API_KEY` | Set key in `.env` or shell; do not pass `--use-stub` |
| Playwright browser missing | Chromium not installed | `python -m playwright install chromium` |
| Figma timeout / blank screenshot | Login, slow load, wrong URL | Use public prototype link (`figma.com/proto/...`); increase `--timeout-seconds`; adapter waits after `domcontentloaded` for canvas render |
| `terminal_state=blocked` + VLM 404 model | Deprecated model id | `gemini-2.0-flash` shut down 2026-06-01; set `GEMINI_MODEL=gemini-2.5-flash` or `gemini-3.5-flash` |
| `terminal_state=blocked` + VLM error | API key, quota, network | Check key; confirm `generativelanguage.googleapis.com:443`; adjust `GEMINI_REQUEST_TIMEOUT_SECONDS` |
| `terminal_state=blocked` + VLM 503 | Gemini API high demand (transient) | Wait and re-run; not a UX finding — `system-runtime issue` |
| `terminal_state=max_steps` | Goal too hard for `max_steps` | Increase `--max-steps` for test only; note in results |
| Recording missing | Context closed before finalize | Re-run; check `ux_test_recording.webm` path on stderr |

### Run CLI Help

```bash
python3 ./scripts/ux_testing.py --help
```

### Lint / Test (Future)

```bash
pytest
ruff check .
```

### Manual Verification (ongoing)

- [ ] Run completes with terminal state in `ux_result.json`
- [ ] `action_trace.json` records steps with actions and observation refs
- [ ] Screenshots exist for each step
- [ ] `ux_test_recording.webm` captures the session
- [ ] Runner prints `SELECTED_TARGET`, `SELECTED_ADAPTER`, `SELECTED_RUNNER` metadata
- [ ] Clicks use normalized visual coordinates (0–1000 in VLM; pixels in trace as `x_px`/`y_px`), not Figma node IDs or CSS selectors
- [ ] Failed click logged without automatic UX defect classification

### Verify Phase 4+ Output

```bash
ls /tmp/ux_report_output/persona_report.md
ls /tmp/ux_report_output/ux_report.md
ls /tmp/ux_report_output/index.html
python3 -c "import json; r=json.load(open('/tmp/ux_report_output/ux_result.json')); print(r.get('skill',{}).get('primary_report'))"
```

### Verify Phase 4.5 Output (after implementation)

```bash
python3 -c "import json; r=json.load(open('/tmp/ux_publish_smoke/ux_result.json')); print(r.get('skill',{}).get('report_url'))"
curl -I "$(python3 -c "import json; print(json.load(open('/tmp/ux_publish_smoke/ux_result.json'))['skill']['report_url'])")"
```

### Documentation: OpenClaw Skill Usage Model

After Skill documentation updates, confirm:

- [ ] `SKILL.md` describes NL user input → structured input → CLI → artifacts → user-facing return
- [ ] `docs/PRD.md` documents three main usage scenarios (web redesign, Figma prototype, future devices)
- [ ] User-facing vs system-facing output files are distinguished
- [ ] Phase 1 output does **not** claim `ux_report.md` or `index.html` exist yet
- [ ] Android / Windows described as planned only

---

## Phase 5.5 — Visual click grounding (G1 + G2)

Plan: **`docs/GROUNDING.md`**. Formal acceptance fixtures: **`docs/fixtures/GROUNDING_REGRESSION.md`**.

### Verification tiers

| Tier | Scope | Validates grounding? | 5.5 sign-off |
|---|---|:---:|:---:|
| **0 — Unit** | Coordinate + hover helpers | No | Required |
| **1 — Smoke** | `--use-stub` pipeline | **No** | Pre-merge only |
| **2 — Formal regression** | Gemini E2E, fixtures A–C (+ E spot-check) | **Yes** | **Required** |

> **Stub smoke does not prove marker alignment.** Tier 2 is mandatory before calling Phase 5.5 complete.

### Tier 0 — Unit tests (no browser)

```bash
python3 .tmp/test_coordinates.py
python3 .tmp/test_hover_alignment.py
python3 .tmp/test_refine.py
```

**Confirm:**

- [ ] All three exit 0 (`coordinates`, `hover alignment`, `refine` unit tests OK)

### Tier 1 — Smoke (stub — pipeline only)

**G1 wiring:**

```bash
python3 ./scripts/ux_testing.py \
  --target web \
  --url "https://example.com" \
  --persona "visitor" \
  --goal "G1 coordinate smoke" \
  --output-dir /tmp/ux_g1_stub \
  --max-steps 2 \
  --use-stub
```

**Confirm:**

- [ ] `schema_version` **2**, `coordinate_space` **norm_1000**
- [ ] Step 0 action has `x`/`y`, `x_px`/`y_px`

**G2 wiring:**

```bash
python3 ./scripts/ux_testing.py \
  --target web \
  --url "https://example.com" \
  --persona "visitor" \
  --goal "G2 hover alignment smoke" \
  --output-dir /tmp/ux_g2_stub \
  --max-steps 2 \
  --use-stub
```

**Confirm:**

- [ ] `hover.alignment` present; stub uses `aligned`, `alignment_passes` **1**
- [ ] **Do not** use this tier to judge click accuracy on real UIs

**UVG wiring (stub):**

```bash
python3 ./scripts/ux_testing.py \
  --target web \
  --url "https://example.com" \
  --persona "visitor" \
  --goal "UVG smoke" \
  --output-dir /tmp/ux_uvg_stub \
  --max-steps 2 \
  --use-stub
```

**Confirm:**

- [ ] stderr: `SELECTED_GROUNDING=uvg`
- [ ] `action_trace.json`: `"grounding": "uvg"`
- [ ] Step 0 click has `refine` with `coarse`, `fine`, `crop.screenshot`
- [ ] `screenshots/step-000-refine-crop.png` exists

### Tier 2 — Formal regression (Gemini E2E — required for UVG sign-off)

Run on cloud VM with `GOOGLE_API_KEY` set. **No `--use-stub`.** Required **after UVG L1+L2 implementation** for Phase 5.5 completion (G1+G2 alone insufficient — see `grounding-A-test-1`).

**Full procedure:** **`docs/fixtures/GROUNDING_REGRESSION.md`**

| Scenario | Fixture | Runs | Pass |
|---|---|---:|---|
| A — tablet setup flow | `FIGMA_SETUP_PROTO_URL` | 3 | ≥2 `done` on desktop — **passed 2026-07-09** |
| B — icon-only | `FIGMA_ICON_ONLY_URL` (fill in fixtures doc) | 3 | ≥2 marker inside icon bounds |
| C — icon + label | `FIGMA_COMPOSITE_URL` (fill in fixtures doc) | 3 | ≥2 marker on whole button |
| E — scroll/type (spot) | wikipedia.org | 1 | trace uses `scroll`/`type` appropriately |

**Per run, review:** `screenshots/step-*-refine-crop.png`, `screenshots/step-*-hover*.png`, `action_trace.json` (`refine`, `hover.alignment`, `alignment_passes`, `target_kind`).

**Record results** in the table in `docs/fixtures/GROUNDING_REGRESSION.md`.

---

## General Definition of Done

A task is done only when:

- Relevant code or docs updated for the **current phase** in `docs/TASKS.md`
- Verification steps run or explicitly marked N/A for the phase
- Changed files summarized
- Risks listed
- No secrets exposed
- Architecture decisions recorded in `docs/DECISIONS.md` when applicable
