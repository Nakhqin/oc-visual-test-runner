# Grounding regression fixtures — Phase 5.5 formal acceptance

**Purpose:** Formal **Gemini E2E** regression for visual click grounding. Used for **UVG sign-off** (Phase 5.5b).  
**Not a substitute for:** stub smoke or unit tests — those only verify pipeline wiring.

**Primary doc:** `docs/GROUNDING.md` (UVG stack + scenarios A–E).  
**Baseline failure:** `grounding-A-test-1` — G1+G2 alone insufficient.  
**Runner:** cloud VM `170.106.175.128`, repo `/root/oc-visual-test-runner`, `GOOGLE_API_KEY` via `.env` / `source ~/.bashrc`.

---

## Test tiers (summary)

| Tier | What | Proves grounding quality? | Required for 5.5 sign-off? |
|---|---|---|:---:|
| **0 — Unit** | `.tmp/test_coordinates.py`, `.tmp/test_hover_alignment.py` | No | Yes (fast gate) |
| **1 — Smoke** | `--use-stub`, example.com | No — schema + loop only | Yes (pre-merge sanity) |
| **2 — Formal regression** | Gemini, fixtures below, 3× per scenario | **Yes** | **Yes (after UVG L1+L2)** |

**Phase 5.5 is not accepted on stub smoke alone.** Tier 2 must pass scenarios **A–C** after **UVG** is implemented (G1+G2 alone failed scenario A).

---

## Fixtures

Record the **canonical URL** used for each scenario. Update this file when protos change.

| ID | Scenario | Target | Fixture URL | Goal (exact) | Persona (suggested) |
|---|---|---|---|---|---|
| **A** | Tablet setup flow (Figma) | `figma` | `FIGMA_SETUP_PROTO_URL` below | `Complete the first-time tablet setup and reach the home screen.` | `FIGMA_PERSONA` below (Chinese first-time tablet user) |
| **B** | Icon-only | `figma` | `FIGMA_ICON_ONLY_URL` — **TBD** | `Open the menu.` (or close/back — match screen) | `FIGMA_PERSONA` below |
| **C** | Icon + label button | `figma` or `web` | `FIGMA_COMPOSITE_URL` or web fallback — **TBD** | `Tap the Continue button.` | `FIGMA_PERSONA` below |
| **D** | Web sanity | `web` | `https://example.com` | `Click the More information link.` | `A cautious first-time visitor.` |
| **E** | Non-click (G2 out of scope) | `web` | `https://www.wikipedia.org` | `Scroll down to find the language list; do not click unless necessary.` | `FIGMA_PERSONA` below |

### Scenario A — tablet setup proto (confirmed project proto)

Aligns with **`docs/PRD.md`** scenario 2: first-time tablet setup to home — **not** a single-step “Select English” micro-goal.

```bash
export FIGMA_SETUP_PROTO_URL='https://www.figma.com/proto/rqLUySVeWpFeu8E9sAwkrW/Test-test?page-id=0%3A1&node-id=10-10157&p=f&scaling=min-zoom&content-scaling=fixed&starting-point-node-id=10%3A10157'

export FIGMA_PERSONA='A cautious first-time Chinese tablet user who is not familiar with this device. They normally read Chinese and expect the device to use Chinese.'

export FIGMA_GOAL='Complete the first-time tablet setup and reach the home screen.'

# Legacy alias (same URL):
export FIGMA_LANGUAGE_LIST_URL="$FIGMA_SETUP_PROTO_URL"
```

> Proto may open **before** the language screen (e.g. welcome / Next). That is expected — the persona should progress through setup. On the language screen, a Chinese persona should reasonably choose **简体中文** (not English unless the goal says otherwise).

### Scenarios B & C — fill before formal run

1. Pick a **public** `figma.com/proto/...` frame with a clear icon-only control (B) or icon+label button (C).
2. Paste URLs into the table above and export env vars:

```bash
export FIGMA_ICON_ONLY_URL='https://www.figma.com/proto/...'
export FIGMA_COMPOSITE_URL='https://www.figma.com/proto/...'
```

**Web fallback (C only):** any page with a visible icon+text button (e.g. primary CTA with leading icon).

---

## Formal run commands (Tier 2)

**Prerequisites on VM:**

```bash
cd /root/oc-visual-test-runner
source ~/.bashrc   # or: set -a && source .env && set +a
# Confirm: python3 -c "import os; print('key len', len(os.environ.get('GOOGLE_API_KEY','')))"
```

**Do not pass `--use-stub`.** Run each scenario **3 times** with distinct output dirs.

### Scenario A — template

