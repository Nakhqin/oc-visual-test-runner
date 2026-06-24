# oc-visual-test-runner — Skill Execution Contract

## Purpose

Run persona-based visual UX walkthroughs. The runner simulates a human participant: a VLM observes the screen, decides structured actions from an assigned persona, and a platform adapter executes those actions until a terminal state is reached.

## Inputs

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

## Future Command Examples

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

> **Phase 1:** Runtime implementation in progress. Commands above define the intended CLI contract.

## Output Files

Each run writes to `output_dir`:

| File | Purpose |
|---|---|
| `ux_result.json` | Terminal state, summary, classifications |
| `action_trace.json` | Step-by-step action and observation log |
| `ux_test_recording.webm` | Screen recording of the walkthrough |
| `screenshots/` | Observation frame images per step |

Terminal states: `done`, `blocked`, `max_steps`, `timeout`.

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

A failed click may be caused by:

- prototype limitation
- automation limitation
- system/runtime issue
- wrong target
- no visible response
- interaction limitation

UX findings require explicit persona reasoning or verified criteria—not click failure alone.

## Current Phase

**Phase 1 — browser visual runner.** Runtime implementation for `figma` and `web` via shared browser adapter. See `docs/TASKS.md` for the implementation roadmap.
