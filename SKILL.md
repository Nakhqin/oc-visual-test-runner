# oc-visual-test-runner — Skill Execution Contract

## Purpose

This project is an **OpenClaw Skill runtime** for persona-based visual UI testing. Users interact with OpenClaw through natural-language requests. OpenClaw converts those requests into structured runner parameters, invokes the CLI runner, and returns a human-readable summary plus links or paths to the generated report and evidence.

The runner simulates a human participant: a VLM observes the screen, decides structured actions from an assigned persona, and a platform adapter executes those actions until a terminal state is reached.

## Skill Usage Flow

```text
1. User asks OpenClaw in natural language (target, URL, persona, goal, optional constraints)
2. OpenClaw derives structured Skill input (see below)
3. OpenClaw invokes scripts/ux_testing.py with structured parameters
4. Runner executes the visual agent loop and writes artifacts to output_dir
5. OpenClaw reads ux_result.json and evidence paths
6. OpenClaw returns a concise user-facing summary — not raw logs
```

## User-Facing Input (Natural Language)

Typical user input may include:

- **target type:** `figma` or `web`
- **URL:** Figma prototype URL or website URL
- **persona:** simulated user profile
- **goal:** task the persona should try to complete
- **optional constraints:** max steps, timeout, viewport size, language, notes or context

Example natural-language inputs:

- "Test this Figma prototype as an elderly user who is not familiar with tablets. The goal is to enable privacy space."
- "Review this website as a first-time visitor. The goal is to find the pricing page and understand which plan to choose."
- "Use a cautious first-time user persona and check whether the onboarding flow is understandable."

See `docs/PRD.md` for full usage scenarios.

## Skill-Level Structured Input

OpenClaw converts the natural-language request into structured parameters:

| Field | Required | Description |
|---|---|---|
| `target` | Yes | `figma` or `web` (Phase 1) |
| `url` | Yes | Figma prototype URL or web URL |
| `persona` | Yes | Participant persona for VLM reasoning |
| `goal` | Yes | Task or scenario the persona should attempt |
| `output_dir` | Yes | Directory for run artifacts |
| `max_steps` | No | Maximum agent loop iterations (default: 10) |
| `timeout_seconds` | No | Overall run timeout (default: 180 seconds) |
| `viewport_width` | No | Browser viewport width in pixels (Phase 1+) |
| `viewport_height` | No | Browser viewport height in pixels (Phase 1+) |
| `run_id` | No | Correlation id for Skill / OpenClaw / Feishu integration |

Example structured input:

```json
{
  "target": "figma",
  "url": "https://www.figma.com/proto/...",
  "persona": "A first-time tablet user who is cautious and not familiar with this device.",
  "goal": "Complete the first-time setup flow.",
  "output_dir": "/tmp/ux_report_output",
  "max_steps": 10,
  "timeout_seconds": 180,
  "viewport_width": 1280,
  "viewport_height": 900,
  "run_id": "example-run-id"
}
```

## CLI Inputs (Runner Layer)

The CLI accepts the core fields below. Optional viewport and `run_id` fields are planned for Phase 1+ CLI flags or OpenClaw-side injection — see `docs/TASKS.md`.

| Input | Required | Description |
|---|---|---|
| `target` | Yes | Target type: `figma` or `web` (Phase 1) |
| `url` | Yes | Figma prototype URL or web URL to open |
| `persona` | Yes | Participant persona for VLM reasoning |
| `goal` | Yes | Task or scenario the persona should attempt |
| `output_dir` | Yes | Directory for run artifacts |
| `max_steps` | No | Maximum agent loop iterations (default: 10) |
| `timeout_seconds` | No | Overall run timeout (default: 180 seconds) |

## Supported Targets (Phase 1)

| Target | Description |
|---|---|
| `figma` | Figma prototype URL opened in a browser |
| `web` | Normal website URL opened in a browser |

Both targets use a **shared browser adapter**.

## Planned Targets (not implemented)

| Target | Notes |
|---|---|
| `android` | Future platform adapter |
| `windows` | Future platform adapter |

## Runner Principle

- **VLM** is the visual decision-maker: observes the screen, reasons from persona, decides the next action, explains why a target appears actionable, reacts to hover or visual feedback, and decides whether the task is done, blocked, or needs another step.
- **Platform adapter** executes actions and returns observations: opens the target, captures frames, executes actions, records evidence, returns feedback.

## Runner Invocation

OpenClaw invokes the runner through the CLI.

**Figma target:**

```bash
python3 ./scripts/ux_testing.py \
  --target figma \
  --url "$URL" \
  --persona "$PERSONA" \
  --goal "$GOAL" \
  --output-dir /tmp/ux_report_output \
  --max-steps 10
```

**Web target:**

```bash
python3 ./scripts/ux_testing.py \
  --target web \
  --url "$URL" \
  --persona "$PERSONA" \
  --goal "$GOAL" \
  --output-dir /tmp/ux_report_output \
  --max-steps 10
```

The runner should print enough metadata for OpenClaw to know what was selected:

```text
SELECTED_TARGET=figma
SELECTED_ADAPTER=browser
SELECTED_RUNNER=visual_agent
```

