# Start Here

Use this checklist when creating a new project from this starter.

## 1. Define the Project

Update:

- `README.md`
- `.cursor/rules/90-project-context.mdc`
- `docs/CONTEXT.md`

Keep these files short and factual.

## 2. Define the Work

Update:

- `docs/PRD.md`
- `docs/TASKS.md`
- `docs/DECISIONS.md`

Do not turn the PRD into a long essay. Write clear scope, requirements, and success criteria.

## 3. Define the Architecture

Update:

- `docs/ARCHITECTURE.md`

Only document architecture that actually exists or has been explicitly decided.

## 4. Define Verification

Update:

- `docs/VERIFY.md`

Cursor Agent should know how to check work before claiming completion.

## 5. Configure Tools

If MCP is needed:

1. Copy `.cursor/mcp.json.example` to `.cursor/mcp.json`.
2. Add only the MCP servers required for this project.
3. Do not put real tokens in config files.
4. Prefer read-only tools unless write access is required.

## 6. For Large Tasks

Ask Cursor to create a plan first and save it under:

```text
.cursor/plans/
```

Then execute the plan step by step.
