# Visual Click Grounding — Structural Improvement Plan

**Status:** **G1 + G2 + UVG L1/L2 implemented (2026-07-08)**; Tier 2 re-validation pending.  
**Triggers:** Figma E2E showed VLM coordinates landing off-target (e.g. red marker left of list item text while intending to click **English**). Runner execution matches coordinates; failure is **visual grounding**, not coordinate-space mismatch from Figma scaling.

**Relationship to phases:** Phase 5 (OpenClaw/Feishu delivery) may complete on current grounding. **Phase 5.5** implements this plan. Phase 6+ (Android/Windows design) unchanged.

---

## Problem statement

### Confirmed behavior (current architecture)

```text
observe screenshot (1280×900 viewport)
  → VLM returns action JSON (e.g. click x,y in pixel space)
  → move_to(x,y) → hover screenshot (red marker at x,y)
  → VLM hover phase (e.g. click_current)
  → Playwright mouse.click at viewport pixels
```

Screenshot pixels and click pixels use the **same viewport coordinate system**. Figma prototype letterboxing/scaling appears **inside** the screenshot; it does not create a separate mapping layer.

### Confirmed failure mode

- VLM **mis-estimates** target position in the image (marker not on control).
- Hover phase may **`click_current`** at a visibly wrong marker instead of **`move_to`** to refine.
- Result: runner is faithful; **grounding quality** is the bottleneck.

### Not the primary cause

- Figma URL `scaling=` parameters causing runner coordinate transform errors.
- Playwright viewport vs screenshot size mismatch (both 1280×900 by default).

---

## Design principles (unchanged)

| Principle | Notes |
|---|---|
| Visual-first | No Figma API node IDs, no CSS-selector-first automation |
| Same frame | Observation image and click coordinates refer to one viewport |
| Hover is structural | Phase 1.5 hover loop stays; role evolves (see G2) |
| Traceability | `action_trace.json` records coordinates, hover, verification |
| Failed clicks ≠ UX defects | Grounding telemetry ≠ product UX classification |

---

## Universal Visual Grounding (UVG) — target architecture

**Goal:** A **single, control-agnostic** pointing pipeline for every coordinate `click` — text, icon, icon+label, button — without per-UI hacks (no row indices, no Figma node IDs).

**What “solved” means (honest scope):**

| In scope | Out of scope |
|---|---|
| Same runner path for all point-click targets | 100% success on every arbitrary UI |
| Converge or **`blocked`** — no off-target `click_current`, no `max_steps` wasted on observe `move_to` loops | One-shot Gemini `(x,y)` always correct |
| Tier 2 regression A–C each ≥2/3 final-hover on target | DOM-selector-first or Figma API primary path |

**Root cause (generic):** A single full-viewport VLM estimate of `(x_norm, y_norm)` has high variance when targets are small or surrounded by whitespace (common in Figma protos and web). **G1** fixes number format; **G2** blocks blind clicks — neither removes estimation variance.

### UVG stack (mandatory for point-click path)

```text
Observe
  → semantic target + coarse (x₀, y₀)     # which control; may be imprecise
        ↓
L1  ROI refine (universal G3 — mandatory)
  → crop fixed viewport fraction centered on (x₀, y₀)
  → second VLM call: norm within crop only → map to global (x₁, y₁)
        ↓
L2  Convergence alignment (G2 upgraded)
  → move_to(x₁, y₁)
  → repeat up to N_hover (does NOT consume observe max_steps):
        hover screenshot → VLM: on-target? click_current : move_to / move_by_delta / wait
  → if exhausted without aligned → blocked (Interaction limitation) or explicit unresolved trace
        ↓
L3  Optional spatial model (G4 — only if L1+L2 below bar after measurement)
  → bbox → center → re-enter L2
        ↓
click_current → execute
```

| Layer | Replaces / extends | Applies to |
|---|---|---|
| **G1** (done) | Pixel I/O | All `move_to` / `click` coords — foundation |
| **L1 — ROI refine** | G3 “optional if needed” | **Every** `click` with coordinates |
| **L2 — Convergence hover** | G2 single-pass / observe `move_to` churn | **Every** `click` path; budget separate from `max_steps` |
| **L3 — Spatial model** | G4 deferred | Fallback when telemetry shows L1+L2 insufficient |

