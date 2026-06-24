# oc-visual-test-runner

A persona-based visual UX testing runner for Figma prototypes and websites. It simulates a human participant by letting a VLM observe the screen, decide a structured action, execute that action through a platform adapter, observe feedback, and continue until a terminal state is reached.

## Current Supported Targets (Phase 1)

| Target | Description |
|---|---|
| `figma` | Figma prototype URL opened in a browser |
| `web` | Normal website URL opened in a browser |

Both use a **shared browser adapter**.

## Planned Targets

| Target | Status |
|---|---|
| `android` | Future adapter (design Phase 5; implementation Phase 6) |
| `windows` | Future adapter (design Phase 5; implementation Phase 6) |

## Core Concept

```text
VLM observes screen → decides action → adapter executes → runner observes feedback → trace/result output
```

The VLM behaves like a user looking at the interface: deciding what appears actionable, moving the cursor or pointer, observing feedback, and continuing the walkthrough.

## Why This Exists

Traditional UX testing often relies on manual sessions or brittle automation (DOM selectors, Figma API node mapping). This runner simulates **persona-based UX walkthroughs** more like a human participant—visual observation and action, not selector-first scripts.

## High-Level Architecture

| Component | Role |
|---|---|
| **Visual agent loop** | Orchestrates observe → decide → act → record until terminal state |
| **Target config** | Parses `target`, `url`, `persona`, `goal`, limits |
| **Platform adapter** | Opens target, captures observations, executes actions, records evidence |
| **Observation frames** | Screenshot + metadata per loop iteration |
| **Action schema** | Structured VLM actions (`click`, `scroll`, `done`, `blocked`, etc.) |
| **Trace writer** | Persists `action_trace.json` and step screenshots |
| **Result writer** | Persists `ux_result.json` with terminal state and classifications |

```text
target config
    ↓
platform adapter
    ↓
observation frame
    ↓
VLM action decision
    ↓
action execution
    ↓
feedback observation
    ↓
trace / result output
    ↑
    └── visual agent loop (repeat)
```

## Future CLI Shape

> Planned CLI — see `docs/TASKS.md` for Phase 1 implementation status.

```bash
python3 ./scripts/ux_testing.py \
  --target figma \
  --url "$URL" \
  --persona "$PERSONA" \
  --goal "$GOAL" \
  --output-dir /tmp/ux_report_output \
  --max-steps 10
```

```bash
python3 ./scripts/ux_testing.py \
  --target web \
  --url "$URL" \
  --persona "$PERSONA" \
  --goal "$GOAL" \
  --output-dir /tmp/ux_report_output \
  --max-steps 10
```

## Expected Future Output Contract

```text
/tmp/ux_report_output/
├── ux_result.json
├── action_trace.json
├── ux_test_recording.webm
└── screenshots/
```

## Current Phase

**Phase 1 — browser visual runner for `figma` and `web`.** See `docs/TASKS.md`.

## Out of Scope (Phase 1)

- No Android or Windows adapters yet
- No OpenClaw deployment integration yet
- No Figma API grounding or DOM-selector-first automation

## Development (Phase 1)

```bash
pip install -r requirements.txt
python3 ./scripts/ux_testing.py --help
```

See `docs/VERIFY.md` for full install and smoke-test steps.

## Documentation Map

| File | Purpose |
|---|---|
| `requirements.txt` | Phase 1 Python dependencies |
| `AGENTS.md` | Instructions for Cursor agents |
| `START_HERE.md` | Onboarding checklist |
| `docs/PRD.md` | Product requirements |
| `docs/ARCHITECTURE.md` | System design |
| `docs/TASKS.md` | Implementation roadmap |
| `docs/DECISIONS.md` | Architecture decision log |
| `docs/VERIFY.md` | Verification steps |
| `docs/CONTEXT.md` | Stable project facts |
