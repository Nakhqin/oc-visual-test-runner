# Start Here — oc-visual-test-runner

Onboarding checklist for contributors and Cursor agents.

## Read in This Order

1. **`README.md`** — project name, summary, targets, architecture, current phase
2. **`SKILL.md`** — skill contract: inputs, outputs, action protocol, classifications
3. **`.cursor/rules/90-project-context.mdc`** — short project facts and non-goals
4. **`docs/PRD.md`** — problem, scope, requirements, success criteria
5. **`docs/ARCHITECTURE.md`** — components, data flow, planned interfaces
6. **`docs/TASKS.md`** — implementation roadmap; work only on the current phase
7. **`docs/VERIFY.md`** — how to verify work at each phase

## For Large Changes

8. Create a plan under **`.cursor/plans/`** before multi-file or architectural work.

## Phase 0 Rules

9. **Phase 0 allows only scaffold and documentation changes.** No runtime code, no API calls, no Playwright, no Gemini integration.

## When Runtime Starts

10. **Runtime implementation begins in Phase 1.** See `docs/TASKS.md` for the browser visual runner milestone.

## Optional Setup (later phases)

When Phase 1 lands:

1. Copy `.env.example` to `.env` and set values locally (never commit `.env`).
2. Install dependencies per `docs/VERIFY.md`.
3. Run verification commands before claiming completion.

## Agent Reminders

- Read `AGENTS.md` for the full working contract.
- Record architecture decisions in `docs/DECISIONS.md`.
- Stay within the current phase in `docs/TASKS.md`.
