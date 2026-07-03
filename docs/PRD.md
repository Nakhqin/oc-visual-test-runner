# PRD — oc-visual-test-runner

## Problem

UX testing on live prototypes and websites often relies on manual sessions or brittle automation (DOM selectors, Figma API node mapping). These approaches miss what real users experience visually and break when designs or DOM structures change.

Teams need an **OpenClaw Skill** that simulates a **human participant**: the user asks in natural language; OpenClaw derives structured parameters, invokes the runner, and returns a concise summary with report and evidence links.

## Target Users

- UX researchers and designers validating Figma prototypes
- Product and QA teams reviewing live websites before deeper user testing
- Designers seeking quick prototype feedback before coworker review or recruitment
- OpenClaw users invoking visual UX runs as a Skill

## Main Usage Scenarios

### Scenario 1: Redesigning an Existing Website

A designer or product team wants to redesign or update an already launched website. Normally this requires recruiting users and running sessions that take time.

**User provides (via natural language):** website URL, persona, goal.

**Example request:**

> "Test this website as a first-time visitor who wants to understand the product and find the pricing page."

**OpenClaw should return:**

- whether the persona completed the goal
- where the persona hesitated or got blocked
- which UI elements appeared clickable or confusing
- classification: UX issue, prototype/site limitation, automation issue, or system-runtime issue
- report and evidence links

**Value:** Helps designers narrow scope before deeper human user testing.

### Scenario 2: Reviewing a New Figma Prototype

A designer has completed a Figma prototype and wants quick feedback before showing coworkers or recruiting test users. Coworker feedback is useful but biased and still takes time.

**User provides:** Figma prototype URL, persona, goal.

**Example request:**

> "Use this Figma prototype and test it as a first-time tablet user. The goal is to complete the first-time setup flow."

**OpenClaw should return:**

- whether the persona understood the current screen
- what the persona tried to click
- whether hover or visual feedback helped (Phase 1.5+)
- whether the flow progressed after clicking
- where the persona got blocked
- report and evidence links

**Value:** Helps designers find likely usability problems and narrow scope for later detailed user testing.

### Scenario 3: Future Device UI Testing (Planned)

Future targets may include **Android** and **Windows**. The same Skill model applies: user provides target, persona, and goal; OpenClaw converts to structured parameters; a platform adapter captures the screen and executes actions; the visual agent loop observes, acts, verifies feedback, and records evidence.

**Not implemented.** Documented for future adapter phases only.

## Skill Interaction Model

1. **What the user asks for** — natural-language UX test request (target, URL, persona, goal, optional constraints).
2. **What OpenClaw derives** — structured Skill input per `SKILL.md` (`target`, `url`, `persona`, `goal`, `output_dir`, limits, viewport, `run_id`).
3. **How the Skill invokes the runner** — OpenClaw calls `scripts/ux_testing.py` with structured CLI parameters; runner prints `SELECTED_*` metadata.
4. **What the runner generates** — artifacts under `output_dir` (phase-dependent; see below).
5. **What OpenClaw returns** — concise user-facing summary plus report/evidence paths — not raw logs.

## Core Use Cases

1. **Web flow walkthrough** — Live website URL, persona, goal; OpenClaw returns summary and evidence.
2. **Figma prototype walkthrough** — Prototype URL via shared browser adapter; same return shape.
3. **Skill orchestration** — OpenClaw converts NL → structured input → CLI → reads `ux_result.json` → user-facing response.

## In Scope

| Phase | Scope |
|---|---|
| 0 | Project scaffold: documentation, context, rules |
| 1 | Browser visual runner for `figma` and `web`; Phase 1 output contract |
| 1.5 | Cursor marker + hover observation loop |
| 2 | Post-click verification and retry logic |
| 3 | Persona report (`persona_report.md`) |
| 4 | Formal `ux_report.md`, `index.html`; `skill` block in `ux_result.json` |
| 4.5 | Public report publish: `skill.report_url` (runner-only; no OpenClaw) |
| 5 | OpenClaw / Feishu-style Skill delivery end-to-end (returns `report_url`) |
| 6 | Android/Windows adapter design |
| 7 | Android/Windows implementation exploration |

## Out of Scope

