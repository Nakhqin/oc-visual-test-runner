from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from adapters.browser import ObservationFrame
from core.actions import Action, ActionParseError, extract_json_object, parse_action_payload
from core.config import TargetConfig
from core.hover import validate_hover_action
from core.refine import (
    CropRegion,
    crop_norm_to_global_norm,
    parse_refine_payload,
)

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
ENV_GOOGLE_API_KEY = "GOOGLE_API_KEY"
ENV_GEMINI_MODEL = "GEMINI_MODEL"
ENV_GEMINI_REQUEST_TIMEOUT_SECONDS = "GEMINI_REQUEST_TIMEOUT_SECONDS"
DEFAULT_GEMINI_REQUEST_TIMEOUT_SECONDS = 90

ACTION_PROMPT = """You are simulating a human participant in a visual UX test.

Persona:
{persona}

Goal:
{goal}

Target type: {target}
Page URL: {page_url}
Step index: {step_index} (max steps for this run: {max_steps})

Previous steps:
{history}

Look at the screenshot and choose the single next action as a JSON object only.
The screenshot includes a red circular cursor marker showing the participant pointer.

- When you intend to click a target, use click with x,y — the runner will move there, show a hover screenshot with the red marker, and ask you to align the pointer before clicking.

Allowed action types:
- move_to (requires x, y)
- move_by_delta (requires delta_x, delta_y)
- click (requires x, y; optional target_kind — see click rules below)
- scroll (optional delta_y)
- wait (optional wait_ms)
- type (requires text)
- done (requires reason — task completed from persona perspective)
- blocked (requires reason — persona cannot proceed)

Rules:
- Respond with JSON only. No markdown unless wrapping a single JSON object.
- Include "reason" explaining why the persona would take this action or stop.
- Use normalized coordinates: x and y are integers from 0 to 1000 inclusive, relative to the screenshot viewport (0,0 = top-left; 1000,1000 = bottom-right).
- move_by_delta uses pixel offsets (delta_x, delta_y), not normalized values.
- Do not use click_current in this phase — the runner handles confirmation after hover.
- Do not assume DOM selectors or Figma node IDs.
- A failed or unproductive click is not automatically a UX issue.
- Prefer done or blocked when the goal is clearly achieved or impossible.
- Prefer scroll, type, or wait when that fits the goal — do not choose click when scrolling or typing is correct.
- Do not use move_to on observe to fine-tune an upcoming click — use click with your best center estimate; the runner applies ROI refine and hover alignment automatically.

When choosing click (coarse target selection):
- Aim at the center of the intended tappable control (text row, icon, icon+label button, or button chrome) — not card margin or gutter whitespace.
- Optional target_kind on click: "text" | "icon" | "composite" | "button" — describes the control type you are targeting.
- Text / list rows: center on the label or row hit area.
- Icon-only: name the icon in reason (e.g. "close X", "menu hamburger"); center on the icon graphic.
- Icon + label: center on the combined control, not only the text side.

Example:
{{"type": "click", "x": 500, "y": 350, "target_kind": "button", "reason": "The primary call-to-action looks tappable."}}
"""

HOVER_ACTION_PROMPT = """You are simulating a human participant in a visual UX test.

Persona:
{persona}

Goal:
{goal}

Target type: {target}
Page URL: {page_url}
Step index: {step_index} (max steps for this run: {max_steps})

Previous steps:
{history}

The participant moved the pointer to ({hover_x}, {hover_y}) intending to click there.
The screenshot shows the UI with a red circular cursor marker at the pointer position.

This is the **alignment phase**: align the red marker onto the intended tappable control, then click. Do not treat this as a weak confirm-only step.

Review the marker position and choose the single next action as JSON only.

Allowed action types:
- click_current (confirm click at the marked pointer position — only when marker is on target)
- move_to (requires x, y — move pointer onto the control center)
- move_by_delta (requires delta_x, delta_y — nudge pointer in pixels)
- wait (optional wait_ms — let UI finish loading or animating)
- done (requires reason — goal achieved from persona perspective)
- blocked (requires reason — persona cannot proceed)

Alignment rules (all control types — text, icon-only, icon+label, button):
- The red marker must overlap the intended **tappable control** before click_current.
- Do **not** use click_current if the marker is on blank whitespace, padding beside a list item, or a neighboring control.
- Text / list rows: if marker is beside a label, move_to the **label or row center**.
- Icon-only: move_to the **center of the icon graphic** (name the icon in reason); not adjacent padding or a neighboring icon.
- Icon + label: move_to the **center of the combined hit area**, not only the text side.
- Small icons: partial overlap with whitespace is not enough — center on the glyph.

Rules:
- Respond with JSON only. No markdown unless wrapping a single JSON object.
- Include "reason" referencing what you see at the pointer and whether the marker is on target.
- Coordinates (x, y) use the same 0–1000 normalized grid. move_by_delta uses pixel offsets.
- Do not use click with x,y here — use click_current only after alignment.
- Optional on click_current: alignment "aligned" | "adjusted" | "clicked_off_target" (use clicked_off_target only if you must click despite visible misalignment).
- Optional target_kind on adjustments: "text" | "icon" | "composite" | "button".
- A failed or unproductive click is not automatically a UX issue.

Examples:
{{"type": "move_to", "x": 520, "y": 360, "target_kind": "text", "reason": "Marker is left of the English row; moving onto the label center."}}
{{"type": "click_current", "alignment": "aligned", "reason": "Marker is on the Settings button; confirming click."}}
"""

