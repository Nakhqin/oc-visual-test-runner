# Project Context

Stable facts for oc-visual-test-runner. Keep this file short.

## Project Summary

**OpenClaw Skill runtime** for persona-based visual UI testing. Users ask OpenClaw in natural language; OpenClaw derives structured parameters, invokes `scripts/ux_testing.py`, and returns a concise summary plus report and evidence links. The runner is not only a standalone CLI — it is the execution layer behind the Skill.

## Current Stage

**Phase 3 complete — Phase 4 next.** Persona report with optional Gemini polish implemented.

## Users / Audience

- Designers and product teams reviewing live websites before deeper user testing
- Designers seeking quick Figma prototype feedback
- OpenClaw users invoking visual UX tests as a Skill
- Developers smoke-testing the CLI directly

## Skill Usage (One Line)

NL request → OpenClaw structured input → CLI runner → artifacts → OpenClaw user-facing summary.

Full contract: `SKILL.md`.

## Tech Stack Expectation

| Layer | Planned choice | Phase |
|---|---|---|
| Language | Python | 1 |
| CLI | `scripts/ux_testing.py` | 1 |
| Browser automation | Playwright (visual control) | 1 |
| VLM | Google Gemini via `google-genai` (`GOOGLE_API_KEY`, default `gemini-2.5-flash`) | 1 |
| Skill orchestration | OpenClaw (NL → structured input → user return) | 5 |

## Phase 1 Targets

- `figma` — Figma prototype URL via shared browser adapter
- `web` — Web URL via shared browser adapter

## Planned Targets

- `android` (Phase 6 design, Phase 7 exploration) — **not implemented**
- `windows` (Phase 6 design, Phase 7 exploration) — **not implemented**

## Output Contract (by Phase)

| Phase | Artifacts |
|---|---|
| 1 | `ux_result.json`, `action_trace.json`, `ux_test_recording.webm`, `screenshots/` |
| 3 | Minimal human-readable report |
| 4 | `ux_report.md`, `index.html`; improved `ux_result.json` |
| 5 | OpenClaw / Feishu-style end-to-end Skill delivery |

User-facing vs system-facing roles: see `SKILL.md`.

## Important Constraints

- Persona-based visual behavior; VLM is the decision-maker, adapter executes
- No Figma API grounding; no DOM-selector-first automation
- Failed clicks are not automatically UX issues
- User-facing Skill return is a summary — not raw runner logs

## Current Assumptions

- Gemini via `google-genai` is the Phase 1 VLM provider (default `gemini-2.5-flash`)
- Primary Gemini E2E verification uses a **US cloud runner**; local CN dev may need VPN for Gemini or use `--use-stub` for browser-only checks
- Figma prototypes are tested as browser pages, not via Figma REST API
- Default output directory placeholder: `/tmp/ux_report_output`
- `viewport_width`, `viewport_height`, `run_id` are Skill-level fields; CLI flags may follow in Phase 1+

## Things Cursor Agent Should Not Assume

- Full visual agent loop works for Phase 1 targets — see `docs/TASKS.md` and `docs/VERIFY.md` verification record
- `ux_report.md` or `index.html` exist in Phase 1 — Phase 4
- OpenClaw NL → user return works end-to-end — Phase 5
- Legacy `figma_runner.py` / `web_runner.py` exist in this repo
- Failed clicks imply UX bugs
