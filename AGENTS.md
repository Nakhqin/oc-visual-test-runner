# AGENTS.md

This file gives coding agents the minimum repo context needed to work safely.

## Start Here

1. Read `README.md` for the project overview.
2. Read `.cursor/rules/90-project-context.mdc` for current project facts.
3. Read `docs/PRD.md` if the task affects product behavior.
4. Read `docs/ARCHITECTURE.md` if the task affects structure, integration, or refactoring.
5. Read `docs/TASKS.md` for current priorities.
6. Read `docs/VERIFY.md` before claiming the task is complete.

## Working Rules

- Make small, reviewable changes.
- Do not assume missing project details.
- Do not introduce new tools, frameworks, dependencies, or architecture patterns without justification.
- Keep documentation updated when behavior, setup, or architecture changes.
- Prefer a written plan for multi-file, risky, or architectural changes.

## Verification

Before finishing, provide:

- changed files
- verification steps performed or recommended
- known risks
- unresolved questions, if any

## Boundaries

- Do not commit secrets.
- Do not run destructive commands without explicit approval.
- Do not modify deployment or production configuration unless explicitly asked.
