import pytest

from app.core.exceptions import StructuredOutputError
from app.core.llm import FakeLLMProvider, Message
from app.models import UXPlan


async def test_fake_provider_returns_queued_model():
    plan = UXPlan(product="p", user_goals=["g"], screens=[{"id": "h", "purpose": "x"}])
    llm = FakeLLMProvider([plan])
    out = await llm.invoke_structured([Message("user", "hi")], UXPlan)
    assert out.value == plan
    assert out.usage.model == "fake"


async def test_fake_provider_parses_json_string():
    llm = FakeLLMProvider(
        ['{"product":"p","user_goals":["g"],"screens":[{"id":"h","purpose":"x"}]}']
    )
    out = await llm.invoke_structured([], UXPlan)
    assert out.value.product == "p"


async def test_fake_provider_schema_mismatch():
    llm = FakeLLMProvider(["not json"])
    with pytest.raises(ValueError):
        await llm.invoke_structured([], UXPlan)
    with pytest.raises(StructuredOutputError):
        await FakeLLMProvider().invoke_structured([], UXPlan)


async def test_provider_sdk_errors_surface_as_llm_errors():
    """A 429 or timeout must be a UIBuilderError so the graph fails one screen, not the run."""
    from app.core.exceptions import LLMError
    from app.core.llm import _call

    async def rate_limited() -> None:
        raise RuntimeError("Error code: 429")

    with pytest.raises(LLMError, match="RuntimeError: Error code: 429"):
        await _call(rate_limited)


async def test_rate_limits_are_retried_with_growing_waits_before_failing():
    """The SDK's sub-second retries never outlast a tokens-per-minute window; ours do."""
    from app.core.exceptions import LLMError
    from app.core.llm import RATE_LIMIT_BACKOFF_S, _call

    class RateLimitError(Exception):
        status_code = 429

    waits: list[float] = []

    async def sleep(s: float) -> None:
        waits.append(s)

    attempts = 0

    async def flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts <= 2:
            raise RateLimitError("Rate limit reached")
        return "ok"

    assert await _call(flaky, sleep=sleep) == "ok"
    assert waits == list(RATE_LIMIT_BACKOFF_S[:2])

    async def always() -> str:
        raise RateLimitError("Rate limit reached")

    waits.clear()
    with pytest.raises(LLMError, match="RateLimitError"):
        await _call(always, sleep=sleep)
    assert waits == list(RATE_LIMIT_BACKOFF_S)  # every wait used, then the screen fails

    async def auth() -> str:
        raise PermissionError("bad key")

    waits.clear()
    with pytest.raises(LLMError, match="PermissionError"):
        await _call(auth, sleep=sleep)
    assert waits == []  # only rate limits are worth waiting for


async def test_a_runaway_output_is_sampled_again_then_fails():
    """A small model can loop until the token cap; a fresh sample usually clears it."""
    from app.core.exceptions import LLMError
    from app.core.llm import RUNAWAY_RETRIES, _call

    class LengthFinishReasonError(Exception):
        pass

    attempts = 0

    async def flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts <= RUNAWAY_RETRIES:
            raise LengthFinishReasonError("length limit was reached")
        return "ok"

    assert await _call(flaky) == "ok"
    assert attempts == RUNAWAY_RETRIES + 1

    async def always() -> str:
        raise LengthFinishReasonError("length limit was reached")

    with pytest.raises(LLMError, match="LengthFinishReasonError"):
        await _call(always)