REFINE_ACTION_PROMPT = """You are refining a click target on a cropped region of a UX test screenshot.

Persona:
{persona}

Goal:
{goal}

Target type: {target}
Step index: {step_index}

The full screenshot was cropped around a coarse click estimate. You see ONLY this crop.
Coordinates are normalized 0–1000 relative to **this crop image** (0,0 = top-left of crop; 1000,1000 = bottom-right of crop).

Coarse intent from the previous step:
- target_kind: {target_kind}
- reason: {coarse_reason}

Point at the **center** of the intended tappable control (text, icon, icon+label, or button) visible in this crop.

Respond with JSON only:
{{"x": <int 0-1000>, "y": <int 0-1000>, "reason": "<why this point is the control center>"}}

Rules:
- x and y must be integers from 0 to 1000 inclusive.
- If the control is not visible in this crop, still return your best point toward it and explain in reason.
- Do not output markdown.
"""

PERSONA_REPORT_SYNTHESIS_PROMPT = """You are writing a first-person UX test experience report as the participant persona below.

Persona:
{persona}

Goal:
{goal}

Terminal state: {terminal_state}

Rewrite the draft report into a cohesive first-person narrative in Markdown.

Rules:
- Stay in first person as the persona throughout the main sections.
- Do not invent steps, clicks, or outcomes that are not supported by the draft.
- Do not classify click verification telemetry as confirmed UX defects.
- Keep the sections "给审查者的证据" and "审查者备注" (reviewer-facing). You may lightly tidy them but do not remove evidence paths.
- Preserve factual paths, step references, and reviewer telemetry.
- Target length: about 300-600 words for the narrative sections; the journey may be longer.
- Output Markdown only. No JSON.

Draft report:
{draft}
"""


class VlmDecisionError(RuntimeError):
    """Raised when the VLM client cannot produce a decision."""


def _format_history(history: list[dict[str, Any]]) -> str:
    if not history:
        return "(none — first step)"
    lines: list[str] = []
    for entry in history:
        action = entry.get("action", {})
        lines.append(
            f"- step {entry.get('step')}: {action.get('type')} — {action.get('reason', '')}"
        )
    return "\n".join(lines)


def build_vlm_prompt(
    config: TargetConfig,
    frame: ObservationFrame,
    step_index: int,
    history: list[dict[str, Any]],
) -> str:
    return ACTION_PROMPT.format(
        persona=config.persona,
        goal=config.goal,
        target=config.target,
        page_url=frame.url,
        step_index=step_index,
        max_steps=config.max_steps,
        history=_format_history(history),
    )


def build_hover_vlm_prompt(
    config: TargetConfig,
    frame: ObservationFrame,
    step_index: int,
    history: list[dict[str, Any]],
    *,
    hover_x: int,
    hover_y: int,
) -> str:
    return HOVER_ACTION_PROMPT.format(
        persona=config.persona,
        goal=config.goal,
        target=config.target,
        page_url=frame.url,
        step_index=step_index,
        max_steps=config.max_steps,
        history=_format_history(history),
        hover_x=hover_x,
        hover_y=hover_y,
    )


def build_refine_vlm_prompt(
    config: TargetConfig,
    coarse: Action,
    step_index: int,
) -> str:
    return REFINE_ACTION_PROMPT.format(
        persona=config.persona,
        goal=config.goal,
        target=config.target,
        step_index=step_index,
        target_kind=coarse.target_kind or "(not specified)",
        coarse_reason=coarse.reason or "(no reason recorded)",
    )


def parse_vlm_response(text: str) -> Action:
    payload = extract_json_object(text)
    return parse_action_payload(payload)


def parse_hover_vlm_response(text: str) -> Action:
    action = parse_vlm_response(text)
    try:
        validate_hover_action(action)
    except ValueError as exc:
        raise ActionParseError(str(exc)) from exc
    return action


def gemini_request_timeout_seconds() -> int:
    raw = os.environ.get(ENV_GEMINI_REQUEST_TIMEOUT_SECONDS, "").strip()
    if not raw:
        return DEFAULT_GEMINI_REQUEST_TIMEOUT_SECONDS
    try:
        return max(int(raw), 1)
    except ValueError:
        return DEFAULT_GEMINI_REQUEST_TIMEOUT_SECONDS


