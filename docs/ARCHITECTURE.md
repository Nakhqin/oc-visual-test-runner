# Architecture — oc-visual-test-runner

## Overview

oc-visual-test-runner implements a **universal visual agent loop** driven by target configuration. A platform adapter exposes the target surface; each iteration captures an observation frame, asks a VLM for a structured action, executes it visually, observes feedback, and appends to the trace until a terminal condition.

Phase 1 targets (`figma`, `web`) share one **browser platform adapter**. Future targets (`android`, `windows`) will add dedicated adapters behind the same loop interface.

> **Phase 0:** Architecture below is **planned**. No runtime implementation exists yet.

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
| `scripts/ux_testing.py` | CLI entrypoint | **Planned** (Phase 1) |
| Target config | Parse and validate CLI/skill inputs | **Planned** (Phase 1) |
| Core visual agent loop | Orchestrate observe → decide → act → feedback → record | **Planned** (Phase 1) |
| Browser platform adapter | Navigate, capture frames, visual click/type/scroll | **Planned** (Phase 1) |
| Observation frame | Screenshot + metadata (step, viewport, timestamp) | **Planned** (Phase 1) |
| VLM client | Send frame + persona/goal context; parse structured action | **Planned** (Phase 1) |
| Action schema | Protocol types per `SKILL.md` | **Planned** (Phase 1) |
| Trace writer | `action_trace.json`, screenshots | **Planned** (Phase 1) |
| Result writer | `ux_result.json`, classifications | **Planned** (Phase 1) |
| Recording capture | `ux_test_recording.webm` | **Planned** (Phase 1) |
| Cursor/hover observer | Marker overlay, hover-before-click | **Planned** (Phase 1.5) |
| Post-click verifier | Confirm UI change; retry policy | **Planned** (Phase 2) |
| Report generator | Minimal human-readable summary | **Planned** (Phase 3) |
| Skill integration | OpenClaw-compatible wrapper | **Planned** (Phase 4) |
| Android adapter | Device/emulator visual control | **Planned** (Phase 5–6) |
| Windows adapter | Desktop visual control | **Planned** (Phase 5–6) |

## Main Directories

| Path | Purpose | Status |
|---|---|---|
| `scripts/ux_testing.py` | CLI entry | **Planned** (Phase 1) |
| `scripts/core/` | Visual agent loop, config, writers | **Planned** (Phase 1) — do not create in Phase 0 |
| `scripts/adapters/` | Platform adapters (browser, future android/windows) | **Planned** (Phase 1+) — do not create in Phase 0 |
| `scripts/targets/` | Target-specific config/helpers | **Planned** (Phase 1+) — do not create in Phase 0 |
| `docs/` | Product and architecture docs | **Exists** (Phase 0) |
| `scripts/` | Setup helpers | **Exists** (Phase 0) |

Exact package layout will be decided at Phase 1 start and recorded in `docs/DECISIONS.md`.

## Data Flow

1. **Load target config** — `target=figma|web`, URL, persona, goal, output_dir, limits.
2. **Initialize platform adapter** — Browser opens URL; viewport set; recording started.
3. **Loop:**
   - Adapter captures **observation frame** (screenshot + metadata).
   - **VLM** receives persona, goal, history, frame; returns structured action.
   - **Action executor** invokes adapter (e.g. `move_to`, `click`).
   - **Feedback observation** — capture post-action frame or hover state.
   - **Trace writer** appends to `action_trace.json`; save screenshot.
   - Exit if action is `done` or `blocked`, or limits exceeded.
4. **Finalize** — Write `ux_result.json`; stop recording → `ux_test_recording.webm`.

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