**`target_kind`** (`text` | `icon` | `composite` | `button`) affects **prompt wording only** — not runner branches.

### Why norm coordinates still fail (FAQ)

| Myth | Fact |
|---|---|
| “0–1000 should be more accurate than pixels” | Same visual estimation task; format alone does not shrink error |
| “Hover move_to fixes it” | Correction coords are the **same model**; without L1 ROI, errors often shift (e.g. below → left) not vanish |
| “Figma scaling breaks runner coords” | Screenshot and click share one viewport; failure is **VLM geometry**, not adapter mapping |

Confirmed from scenario A run `grounding-A-test-1`: G2 refused off-target `click_current` but observe/hover coords remained wrong; run ended `max_steps` after many observe-only `move_to` steps.

### L1 — ROI refine (universal G3)

**Goal:** Reduce effective search area so the same norm grid is finer **relative to the target**.

| Parameter | Default (implement at 5.5b) |
|---|---|
| Crop size | ~25% × 25% of viewport (e.g. 320×225 @ 1280×900), min 240×240 |
| Center | `(x₀, y₀)` from observe after pixel mapping |
| Second VLM | Norm 0–1000 **within crop**; map back to global norm/px |
| Trace | `refine.crop`, `refine.coarse`, `refine.fine`, optional crop PNG |

**When coarse point is far off:** crop may miss target → L2 may still fail → `blocked` (acceptable; no silent mis-click).

**Not list-specific:** same crop for icons, buttons, and text rows.

### L2 — Convergence alignment (G2 upgrade)

**Goal:** Closed-loop visual servo until aligned or give up — **inside hover sub-loop**, not across observe steps.

| Current G2 gap | UVG L2 fix |
|---|---|
| Hover `move_to` then next **observe** step burns `max_steps` | All adjust passes stay in **one** click intent; hover budget `N_hover` (e.g. 5) |
| Single model re-estimate without smaller ROI | Preceded by **L1** on every click |
| `click_current` when “close” | Require `alignment: aligned` (or adjusted after L1) before click |

**Convergence exit:**

- **Success:** `click_current` with marker on target (human review + optional VLM `alignment`)
- **Failure:** `blocked` with reason after `N_hover` — **not** 6+ observe `move_to` steps

### L3 — Dedicated spatial model (G4)

Evaluate only after L1+L2 measured on Tier 2 regression. Universal **bbox** output → center → L2. Requires DECISIONS on dependency, cost, latency.

---

## Improvement tracks (history + UVG mapping)

### G1 — Normalized coordinate protocol (priority 1)

**Goal:** Replace raw viewport pixels in VLM I/O with a stable normalized grid; runner maps to pixels at execution boundary.

**Proposal:**

| Layer | Format |
|---|---|
| VLM output (observe) | `x_norm`, `y_norm` in **0–1000** (integers), or single JSON fields `x`,`y` documented as 0–1000 |
| Runner internal | `x_px = round(x_norm / 1000 * (viewport_width - 1))` (document exact formula in DECISIONS at implementation) |
| Trace / reports | Store **both** normalized and pixel values for audit |
| Backward compatibility | One release: breaking change to action JSON in trace with `schema_version` bump, or dual-read during transition |

**Why:**

- Resolves PRD open question (normalized vs pixel).
- Model vendors often perform better on bounded integer grids than absolute pixels.
- Keeps universal loop; only changes action protocol + mapping helper.

**Non-goals (G1):** Changing viewport size logic; adding new dependencies.

**Exit criteria:**

- [x] VLM prompts require 0–1000 coordinates only.
- [x] `parse_action_payload` / executor use shared `norm_to_pixel()` helper (`scripts/core/coordinates.py`).
- [x] Unit tests: corners, center, round-trip (`.tmp/test_coordinates.py`).
- [ ] Tier 2 regression A–C (UVG complete): see exit criteria below.

**Status:** Foundation for UVG L2 — **superseded by UVG L2 convergence requirements** (see above).

### G2 — Hover as alignment phase (priority 2)

**Goal:** Redefine hover from “confirm click” to **“align pointer on the interactive target, then click.”**

Alignment applies to **any tappable control** — not text-only:

