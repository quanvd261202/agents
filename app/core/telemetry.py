"""Phase 17 observability. Anything that costs something (a model call, a retrieval, a render)
records itself into the collector of the graph node it runs under; the node hands the records
into graph state, and `uib run` sums them per screen and per run. No collector active means the
record is dropped, so libraries and tests can call `record` freely."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field

Record = dict[str, float | str]


@dataclass
class Collector:
    records: list[Record] = field(default_factory=list)


_current: ContextVar[Collector | None] = ContextVar("uib_telemetry", default=None)


def record(kind: str, **fields: float | str) -> None:
    collector = _current.get()
    if collector is not None:
        collector.records.append({"kind": kind, **fields})


@contextmanager
def collect() -> Iterator[Collector]:
    """Everything recorded inside the block, and in tasks it awaits, lands in the yielded
    collector. Nesting keeps records in the innermost block only."""
    collector = Collector()
    token = _current.set(collector)
    try:
        yield collector
    finally:
        _current.reset(token)


def totals(records: list[Record]) -> dict[str, float]:
    """LLM calls and tokens, render time and node time, summed."""
    out = {
        "llm_calls": 0.0,
        "input_tokens": 0.0,
        "output_tokens": 0.0,
        "render_ms": 0.0,
        "retrievals": 0.0,
    }
    for r in records:
        if r["kind"] == "llm":
            out["llm_calls"] += 1
            out["input_tokens"] += float(r.get("input_tokens", 0))
            out["output_tokens"] += float(r.get("output_tokens", 0))
        elif r["kind"] == "render":
            out["render_ms"] += float(r.get("ms", 0))
        elif r["kind"] == "retrieval":
            out["retrievals"] += 1
    return out
