# Nana Cursor Starter Kit

A minimal starter kit for Cursor-based projects.

The goal is to give Cursor Agent enough structure to work safely without bloating context.

## What This Includes

```text
.cursor/
  rules/
    00-agent-discipline.mdc
    10-code-quality.mdc
    20-safety.mdc
    90-project-context.mdc
  plans/
    .gitkeep
  mcp.json.example

docs/
  PRD.md
  ARCHITECTURE.md
  TASKS.md
  DECISIONS.md
  VERIFY.md
  CONTEXT.md

AGENTS.md
START_HERE.md
.cursorignore
.gitignore
.env.example
```

## First Setup

1. Rename this folder to your project name.
2. Update `README.md` with the real project overview.
3. Update `.cursor/rules/90-project-context.mdc` with stable project facts.
4. Fill in `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/TASKS.md`, and `docs/VERIFY.md`.
5. Copy `.cursor/mcp.json.example` to `.cursor/mcp.json` only when MCP is needed.
6. Copy `.env.example` to `.env` locally and never commit real secrets.

## Best Practice

Use this starter as a skeleton, not as a project encyclopedia.

- Rules should be short and strict.
- Docs should describe current reality.
- Plans should be created before large changes.
- Skills should be added only for specialized workflows.
- MCP should use the minimum permissions needed.
