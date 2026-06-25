from __future__ import annotations

import os
from typing import Any

from adapters.browser import ObservationFrame
from core.actions import Action, ActionParseError, extract_json_object, parse_action_payload
from core.config import TargetConfig

DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
ENV_GOOGLE_API_KEY = "GOOGLE_API_KEY"
ENV_GEMINI_MODEL = "GEMINI_MODEL"

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


def parse_vlm_response(text: str) -> Action:
    payload = extract_json_object(text)
    return parse_action_payload(payload)


class GeminiDecisionMaker:
    """Gemini VLM decision maker for the visual agent loop."""

    source = "gemini"

    def __init__(self, *, api_key: str, model_name: str = DEFAULT_GEMINI_MODEL) -> None:
        self._api_key = api_key
        self._model_name = model_name
        self._history: list[dict[str, Any]] = []

    def decide(
        self,
        config: TargetConfig,
        frame: ObservationFrame,
        step_index: int,
    ) -> Action:
        prompt = build_vlm_prompt(config, frame, step_index, self._history)
        try:
            response_text = self._generate(prompt, frame)
            action = parse_vlm_response(response_text)
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

        self._history.append(
            {
                "step": step_index,
                "action": action.to_dict(),
            }
        )
        return action

    def _generate(self, prompt: str, frame: ObservationFrame) -> str:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise VlmDecisionError(
                "google-generativeai is not installed. Run: pip install -r requirements.txt"
            ) from exc

        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(self._model_name)
        image_bytes = frame.image_path.read_bytes()

        try:
            response = model.generate_content(
                [
                    prompt,
                    {"mime_type": "image/png", "data": image_bytes},
                ]
            )
        except Exception as exc:
            raise VlmDecisionError(str(exc)) from exc

        text = getattr(response, "text", None)
        if not text or not text.strip():
            raise VlmDecisionError("empty response from Gemini")
        return text
