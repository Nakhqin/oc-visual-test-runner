# Decisions

Record meaningful product and engineering decisions here.

---

### 2026-06-24 — Adopt universal visual agent runner architecture

**Status:** Accepted

**Context:**
The project needs one orchestration model that works across Figma prototypes, websites, and future platforms.

**Decision:**
Organize the runner around a **universal visual agent loop**: target config → platform adapter → observation frame → VLM action decision → action execution → feedback observation → trace/result output.

**Reasoning:**
Single loop reduces duplication; new targets add adapters, not new runners.

**Consequences:**
- CLI entry at `scripts/ux_testing.py` orchestrates the loop (Phase 1).
- Android/Windows plug in as future adapters.

---

### 2026-06-24 — Use shared browser adapter for figma and web

**Status:** Accepted

**Context:**
Phase 1 targets are Figma prototype URLs and web URLs. Both render in a browser surface.

**Decision:**
Implement one **browser platform adapter** serving both `figma` and `web` targets. Target type affects navigation/wait behavior only.

**Reasoning:**
Avoids duplicate automation stacks; Figma prototypes are exercised as browser pages.

**Consequences:**
- No separate Figma runner vs web runner in Phase 1.
- Figma-specific quirks handled in adapter config, not a second codebase path.

---

### 2026-06-24 — Treat Android and Windows as future adapters

**Status:** Accepted

**Context:**
Mobile and desktop native surfaces require different capture and input mechanisms.

**Decision:**
Document `android` and `windows` as **planned future adapter targets**. Design in Phase 5; implementation exploration in Phase 6. Do not implement in Phase 0–1.

**Reasoning:**
Keeps Phase 1 focused on browser-based validation of the visual agent loop.

**Consequences:**
SKILL.md and docs list android/windows as planned only.
Phase 5 produces design docs; Phase 6 produces spikes.

---

### 2026-06-24 — Use low-frequency observation frames before full real-time streaming

**Status:** Accepted

**Context:**
Continuous video streaming to the VLM would increase cost and complexity.

**Decision:**
Capture **observation frames at loop cadence** (screenshot per step) before investing in full real-time streaming.

**Reasoning:**
Sufficient for persona walkthroughs in Phase 1; simpler to implement and debug.

**Consequences:**
Transient UI feedback may be missed until Phase 1.5 hover loop or higher capture rates.
Screen recording (`ux_test_recording.webm`) provides human review, not per-frame VLM input initially.

---

### 2026-06-24 — Require cursor marker and hover observation in Phase 1.5

**Status:** Accepted

**Context:**
Coordinate-only clicks without visible cursor feedback reduce VLM spatial reasoning quality.

**Decision:**
Phase 1.5 adds a **cursor marker overlay** and **hover-before-click observation** in the agent loop.

**Reasoning:**
Improves persona simulation fidelity and action explainability.

**Consequences:**
Phase 1 may ship without hover loop; Phase 1.5 is a required follow-up, not optional polish.
Trace should record hover/marker steps when enabled.

---

### 2026-06-24 — Failed clicks must not automatically be classified as UX issues

**Status:** Accepted

**Context:**
Click failures may stem from prototype limits, automation limits, wrong targets, or no visible response—not necessarily bad UX.

**Decision:**
Failed clicks are **runner telemetry**. UX findings require explicit persona reasoning or verified criteria—never automatic promotion from click failure alone.

**Reasoning:**
Separates automation reliability from product UX quality.

**Consequences:**
Classification schema uses distinct categories (UX issue, prototype limitation, automation limitation, etc.) per `SKILL.md`.
Phase 2 verification informs but does not auto-tag UX defects.

---

## Decision Template

### YYYY-MM-DD — Decision Title

**Status:** Proposed / Accepted / Rejected / Superseded

**Context:**
...

**Decision:**
...

**Reasoning:**
...

**Consequences:**
...

---