```bash
RUN=grounding-A-$(date +%Y%m%d-%H%M%S)
python3 scripts/ux_testing.py \
  --target figma \
  --url "$FIGMA_SETUP_PROTO_URL" \
  --persona "$FIGMA_PERSONA" \
  --goal "$FIGMA_GOAL" \
  --output-dir "/tmp/ux_grounding/${RUN}" \
  --max-steps 15 \
  --timeout-seconds 300 \
  --run-id "$RUN" \
  2>&1 | tee "/tmp/ux_grounding/${RUN}.log"
```

### Scenario B — template

```bash
RUN=grounding-B-$(date +%Y%m%d-%H%M%S)
python3 scripts/ux_testing.py \
  --target figma \
  --url "$FIGMA_ICON_ONLY_URL" \
  --persona "$FIGMA_PERSONA" \
  --goal "Open the menu." \
  --output-dir "/tmp/ux_grounding/${RUN}" \
  --max-steps 10 \
  --timeout-seconds 180 \
  --run-id "$RUN"
```

### Scenario C — template

```bash
RUN=grounding-C-$(date +%Y%m%d-%H%M%S)
python3 scripts/ux_testing.py \
  --target figma \
  --url "$FIGMA_COMPOSITE_URL" \
  --persona "$FIGMA_PERSONA" \
  --goal "Tap the Continue button." \
  --output-dir "/tmp/ux_grounding/${RUN}" \
  --max-steps 10 \
  --timeout-seconds 180 \
  --run-id "$RUN"
```

### Scenario E — template (spot-check)

```bash
RUN=grounding-E-$(date +%Y%m%d-%H%M%S)
python3 scripts/ux_testing.py \
  --target web \
  --url "https://www.wikipedia.org" \
  --persona "$FIGMA_PERSONA" \
  --goal "Scroll down to find the language list; do not click unless necessary." \
  --output-dir "/tmp/ux_grounding/${RUN}" \
  --max-steps 8 \
  --timeout-seconds 180 \
  --run-id "$RUN"
```

---

## Evidence to review (each run)

| Artifact | What to check |
|---|---|
| `screenshots/step-*-hover.png` | Red marker **on** intended control before click (primary pass/fail) |
| `screenshots/step-*-hover-2.png` (+) | G2 adjustment pass — marker moved toward target |
| `action_trace.json` | `hover.alignment`, `hover.alignment_passes`, `target_kind`; norm `x`/`y` + `x_px`/`y_px` |
| `ux_result.json` | `terminal_state`; not spurious `blocked` |
| Recording | Optional — confirms click timing |

**Helper — list hover shots:**

```bash
ls -la /tmp/ux_grounding/<RUN>/screenshots/*hover*
```

---

## Result log (copy per formal test session)

### Scenario A — setup flow

| Run ID | `terminal_state` done? | Language step: **简体中文** hover OK? | Other clicks on stated target? | Notes |
|---|---|:---:|:---:|:---:|
| A-1 | | | | |
| A-2 | | | | |
| A-3 | | | | |

### Scenarios B / C / E

| Run ID | Scenario | Marker on target at final hover? (Y/N) | `alignment` / passes | Notes |
|---|---|:---:|:---:|---|
| B-1 | icon-only | | | |
| B-2 | | | | |
| B-3 | | | | |
| C-1 | composite | | | |
| C-2 | | | | |
| C-3 | | | | |
| E-1 | scroll/type | — | — | trace used scroll/type? |

---

## Pass / fail rules

| Rule | Threshold |
|---|---|
| **A — setup flow** | ≥ **2 / 3** runs: `terminal_state: done` (home / setup complete per VLM); on language step, Chinese persona clicks **简体中文** with marker on that row at final hover; other clicks land on controls named in step `reason` |
| **B — icon-only** | ≥ **2 / 3** runs: marker **inside** target icon bounds |
| **C — composite** | ≥ **2 / 3** runs: marker on **whole button** hit area |
| **E — non-click** | ≥ **1 / 1** spot-check: appropriate `scroll`/`type`; no spurious click-only path |
| **Regression guard** | `blocked` rate on A–C not materially worse than pre-UVG baseline (team judgment) |
| **UVG trace** | Click steps include `refine` block; alignment in hover, not observe `move_to` churn |

**If A–C fail after 3× each:** document failures in the log; implement **UVG** (L1 ROI refine + L2 convergence hover) per `docs/GROUNDING.md` before G4/L3 spatial model.

---

## Related

| File | Role |
|---|---|
| `docs/VERIFY.md` | Tier 0–1 commands + link here for Tier 2 |
| `docs/GROUNDING.md` | G1/G2 design and scenario definitions |
| `docs/TASKS.md` | Phase 5.5 exit criteria |
