# PRD — oc-visual-test-runner

## Problem

UX testing on live prototypes and websites often relies on manual sessions or brittle automation (DOM selectors, Figma API node mapping). These approaches miss what real users experience visually and break when designs or DOM structures change.

Teams need a runner that simulates a **human participant**: observe the screen, reason from a persona, decide the next action, act through visual controls, observe feedback, and produce an auditable trace.

## Target Users

- UX researchers and designers validating Figma prototypes
- Product and QA teams smoke-testing web flows with persona scenarios
- OpenClaw orchestrators invoking visual UX runs as a skill

## Core Use Cases

1. **Figma prototype walkthrough** — Given a prototype URL, persona, and goal, complete or block with trace and recording.
2. **Web flow walkthrough** — Same runner against a web URL via the shared browser adapter.
3. **Skill invocation** — OpenClaw (or CLI) passes target config and receives structured output per `SKILL.md`.

## In Scope

| Phase | Scope |
|---|---|
| 0 | Project scaffold: documentation, context, rules |
| 1 | Browser visual runner for `figma` and `web` |
| 1.5 | Cursor marker + hover observation loop |
| 2 | Post-click verification and retry logic |
| 3 | Minimal report output |
| 4 | OpenClaw skill integration |
| 5 | Android/Windows adapter design |
| 6 | Android/Windows implementation exploration |

## Out of Scope

- Figma REST/API resolver, node ID lookup, layer name matching, `absoluteBoundingBox` mapping
- DOM-selector-first or accessibility-tree-first automation as the primary model
- Legacy runner migration (`figma_runner.py`, `web_runner.py`, patch/backup/old reports)
- Automatic treatment of failed clicks as UX defects
- Android and Windows implementation in Phase 0–1
- Production hosting, multi-tenant SaaS, or real-time collaborative viewing

## Functional Requirements

### FR-1 Visual agent loop

Repeat: capture observation frame → VLM structured action → execute via platform adapter → observe feedback → record trace, until `done`, `blocked`, `max_steps`, or `timeout`.

### FR-2 Target configuration

Accept `target`, `url`, `persona`, `goal`, `output_dir`, and optional `max_steps`, `timeout_seconds`.

### FR-3 Platform adapter (Phase 1)

Shared browser adapter for `figma` and `web` using visual mouse/keyboard control.

### FR-4 VLM responsibilities

Observe screen, reason from persona, decide next action, explain why target appears actionable, react to hover/visual feedback, decide terminal state.

### FR-5 Adapter responsibilities

Open target, capture observations, execute actions, record evidence, return feedback.

### FR-6 Action protocol

Structured actions per `SKILL.md`: `move_to`, `move_by_delta`, `click`, `click_current`, `scroll`, `wait`, `type`, `done`, `blocked`.

### FR-7 Output

Write `ux_result.json`, `action_trace.json`, `ux_test_recording.webm`, and `screenshots/` to `output_dir`.

### FR-8 Classification

Use defined categories. Failed clicks alone shall not imply a UX issue.

## Non-Functional Requirements

- **Security:** API keys in `.env` only; no secrets in committed traces
- **Reliability:** Graceful terminal states on adapter/VLM errors
- **Maintainability:** Phased delivery, documented decisions
- **Observability:** `action_trace.json` and screenshots as auditable evidence
- **Performance:** Acceptable for UX research sessions (exact SLO TBD in Phase 1)

## Success Criteria

- Phase 0: All scaffold docs describe oc-visual-test-runner; no runtime files added
- Phase 1: End-to-end run against Figma prototype URL and web URL with full output contract
- Persona reaches `done` or `blocked` with auditable steps
- No Figma API or CSS selectors for primary interaction
- OpenClaw invokes skill per `SKILL.md` (Phase 4)

## Open Questions

- Normalized vs pixel coordinates for pointer actions (Phase 1)
- Default `max_steps` and `timeout_seconds`
- VLM prompt template ownership and versioning
- Minimal report schema beyond `ux_result.json` (Phase 3)
- Screen recording capture method and quality settings (Phase 1)
