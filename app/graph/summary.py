"""The run summary: what each screen cost, how it ended and whether it is acceptable."""

from __future__ import annotations

from typing import Any

from app.core.telemetry import Record, totals


def screen_summary(screen: dict[str, Any]) -> dict[str, Any]:
    plan = screen["screen"]
    usage: list[Record] = screen.get("usage") or []
    verification = screen.get("verification_result")
    fix = screen.get("fix_result")
    events = screen.get("learning_events") or []
    issues = {"critical": 0, "major": 0, "minor": 0}
    for issue in verification.issues if verification is not None else []:
        issues[issue.severity.value] += 1
    errors = screen.get("errors") or []
    status = verification.status if verification is not None else "failed"
    return {
        "screen": plan.id,
        "recipe": screen["design_spec"].recipe if screen.get("design_spec") else None,
        "status": status,
        # Phase 17 acceptance: the screen rendered, passed deterministic validation and
        # screenshot verification, and nothing failed on the way.
        "accepted": status == "pass" and not errors,
        "issues": issues,
        "fixes": screen.get("iteration", 0),
        "fix_source": fix.source if fix is not None and fix.status == "success" else None,
        "lessons_learned": sum(1 for e in events if e.kind == "fix_verified"),
        "errors": errors,
        **totals(usage),
    }


def summarize(state: dict[str, Any]) -> dict[str, Any]:
    screens = [screen_summary(s) for s in state.get("screens") or []]
    run_usage: list[Record] = list(state.get("usage") or [])
    for s in state.get("screens") or []:
        run_usage.extend(s.get("usage") or [])
    return {
        "run_id": state.get("run_id"),
        "requirement": state.get("user_requirement"),
        "screens": screens,
        "accepted": bool(screens) and all(s["accepted"] for s in screens),
        **totals(run_usage),
    }


def format_summary(summary: dict[str, Any]) -> str:
    lines = [
        f"{'screen':<12}{'status':<10}{'fixes':>6}{'llm':>5}{'tokens in/out':>16}{'render ms':>11}"
    ]
    for s in summary["screens"]:
        tokens = f"{int(s['input_tokens'])}/{int(s['output_tokens'])}"
        lines.append(
            f"{s['screen']:<12}{s['status']:<10}{s['fixes']:>6}{int(s['llm_calls']):>5}"
            f"{tokens:>16}{int(s['render_ms']):>11}"
        )
    total = f"{int(summary['input_tokens'])}/{int(summary['output_tokens'])}"
    verdict = "accepted" if summary["accepted"] else "not accepted"
    lines.append(
        f"{'run':<12}{verdict:<10}{'':>6}{int(summary['llm_calls']):>5}{total:>16}"
        f"{int(summary['render_ms']):>11}"
    )
    return "\n".join(lines)
