"""Shared plumbing for the LLM agents: one structured call, repair retries on semantic failure.

Schema drift is already impossible (structured outputs + StrictModel). What is still possible is
an output that parses but names something the registries do not know, so every agent that can
produce an ID passes a `validate` callback and gets `max_repairs` chances to repair it.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, TypeVar

from pydantic import BaseModel

from app.core.exceptions import ValidationError
from app.core.llm import LLMProvider, Message
from app.core.logging import get_logger
from app.core.telemetry import record

T = TypeVar("T", bound=BaseModel)

log = get_logger(__name__)

_REPAIR = (
    "That output is invalid: {error}\nReturn the whole object again, changing only what is invalid."
)


class Agent:
    """Base for the Phase 07-10 agents."""

    name = "agent"
    #: Repairs after the first attempt. Small models often fix one rule and trip another.
    max_repairs = 2

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def _invoke(
        self,
        system: str,
        user: str | list[dict[str, Any]],
        schema: type[T],
        validate: Callable[[T], T] | None = None,
    ) -> T:
        messages: Sequence[Message] = [Message("system", system), Message("user", user)]
        last: ValidationError | None = None
        for attempt in range(1, self.max_repairs + 2):
            result = await self._llm.invoke_structured(messages, schema)
            log.info(
                "agent.call",
                agent=self.name,
                attempt=attempt,
                model=result.usage.model,
                input_tokens=result.usage.input_tokens,
                output_tokens=result.usage.output_tokens,
            )
            record(
                "llm",
                agent=self.name,
                attempt=attempt,
                model=result.usage.model,
                input_tokens=result.usage.input_tokens,
                output_tokens=result.usage.output_tokens,
                ms=round(result.usage.latency_ms, 1),
            )
            if validate is None:
                return result.value
            try:
                return validate(result.value)
            except ValidationError as e:
                last = e
                log.warning("agent.invalid_output", agent=self.name, attempt=attempt, error=str(e))
                messages = [
                    *messages,
                    Message("assistant", result.value.model_dump_json()),
                    Message("user", _REPAIR.format(error=e)),
                ]
        assert last is not None
        raise last


def brief_block(brief: str) -> str:
    """The user's original requirement, appended verbatim to a prompt when there is one."""
    return f"\n\nThe user's brief, verbatim:\n{brief.strip()}" if brief.strip() else ""
