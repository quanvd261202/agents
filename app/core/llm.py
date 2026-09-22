"""LLM abstraction. Nothing outside app.agents should depend on a concrete provider."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from app.core.exceptions import ConfigurationError, StructuredOutputError

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


class AnthropicLLMProvider:
    """LangChain-backed provider. Imported lazily so tests need no API key."""

    def __init__(self, model: str, temperature: float = 0.2) -> None:
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as e:  # pragma: no cover
            raise ConfigurationError("langchain-anthropic is not installed") from e
        self._model_name = model
        self._chat = ChatAnthropic(model=model, temperature=temperature)

    @staticmethod
    def _to_lc(messages: Sequence[Message]) -> list[tuple[str, Any]]:
        return [(m.role, m.content) for m in messages]

    async def invoke_structured(self, messages: Sequence[Message], schema: type[T]) -> LLMResult[T]:
        import time

        start = time.perf_counter()
        runnable = self._chat.with_structured_output(schema, include_raw=True)
        out = await runnable.ainvoke(self._to_lc(messages))
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
        out = await self._chat.ainvoke(self._to_lc(messages))
        meta = getattr(out, "usage_metadata", None) or {}
        usage = LLMUsage(
            input_tokens=meta.get("input_tokens", 0),
            output_tokens=meta.get("output_tokens", 0),
            model=self._model_name,
            latency_ms=(time.perf_counter() - start) * 1000,
        )
        return LLMResult(value=str(out.content), usage=usage)


def build_llm_provider(provider: str, model: str) -> LLMProvider:
    if provider == "fake":
        return FakeLLMProvider()
    if provider == "anthropic":
        return AnthropicLLMProvider(model=model)
    raise ConfigurationError(f"Unknown LLM provider: {provider}")