| Target type | Examples | Alignment aim |
|---|---|---|
| Text / list row | Language list item, menu label | Marker on **text block** or row hit area center |
| Icon-only | Close (×), back arrow, hamburger, settings gear | Marker on **icon graphic center** (inside visible icon bounds) |
| Icon + label | Primary button with leading icon | Marker on **whole control center** — not biased to text-only side |
| Chrome / button | Filled or outlined button without separate icon | Marker on **button interior center**, not outer margin |

**Unified rule:** G2 aligns to the **interactive hit target**, not “must have visible text.”

**Proposal:**

| Phase | Responsibility |
|---|---|
| Observe | Coarse target selection — identify **which control** (text row, icon, or composite); coordinates may be imprecise |
| Hover | **Alignment** — if red marker is not on the intended control, must `move_to` / `move_by_delta`; **forbid** `click_current` when marker is clearly off target |
| Execute | `click_current` only after alignment pass |

**Prompt rules (conceptual):**

- **All targets:** “The red marker must overlap the intended **tappable control** (text, icon, or button) before `click_current`.”
- **Text / list rows:** “If marker is on whitespace beside a list item, adjust toward the **label or row center**.”
- **Icon-only:** “Name the icon in `reason` (e.g. ‘close X’, ‘menu hamburger’). Aim at the **center of the icon graphic**, not adjacent padding or a neighboring icon.”
- **Icon + label:** “Treat icon and label as one control; aim at the **center of the combined hit area**, not only the text side.”
- **Small targets:** “For small icons, fine-tune toward the **visual center** of the glyph; partial overlap with whitespace is not enough.”
- **Observe:** “Prefer coordinates at the **center of the control** (text block, icon, or button interior), not card margin or gutter.”

**Trace additions (optional):**

- `hover.alignment`: `aligned` | `adjusted` | `clicked_off_target` (runner or post-hoc tag from VLM reason)
- `hover.target_kind`: `text` | `icon` | `composite` | `button` (optional; from VLM `reason` for regression review)

**Exit criteria:**

- [x] Updated `HOVER_ACTION_PROMPT` and observe prompt in `vlm.py` (text + icon + composite rules).
- [x] Hover sub-loop: up to 3 alignment passes with per-pass screenshots and trace metadata.
- [ ] **Scenario A (setup flow):** Figma tablet setup — Chinese persona reaches home (`done`) in ≥2/3 runs; language step marker on **简体中文** when that row is clicked.
- [ ] **Scenario B (icon-only):** Proto with a distinct icon target (e.g. close, menu) — marker **inside icon bounds** in ≥2/3 runs.
- [ ] **Scenario C (icon+label):** Proto with icon+text button — marker on **whole control** in ≥2/3 runs.
- [ ] Tier 2 regression A–C: ≥2/3 final-hover on target (**insufficient with G2 alone** — see `grounding-A-test-1`).

**Status:** Partial — prompts + sub-loop shipped; **not sufficient alone**. Absorbed into **UVG L2**.

---

#### G2 scope — what it binds to (and what it does not)

G2 is **not** a global interaction policy. It applies only when the runner enters the **point-click hover path**:

```text
observe → action type "click" with coordinates
  → move_to → hover screenshot → hover-phase VLM → click_current (or adjust)
```

Confirmed trigger (implementation): `scripts/core/hover.py` — `action_triggers_hover` is true only for `click` with `x` and `y`.

| Action / path | G2 alignment applies? | Notes |
|---|---|---|
| `click` (with coordinates) | **Yes** | Primary G2 target |
| `click_current` | **Yes** (hover phase only) | After alignment |
| `scroll` | **No** | Observe may return directly; no hover loop |
| `type` | **No** | May follow a separate `click` to focus input (that click uses G2) |
| `wait` | **No** | Timing / loading |
| `move_to` / `move_by_delta` (observe) | **No** | Coarse reposition without click intent |
| `done` / `blocked` | **No** | Terminal |

**Implication:** G2 does **not** restrict which UI patterns are testable. It only improves **coordinate accuracy for point clicks**. Scroll, typing, and multi-step sequences remain valid without G2 prompts.

The text / icon / button table above describes **visual anchor types when aligning a click** — not an allowlist of testable UI.

#### Special interactions — how to handle without breaking G2