```text
SELECTED_TARGET=web
SELECTED_ADAPTER=browser
SELECTED_RUNNER=visual_agent
```

> **Phase 1 (current):** CLI and config validation exist; selection metadata and full loop are planned. See `docs/TASKS.md`.

## User-Facing Return (OpenClaw → User)

The final response to the user should **not** be raw logs. OpenClaw returns a concise summary plus report and evidence links or paths.

The user-facing response should include:

- test status
- target
- persona
- goal
- final outcome (`done`, `blocked`, `max_steps`, `timeout`)
- main finding
- classification
- report link or path
- recording link or path
- result JSON link or path when useful

Example user-facing return:

```text
UX visual test completed.

Target: figma
Persona: first-time tablet user
Goal: complete first-time setup flow
Outcome: blocked
Main finding: the persona identified the primary action but the prototype did not visibly progress after clicking.
Classification: Prototype limitation / Automation limitation, not confirmed UX issue

Report: /tmp/ux_report_output/index.html
Recording: /tmp/ux_report_output/ux_test_recording.webm
Result JSON: /tmp/ux_report_output/ux_result.json
```

> **Phase 3+:** `persona_report.md` is the minimal first-person report. **Phase 4+:** `index.html` and `ux_report.md` become the primary formal report paths. OpenClaw may summarize from `ux_result.json` and link to `persona_report.md`, recording, and screenshots.

## Output Files

Each run writes to `output_dir`. Full contract by phase — see [Phase Deliverables](#phase-deliverables).

```text
/tmp/ux_report_output/
├── ux_result.json
├── action_trace.json
├── persona_report.md     # Phase 3+
├── ux_report.md          # Phase 4+
├── index.html            # Phase 4+
├── ux_test_recording.webm
└── screenshots/
```

### User-facing files

| File | Purpose | Phase |
|---|---|---|
| `persona_report.md` | First-person minimal UX experience report | 3+ |
| `index.html` | Main human-readable report | 4+ |
| `ux_report.md` | Markdown report for review and versioning | 4+ |
| `ux_test_recording.webm` | Recording of the visual test | 1+ |
| Selected screenshots | Visual evidence in report context | 1+ |

### System-facing files

| File | Purpose | Phase |
|---|---|---|
| `ux_result.json` | Structured result for OpenClaw / Skill / Feishu integration | 1+ |
| `action_trace.json` | Detailed action and reasoning trace for debugging and audit | 1+ |
| Raw screenshots in `screenshots/` | Evidence and reproduction support | 1+ |

Terminal states: `done`, `blocked`, `max_steps`, `timeout`.

## Report Content (Planned)

Human-readable reports (`ux_report.md`, `index.html`) should eventually include:

- test setup (target, URL, viewport, limits)
- persona and goal
- final outcome
- journey timeline
- actions taken
- target selected by the VLM
- reason for each action
- hover or visual feedback (Phase 1.5+)
- post-click verification (Phase 2 — implemented)
- findings and classification with evidence
- evidence screenshots and recording link
- recommendations

## Phase Deliverables

| Phase | Runner / Skill output |
|---|---|
| **1** (current) | `ux_result.json`, `action_trace.json`, `ux_test_recording.webm`, `screenshots/` |
| **1.5** | Adds cursor marker, hover observation frames; VLM decides click / adjust / wait / block after hover feedback |
| **2** | Adds post-click verification and retry or blocked logic |
| **3** | Adds `persona_report.md` (trace synthesis + optional Gemini polish) |
| **4** | Adds formal `ux_report.md`, `index.html`; improves `ux_result.json` for OpenClaw Skill integration |
| **5** | Connects Skill back into OpenClaw / Feishu-style delivery end-to-end |
| **6–7** | Android / Windows adapter design and exploration (future targets only) |

## Action Protocol (planned)

Future supported actions:

| Action | Description |
|---|---|
| `move_to` | Move cursor/pointer to coordinates |
| `move_by_delta` | Move cursor by relative offset |
| `click` | Click at coordinates |
| `click_current` | Click at current cursor position |
| `scroll` | Scroll the viewport |
| `wait` | Pause for UI feedback |
| `type` | Enter text |
| `done` | Task completed successfully |
| `blocked` | Persona cannot proceed; explain why |

## Classification Categories

Outcomes may be tagged with one or more of:

- **UX issue** — Genuine usability problem observed by the persona
- **Prototype limitation** — Figma prototype cannot represent the real flow
- **System-runtime issue** — Environment, crash, or infrastructure failure
- **Interaction limitation** — Target surface does not support the attempted interaction
- **Automation limitation** — Runner or adapter could not perform the action reliably

## Important Classification Rule

**A failed click does not automatically equal a UX issue.**

A failed or unproductive click may mean:

- the prototype or site did not respond
- the target was wrong
- the model misread the UI
- the browser automation failed
- the system timed out
- the UI affordance is genuinely unclear

The report should explain the **evidence behind the classification**. UX findings require explicit persona reasoning or verified criteria—not click failure alone.

## Current Phase

**Phase 3 complete; Phase 4 next.** Persona report (`persona_report.md`) with optional Gemini synthesis. Formal OpenClaw reports remain **planned** (Phase 4–5). See `docs/TASKS.md`.
