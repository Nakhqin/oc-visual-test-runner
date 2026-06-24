# Project Context

Stable facts for oc-visual-test-runner. Keep this file short.

## Project Summary

Persona-based visual UX testing runner. A VLM observes the screen, reasons from a persona, decides structured actions, and a platform adapter executes them visually until `done`, `blocked`, `max_steps`, or `timeout`.

## Current Stage

**Phase 0 — scaffold conversion.** Documentation and context only. No runtime, no API calls, no Playwright, no Gemini integration.

## Users / Audience

- UX researchers and designers (Figma prototypes)
- Product and QA teams (web flows)
- OpenClaw orchestrators (skill invocation)

## Tech Stack Expectation

| Layer | Planned choice | Phase |
|---|---|---|
| Language | Python | 1 |
| CLI | `scripts/ux_testing.py` | 1 |
| Browser automation | Playwright (visual control) | 1 |
| VLM | Google Gemini (`GOOGLE_API_KEY`) | 1 |

Not confirmed from the current repository: exact package layout, `requirements.txt`, internal module names.

## Phase 1 Targets

- `figma` — Figma prototype URL via shared browser adapter
- `web` — Web URL via shared browser adapter

## Planned Targets

- `android` (Phase 5 design, Phase 6 exploration)
- `windows` (Phase 5 design, Phase 6 exploration)

## Important Constraints

- Persona-based visual behavior; VLM is the decision-maker, adapter executes
- No Figma API grounding; no DOM-selector-first automation
- Failed clicks are not automatically UX issues
- Output contract: `ux_result.json`, `action_trace.json`, `ux_test_recording.webm`, `screenshots/`

## Current Assumptions

- Gemini is the Phase 1 VLM provider
- Figma prototypes are tested as browser pages, not via Figma REST API
- Default output directory placeholder: `/tmp/ux_report_output`

## Things Cursor Agent Should Not Assume

- Runtime or `scripts/ux_testing.py` already exists
- Legacy `figma_runner.py` / `web_runner.py` exist in this repo
- Figma MCP or Figma API is required for Phase 1
- Failed clicks imply UX bugs
- Phase 1 code already exists — check `docs/TASKS.md` first
- Implementation directories (`scripts/core/`, `scripts/adapters/`, `scripts/targets/`) exist — they are planned, not present in Phase 0
