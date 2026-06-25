# Architecture — oc-visual-test-runner

## Overview

oc-visual-test-runner is the **OpenClaw Skill runtime** for persona-based visual UI testing. Users ask OpenClaw in natural language; OpenClaw derives structured parameters, invokes the CLI runner, and returns a human-readable summary with report and evidence links.

The runner implements a **universal visual agent loop** driven by target configuration. A platform adapter exposes the target surface; each iteration captures an observation frame, asks a VLM for a structured action, executes it visually, observes feedback, and appends to the trace until a terminal condition.

Phase 1 targets (`figma`, `web`) share one **browser platform adapter**. Future targets (`android`, `windows`) will add dedicated adapters behind the same loop and Skill model.

> **Phase 1:** CLI and config exist; browser adapter, agent loop, and VLM integration are in progress.

## OpenClaw Skill Flow

```text
┌──────────────────────────────────────────────────────────────┐
│  User (natural language)                                      │
│  "Test this site as a first-time visitor… find pricing"       │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  OpenClaw Skill layer                                         │
│  NL → structured input (target, url, persona, goal, limits)   │
│  invokes CLI → reads ux_result.json → user-facing summary     │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  scripts/ux_testing.py (CLI)                                  │
│  prints SELECTED_TARGET / SELECTED_ADAPTER / SELECTED_RUNNER  │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
                    [Visual Agent Loop — below]
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  output_dir artifacts → OpenClaw → user (summary + links)     │
└──────────────────────────────────────────────────────────────┘
```

## System Diagram

