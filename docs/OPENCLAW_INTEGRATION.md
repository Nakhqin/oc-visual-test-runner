# OpenClaw Integration — Phase 5 Plan

Phase 5 delivery plan for wiring **oc-visual-test-runner** into **OpenClaw** on the cloud VM, with replies via the **existing Feishu channel**.

**Status:** Phase 5.1 helpers implemented in repo; **5.2 OpenClaw wiring in progress** (NL-first path). Runner Phases 1–4.5 complete.

**Implementation path (agreed):** Feishu NL as main line; fixed JSON only for internal pathway smoke — not a separate milestone.

---

## Confirmed decisions (2026-07-03)

| Topic | Decision |
|---|---|
| **Deployment** | OpenClaw Skill and runner run on the **same VM** (`170.106.175.128`) |
| **NL → structured input** | **OpenClaw main agent** extracts fields — not implemented in this repo |
| **Feishu** | Use the **existing OpenClaw Feishu channel** for user-facing replies |
| **Report URL** | Consume `skill.report_url` from Phase 4.5 publish — **no duplicate publish in OpenClaw** |

Record: `docs/DECISIONS.md` — Phase 5 OpenClaw integration scope.

---

## Goal (exit criteria)

A user sends a **natural-language** UX test request in Feishu. OpenClaw:

1. Derives structured Skill input per `SKILL.md`
2. Invokes `scripts/ux_testing.py` on the same VM
3. Reads `ux_result.json` after the run
4. Replies in Feishu with a **concise summary** and a **clickable `report_url`** (plus recording link when published)

The reply must **not** be raw runner stderr or full trace logs.

---

## Architecture on the VM

```text
Feishu user (NL message)
        │
        ▼
OpenClaw (same VM: 170.106.175.128)
  ├── main agent: NL → { target, url, persona, goal, … }
  ├── subprocess: scripts/ux_testing.py
  └── format reply from ux_result.json → Feishu channel
        │
        ▼
Runner (this repo)
  ├── visual agent loop → /tmp/ux_{run_id}/
  ├── publish → /var/www/ux-reports/{run_id}/
  └── ux_result.json.skill.report_url
        │
        ▼
Static HTTP :8080 → http://170.106.175.128:8080/{run_id}/index.html
        │
        ▼
Feishu reply (summary + report_url link)
```

### Components already running (Phase 4.5 verified)

| Component | Location / value |
|---|---|
| Runner repo | e.g. `~/oc-visual-test-runner` |
| Python venv | `.venv` with Playwright + dependencies |
| Publish dir | `/var/www/ux-reports` |
| Public base URL | `http://170.106.175.128:8080` |
| Static host | `python3 -m http.server 8080 --bind 0.0.0.0 --directory /var/www/ux-reports` |

