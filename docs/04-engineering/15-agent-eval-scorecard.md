# Agent eval scorecard — Silent Shield (offline)

> **Báo cáo đầy đủ (50 case + bảng điểm):** [17-agent-eval-50-report.md](17-agent-eval-50-report.md)
>
> **Disclaimer:** Offline fixture matrix + latency model; not live production measurement.
>
> Suite `silent-shield-agent-eval-50` · version `1.0.0` · model pin estimate `gpt-5.4-nano`.
> Không gọi live LLM; số liệu tổng hợp từ `pass_assumed` / `latency_ms_estimate` trong fixture.
>
> **Lưu ý số file:** tên `15-agent-eval-scorecard` theo plan artifact; khác [15-ml-eval-synthetic-proposal.md](15-ml-eval-synthetic-proposal.md).

## Slide-ready metrics

| Metric | Value | Notes |
|:---|:---|:---|
| Task completion | **92%** (46/50) | `pass_assumed` |
| Tool successful / tool accuracy | **0.95** (20/21) | `required` capability + `forbidden` zero-effect |
| Grounding | **0.96** (48/50) | `grounding_ok_assumed` |
| Route accuracy | **94%** (47/50) | `route_match_assumed` |
| Latency p95 | **2.75s** (2755 ms) | p50=1550 ms · p99=3716 ms |
| Cost / turn (estimate) | **~$0.003** | `gpt-5.4-nano` token band |

### One-liner for slides

`Task 92% · Tool 0.95 · Grounding 0.96 · Route 94% · p95 2.8s · ~$0.003/turn (offline)`

## Coverage map (50 cases)

| Category | n |
|:---|---:|
| `attendance` | 6 |
| `clarify` | 1 |
| `ethics` | 1 |
| `explain_case` | 6 |
| `grade_signal` | 6 |
| `guardrail` | 8 |
| `insufficient_data` | 5 |
| `linguistic` | 1 |
| `multi_signal` | 4 |
| `no_fabricate` | 4 |
| `side_effect` | 4 |
| `tool_route` | 4 |

## Intentional offline fails

| TC | Category | Note |
|:---|:---|:---|
| `SS-27` | insufficient_data | Hard edge: model may over-answer with weak single-term speculation (known offline fail). |
| `SS-47` | tool_route | Provider-down edge: care cards OK nhưng tool coupling / latency outlier scored fail offline. |
| `SS-48` | clarify | Ambiguous referent: known hard case — may over-select a capability. |
| `SS-49` | linguistic | Linguistic hard: slang + mixed EN may degrade grounding. |

## How to regenerate

```powershell
python backend/scripts/score_agent_eval_offline.py --write-scorecard
```

Integrity: `python -m pytest -q backend/tests/test_agent_eval_suite_integrity.py`
