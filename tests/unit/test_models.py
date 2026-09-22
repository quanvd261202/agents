import pytest
from pydantic import ValidationError

from app.models import ClarifierOutput, DesignSpec


def test_design_spec_find_nested():
    spec = DesignSpec(
        screen_id="s",
        recipe="r",
        visual_style="v",
        theme="t",
        sections=[{"id": "a", "type": "hero", "children": [{"id": "b", "type": "cta"}]}],
    )
    assert spec.find("b") is not None
    assert spec.find("zzz") is None


def test_strict_models_reject_unknown_fields():
    with pytest.raises(ValidationError):
        DesignSpec(
            screen_id="s",
            recipe="r",
            visual_style="v",
            theme="t",
            sections=[{"id": "a", "type": "hero"}],
            css="body{}",
        )


def test_clarifier_max_three_questions():
    qs = [{"question": f"q{i}"} for i in range(4)]
    with pytest.raises(ValidationError):
        ClarifierOutput(status="needs_clarification", questions=qs)
