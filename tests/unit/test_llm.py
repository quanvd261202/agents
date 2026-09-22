import pytest

from app.core.exceptions import StructuredOutputError
from app.core.llm import FakeLLMProvider, Message
from app.models import UXPlan


async def test_fake_provider_returns_queued_model():
    plan = UXPlan(
        product="p", user_goals=["g"], journey=["j"], screens=[{"id": "h", "purpose": "x"}]
    )
    llm = FakeLLMProvider([plan])
    out = await llm.invoke_structured([Message("user", "hi")], UXPlan)
    assert out.value == plan
    assert out.usage.model == "fake"


async def test_fake_provider_parses_json_string():
    llm = FakeLLMProvider(
        ['{"product":"p","user_goals":["g"],"journey":["j"],"screens":[{"id":"h","purpose":"x"}]}']
    )
    out = await llm.invoke_structured([], UXPlan)
    assert out.value.product == "p"


async def test_fake_provider_schema_mismatch():
    llm = FakeLLMProvider(["not json"])
    with pytest.raises(ValueError):
        await llm.invoke_structured([], UXPlan)
    with pytest.raises(StructuredOutputError):
        await FakeLLMProvider().invoke_structured([], UXPlan)