- Figma REST/API resolver, node ID lookup, layer name matching, `absoluteBoundingBox` mapping
- DOM-selector-first or accessibility-tree-first automation as the primary model
- Legacy runner migration (`figma_runner.py`, `web_runner.py`, patch/backup/old reports)
- Automatic treatment of failed clicks as UX defects
- Android and Windows implementation in Phase 0–1
- Formal `ux_report.md` / `index.html` in Phase 1 (Phase 4)
- OpenClaw / Feishu end-to-end Skill delivery in Phase 1 (Phase 5)
- Production hosting, multi-tenant SaaS, or real-time collaborative viewing

## Functional Requirements

### FR-1 Visual agent loop

Repeat: capture observation frame → VLM structured action → execute via platform adapter → observe feedback → record trace, until `done`, `blocked`, `max_steps`, or `timeout`.

### FR-2 Target configuration

Accept Skill-level structured input: `target`, `url`, `persona`, `goal`, `output_dir`, optional `max_steps`, `timeout_seconds`, `viewport_width`, `viewport_height`, `run_id`. OpenClaw derives these from natural-language user requests.

### FR-2b Skill invocation metadata

Runner prints selection metadata (`SELECTED_TARGET`, `SELECTED_ADAPTER`, `SELECTED_RUNNER`) for OpenClaw.

### FR-3 Platform adapter (Phase 1)

Shared browser adapter for `figma` and `web` using visual mouse/keyboard control.

### FR-4 VLM responsibilities

Observe screen, reason from persona, decide next action, explain why target appears actionable, react to hover/visual feedback, decide terminal state.

### FR-5 Adapter responsibilities

Open target, capture observations, execute actions, record evidence, return feedback.

### FR-6 Action protocol

Structured actions per `SKILL.md`: `move_to`, `move_by_delta`, `click`, `click_current`, `scroll`, `wait`, `type`, `done`, `blocked`.

### FR-7 Output (by phase)

| Phase | Artifacts |
|---|---|
| 1 | `ux_result.json`, `action_trace.json`, `ux_test_recording.webm`, `screenshots/` |
| 3 | `persona_report.md` |
| 4 | `ux_report.md`, `index.html`; `skill` block in `ux_result.json` |
| 4.5 | Public publish: `skill.report_url`, `skill.report_base_url` |
| 5 | OpenClaw user return with clickable `report_url` |

User-facing vs system-facing file roles: see `SKILL.md`.

### FR-8 Classification

Use defined categories. Failed clicks alone shall not imply a UX issue. Reports explain evidence behind classification.

### FR-9 User-facing Skill return

OpenClaw returns a concise summary (status, target, persona, goal, outcome, main finding, classification) plus **`skill.report_url`** and evidence links — not raw runner logs. Phase 4.5 provides the public URL; Phase 5 delivers it to the user (e.g. Feishu).

## Non-Functional Requirements

- **Security:** API keys in `.env` only; no secrets in committed traces
- **Reliability:** Graceful terminal states on adapter/VLM errors
- **Maintainability:** Phased delivery, documented decisions
- **Observability:** `action_trace.json` and screenshots as auditable evidence
- **Performance:** Acceptable for UX research sessions (exact SLO TBD in Phase 1)

## Success Criteria

- Phase 0: All scaffold docs describe oc-visual-test-runner; no runtime files added
- Phase 1: End-to-end run against Figma prototype URL and web URL with Phase 1 output contract
- Persona reaches `done` or `blocked` with auditable steps
- No Figma API or CSS selectors for primary interaction
- OpenClaw converts NL request to structured input and invokes CLI (Phase 5 end-to-end)
- User receives concise summary plus public **`report_url`** (Phase 4.5 publish + Phase 5 delivery)

## Open Questions

- Normalized vs pixel coordinates for pointer actions (Phase 1)
- CLI flags for `viewport_width`, `viewport_height`, `run_id` (Phase 1+)
- VLM prompt template ownership and versioning
- Persona report (Phase 3); formal HTML/Markdown reports (Phase 4); public publish URL (Phase 4.5)
- Screen recording capture method and quality settings (Phase 1)
- OpenClaw NL → structured input conversion ownership (OpenClaw layer vs this repo) — **resolved:** OpenClaw main agent; see `docs/DECISIONS.md` Phase 5 scope
