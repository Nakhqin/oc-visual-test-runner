# visual-test-runner — OpenClaw Skill

Persona-based visual UX testing for **web** and **Figma** prototypes on this VM.  
Invoke via **bash** only — no custom exec tool or MCP shell server required.

## Workspace

```text
/root/ux-test-runner
```

## When to use

User asks to test a website or Figma prototype as a persona (natural language in Feishu).

## Required inputs (extract from user message)

| Field | Notes |
|---|---|
| `target` | `figma` or `web` |
| `url` | Absolute http(s) URL |
| `persona` | Simulated user profile |
| `goal` | Task to attempt |
| `run_id` | Optional; e.g. `feishu-{message_id}` |

Ask **one** clarifying question if `url` or `goal` is missing.

## How to run (shell)

```bash
cd /root/ux-test-runner

export UX_REPORT_PUBLIC_DIR=/var/www/ux-reports
export UX_REPORT_PUBLIC_BASE_URL=http://170.106.175.128:8080

RUN_ID="feishu-REPLACE_ME"
OUTPUT_DIR="/tmp/ux_${RUN_ID}"

python3 scripts/ux_testing.py \
  --target TARGET \
  --url "URL" \
  --persona "PERSONA" \
  --goal "GOAL" \
  --output-dir "${OUTPUT_DIR}" \
  --run-id "${RUN_ID}" \
  --max-steps 10
```

Replace `TARGET`, `URL`, `PERSONA`, `GOAL`, and `RUN_ID`.

## Feishu reply

After a successful run:

```bash
cd /root/ux-test-runner
python3 scripts/format_skill_reply.py --output-dir "${OUTPUT_DIR}"
```

Send the **stdout** to the user. Do not send raw runner logs.

On failure:

```bash
python3 scripts/format_skill_reply.py --error "reason" --run-id "${RUN_ID}"
```

## Full agent instructions

See `/root/ux-test-runner/docs/openclaw/AGENT_PROMPT.md` (or repo `docs/openclaw/AGENT_PROMPT.md`).

## Contract

Runner protocol and artifacts: `/root/ux-test-runner/SKILL.md`.