```text
┌─────────────────────────────────────────────────────────────┐
│                     Target Config                            │
│  target, url, persona, goal, output_dir, limits             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Core Visual Agent Loop                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Platform    │───▶│ Observation  │───▶│ VLM Action   │  │
│  │  Adapter     │    │ Frame        │    │ Decision     │  │
│  └──────▲───────┘    └──────────────┘    └──────┬───────┘  │
│         │                                         │          │
│         │         ┌──────────────┐                │          │
│         └─────────│   Action     │◀───────────────┘          │
│                   │  Execution   │                           │
│                   └──────┬───────┘                           │
│                          │                                   │
│                          ▼                                   │
│                   ┌──────────────┐                           │
│                   │  Feedback    │                           │
│                   │  Observation │                           │
│                   └──────┬───────┘                           │
│                          │                                   │
│                          ▼                                   │
│                   ┌──────────────┐                           │
│                   │ Trace Writer │──▶ action_trace.json      │
│                   │ Result Writer│──▶ ux_result.json         │
│                   │ Evidence     │──▶ screenshots/, .webm    │
│                   └──────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

## Main Components

| Component | Responsibility | Status |
|---|---|---|
| `scripts/ux_testing.py` | CLI entrypoint; prints `SELECTED_*` metadata | **Partial** (Phase 1) |
| Target config | Parse and validate CLI/Skill inputs | **Partial** (Phase 1) |
| Core visual agent loop | Orchestrate observe → decide → act → feedback → record | **Partial** (Phase 1 — stub decision) |
| Browser platform adapter | Navigate, capture frames, visual click/type/scroll | **Planned** (Phase 1) |
| Observation frame | Screenshot + metadata (step, viewport, timestamp) | **Planned** (Phase 1) |
| VLM client | Send frame + persona/goal context; parse structured action | **Partial** (Phase 1 — Gemini) |
| Action schema | Protocol types per `SKILL.md` | **Partial** (Phase 1 — `core/actions.py`) |
| Trace writer | `action_trace.json`, screenshots | **Partial** (Phase 1 — initial step) |
| Result writer | `ux_result.json`, classifications | **Partial** (Phase 1 — blocked stub) |
| Recording capture | `ux_test_recording.webm` | **Planned** (Phase 1) |
| Cursor/hover observer | Marker overlay, hover-before-click | **Planned** (Phase 1.5) |
| Post-click verifier | Confirm UI change; retry policy | **Planned** (Phase 2) |
| Report generator (minimal) | Phase 3 human-readable summary | **Planned** (Phase 3) |
| Report generator (formal) | `ux_report.md`, `index.html` | **Planned** (Phase 4) |
| Skill delivery layer | OpenClaw / Feishu-style end-to-end return | **Planned** (Phase 5) |
| Android adapter | Device/emulator visual control | **Planned** (Phase 6–7) |
| Windows adapter | Desktop visual control | **Planned** (Phase 6–7) |

## Main Directories

| Path | Purpose | Status |
|---|---|---|
| `scripts/ux_testing.py` | CLI entry | **Exists** (Phase 1 — config validation) |
| `scripts/core/` | Visual agent loop, config, writers | **Partial** (Phase 1) |
| `scripts/adapters/browser.py` | Browser platform adapter | **Partial** (Phase 1 — initial capture) |
| `scripts/targets/` | Target-specific config/helpers | **Planned** (Phase 1+) — do not create in Phase 0 |
| `docs/` | Product and architecture docs | **Exists** (Phase 0) |
| `scripts/` | Setup helpers | **Exists** (Phase 0) |

Exact package layout will be decided at Phase 1 start and recorded in `docs/DECISIONS.md`.

## Data Flow

### Skill path (user-facing)

1. **User request** — natural language (target, URL, persona, goal, optional constraints).
2. **OpenClaw** — derives structured Skill input per `SKILL.md`.
3. **CLI invocation** — `scripts/ux_testing.py` with structured parameters; runner prints `SELECTED_*` metadata.
4. **Runner loop** — see below.
5. **OpenClaw return** — concise summary + report/evidence paths (not raw logs).

### Runner loop (execution)
1. **Load target config** — `target=figma|web`, URL, persona, goal, output_dir, limits, optional viewport, `run_id`.
2. **Initialize platform adapter** — Browser opens URL; viewport set; recording started.
3. **Loop:**
   - Adapter captures **observation frame** (screenshot + metadata).
   - **VLM** receives persona, goal, history, frame; returns structured action.
   - **Action executor** invokes adapter (e.g. `move_to`, `click`).
   - **Feedback observation** — capture post-action frame or hover state.
   - **Trace writer** appends to `action_trace.json`; save screenshot.
   - Exit if action is `done` or `blocked`, or limits exceeded.
4. **Finalize** — Write `ux_result.json`; stop recording → `ux_test_recording.webm`. Phase 3+ adds reports; Phase 4 adds `ux_report.md` and `index.html`.

## Output Artifacts

| Artifact | Audience | Phase |
|---|---|---|
| `ux_result.json` | System — OpenClaw / Skill / Feishu | 1+ |
| `action_trace.json` | System — debug, audit | 1+ |
| `screenshots/` | Both — evidence | 1+ |
| `ux_test_recording.webm` | User-facing evidence | 1+ |
| Minimal report | User-facing | 3+ |
| `ux_report.md`, `index.html` | User-facing primary report | 4+ |

See `SKILL.md` for report content expectations and user-facing return format.

## External Services

| Service | Purpose | Required? |
|---|---|---|
| Google Gemini (VLM) | Action decisions from observation frames | Yes (Phase 1) |
| Figma prototype URL | Live prototype in browser | For `figma` target |
| Target web URL | Page under test | For `web` target |
| Figma REST API | — | **No** |

## Key Interfaces (planned)

| Interface | Purpose |
|---|---|
| `PlatformAdapter` | `open`, `capture_frame`, `move_to`, `click`, `scroll`, `type`, `close` |
| `ActionProtocol` | Structured VLM action schema — see `SKILL.md` |
| `ObservationFrame` | Image + metadata for one loop iteration |
| `ActionTrace` | Serialized step log → `action_trace.json` |
| `UxResult` | Terminal state + classifications → `ux_result.json` |

## Constraints

- Visual interaction for Phase 1; no Figma node resolver or selector engine
- Low-frequency observation frames before full real-time streaming (see `docs/DECISIONS.md`)
- Traces must not contain secrets
- Failed clicks are telemetry; UX classification requires explicit criteria
- One browser adapter serves both `figma` and `web` in Phase 1

## Known Tradeoffs

- **VLM latency vs fidelity:** Each step requires a model call; acceptable for research, not sub-second CI
- **Coordinate clicks vs selectors:** More human-like but sensitive to layout/viewport changes
- **Shared browser adapter:** Less duplication; Figma-specific quirks in navigation/wait logic only
- **Low-frequency frames:** Lower cost and simpler loop; may miss transient UI feedback until Phase 1.5+

## Architecture Decisions

See `docs/DECISIONS.md`.
