---
name: oc-visual-test-runner
description: Persona-based visual UX testing for web and Figma prototypes via scripts/ux_testing.py on this VM. Use for Feishu NL walkthrough requests; not the legacy ux_test_runner skill.
---

# oc-visual-test-runner

Persona-based visual UX testing for **web** and **Figma** prototypes on this VM.  
Invoke via **bash** only — no custom exec tool or MCP shell server required.

**Not the same skill as** `ux_test_runner` / `~/.openclaw/skills/ux-test-skill/` (legacy). This skill always uses workspace `/root/oc-visual-test-runner`.

## Workspace

```text
/root/oc-visual-test-runner
```

| Item | Value |
|---|---|
| CLI | `python3 scripts/ux_testing.py` |
| Reply formatter | `python3 scripts/format_skill_reply.py` |
| Optional wrapper | `./scripts/openclaw/invoke_runner.sh` |
| Publish dir | `/var/www/ux-reports` |
| Public base URL | `http://170.106.175.128:8080` |

## When to use

User asks (e.g. in Feishu) to test a website or Figma prototype as a persona — UI/UX walkthrough, onboarding, or visual review.

Explicit invoke: `/oc-visual-test-runner` or `/skill oc-visual-test-runner`.

## Extract from natural language

| Field | Rule |
|---|---|
| `target` | `figma` if URL contains `figma.com`; else `web` |
| `url` | First absolute `http://` or `https://` URL |
| `persona` | User-stated role; if vague use `first-time visitor` |
| `goal` | What the persona should try to accomplish |
| `run_id` | e.g. `feishu-{message_id}` — letters, digits, `._-` only |
| `max_steps` | Default `10` (use `2` for quick smoke) |

**If `url` or `goal` is missing, ask ONE clarifying question before running any command.** Do not invent a goal.

## How to run (bash)

Every production run:

1. `cd` to workspace  
2. `export` publish env (and ensure `GOOGLE_API_KEY` is set for Gemini)  
3. Run `ux_testing.py`  
4. Run `format_skill_reply.py`  
5. Send formatter **stdout** as the Feishu reply — not raw logs or `action_trace.json`

```bash
cd /root/oc-visual-test-runner

export UX_REPORT_PUBLIC_DIR=/var/www/ux-reports
export UX_REPORT_PUBLIC_BASE_URL=http://170.106.175.128:8080
# GOOGLE_API_KEY must be in the shell environment for Gemini runs

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

Replace `TARGET`, `URL`, `PERSONA`, `GOAL`, and `RUN_ID` with values from the user message.

**Pathway / smoke only** (no Gemini): add `--use-stub`.

### Optional wrapper

```bash
cd /root/oc-visual-test-runner
./scripts/openclaw/invoke_runner.sh \
  "${RUN_ID}" "TARGET" "URL" "PERSONA" "GOAL" 10
```

## Feishu reply

After exit 0:

```bash
cd /root/oc-visual-test-runner
python3 scripts/format_skill_reply.py --output-dir "${OUTPUT_DIR}"
```

Send that command’s **stdout** to the user.

On failure (non-zero exit or missing `ux_result.json`):

```bash
cd /root/oc-visual-test-runner
python3 scripts/format_skill_reply.py \
  --error "brief reason from stderr" \
  --run-id "${RUN_ID}"
```

### Reply rules

- Must include **Report:** with `skill.report_url` when publish env is set.
- Include outcome and main finding even for `blocked` or `max_steps`.
- Do not paste `action_trace.json` or full stderr.
- Keep under ~30 lines.

## Example

**User:** 用 first-time visitor 测一下 https://example.com ，看看首页主要信息是否清楚。

**Extracted:** `web` / `https://example.com` / `first-time visitor` / `Check whether the homepage main information is clear` / `run_id=feishu-om_xxx`

**Commands:**

```bash
cd /root/oc-visual-test-runner
export UX_REPORT_PUBLIC_DIR=/var/www/ux-reports
export UX_REPORT_PUBLIC_BASE_URL=http://170.106.175.128:8080

python3 scripts/ux_testing.py \
  --target web \
  --url "https://example.com" \
  --persona "first-time visitor" \
  --goal "Check whether the homepage main information is clear" \
  --output-dir /tmp/ux_feishu-om_xxx \
  --run-id feishu-om_xxx \
  --max-steps 10

python3 scripts/format_skill_reply.py --output-dir /tmp/ux_feishu-om_xxx
```

## Prerequisites

- Static host on `:8080` serving `/var/www/ux-reports` (Phase 4.5)
- Playwright Chromium available for the runner
- `GOOGLE_API_KEY` for production NL runs (not `--use-stub`)

## Contract

Runner protocol and artifacts: `/root/oc-visual-test-runner/SKILL.md`  
Integration plan: `/root/oc-visual-test-runner/docs/OPENCLAW_INTEGRATION.md`  
Long-form reference (optional): `/root/oc-visual-test-runner/docs/openclaw/AGENT_PROMPT.md`
