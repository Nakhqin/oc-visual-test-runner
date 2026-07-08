"""Unit tests for G2 hover alignment helpers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from core.actions import Action, ActionParseError, parse_action_payload
from core.hover import derive_hover_alignment


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


def main() -> None:
    test_derive_aligned_first_pass()
    test_derive_adjusted_after_reposition()
    test_derive_vlm_alignment_override()
    test_derive_unresolved_on_move()
    test_parse_hover_optional_fields()
    test_parse_invalid_target_kind()
    print("hover alignment unit tests OK")


if __name__ == "__main__":
    main()
