# OpenClaw reference — oc-visual-test-runner

**Status:** Reference / long-form notes. **Do not** paste this file into OpenClaw Agent Instructions.

OpenClaw loads skills from `SKILL.md` automatically. The installable skill is:

```text
docs/openclaw/OPENCLAW_SKILL.md
  → ~/.openclaw/skills/oc-visual-test-runner/SKILL.md
```

That file has YAML frontmatter (`name: oc-visual-test-runner`) and the full bash + Feishu reply instructions.

**Not** the legacy skill `ux_test_runner` (`~/.openclaw/skills/ux-test-skill/`).

---

## Environment (this deployment)

| Item | Value |
|---|---|
| OS | OpenCloudOS 9.4 |
| Workspace | `/root/oc-visual-test-runner` |
| Python | `python3` |
| CLI | `python3 scripts/ux_testing.py` |
| OpenClaw Skill file | `~/.openclaw/skills/oc-visual-test-runner/SKILL.md` |
| Publish dir | `/var/www/ux-reports` |
| Public base URL | `http://170.106.175.128:8080` |

---

## Install / refresh Skill (Phase 5.2)

```bash
mkdir -p ~/.openclaw/skills/oc-visual-test-runner
cp /root/oc-visual-test-runner/docs/openclaw/OPENCLAW_SKILL.md \
   ~/.openclaw/skills/oc-visual-test-runner/SKILL.md

openclaw skills list | grep -i oc-visual
# Expect: oc-visual-test-runner  ✓ ready

# New Feishu session so the agent picks up the skill:
# /new   or: openclaw gateway restart
```

---

## Role (summary)

When the user asks to test a URL as a persona:

1. Extract structured fields from natural language (or ask one clarifying question).
2. Run the runner via **bash** on this VM (`/root/oc-visual-test-runner`).
3. Format a concise Feishu reply with **clickable report link** — not raw logs or `action_trace.json`.

Full command templates and reply rules live in `OPENCLAW_SKILL.md` (installed copy above).

---

## Extract from NL

| Field | Rule |
|---|---|
| `target` | `figma` if URL contains `figma.com`; else `web` |
| `url` | First absolute `http://` or `https://` URL |
| `persona` | User-stated role; if vague use `first-time visitor` |
| `goal` | What the persona should try to accomplish |
| `run_id` | e.g. `feishu-{message_id}` — letters, digits, `._-` only |
| `max_steps` | Default `10` (use `2` for quick smoke) |

**If `url` or `goal` is missing, ask ONE clarifying question in Feishu before running any command.**

---

## Execution model

Use the platform’s **default shell command execution** (bash). Do not assume a custom Tool name.

Every run:

1. `cd` to workspace  
2. `export` publish env (and ensure `GOOGLE_API_KEY` is set for real runs)  
3. Run **`./scripts/openclaw/invoke_runner.sh`** once — **stdout is the Feishu reply**  
4. Send that stdout as the Feishu message body — **no interim “Executing…” message**

For ops/debug only: direct `ux_testing.py` + separate `format_skill_reply.py` (see `OPENCLAW_SKILL.md`).

---

## Feishu reply rules

- Use **stdout** of `invoke_runner.sh` (or `format_skill_reply.py` in debug flows) as the message body **unchanged**.
- Shape: **Status** (+ **Reason** if blocked/stopped) → **Summary** → **Full report**.
- Language: formatter auto-detects Chinese vs English from `goal`/`persona` (or `--lang`).
- **Must** use exec with project `.venv` PATH; never legacy `ux_test_runner` / `--report-file`.
- Do not paste `action_trace.json` or full stderr.
- Keep under ~30 lines.

---

## Prerequisites (ops)

- Static host on `:8080` serving `/var/www/ux-reports` (Phase 4.5)
- `python3 -m playwright install chromium` in workspace venv if needed
- `GOOGLE_API_KEY` for production NL runs (not `--use-stub`)

Contract details: repo root `SKILL.md` and `docs/OPENCLAW_INTEGRATION.md`.
