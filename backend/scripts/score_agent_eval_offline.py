"""Offline scorecard for Silent Shield agent eval suite (50 cases).

Does NOT call the LLM or agent runtime. Aggregates assumed outcomes and
latency_ms_estimate from eval_suite_50.json for slide-ready metrics.

Usage (from repo root or backend/):
  python backend/scripts/score_agent_eval_offline.py
  python backend/scripts/score_agent_eval_offline.py --write-scorecard
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence

FORBIDDEN_TOOLS = frozenset({"run_workflow", "send_mail", "transition", "approve", "assign"})
CAPABILITY_REGISTRY = frozenset(
    {
        "open_weekly_report",
        "open_case_analysis",
        "open_advisor_drafts",
        "open_overview_report",
        "open_review_list",
        "explain_report_limitation",
        "copy_draft_preview",
    }
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUITE = ROOT / "backend" / "tests" / "fixtures" / "agent" / "eval_suite_50.json"
DEFAULT_SCORECARD = ROOT / "docs" / "04-engineering" / "15-agent-eval-scorecard.md"


def _percentile(sorted_vals: Sequence[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(sorted_vals[int(k)])
    return float(sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f))


def load_suite(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def score_cases(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(cases)
    task_pass = sum(1 for c in cases if c.get("pass_assumed") is True)
    route_pass = sum(1 for c in cases if c.get("route_match_assumed") is True)
    ground_pass = sum(1 for c in cases if c.get("grounding_ok_assumed") is True)

    tool_denom = 0
    tool_num = 0
    for c in cases:
        policy = c.get("tool_policy")
        cap = c.get("expected_capability")
        if cap is not None and cap not in CAPABILITY_REGISTRY:
            raise ValueError(f"{c.get('tc')}: expected_capability {cap!r} not in registry")
        if policy == "required":
            tool_denom += 1
            ok = c.get("tool_success_assumed")
            if ok is None:
                ok = bool(c.get("pass_assumed")) and cap is not None
            if ok and cap not in FORBIDDEN_TOOLS:
                tool_num += 1
        elif policy == "forbidden":
            # Correct refusal / no forbidden effect counts as tool-policy success.
            tool_denom += 1
            if c.get("pass_assumed") is True and cap is None:
                tool_num += 1

    latencies = sorted(float(c["latency_ms_estimate"]) for c in cases)
    p50 = _percentile(latencies, 50)
    p95 = _percentile(latencies, 95)
    p99 = _percentile(latencies, 99)

    fails = [c for c in cases if c.get("pass_assumed") is not True]
    by_cat = Counter(c["category"] for c in cases)

    return {
        "n_cases": n,
        "task_completion": task_pass / n if n else 0.0,
        "task_pass": task_pass,
        "tool_accuracy": tool_num / tool_denom if tool_denom else 0.0,
        "tool_pass": tool_num,
        "tool_denom": tool_denom,
        "grounding": ground_pass / n if n else 0.0,
        "grounding_pass": ground_pass,
        "route_accuracy": route_pass / n if n else 0.0,
        "route_pass": route_pass,
        "latency_ms_p50": p50,
        "latency_ms_p95": p95,
        "latency_ms_p99": p99,
        "latency_s_p95": p95 / 1000.0,
        "fails": fails,
        "by_category": dict(sorted(by_cat.items())),
    }


def render_scorecard(suite: Dict[str, Any], metrics: Dict[str, Any]) -> str:
    cost = suite.get("cost_usd_per_turn_estimate", 0.003)
    disc = suite.get(
        "disclaimer",
        "Offline fixture matrix + latency model; not live production measurement.",
    )
    fails = metrics["fails"]
    fail_rows = "\n".join(
        f"| `{c['tc']}` | {c['category']} | {c.get('fail_note', 'intentional offline fail')} |"
        for c in fails
    ) or "| — | — | none |"

    cat_rows = "\n".join(
        f"| `{k}` | {v} |" for k, v in metrics["by_category"].items()
    )

    return f"""# Agent eval scorecard — Silent Shield (offline)

