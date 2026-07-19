"""Generate docs/04-engineering/17-agent-eval-50-report.md from eval_suite_50.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from scripts.score_agent_eval_offline import score_cases  # noqa: E402

SUITE = ROOT / "backend" / "tests" / "fixtures" / "agent" / "eval_suite_50.json"
OUT = ROOT / "docs" / "04-engineering" / "17-agent-eval-50-report.md"


def main() -> None:
    suite = json.loads(SUITE.read_text(encoding="utf-8"))
    cases = suite["cases"]
    m = score_cases(cases)
    cost = suite.get("cost_usd_per_turn_estimate", 0.003)
    disc = suite.get(
        "disclaimer",
        "Offline fixture matrix + latency model; not live production measurement.",
    )

    by_cat = m["by_category"]
    cat_rows = "\n".join(f"| `{k}` | {v} |" for k, v in by_cat.items())

    fail_rows = "\n".join(
        f"| `{c['tc']}` | {c['category']} | {c.get('fail_note', 'intentional offline fail')} |"
        for c in m["fails"]
    )

    case_rows = []
    for c in cases:
        q = c["input"]["question"].replace("|", "/").replace("\n", " ")
        seed = c.get("seed_ref") or "—"
        status = "PASS" if c["pass_assumed"] else "FAIL"
        cap = c.get("expected_capability") or "—"
        case_rows.append(
            "| {tc} | {cat} | {surf} | {route} | {pol} | `{cap}` | {out} | **{st}** | {lat} | {seed} | {q} |".format(
                tc=c["tc"],
                cat=c["category"],
                surf=c["surface"],
                route=c["expected_route"],
                pol=c["tool_policy"],
                cap=cap,
                out=c["expected_outcome"],
                st=status,
                lat=c["latency_ms_estimate"],
                seed=seed,
                q=q,
            )
        )
    case_table = "\n".join(case_rows)

    body = f"""# Báo cáo bộ 50 test case — Agent eval (offline)

| | |
|:---|:---|
| Suite | `{suite.get("suite_id")}` |
| Version | `{suite.get("version")}` |
| Mode | `{suite.get("mode")}` — **không đo live / không gọi LLM** |
| Model pin (estimate) | `{suite.get("model_pin_estimate")}` |
| Fixture | [`backend/tests/fixtures/agent/eval_suite_50.json`](../../backend/tests/fixtures/agent/eval_suite_50.json) |
| Scorer | [`backend/scripts/score_agent_eval_offline.py`](../../backend/scripts/score_agent_eval_offline.py) |
| Integrity | [`backend/tests/test_agent_eval_suite_integrity.py`](../../backend/tests/test_agent_eval_suite_integrity.py) |
| Scorecard ngắn | [15-agent-eval-scorecard.md](15-agent-eval-scorecard.md) |

> **Disclaimer:** {disc}

## 1. Mục đích

Báo cáo này là bằng chứng / tài liệu slide cho đánh giá luồng agent Silent Shield trên **50 test case** bao phủ:

- Global Agent (`overview` turns, capability cards)
- Case explanation (FR-08 grounded / refusal)
- Guardrails, forbidden tools, insufficient data, attendance (CORE-03)

Methodology metric names tham chiếu reference Learning Analytics (task / tool / grounding / latency / cost), **remap** sang domain Silent Shield — không copy SQL/CTĐT.

Liên quan Sprint: evidence mở rộng cho **T05** (tool/RBAC/adversarial matrix); không claim production live gate.

## 2. Bảng điểm tổng hợp (slide-ready)

| Metric | Value | Công thức offline |
|:---|:---|:---|
| Task completion | **{m['task_completion']:.0%}** ({m['task_pass']}/{m['n_cases']}) | `% pass_assumed == true` |
| Tool successful / tool accuracy | **{m['tool_accuracy']:.2f}** ({m['tool_pass']}/{m['tool_denom']}) | `tool_policy=required` (capability) + `forbidden` (zero-effect) |
| Grounding | **{m['grounding']:.2f}** ({m['grounding_pass']}/{m['n_cases']}) | `% grounding_ok_assumed` |
| Route accuracy | **{m['route_accuracy']:.0%}** ({m['route_pass']}/{m['n_cases']}) | `% route_match_assumed` |
| Latency p95 | **{m['latency_s_p95']:.2f}s** ({m['latency_ms_p95']:.0f} ms) | p95 của `latency_ms_estimate` (p50={m['latency_ms_p50']:.0f} · p99={m['latency_ms_p99']:.0f}) |
| Cost / turn (estimate) | **~${cost:.3f}** | `{suite.get('model_pin_estimate')}` token band cố định |

### One-liner copy slide

```text
Task {m['task_completion']:.0%} · Tool {m['tool_accuracy']:.2f} · Grounding {m['grounding']:.2f} · Route {m['route_accuracy']:.0%} · p95 {m['latency_s_p95']:.1f}s · ~${cost:.3f}/turn (offline)
```

## 3. Coverage map

| Category | n |
|:---|---:|
{cat_rows}

| Surface | Ý nghĩa |
|:---|:---|
| `case_explanation` | `POST …/explanation` / FR-08 |
| `overview` | `POST /agent/turns` Global Agent overview graph |

## 4. Fail có chủ đích (4/50)

| TC | Category | Ghi chú |
|:---|:---|:---|
{fail_rows}

Các case còn lại (46) `pass_assumed: true` theo contract fixture.

## 5. Danh sách đầy đủ 50 test case

| TC | Category | Surface | Route | Tool policy | Capability | Outcome | Result | Latency ms | Seed | Question |
|:---|:---|:---|:---|:---|:---|:---|:---|---:|:---|:---|
{case_table}

## 6. Cách đọc cột

| Cột | Ý nghĩa |
|:---|:---|
| Route | `answer` / `tool` / `clarify` / `refuse` / `provider_unavailable` |
| Tool policy | `required` phải chọn capability; `forbidden` tuyệt đối không side-effect; `none`/`optional` |
| Outcome | Kết quả nghiệp vụ kỳ vọng (`grounded_ok`, `refusal`, `insufficient_data`, …) |
| Result | Offline assumed PASS/FAIL — **không** phải kết quả gọi live model |
| Seed | Nguồn tái sử dụng ADV-* / OV-* nếu có |
| Latency ms | Ước lượng theo loại route (refuse nhanh, tool/overview chậm hơn) |

## 7. Regenerated / verify

```powershell
# In bảng metric + ghi lại scorecard ngắn
python backend/scripts/score_agent_eval_offline.py --write-scorecard

# Sinh lại báo cáo đầy đủ này
Push-Location backend
python scripts/generate_agent_eval_report.py
Pop-Location

# Integrity
Push-Location backend
python -m pytest -q tests/test_agent_eval_suite_integrity.py
Pop-Location
```

## 8. Ranh giới / không claim

- Không phải đo latency/cost production từ LangSmith hay HTTP.
- Không thay thế T05 live/FE e2e.
- Không chứa PII/MSSV thật; câu hỏi dùng ngữ cảnh pseudonym / fixture sẵn có.
- `reference-Learning-Analytics-AI/` không commit; chỉ tham chiếu methodology ngoài repo.
"""

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body, encoding="utf-8")
    print(f"wrote {OUT} ({m['n_cases']} cases)")


if __name__ == "__main__":
    main()
