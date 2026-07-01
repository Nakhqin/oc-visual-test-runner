# oc-visual-test-runner

An **OpenClaw Skill runtime** for persona-based visual UI testing on Figma prototypes and websites. Users ask OpenClaw in natural language; OpenClaw derives structured runner parameters, invokes this project's CLI runner, and returns a concise summary plus report and evidence links.

The runner is not only a standalone Python script — it is the execution layer behind the Skill. Direct CLI use is supported for development and smoke tests.

## How Users Use the Skill

```text
User natural-language request
    ↓
OpenClaw derives structured parameters (target, url, persona, goal, limits, viewport, run_id)
    ↓
OpenClaw invokes scripts/ux_testing.py
    ↓
Runner executes visual agent loop (observe → decide → act → record)
    ↓
Runner writes result JSON, trace, recording, screenshots (and later reports)
    ↓
OpenClaw returns human-readable summary + report/evidence paths
```

See `SKILL.md` for the full Skill contract, structured input example, and user-facing return format. See `docs/PRD.md` for main usage scenarios.

## Main Usage Scenarios

| Scenario | Target | Value |
|---|---|---|
| Redesigning an existing website | `web` | Narrow UX scope before deeper human user testing |
| Reviewing a new Figma prototype | `figma` | Quick persona feedback before coworker review or recruitment |
| Future device UI testing | `android`, `windows` (planned) | Same Skill model on native surfaces — **not implemented** |

Example user request:

> "Test this website as a first-time visitor who wants to understand the product and find the pricing page."

OpenClaw should return whether the persona completed the goal, where they hesitated, what looked clickable or confusing, classification (UX issue vs limitation vs automation/system issue), and links to the report and evidence.

## Current Supported Targets (Phase 1)

| Target | Description |
|---|---|
| `figma` | Figma prototype URL opened in a browser |
| `web` | Normal website URL opened in a browser |

Both use a **shared browser adapter**.

## Planned Targets

| Target | Status |
|---|---|
| `android` | Future adapter (design Phase 6; implementation Phase 7) |
| `windows` | Future adapter (design Phase 6; implementation Phase 7) |

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

## Runner Invocation (Skill → CLI)

OpenClaw calls the runner through the CLI. The runner prints selection metadata for the Skill layer, for example:

```text
SELECTED_TARGET=figma
SELECTED_ADAPTER=browser
SELECTED_RUNNER=visual_agent
```

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

> **Phase 1.5 (complete):** Cursor marker + hover-before-click loop — see `docs/VERIFY.md`. **Current:** Phase 2 — see `docs/TASKS.md`.

## Output Contract (by Phase)

**Phase 1 (implemented target):**

```text
/tmp/ux_report_output/
├── ux_result.json          # system-facing — OpenClaw / Skill integration
├── action_trace.json       # system-facing — debug and audit
├── ux_test_recording.webm  # user-facing evidence
└── screenshots/            # user-facing + raw evidence
```

**Phase 3+ (planned):** minimal human-readable report  
**Phase 4+ (planned):** `ux_report.md`, `index.html`, improved `ux_result.json` for Skill delivery  
**Phase 5 (planned):** OpenClaw / Feishu-style end-to-end Skill delivery

Full file purposes: see `SKILL.md`.

## Current Phase

**Phase 2 — post-click verification and retry logic.** Phase 1.5 (cursor marker + hover loop) implemented — see `docs/VERIFY.md`. Phase 1 complete (2026-07-01).

## Out of Scope (Phase 1)

- No Android or Windows adapters yet
- No formal `ux_report.md` / `index.html` yet (Phase 4)
- No OpenClaw / Feishu end-to-end Skill delivery yet (Phase 5)
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
| `SKILL.md` | OpenClaw Skill execution contract (primary usage model) |
| `requirements.txt` | Phase 1 Python dependencies |
| `AGENTS.md` | Instructions for Cursor agents |
| `START_HERE.md` | Onboarding checklist |
| `docs/PRD.md` | Product requirements |
| `docs/ARCHITECTURE.md` | System design |
| `docs/TASKS.md` | Implementation roadmap |
| `docs/DECISIONS.md` | Architecture decision log |
| `docs/VERIFY.md` | Verification steps |
| `docs/CONTEXT.md` | Stable project facts |