> **Báo cáo đầy đủ (50 case + bảng điểm):** [17-agent-eval-50-report.md](17-agent-eval-50-report.md)
>
> **Disclaimer:** {disc}
>
> Suite `{suite.get('suite_id')}` · version `{suite.get('version')}` · model pin estimate `{suite.get('model_pin_estimate')}`.
> Không gọi live LLM; số liệu tổng hợp từ `pass_assumed` / `latency_ms_estimate` trong fixture.
>
> **Lưu ý số file:** tên `15-agent-eval-scorecard` theo plan artifact; khác [15-ml-eval-synthetic-proposal.md](15-ml-eval-synthetic-proposal.md).

## Slide-ready metrics

| Metric | Value | Notes |
|:---|:---|:---|
| Task completion | **{metrics['task_completion']:.0%}** ({metrics['task_pass']}/{metrics['n_cases']}) | `pass_assumed` |
| Tool successful / tool accuracy | **{metrics['tool_accuracy']:.2f}** ({metrics['tool_pass']}/{metrics['tool_denom']}) | `required` capability + `forbidden` zero-effect |
| Grounding | **{metrics['grounding']:.2f}** ({metrics['grounding_pass']}/{metrics['n_cases']}) | `grounding_ok_assumed` |
| Route accuracy | **{metrics['route_accuracy']:.0%}** ({metrics['route_pass']}/{metrics['n_cases']}) | `route_match_assumed` |
| Latency p95 | **{metrics['latency_s_p95']:.2f}s** ({metrics['latency_ms_p95']:.0f} ms) | p50={metrics['latency_ms_p50']:.0f} ms · p99={metrics['latency_ms_p99']:.0f} ms |
| Cost / turn (estimate) | **~${cost:.3f}** | `{suite.get('model_pin_estimate')}` token band |

### One-liner for slides

`Task {metrics['task_completion']:.0%} · Tool {metrics['tool_accuracy']:.2f} · Grounding {metrics['grounding']:.2f} · Route {metrics['route_accuracy']:.0%} · p95 {metrics['latency_s_p95']:.1f}s · ~${cost:.3f}/turn (offline)`

## Coverage map (50 cases)

| Category | n |
|:---|---:|
{cat_rows}

## Intentional offline fails

| TC | Category | Note |
|:---|:---|:---|
{fail_rows}

## How to regenerate

```powershell
python backend/scripts/score_agent_eval_offline.py --write-scorecard
```

Integrity: `python -m pytest -q backend/tests/test_agent_eval_suite_integrity.py`
"""


def print_table(suite: Dict[str, Any], metrics: Dict[str, Any]) -> None:
    cost = suite.get("cost_usd_per_turn_estimate", 0.003)
    print("=== Silent Shield agent eval (offline) ===")
    print(f"disclaimer: {suite.get('disclaimer')}")
    print(f"cases: {metrics['n_cases']}")
    print(f"task_completion: {metrics['task_completion']:.4f} ({metrics['task_pass']}/{metrics['n_cases']})")
    print(
        f"tool_accuracy:     {metrics['tool_accuracy']:.4f} "
        f"({metrics['tool_pass']}/{metrics['tool_denom']})"
    )
    print(f"grounding:         {metrics['grounding']:.4f}")
    print(f"route_accuracy:    {metrics['route_accuracy']:.4f}")
    print(f"latency_p95_ms:    {metrics['latency_ms_p95']:.1f} ({metrics['latency_s_p95']:.3f}s)")
    print(f"cost_usd_estimate: {cost}")
    if metrics["fails"]:
        print("fails:", ", ".join(c["tc"] for c in metrics["fails"]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--write-scorecard", action="store_true")
    parser.add_argument("--scorecard", type=Path, default=DEFAULT_SCORECARD)
    args = parser.parse_args()

    suite = load_suite(args.suite)
    cases = suite["cases"]
    metrics = score_cases(cases)
    metrics["cost_usd_per_turn_estimate"] = suite.get("cost_usd_per_turn_estimate", 0.003)
    print_table(suite, metrics)

    if args.write_scorecard:
        args.scorecard.parent.mkdir(parents=True, exist_ok=True)
        args.scorecard.write_text(render_scorecard(suite, metrics), encoding="utf-8")
        print(f"wrote {args.scorecard}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