Limitations on exotic interactions come from the **current action vocabulary** (`SKILL.md` / `scripts/core/actions.py`), not from G2:

| Interaction | Current support | Recommended handling |
|---|---|---|
| Scroll to reveal | `scroll` | Observe returns `scroll`; **do not** force click alignment |
| Text entry | `type` (+ optional `click` to focus) | G2 only on focus `click` if used |
| Dropdown: open then pick | `click` × 2 | Each `click` may use G2 independently |
| Hover-reveal menu (no click yet) | `move_to` only | No G2; future optional `hover_hold` action if needed |
| Drag / slider | **Not in protocol** | Extend with `drag` (or equivalent) in a **separate milestone**; optional G2 on **start point only** |
| Long press / double click / right click | **Not in protocol** | New action + adapter; point actions may reuse G2 |
| Mobile swipe / gesture | **Future** (Android adapter) | Out of Phase 5.5 scope |

**Implementation rules (G2 prompts):**

1. **Conditional prompts** — G2 alignment rules appear in **hover-phase** (and observe **when choosing `click`**) only; scroll/type/wait prompts must not require `click_current`.
2. **Intent in `reason`** (optional trace field) — e.g. `point_click`, `scroll`, `type`, `drag` — helps regression review; runner routes by `action.type`, not by intent alone.
3. **Unsupported interaction** — return `blocked` with classification **Interaction limitation** per `SKILL.md`; do not fake a `click` when the persona needs drag/swipe/long-press.

**Protocol extensions (post–5.5, if needed):** New actions (`drag`, `long_press`, …) are additive DECISIONS + adapter work. G2 attaches **only where a coordinate endpoint must be visually grounded** — not to every new gesture.

**VERIFY split:**

- **G2 regression set** — scenarios A–C (point-click alignment).
- **Non-G2 regression** — scenario E (scroll/type flows without spurious clicks).
- **Unsupported interactions** — documented backlog; not G2 exit criteria.

---

### G3 / L1 — ROI refine (universal — **mandatory in UVG**)

**Goal:** Same as **UVG L1** above. After observe coarse `(x₀, y₀)`, crop a viewport region centered on the point; second VLM call returns norm **within crop**; map back to global norm/px.

**Status:** **Not optional** under UVG — runs on **every** coordinate `click`, not only list rows or failed runs.

| Parameter | Default (implement at 5.5b) |
|---|---|
| Crop size | ~25% viewport (min 240×240 px) |
| VLM | Norm 0–1000 in crop space |
| Trace | `refine` block on click steps |

**Risks:** Extra latency/cost; crop misses if coarse point very far off → prefer `blocked` over mis-click.

**Exit criteria:** Tier 2 A–C improve vs G1+G2-only baseline; trace includes `refine` on click steps.

---

### G4 / L3 — Dedicated spatial model (deferred)

**Goal:** Same as **UVG L3**. Bbox or dedicated pointing API → center → re-enter L2.

**When:** Only after **L1+L2** measured on Tier 2 regression. Requires DECISIONS on dependency and cost.

---

## Explicit non-goals

- Figma REST API / node resolver as primary click path
- DOM-selector-first automation
- Rewriting browser adapter click mechanism (Playwright `mouse.click` stays)
- Automatic “failed click = UX bug” classification
- **G2 as universal interaction handler** — drag, swipe, long-press, and other gestures require protocol/adapter extensions (see G2 scope)

- **Per-UI coordinate hacks** (e.g. list `row_index` only) — use UVG layers instead
- **Prompt-only “complete fix”** — insufficient without L1+L2 structure

---

## Implementation order

```text
Done:
  G1 — normalized protocol + mapping + tests
  G2 — alignment prompts + hover sub-loop (partial)

Phase 5.5b — UVG (current):
  1. L2' — convergence hover (hover budget; no observe move_to churn; blocked on exhaust)
  2. L1 — mandatory ROI refine on every click path
  3. Tier 2 formal regression (`docs/fixtures/GROUNDING_REGRESSION.md`) — sign-off gate
  4. L3 — spatial model only if L1+L2 below bar

Parallel:
  Phase 5.3 Feishu E2E (may proceed; click quality follows UVG)
```

Phase 5.2/5.3 OpenClaw wiring **may proceed in parallel** with UVG; Feishu E2E quality follows UVG sign-off.

