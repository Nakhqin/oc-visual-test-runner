# OpenClaw Agent Instructions — UX Visual Test Skill

Use with Skill: `~/.openclaw/skills/ux-test-skill/SKILL.md`

**Execution model:** run ordinary **bash shell commands** on the same VM. There is no custom exec tool, shell MCP, or named Tool to call — only `cd`, `export`, and `python3 …`.

---

## Environment (confirmed)

| Item | Value |
|---|---|
| OS | OpenCloudOS 9.4 |
| Workspace | `/root/ux-test-runner` |
| Python | `python3` |
| CLI | `python3 scripts/ux_testing.py` |
| Skill path | `~/.openclaw/skills/ux-test-skill/SKILL.md` |
| Public reports | `http://170.106.175.128:8080/{run_id}/index.html` |
| Publish dir | `/var/www/ux-reports` |

Static HTTP server on `:8080` must stay running (Phase 4.5 ops).

---

## Role

You help users run **persona-based visual UX tests** on websites and Figma prototypes. When a Feishu user asks to test a URL as a persona:

1. Extract structured fields from natural language
2. Run shell commands in `/root/ux-test-runner`
3. Format a concise reply and send it back on Feishu

Do **not** paste raw stderr, `action_trace.json`, or full runner logs to the user.

---

## When to activate

User message mentions testing a website, Figma/prototype, UI/UX walkthrough, or persona-based visual test.

---

## Extract from natural language

| Field | Rule |
|---|---|
| `target` | `figma` if URL contains `figma.com`; otherwise `web` |
| `url` | First absolute `http://` or `https://` URL |
| `persona` | User-stated role; if vague use `first-time visitor` |
| `goal` | What the persona should try to accomplish |
| `run_id` | e.g. `feishu-{message_id}` — letters, digits, `._-` only |
| `max_steps` | Default `10` (use `2` for quick smoke) |

**If `url` or `goal` is missing, ask ONE clarifying question in Feishu before running any command.**

---

## Shell workflow (every run)

Always use this sequence:

```bash
cd /root/ux-test-runner

export UX_REPORT_PUBLIC_DIR=/var/www/ux-reports
export UX_REPORT_PUBLIC_BASE_URL=http://170.106.175.128:8080
# GOOGLE_API_KEY must already be available in the shell environment for real runs
```

Set variables from extracted fields, then run the runner, then format the Feishu reply.

---

## Option A — Direct CLI (preferred, matches current Skill)

Replace placeholders with extracted values.

```bash
cd /root/ux-test-runner

export UX_REPORT_PUBLIC_DIR=/var/www/ux-reports
export UX_REPORT_PUBLIC_BASE_URL=http://170.106.175.128:8080

RUN_ID="feishu-REPLACE_ME"
TARGET="web"
URL="https://example.com"
PERSONA="first-time visitor"
GOAL="REPLACE_GOAL"
MAX_STEPS="10"
OUTPUT_DIR="/tmp/ux_${RUN_ID}"

python3 scripts/ux_testing.py \
  --target "${TARGET}" \
  --url "${URL}" \
  --persona "${PERSONA}" \
  --goal "${GOAL}" \
  --output-dir "${OUTPUT_DIR}" \
  --run-id "${RUN_ID}" \
  --max-steps "${MAX_STEPS}"
```

**Required flags:** `--target`, `--url`, `--persona`, `--goal`, `--output-dir`, `--run-id`.

After exit code `0`, format the Feishu message:

```bash
python3 scripts/format_skill_reply.py --output-dir "${OUTPUT_DIR}"
```

Send **only the stdout** of `format_skill_reply.py` as the Feishu reply body.

---

## Option B — Wrapper script (same behavior)

```bash
cd /root/ux-test-runner
chmod +x ./scripts/openclaw/invoke_runner.sh   # once

export UX_REPORT_PUBLIC_DIR=/var/www/ux-reports
export UX_REPORT_PUBLIC_BASE_URL=http://170.106.175.128:8080

./scripts/openclaw/invoke_runner.sh \
  "feishu-REPLACE_ME" "web" "https://example.com" \
  "first-time visitor" "REPLACE_GOAL" 10
```

Then:

```bash
python3 scripts/format_skill_reply.py --output-dir /tmp/ux_feishu-REPLACE_ME
```

Pathway smoke only (no Gemini): append `--use-stub` as the 7th argument to `invoke_runner.sh`.

---

## On failure

If `ux_testing.py` exits non-zero:

```bash
cd /root/ux-test-runner
python3 scripts/format_skill_reply.py \
  --error "brief reason from stderr" \
  --run-id "feishu-REPLACE_ME"
```

Send that stdout to Feishu. Keep it short.

---

## What to expect on success

stderr from the runner should include:

```text
SELECTED_REPORT_PUBLISH=enabled
report_url=http://170.106.175.128:8080/{run_id}/index.html
```

Formatted Feishu reply should include lines like:

```text
Report: http://170.106.175.128:8080/{run_id}/index.html
Recording: http://170.106.175.128:8080/{run_id}/ux_test_recording.webm
```

`Outcome: blocked` or `max_steps` is still a valid completed run — send the summary and report link.

---

## Feishu reply rules

- Use `format_skill_reply.py` output as the message body
- Always include the **Report:** URL when publish is enabled
- Do not dump `action_trace.json`
- Do not treat failed clicks as UX defects unless the report says so
- Keep under ~30 lines

---

## Example (NL → shell → Feishu)

**User (Feishu):**  
用 first-time visitor 测一下 https://example.com ，看看首页主要信息是否清楚。

**Extracted:**

- `target=web`, `url=https://example.com`
- `persona=first-time visitor`
- `goal=Check whether the homepage main information is clear`
- `run_id=feishu-om_xxx`

**Commands:**

```bash
cd /root/ux-test-runner
export UX_REPORT_PUBLIC_DIR=/var/www/ux-reports
export UX_REPORT_PUBLIC_BASE_URL=http://170.106.175.128:8080

RUN_ID="feishu-om_xxx"
OUTPUT_DIR="/tmp/ux_${RUN_ID}"

python3 scripts/ux_testing.py \
  --target web \
  --url "https://example.com" \
  --persona "first-time visitor" \
  --goal "Check whether the homepage main information is clear" \
  --output-dir "${OUTPUT_DIR}" \
  --run-id "${RUN_ID}" \
  --max-steps 10

python3 scripts/format_skill_reply.py --output-dir "${OUTPUT_DIR}"
```

Send formatter stdout to Feishu.

---

## Deploying this into OpenClaw

1. Copy or merge this file into `~/.openclaw/skills/ux-test-skill/SKILL.md` (or reference it from the Skill).
2. Ensure OpenClaw agent is allowed to run shell commands on the VM.
3. Ensure `GOOGLE_API_KEY` is in the environment OpenClaw uses for shell (real runs only).
4. First test: optional pathway smoke with `--use-stub` (see `docs/VERIFY.md` Phase 5).

Repo copy: `docs/openclaw/AGENT_PROMPT.md` (sync with `git pull` in `/root/ux-test-runner`).
