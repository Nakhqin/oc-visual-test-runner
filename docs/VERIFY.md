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

## Phase 1 — Browser Visual Runner (Current)

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

- [ ] `python3 ./scripts/ux_testing.py --help` succeeds
- [ ] `GOOGLE_API_KEY` is set in `.env` or your shell (never commit the key)
- [ ] You have a **Figma prototype URL** (share link that opens the prototype in browser)
- [ ] You have a **live website URL** to test
- [ ] Output directories are empty or new for each run (avoid mixing artifacts)

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
FIGMA_PERSONA="A first-time tablet user who is cautious and not familiar with this device."
FIGMA_GOAL="Complete the first-time setup flow shown in the prototype."
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
$FIGMA_PERSONA = "A first-time tablet user who is cautious and not familiar with this device."
$FIGMA_GOAL = "Complete the first-time setup flow shown in the prototype."
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

Mark Phase 1 **Done** in `docs/TASKS.md` only when:

- [ ] Test A (web + Gemini) checklist complete
- [ ] Test B (figma + Gemini) checklist complete
- [ ] Both runs produced: `ux_result.json`, `action_trace.json`, `ux_test_recording.webm`, `screenshots/`
- [ ] No secrets committed (`.env` stays local)
- [ ] Known limitations documented (e.g. login-required Figma, timeout, max_steps) in your test notes or PR

**Not required for Phase 1:**

- `ux_report.md` / `index.html` (Phase 4)
- OpenClaw end-to-end Skill delivery (Phase 5)
- Post-click verification / hover loop (Phase 1.5 / 2)

---

### Troubleshooting

| Symptom | Likely cause | What to try |
|---|---|---|
| `SELECTED_DECISION_MAKER=stub` | No `GOOGLE_API_KEY` | Set key in `.env` or shell; do not pass `--use-stub` |
| Playwright browser missing | Chromium not installed | `python -m playwright install chromium` |
| Figma timeout / blank screenshot | Login, slow load, wrong URL | Use public prototype link (`figma.com/proto/...`); increase `--timeout-seconds`; adapter waits after `domcontentloaded` for canvas render |
| `terminal_state=blocked` + VLM 404 model | Deprecated model id | `gemini-2.0-flash` shut down 2026-06-01; set `GEMINI_MODEL=gemini-2.5-flash` or `gemini-3.5-flash` |
| `terminal_state=blocked` + VLM error | API key, quota, network | Check key; confirm `generativelanguage.googleapis.com:443`; adjust `GEMINI_REQUEST_TIMEOUT_SECONDS` |
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
- [ ] Clicks use visual coordinates, not Figma node IDs or CSS selectors
- [ ] Failed click logged without automatic UX defect classification

### Verify Phase 3+ Output (Future)

```bash
# Phase 3 — minimal report (path TBD in DECISIONS.md)
# Phase 4 — formal reports
ls /tmp/ux_report_output/ux_report.md
ls /tmp/ux_report_output/index.html
```

### Documentation: OpenClaw Skill Usage Model

After Skill documentation updates, confirm:

- [ ] `SKILL.md` describes NL user input → structured input → CLI → artifacts → user-facing return
- [ ] `docs/PRD.md` documents three main usage scenarios (web redesign, Figma prototype, future devices)
- [ ] User-facing vs system-facing output files are distinguished
- [ ] Phase 1 output does **not** claim `ux_report.md` or `index.html` exist yet
- [ ] Android / Windows described as planned only

---

## General Definition of Done

A task is done only when:

- Relevant code or docs updated for the **current phase** in `docs/TASKS.md`
- Verification steps run or explicitly marked N/A for the phase
- Changed files summarized
- Risks listed
- No secrets exposed
- Architecture decisions recorded in `docs/DECISIONS.md` when applicable