OpenClaw subprocess **must** inherit publish env vars (see [Environment](#environment-on-the-vm)).

---

## Responsibility split

| Layer | Owner | Phase 5 work |
|---|---|---|
| Visual agent loop, reports, publish | **This repo** (done) | Optional: `skill.recording_url` helper (5.1) |
| NL → structured input | **OpenClaw main agent** | Prompt / tool schema for Skill fields |
| CLI invocation, `run_id`, env | **OpenClaw** | Shell tool or Skill handler on VM |
| User-facing Feishu reply | **OpenClaw** | Template from `ux_result.json` + `SKILL.md` |
| Skill registration / manifest | **OpenClaw config** + **this repo docs** | Manifest snippet in this doc |

**Non-goals (Phase 5):**

- Re-implementing publish (Phase 4.5)
- Feishu SDK or bot code inside this repo
- NL parsing scripts in this repo
- HTTPS / auth for public reports
- Android / Windows adapters

---

## Sub-phases

### Phase 5.1 — Integration contract (this repo)

**Goal:** OpenClaw operators can integrate without reading runner source.

| Task | Status |
|---|---|
| `docs/OPENCLAW_INTEGRATION.md` | Done |
| `scripts/format_skill_reply.py` + `scripts/core/skill_return.py` | Done |
| `scripts/openclaw/invoke_runner.sh` | Done |
| `docs/openclaw/AGENT_PROMPT.md` | Done |
| `skill.recording_url` + `skill.result_json_url` when publish enabled | Done |
| Link from `README.md` / `AGENTS.md` | Done |

### Phase 5.2 — OpenClaw wiring (OpenClaw side) — in progress

**Goal:** Feishu NL → runner → formatted Feishu reply with `report_url`.

| Task | Status |
|---|---|
| Install prompt from `docs/openclaw/AGENT_PROMPT.md` | Todo |
| Register shell tool → `invoke_runner.sh` | Todo |
| Post-run `format_skill_reply.py` → Feishu | Todo |
| Optional pathway smoke (`--use-stub`) before first NL | Todo |
| NL extraction + clarifying question when fields missing | Todo |

**Note:** Fixed JSON invoke is optional internal smoke only — not a separate milestone.

### Phase 5.3 — E2E verification

**Goal:** Close Phase 5 in `docs/TASKS.md` and `docs/VERIFY.md`.

| Task | Status |
|---|---|
| Feishu NL message → full run (Gemini, not stub) | Todo |
| Reply contains clickable `report_url` (public network) | Todo |
| `blocked` / `max_steps` runs still produce readable summary | Todo |
| Document failure modes (no publish env, runner exit 1) | Todo |

---

## Environment on the VM

OpenClaw's runner subprocess should use the same env as manual smoke tests:

```bash
# Publish (required for public report_url in Feishu)
export UX_REPORT_PUBLIC_DIR=/var/www/ux-reports
export UX_REPORT_PUBLIC_BASE_URL=http://170.106.175.128:8080

# Gemini (required for real runs; omit --use-stub)
export GOOGLE_API_KEY=...          # from .env or OpenClaw secret store — never commit
export GEMINI_MODEL=gemini-2.5-flash   # optional

# Optional persona polish
export PERSONA_REPORT_GEMINI=1     # optional
```

Working directory: repo root (or absolute path to `scripts/ux_testing.py`).

Python: `~/oc-visual-test-runner/.venv/bin/python3` (recommended) or activated venv.

---

## CLI invocation (OpenClaw → runner)

OpenClaw invokes the runner via **local subprocess** on the same VM:

```bash
cd /root/oc-visual-test-runner   # adjust to actual path
source .venv/bin/activate

export UX_REPORT_PUBLIC_DIR=/var/www/ux-reports
export UX_REPORT_PUBLIC_BASE_URL=http://170.106.175.128:8080

python3 ./scripts/ux_testing.py \
  --target web \
  --url "https://example.com" \
  --persona "first-time visitor" \
  --goal "find the main information on the homepage" \
  --output-dir "/tmp/ux_${RUN_ID}" \
  --run-id "${RUN_ID}" \
  --max-steps 10 \
  --timeout-seconds 180
```

### `run_id` convention (recommended)

| Source | Example | Notes |
|---|---|---|
| Feishu message id | `feishu-om_xxx` | Traceable to chat thread |
| OpenClaw session id | `oc-session-abc123` | Alternative |
| Omitted | auto `{timestamp}-{uuid}` | OK for dev; harder to correlate in Feishu |

Pass the same value to `--run-id` and use it in `--output-dir` for clarity.

### stdout / stderr OpenClaw should capture

**stdout (selection metadata):**

```text
SELECTED_TARGET=web
SELECTED_ADAPTER=browser
SELECTED_RUNNER=visual_agent
SELECTED_REPORT_PUBLISH=enabled
...
```

**stderr (run result — parse or cross-check with JSON):**

```text
terminal_state=done|blocked|max_steps|timeout
run_id=...
report_url=http://170.106.175.128:8080/{run_id}/index.html
published_dir=/var/www/ux-reports/{run_id}
ux_result=/tmp/ux_{run_id}/ux_result.json
```

**Exit codes:** `0` success, `1` runtime error (e.g. browser), `2` config/validation error.

If `SELECTED_REPORT_PUBLISH=disabled`, warn the user in Feishu that no public link is available (local paths only).

---

## NL extraction (OpenClaw main agent)

OpenClaw maps user Feishu text to Skill-level input per `SKILL.md`:

| Field | Required | Extraction hints |
|---|---|---|
| `target` | Yes | `figma` if Figma/proto URL; else `web` |
| `url` | Yes | First absolute http(s) URL in message |
| `persona` | Yes | User-stated role; default e.g. "first-time visitor" if vague |
| `goal` | Yes | Task sentence; ask clarifying question if missing |
| `max_steps` | No | Default 10 |
| `timeout_seconds` | No | Default 180 |
| `run_id` | No | Generate from Feishu context |

**Example Feishu input:**

> 用 first-time visitor 测一下 https://example.com ，看看首页主要信息是否清楚。

**Derived structured input:**

```json
{
  "target": "web",
  "url": "https://example.com",
  "persona": "first-time visitor",
  "goal": "Check whether the homepage main information is clear",
  "output_dir": "/tmp/ux_feishu-om_xxx",
  "run_id": "feishu-om_xxx"
}
```

If `target`, `url`, `persona`, or `goal` cannot be inferred, OpenClaw should **ask one clarifying question** in Feishu before invoking the runner.

---

## Feishu reply template

Build from `ux_result.json` — not from raw logs. Align with `SKILL.md` **User-Facing Return**.

### Field mapping

| User-facing line | Source |
|---|---|
| Outcome | `terminal_state` |
| Target | `target` |
| Persona | `persona` |
| Goal | `goal` |
| Main finding | `main_finding` |
| Classification | `classifications` (or "(none)") |
| One-line summary | `skill.return_summary` |
| Report link | `skill.report_url` |
| Recording link | `skill.recording_url` (publish) or `{report_base_url}/{artifacts.recording}` |
| Result JSON (optional) | `skill.result_json_url` |

### Example Feishu message

```text
UX visual test completed.

Target: web
Persona: first-time visitor
Goal: Check whether the homepage main information is clear
Outcome: max_steps
Main finding: The agent loop exhausted max_steps without a done or blocked action.
Classification: (none)

Report: http://170.106.175.128:8080/feishu-om_xxx/index.html
Recording: http://170.106.175.128:8080/feishu-om_xxx/ux_test_recording.webm
```

Feishu supports clickable URLs in plain text when the channel renders links.

### Failure reply (runner exit ≠ 0)

```text
UX visual test could not complete.

Reason: <stderr last error line or terminal_state>
Run id: <run_id if known>

Please check runner logs on the VM or retry with a simpler goal.
```

Do **not** paste full `action_trace.json` into Feishu.

---

## OpenClaw Skill registration (outline)

Exact manifest format depends on your OpenClaw version — adjust paths to match deployment.

**Skill metadata (conceptual):**

| Property | Value |
|---|---|
| Name | `oc-visual-test-runner` / `ux-visual-test` |
| Description | Persona-based visual UX testing for web and Figma prototypes |
| Working directory | `/root/oc-visual-test-runner` (VM path) |
| Entry | subprocess → `python3 scripts/ux_testing.py` with structured args |
| Required secrets | `GOOGLE_API_KEY` |
| Required env | `UX_REPORT_PUBLIC_DIR`, `UX_REPORT_PUBLIC_BASE_URL` |
| Timeout | ≥ `timeout_seconds` + buffer (e.g. 300s+) for long runs |

Document the final manifest path in OpenClaw config when registered (outside this repo).

---

## Repo helpers (Phase 5.1)

| Script | Purpose |
|---|---|
| `scripts/openclaw/invoke_runner.sh` | OpenClaw subprocess wrapper (publish env + CLI args) |
| `scripts/format_skill_reply.py` | Print Feishu-ready text from `ux_result.json` |
| `docs/openclaw/AGENT_PROMPT.md` | Copy-paste OpenClaw agent / Skill prompt |

### Pathway smoke (optional, ~5 min)

On the VM, before first Feishu NL test:

```bash
chmod +x ./scripts/openclaw/invoke_runner.sh
./scripts/openclaw/invoke_runner.sh pathway-smoke-001 web https://example.com \
  "first-time visitor" "pathway smoke" 2 --use-stub

./scripts/format_skill_reply.py --output-dir /tmp/ux_pathway-smoke-001
```

Expect clickable `Report:` URL in the formatted output.

### OpenClaw tool flow (NL)

1. User message in Feishu → OpenClaw agent (prompt in `docs/openclaw/AGENT_PROMPT.md`)
2. Agent extracts fields; asks if `url` or `goal` missing
3. Shell tool: `invoke_runner.sh {run_id} {target} {url} {persona} {goal} {max_steps}`
4. Shell tool: `format_skill_reply.py --output-dir /tmp/ux_{run_id}`
5. Send formatter stdout to Feishu channel

---

## Error handling

| Condition | OpenClaw behavior |
|---|---|
| `SELECTED_REPORT_PUBLISH=disabled` | Tell user public link unavailable; include local `output_dir` for ops only if appropriate |
| `terminal_state=blocked` + VLM error | Summarize as system/runtime issue; still send `report_url` if publish succeeded |
| `terminal_state=max_steps` | Not a failure — send summary + report link |
| Runner exit `2` | Ask user to fix missing/invalid parameters |
| Runner exit `1` | Report browser/Gemini failure; suggest retry |
| Run exceeds OpenClaw tool timeout | Consider async pattern (Phase 5+); MVP: increase timeout or reduce `max_steps` |

---

## Verification

See `docs/VERIFY.md` — **Phase 5** checklist.

Minimum E2E:

1. Feishu NL message → OpenClaw extracts fields
2. Runner completes on VM with `SELECTED_REPORT_PUBLISH=enabled`
3. Feishu reply includes `skill.report_url`
4. URL opens in browser from outside the VM

---

## Related documents

| Document | Purpose |
|---|---|
| `SKILL.md` | Skill input/output contract |
| `docs/TASKS.md` | Phase 5 task breakdown |
| `docs/VERIFY.md` | Phase 5 verification steps |
| `docs/DECISIONS.md` | Phase 5 scope decisions |
| `docs/ARCHITECTURE.md` | System flow diagram |