### UVG sign-off (replaces G2-only exit)

| Criterion | Threshold |
|---|---|
| Tier 2 scenarios A, B, C | Each ≥ **2/3** runs: **final** hover frame marker on target hit area |
| Off-target click | No `click_current` when marker clearly off target in final hover |
| `max_steps` churn | No long observe-only `move_to` sequences when a single click intent should converge in hover |
| Scenario E spot-check | `scroll`/`type` paths unaffected |
| `blocked` rate | Not materially worse than pre-UVG baseline (team judgment) |

---

## Verification (planned — `docs/VERIFY.md` Phase 5.5)

**Formal acceptance:** **`docs/fixtures/GROUNDING_REGRESSION.md`** (Tier 2 — Gemini E2E, 3× per scenario). Stub smoke alone is **not** sufficient.

### Regression scenario A — Tablet setup flow (Figma)

- **Proto:** First-time tablet setup (welcome → language list → … → home). Entry URL may start before the language screen.
- **Persona:** Cautious first-time **Chinese** tablet user (reads Chinese; expects Chinese UI).
- **Goal:** “Complete the first-time tablet setup and reach the home screen.” (per `docs/PRD.md` — **not** a micro-goal like “Select English.”)
- **Pass:** `terminal_state: done`; on language step, persona reasonably selects **简体中文** with hover marker on that row; other clicks land on controls named in step `reason`.

### Regression scenario B — Icon-only

- **Proto:** Screen with a distinct icon-only control (e.g. close ×, back arrow, menu hamburger). Figma proto preferred; **web** nav with icon buttons is acceptable if no Figma fixture.
- **Goal:** Persona goal names the icon (e.g. “Open the menu”, “Close this panel”).
- **Pass:** Hover marker **inside the target icon’s visible bounds** (not on adjacent padding or neighboring icon); execution success or expected navigation.

### Regression scenario C — Icon + label (composite control)

- **Proto:** Primary or secondary button with **leading/trailing icon + text** (Figma or web).
- **Goal:** Tap that specific button (e.g. “Continue”, “Settings”).
- **Pass:** Hover marker on the **combined control hit area** (center of button, not text-only side).

### Regression scenario D — Web (sanity)

- **URL:** `https://example.com` or known link/button page.
- **Pass:** Click coordinates land on visible link/control per screenshot review.

### Regression scenario E — Non–point-click (G2 out of scope)

- **Proto:** Page requiring **scroll** and/or **`type`** without a mis-click (e.g. long page with form below fold).
- **Goal:** Scroll to section, optionally focus field and type.
- **Pass:** Trace shows `scroll` / `type` where appropriate; **no** forced `click` when scroll/type is correct; G2 hover loop only appears when a coordinate `click` is chosen.

### Metrics (manual MVP)

| Metric | How |
|---|---|
| Marker on target at hover | Human review of `step-*-hover.png`; check text row, icon bounds, or composite button as applicable |
| Target kind (optional) | VLM `reason` / trace `hover.target_kind` for regression tagging |
| Click execution success | `execution.success` in trace |
| Visible change | Phase 2 verification outcome (telemetry only) |

---

## Files expected to change (implementation)

| Area | Files (planned for UVG) |
|---|---|
| ROI refine (L1) | `scripts/core/refine.py` (or `crop_grounding.py`), `scripts/core/loop.py`, `scripts/core/vlm.py` |
| Convergence hover (L2') | `scripts/core/loop.py`, `scripts/core/hover.py` |
| Coordinate mapping (G1) | `scripts/core/coordinates.py`, `scripts/core/executor.py` |
| Trace schema | `scripts/core/writers.py`, `schema_version` bump if needed |
| Tests | `.tmp/test_coordinates.py`, `.tmp/test_refine.py`, fixture PNG checks |
| Docs | `SKILL.md`, `docs/VERIFY.md`, `docs/fixtures/GROUNDING_REGRESSION.md` |

---

## Related documents

| Document | Role |
|---|---|
| `docs/DECISIONS.md` | Accepted grounding direction (Phase 5.5) |
| `docs/TASKS.md` | Phase 5.5 task breakdown |
| `docs/PRD.md` | Open question resolution for coordinates |
| `docs/ARCHITECTURE.md` | Observe → align → act flow update |
