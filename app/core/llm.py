"""LLM abstraction. Nothing outside app.agents should depend on a concrete provider."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from app.core.exceptions import ConfigurationError, LLMError, StructuredOutputError
from app.core.logging import get_logger

log = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str | list[dict[str, Any]]  # text or multimodal blocks


@dataclass
class LLMUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    latency_ms: float = 0.0


@dataclass
class LLMResult[R]:
    value: R
    usage: LLMUsage = field(default_factory=LLMUsage)


class LLMProvider(Protocol):
    async def invoke_structured(
        self, messages: Sequence[Message], schema: type[T]
    ) -> LLMResult[T]: ...

    async def invoke_text(self, messages: Sequence[Message]) -> LLMResult[str]: ...


class FakeLLMProvider:
    """Deterministic provider for tests: returns queued responses in order."""

    def __init__(self, responses: Sequence[BaseModel | str] = ()) -> None:
        self._queue = list(responses)
        self.calls: list[Sequence[Message]] = []

    def push(self, response: BaseModel | str) -> None:
        self._queue.append(response)

    async def invoke_structured(self, messages: Sequence[Message], schema: type[T]) -> LLMResult[T]:
        self.calls.append(messages)
        if not self._queue:
            raise StructuredOutputError("FakeLLMProvider has no queued response")
        item = self._queue.pop(0)
        if isinstance(item, str):
            item = schema.model_validate_json(item)
        if not isinstance(item, schema):
            raise StructuredOutputError(f"Queued {type(item).__name__}, expected {schema.__name__}")
        return LLMResult(value=item, usage=LLMUsage(model="fake"))

    async def invoke_text(self, messages: Sequence[Message]) -> LLMResult[str]:
        self.calls.append(messages)
        item = self._queue.pop(0) if self._queue else ""
        return LLMResult(value=str(item), usage=LLMUsage(model="fake"))


#: Waits between attempts after a rate limit. The SDK's own retries honour a sub-second
#: retry-after and give up within seconds, which never outlasts a tokens-per-minute window when
#: several screens share it; these do.
RATE_LIMIT_BACKOFF_S: tuple[float, ...] = (2, 5, 10, 20, 40)


#: A small model occasionally degenerates into a repeating structured output until it hits the
#: token cap. Sampling again almost always clears it, so a runaway is retried this many times.
RUNAWAY_RETRIES = 2
#: Caps a runaway early: the largest legitimate output (a copywriter pass over a dense page) is a
#: few thousand tokens.
MAX_OUTPUT_TOKENS = 8192


def _is_rate_limit(e: BaseException) -> bool:
    return type(e).__name__ == "RateLimitError" or getattr(e, "status_code", None) == 429


def _is_runaway(e: BaseException) -> bool:
    return type(e).__name__ == "LengthFinishReasonError"


async def _call[R](
    make_call: Callable[[], Awaitable[R]],
    *,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> R:
    """Provider SDK failures (rate limits, timeouts, auth) surface as the project's LLMError, so
    the graph can fail one screen instead of the whole run. A rate limit is retried with growing
    waits first, because it clears on its own; a runaway output is sampled again."""
    runaways = 0
    for wait in (*RATE_LIMIT_BACKOFF_S, None):
        try:
            return await make_call()
        except Exception as e:  # noqa: BLE001
            if _is_runaway(e) and runaways < RUNAWAY_RETRIES:
                runaways += 1
                log.warning("llm.runaway_output", attempt=runaways)
                continue
            if wait is None or not _is_rate_limit(e):
                raise LLMError(f"{type(e).__name__}: {e}") from e
            log.warning("llm.rate_limited", wait_s=wait, error=str(e)[:160])
            await sleep(wait)
    raise AssertionError("unreachable")  # pragma: no cover


class OpenAILLMProvider:
    """LangChain-backed OpenAI provider. Imported lazily so tests need no API key."""

    def __init__(
        self,
        model: str,
        temperature: float = 0.2,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as e:  # pragma: no cover
            raise ConfigurationError("langchain-openai is not installed") from e
        self._model_name = model
        # Retries back off on 429s, honouring the server's retry-after.
        kwargs: dict[str, Any] = {
            "model": model,
            "temperature": temperature,
            "max_retries": 6,
            "max_tokens": MAX_OUTPUT_TOKENS,
        }
        if base_url:
            kwargs["base_url"] = base_url
        if api_key:
            kwargs["api_key"] = api_key
        self._chat = ChatOpenAI(**kwargs)

    @staticmethod
    def _to_lc(messages: Sequence[Message]) -> list[tuple[str, Any]]:
        return [(m.role, m.content) for m in messages]

    async def invoke_structured(self, messages: Sequence[Message], schema: type[T]) -> LLMResult[T]:
        import time

        start = time.perf_counter()
        # `strict` uses OpenAI structured outputs, so the model cannot return an off-schema object.
        runnable = self._chat.with_structured_output(
            schema, method="json_schema", strict=True, include_raw=True
        )
        out = await _call(lambda: runnable.ainvoke(self._to_lc(messages)))
        if not isinstance(out, dict):
            raise StructuredOutputError("structured output did not return a raw/parsed dict")
        parsed = out.get("parsed")
        if parsed is None:
            raise StructuredOutputError(str(out.get("parsing_error")))
        return LLMResult(value=parsed, usage=self._usage(out["raw"], start))

    async def invoke_text(self, messages: Sequence[Message]) -> LLMResult[str]:
        import time

        start = time.perf_counter()
        out = await _call(lambda: self._chat.ainvoke(self._to_lc(messages)))
        return LLMResult(value=str(out.content), usage=self._usage(out, start))

    def _usage(self, raw: Any, start: float) -> LLMUsage:
        import time

        meta = getattr(raw, "usage_metadata", None) or {}
        return LLMUsage(
            input_tokens=meta.get("input_tokens", 0),
            output_tokens=meta.get("output_tokens", 0),
            model=self._model_name,
            latency_ms=(time.perf_counter() - start) * 1000,
        )


class AnthropicLLMProvider:
    """LangChain-backed provider. Imported lazily so tests need no API key."""

    def __init__(self, model: str, temperature: float = 0.2, api_key: str | None = None) -> None:
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as e:  # pragma: no cover
            raise ConfigurationError("langchain-anthropic is not installed") from e
        self._model_name = model
        kwargs: dict[str, Any] = {"model": model, "temperature": temperature}
        if api_key:
            kwargs["api_key"] = api_key
        self._chat = ChatAnthropic(**kwargs)

    @staticmethod
    def _to_lc(messages: Sequence[Message]) -> list[tuple[str, Any]]:
        return [(m.role, m.content) for m in messages]

    async def invoke_structured(self, messages: Sequence[Message], schema: type[T]) -> LLMResult[T]:
        import time

        start = time.perf_counter()
        runnable = self._chat.with_structured_output(schema, include_raw=True)
        out = await _call(lambda: runnable.ainvoke(self._to_lc(messages)))
        if not isinstance(out, dict):
            raise StructuredOutputError("structured output did not return a raw/parsed dict")
        parsed = out.get("parsed")
        if parsed is None:
            raise StructuredOutputError(str(out.get("parsing_error")))
        raw = out["raw"]
        meta = getattr(raw, "usage_metadata", None) or {}
        usage = LLMUsage(
            input_tokens=meta.get("input_tokens", 0),
            output_tokens=meta.get("output_tokens", 0),
            model=self._model_name,
            latency_ms=(time.perf_counter() - start) * 1000,
        )
        return LLMResult(value=parsed, usage=usage)

    async def invoke_text(self, messages: Sequence[Message]) -> LLMResult[str]:
        import time

        start = time.perf_counter()
        out = await _call(lambda: self._chat.ainvoke(self._to_lc(messages)))
        meta = getattr(out, "usage_metadata", None) or {}
        usage = LLMUsage(
            input_tokens=meta.get("input_tokens", 0),
            output_tokens=meta.get("output_tokens", 0),
            model=self._model_name,
            latency_ms=(time.perf_counter() - start) * 1000,
        )
        return LLMResult(value=str(out.content), usage=usage)


#: Used when `llm_model` is left empty so one setting can serve every provider.
DEFAULT_MODELS = {"openai": "gpt-4o", "anthropic": "claude-sonnet-5", "fake": "fake"}


def build_llm_provider(
    provider: str, model: str = "", base_url: str | None = None, api_key: str | None = None
) -> LLMProvider:
    chosen = model or DEFAULT_MODELS.get(provider, "")
    if provider == "fake":
        return FakeLLMProvider()
    if provider == "openai":
        return OpenAILLMProvider(model=chosen, base_url=base_url, api_key=api_key)
    if provider == "anthropic":
        return AnthropicLLMProvider(model=chosen, api_key=api_key)
    raise ConfigurationError(f"Unknown LLM provider: {provider}")
