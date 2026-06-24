# AGENTS.md

Working contract for Cursor agents on **oc-visual-test-runner**.

## Read Before Working

Read these files in order before making changes:

1. `README.md` — project overview, architecture, current phase
2. `SKILL.md` — skill execution contract (inputs, outputs, action protocol)
3. `.cursor/rules/90-project-context.mdc` — stable project facts and non-goals
4. `docs/PRD.md` — product scope and requirements
5. `docs/ARCHITECTURE.md` — system design and data flow
6. `docs/TASKS.md` — current phase and implementation roadmap
7. `docs/VERIFY.md` — verification steps for the current phase
8. `docs/DECISIONS.md` — accepted architecture decisions

## Project Identity

oc-visual-test-runner is a **persona-based visual UX testing runner**. A VLM observes the screen, decides structured actions, and a platform adapter executes them visually until `done`, `blocked`, `max_steps`, or `timeout`.

Phase 1 targets: **`figma`** and **`web`** via a shared browser adapter. Android and Windows are future adapters only.

## Strict Rules

- **Make small, reviewable changes.** One phase or one concern at a time.
- **Do not assume missing project details.** Inspect the repo; if something is not documented, ask or record an open question—do not invent APIs, paths, or commands.
- **Do not implement broad architecture changes** without checking `docs/TASKS.md` for the current phase.
- **Do not add dependencies** without updating `README.md` and `docs/VERIFY.md`.
- **Update `docs/DECISIONS.md`** when making architecture or protocol decisions.
- **Keep secrets out of the repo.** Use `.env.example` placeholders only; never commit real keys.
- **Failed clicks are not automatically UX issues.** Do not encode that assumption.
- **No legacy Figma API grounding.** No node ID lookup, layer matching, or DOM-selector-first automation as the primary model.
- **Do not migrate or revive** legacy runners unless explicitly assigned in `docs/TASKS.md`.

## Before Finishing

Summarize:

- changed files
- verification performed or recommended (see `docs/VERIFY.md`)
- risks
- open questions, if any

## Boundaries

- Do not run destructive commands without explicit approval.
- Do not modify production or deployment configuration unless explicitly asked.
- Do not create runtime implementation files outside the current phase in `docs/TASKS.md`.
- Do not call external APIs (Gemini, Figma API, etc.) unless the task explicitly requires it and the phase allows it.
