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

### Install Dependencies

```bash
# Placeholder — update when Phase 1 lands
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# Set GOOGLE_API_KEY locally — never commit .env
```

### Run CLI Help

```bash
python3 ./scripts/ux_testing.py --help
```

### Figma Target Smoke Test

```bash
python3 ./scripts/ux_testing.py \
  --target figma \
  --url "$URL" \
  --persona "$PERSONA" \
  --goal "$GOAL" \
  --output-dir /tmp/ux_report_output \
  --max-steps 10
```

### Web Target Smoke Test

```bash
python3 ./scripts/ux_testing.py \
  --target web \
  --url "$URL" \
  --persona "$PERSONA" \
  --goal "$GOAL" \
  --output-dir /tmp/ux_report_output \
  --max-steps 10
```

### Verify Output Files

```bash
ls /tmp/ux_report_output/ux_result.json
ls /tmp/ux_report_output/action_trace.json
ls /tmp/ux_report_output/ux_test_recording.webm
ls /tmp/ux_report_output/screenshots/
```

### Inspect Trace

```bash
# Placeholder — inspect structure once schema is defined
cat /tmp/ux_report_output/action_trace.json
ls /tmp/ux_report_output/screenshots/
```

### Lint / Test (Future)

```bash
# Placeholder — depend on chosen stack
pytest
ruff check .
```

### Manual Verification (Phase 1+)

- [ ] Run completes with terminal state in `ux_result.json`
- [ ] `action_trace.json` records steps with actions and observation refs
- [ ] Screenshots exist for each step
- [ ] `ux_test_recording.webm` captures the session
- [ ] Clicks use visual coordinates, not Figma node IDs or CSS selectors
- [ ] Failed click logged without automatic UX defect classification

---

## General Definition of Done

A task is done only when:

- Relevant code or docs updated for the **current phase** in `docs/TASKS.md`
- Verification steps run or explicitly marked N/A for the phase
- Changed files summarized
- Risks listed
- No secrets exposed
- Architecture decisions recorded in `docs/DECISIONS.md` when applicable
