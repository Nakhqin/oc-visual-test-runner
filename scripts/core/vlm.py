from __future__ import annotations

import os
from typing import Any

from adapters.browser import ObservationFrame
from core.actions import Action, ActionParseError, extract_json_object, parse_action_payload
from core.config import TargetConfig
from core.hover import validate_hover_action

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

- When you intend to click a target, use click with x,y — the runner will move there, capture hover feedback, and ask you to confirm before clicking.

Allowed action types:
- move_to (requires x, y)
- move_by_delta (requires delta_x, delta_y)
- click (requires x, y)
- click_current
- scroll (optional delta_y)
- wait (optional wait_ms)
- type (requires text)
- done (requires reason — task completed from persona perspective)
- blocked (requires reason — persona cannot proceed)

Rules:
- Respond with JSON only. No markdown unless wrapping a single JSON object.
- Include "reason" explaining why the persona would take this action or stop.
- Use pixel coordinates relative to the screenshot viewport.
- Do not assume DOM selectors or Figma node IDs.
- A failed or unproductive click is not automatically a UX issue.
- Prefer done or blocked when the goal is clearly achieved or impossible.

Example:
{{"type": "click", "x": 420, "y": 180, "reason": "The primary call-to-action looks tappable."}}
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

Review hover / visual feedback at the pointer and choose the single next action as JSON only.

Allowed action types:
- click_current (confirm click at the marked pointer position)
- move_to (requires x, y — adjust pointer before clicking)
- move_by_delta (requires delta_x, delta_y — nudge pointer)
- wait (optional wait_ms — let UI finish loading or animating)
- done (requires reason — goal achieved from persona perspective)
- blocked (requires reason — persona cannot proceed)

Rules:
- Respond with JSON only. No markdown unless wrapping a single JSON object.
- Include "reason" referencing what you see at the pointer (tooltip, hover state, ambiguity).
- Do not use click with x,y here — use click_current to confirm the marked position.
- A failed or unproductive click is not automatically a UX issue.

Example:
{{"type": "click_current", "reason": "The button shows a hover state; confirming click."}}
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

    def _generate(self, prompt: str, frame: ObservationFrame) -> str:
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
        image_bytes = frame.image_path.read_bytes()

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
