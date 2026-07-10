---
name: oc-visual-test-runner
description: Run UX tests via exec only — invoke_runner.sh then format_skill_reply.py on this VM. Never use legacy ux_test_runner or --report-file tools.
---

# oc-visual-test-runner

Persona-based visual UX testing for **web** and **Figma** prototypes on this VM.

**Not** the legacy skill `ux_test_runner` (`~/.openclaw/skills/ux-test-skill/`). Never call that skill for these requests.

## Hard rules (must follow)

1. You **MUST** call the **exec** tool. Do **not** only say you will run the test.
2. Do **NOT** use skill `ux_test_runner` or any CLI that takes `--report-file`, JSON report on stdin, or similar legacy report parsers.
3. Do **NOT** invent another Python entrypoint. Allowed only:
   - `./scripts/openclaw/invoke_runner.sh ...` **or** `.venv/bin/python3 scripts/ux_testing.py ...`
   - then `.venv/bin/python3 scripts/format_skill_reply.py --output-dir ...`
4. The Feishu reply body **MUST** be exactly the **stdout** of `format_skill_reply.py` (Status/Summary/Full report, or 状态/测试摘要/完整报告). Do not rewrite, translate, or wrap it in other JSON errors.
5. If the runner fails, run `format_skill_reply.py --error "..."` and send **that** stdout.
6. Every exec block **MUST** set:
   - `PATH="/root/oc-visual-test-runner/.venv/bin:$PATH"`
   - `LANG=C.UTF-8` `PYTHONUTF8=1` `PYTHONIOENCODING=utf-8`
   - `UX_REPORT_PUBLIC_DIR` and `UX_REPORT_PUBLIC_BASE_URL`
7. Success check: directory `/tmp/ux_<run_id>` must exist after the runner. If it does not, you did not run the correct commands — retry with the canonical block below.

## Workspace

```text
/root/oc-visual-test-runner
```

| Item | Value |
|---|---|
| Venv Python | `/root/oc-visual-test-runner/.venv/bin/python3` |
| Wrapper | `./scripts/openclaw/invoke_runner.sh` |
| Formatter | `.venv/bin/python3 scripts/format_skill_reply.py` |
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

## Canonical exec block (prefer this exact pattern)

Replace `RUN_ID`, `TARGET`, `URL`, `PERSONA`, `GOAL`, and `MAX_STEPS`. Prefer this block; do not substitute other report tools.

```bash
export LANG=C.UTF-8
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
export PATH="/root/oc-visual-test-runner/.venv/bin:$PATH"
export UX_REPORT_PUBLIC_DIR=/var/www/ux-reports
export UX_REPORT_PUBLIC_BASE_URL=http://170.106.175.128:8080
# For Gemini runs (not --use-stub): ensure GOOGLE_API_KEY is set, e.g. source ~/.bashrc or the repo .env

cd /root/oc-visual-test-runner

RUN_ID="feishu-REPLACE_ME"
./scripts/openclaw/invoke_runner.sh \
  "${RUN_ID}" "TARGET" "URL" "PERSONA" "GOAL" MAX_STEPS
# Smoke only: append --use-stub as the 7th argument

/root/oc-visual-test-runner/.venv/bin/python3 scripts/format_skill_reply.py \
  --output-dir "/tmp/ux_${RUN_ID}"
```

**Pathway / smoke only** (no Gemini): pass `--use-stub` as the 7th argument to `invoke_runner.sh`.

### Direct CLI alternative (same venv rules)

```bash
export LANG=C.UTF-8 PYTHONUTF8=1 PYTHONIOENCODING=utf-8
export PATH="/root/oc-visual-test-runner/.venv/bin:$PATH"
export UX_REPORT_PUBLIC_DIR=/var/www/ux-reports
export UX_REPORT_PUBLIC_BASE_URL=http://170.106.175.128:8080
cd /root/oc-visual-test-runner

RUN_ID="feishu-REPLACE_ME"
OUTPUT_DIR="/tmp/ux_${RUN_ID}"

/root/oc-visual-test-runner/.venv/bin/python3 scripts/ux_testing.py \
  --target TARGET \
  --url "URL" \
  --persona "PERSONA" \
  --goal "GOAL" \
  --output-dir "${OUTPUT_DIR}" \
  --run-id "${RUN_ID}" \
  --max-steps 10

/root/oc-visual-test-runner/.venv/bin/python3 scripts/format_skill_reply.py \
  --output-dir "${OUTPUT_DIR}"
```

## Feishu reply

Send **only** the stdout of `format_skill_reply.py` to the user. Do not rewrite.

On failure (non-zero exit or missing `ux_result.json`):

```bash
/root/oc-visual-test-runner/.venv/bin/python3 scripts/format_skill_reply.py \
  --error "brief reason from stderr" \
  --run-id "${RUN_ID}"
```

If the user wrote in Chinese and there is no `ux_result.json`, add `--lang zh`.

### Reply shape (required)

1. **Status** — Completed / Blocked / … (`状态: 已完成` / `已阻塞` when Chinese)
2. **Reason** — required when Blocked (or max_steps / timeout)
3. **Summary** — short test summary
4. **Full report** — public report URL

### Reply rules

- Must include **Full report** with `skill.report_url` when publish env is set.
- Do not paste `action_trace.json` or full stderr.
- Keep under ~30 lines.
- Match the user’s language (EN ↔ ZH); do not mix label languages.

## Example

**User:** 用 first-time visitor 测一下 https://example.com ，看看首页主要信息是否清楚。

**Extracted:** `web` / `https://example.com` / `first-time visitor` / `Check whether the homepage main information is clear` / `run_id=feishu-om_xxx`

**Exec (exact pattern):**

```bash
export LANG=C.UTF-8 PYTHONUTF8=1 PYTHONIOENCODING=utf-8
export PATH="/root/oc-visual-test-runner/.venv/bin:$PATH"
export UX_REPORT_PUBLIC_DIR=/var/www/ux-reports
export UX_REPORT_PUBLIC_BASE_URL=http://170.106.175.128:8080
cd /root/oc-visual-test-runner

./scripts/openclaw/invoke_runner.sh \
  "feishu-om_xxx" "web" "https://example.com" \
  "first-time visitor" "Check whether the homepage main information is clear" 10

/root/oc-visual-test-runner/.venv/bin/python3 scripts/format_skill_reply.py \
  --output-dir /tmp/ux_feishu-om_xxx
```

## Prerequisites

- OpenClaw `tools.allow` includes **`exec`**
- Static host on `:8080` serving `/var/www/ux-reports` (Phase 4.5)
- Project `.venv` with Playwright Chromium
- `GOOGLE_API_KEY` for production NL runs (not `--use-stub`)
- Prefer disabling legacy `ux-test-skill` on this VM to avoid tool confusion

## Contract

Runner protocol and artifacts: `/root/oc-visual-test-runner/SKILL.md`  
Integration plan: `/root/oc-visual-test-runner/docs/OPENCLAW_INTEGRATION.md`  
Long-form reference (optional): `/root/oc-visual-test-runner/docs/openclaw/AGENT_PROMPT.md`
