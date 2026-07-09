"""Unit tests for G2 hover alignment helpers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from core.actions import Action, ActionParseError, parse_action_payload
from core.hover import (
    derive_hover_alignment,
    hover_adjustment_stalled,
    coerce_hover_to_click,
    should_force_hover_click,
)


def test_derive_aligned_first_pass() -> None:
    assert (
        derive_hover_alignment(pass_count=1, final_action_type="click_current")
        == "aligned"
    )


def test_derive_adjusted_after_reposition() -> None:
    assert (
        derive_hover_alignment(pass_count=2, final_action_type="click_current")
        == "adjusted"
    )


def test_derive_vlm_alignment_override() -> None:
    assert (
        derive_hover_alignment(
            pass_count=1,
            final_action_type="click_current",
            vlm_alignment="clicked_off_target",
        )
        == "clicked_off_target"
    )


def test_derive_unresolved_on_move() -> None:
    assert (
        derive_hover_alignment(pass_count=3, final_action_type="move_to")
        == "unresolved"
    )


def test_parse_hover_optional_fields() -> None:
    action = parse_action_payload(
        {
            "type": "click_current",
            "alignment": "aligned",
            "target_kind": "icon",
            "reason": "Marker on menu icon.",
        }
    )
    assert action.alignment == "aligned"
    assert action.target_kind == "icon"


def test_parse_invalid_target_kind() -> None:
    try:
        parse_action_payload(
            {"type": "click", "x": 100, "y": 200, "target_kind": "slider", "reason": "x"}
        )
        raise AssertionError("expected ActionParseError")
    except ActionParseError as exc:
        assert "target_kind" in str(exc)


def _move_pass(x: int, y: int) -> dict:
    return {
        "decision": {
            "action": {
                "type": "move_to",
                "x": x,
                "y": y,
                "reason": "nudge",
            }
        }
    }


def test_hover_stall_detects_tiny_moves() -> None:
    passes = [_move_pass(500, 500), _move_pass(502, 501), _move_pass(503, 502)]
    assert hover_adjustment_stalled(passes) is True


def test_hover_stall_detects_oscillation() -> None:
    passes = [_move_pass(500, 500), _move_pass(520, 520), _move_pass(500, 500)]
    assert hover_adjustment_stalled(passes) is True


def test_should_force_on_final_pass() -> None:
    action = Action(type="move_to", x=500, y=500, reason="nudge")
    assert (
        should_force_hover_click(
            pass_index=5,
            passes=[_move_pass(500, 500)],
            hover_action=action,
        )
        is True
    )


def test_coerce_hover_to_click() -> None:
    action = Action(type="move_to", x=500, y=500, reason="still adjusting")
    coerced = coerce_hover_to_click(action, prefix="test:")
    assert coerced.type == "click_current"
    assert coerced.alignment == "adjusted"
    assert "test:" in coerced.reason


def main() -> None:
    test_derive_aligned_first_pass()
    test_derive_adjusted_after_reposition()
    test_derive_vlm_alignment_override()
    test_derive_unresolved_on_move()
    test_parse_hover_optional_fields()
    test_parse_invalid_target_kind()
    test_hover_stall_detects_tiny_moves()
    test_hover_stall_detects_oscillation()
    test_should_force_on_final_pass()
    test_coerce_hover_to_click()
    print("hover alignment unit tests OK")


if __name__ == "__main__":
    main()