class GeminiDecisionMaker:
    """Gemini VLM decision maker for the visual agent loop."""

    source = "gemini"

    def __init__(
        self,
        *,
        api_key: str,
        model_name: str = DEFAULT_GEMINI_MODEL,
        request_timeout_seconds: int | None = None,
    ) -> None:
        self._api_key = api_key
        self._model_name = model_name
        self._request_timeout_seconds = (
            request_timeout_seconds
            if request_timeout_seconds is not None
            else gemini_request_timeout_seconds()
        )
        self._history: list[dict[str, Any]] = []

    def decide(
        self,
        config: TargetConfig,
        frame: ObservationFrame,
        step_index: int,
        *,
        phase: str = "observe",
        pending_action: Action | None = None,
    ) -> Action:
        if phase == "hover":
            if pending_action is None or pending_action.x is None or pending_action.y is None:
                return Action(
                    type="blocked",
                    reason="VLM hover decision missing pending click coordinates",
                )
            prompt = build_hover_vlm_prompt(
                config,
                frame,
                step_index,
                self._history,
                hover_x=pending_action.x,
                hover_y=pending_action.y,
            )
            parse_response = parse_hover_vlm_response
        else:
            prompt = build_vlm_prompt(config, frame, step_index, self._history)
            parse_response = parse_vlm_response

        try:
            response_text = self._generate(prompt, frame)
            action = parse_response(response_text)
        except (ActionParseError, VlmDecisionError) as exc:
            return Action(
                type="blocked",
                reason=f"VLM decision failed: {exc}",
            )
        except Exception as exc:
            return Action(
                type="blocked",
                reason=f"VLM request failed: {exc}",
            )

        history_label = f"{step_index}:hover" if phase == "hover" else step_index
        self._history.append(
            {
                "step": history_label,
                "action": action.to_dict(),
            }
        )
        return action

    def refine_click_coordinates(
        self,
        config: TargetConfig,
        frame: ObservationFrame,
        coarse: Action,
        step_index: int,
        *,
        crop_image_path: Path,
        crop_region: CropRegion,
    ) -> Action:
        _ = frame
        if coarse.x is None or coarse.y is None:
            return coarse

        prompt = build_refine_vlm_prompt(config, coarse, step_index)
        try:
            response_text = self._generate_from_path(prompt, crop_image_path)
            payload = extract_json_object(response_text)
            local_x, local_y, reason = parse_refine_payload(payload)
            global_x, global_y = crop_norm_to_global_norm(
                local_x,
                local_y,
                crop_region,
                frame.viewport_width,
                frame.viewport_height,
            )
        except (ActionParseError, VlmDecisionError) as exc:
            return Action(
                type="click",
                x=coarse.x,
                y=coarse.y,
                reason=f"refine fallback: {exc}",
                target_kind=coarse.target_kind,
            )
        except Exception as exc:
            return Action(
                type="click",
                x=coarse.x,
                y=coarse.y,
                reason=f"refine fallback: {exc}",
                target_kind=coarse.target_kind,
            )

        return Action(
            type="click",
            x=global_x,
            y=global_y,
            reason=reason or coarse.reason,
            target_kind=coarse.target_kind,
        )

    def _generate(self, prompt: str, frame: ObservationFrame) -> str:
        return self._generate_from_path(prompt, frame.image_path)

    def _generate_from_path(self, prompt: str, image_path: Path) -> str:
        return self._generate_from_bytes(prompt, image_path.read_bytes())

    def _generate_from_bytes(self, prompt: str, image_bytes: bytes) -> str:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise VlmDecisionError(
                "google-genai is not installed. Run: pip install -r requirements.txt"
            ) from exc

        timeout_ms = max(self._request_timeout_seconds, 1) * 1000
        client = genai.Client(
            api_key=self._api_key,
            http_options=types.HttpOptions(timeout=timeout_ms),
        )

        try:
            response = client.models.generate_content(
                model=self._model_name,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                ],
            )
        except Exception as exc:
            raise VlmDecisionError(str(exc)) from exc

        text = getattr(response, "text", None)
        if not text or not text.strip():
            raise VlmDecisionError("empty response from Gemini")
        return text


def synthesize_persona_report_with_gemini(
    *,
    draft: str,
    config: TargetConfig,
    terminal_state: str,
    api_key: str,
    model_name: str = DEFAULT_GEMINI_MODEL,
    request_timeout_seconds: int | None = None,
) -> str:
    """Optional Phase 3 Gemini polish for persona_report.md."""
    prompt = PERSONA_REPORT_SYNTHESIS_PROMPT.format(
        persona=config.persona,
        goal=config.goal,
        terminal_state=terminal_state,
        draft=draft,
    )
    timeout = (
        request_timeout_seconds
        if request_timeout_seconds is not None
        else gemini_request_timeout_seconds()
    )
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise VlmDecisionError(
            "google-genai is not installed. Run: pip install -r requirements.txt"
        ) from exc

    timeout_ms = max(timeout, 1) * 1000
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=timeout_ms),
    )
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt],
        )
    except Exception as exc:
        raise VlmDecisionError(str(exc)) from exc

    text = getattr(response, "text", None)
    if not text or not text.strip():
        raise VlmDecisionError("empty persona report synthesis from Gemini")
    return text.strip() + "\n"
