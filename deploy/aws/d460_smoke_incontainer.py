"""Live D460 smoke — run inside silent-shield-api container (no password printed)."""
from __future__ import annotations

import json
import urllib.request

from app.config import get_settings


def main() -> int:
    pw = get_settings().auth_seed_password.get_secret_value()
    req = urllib.request.Request(
        "http://127.0.0.1:8000/auth/login",
        data=json.dumps({"username": "quanly", "password": pw}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        login = json.load(resp)
        raw_cookie = resp.headers.get("Set-Cookie", "")
    print("login", {k: login.get(k) for k in ("account_id", "active_role", "roles")})
    token = None
    for part in raw_cookie.split(";"):
        part = part.strip()
        if part.startswith("ss_session="):
            token = part.split("=", 1)[1]
            break
    if not token:
        print("no_ss_session_cookie")
        return 1
    headers = {"Cookie": f"ss_session={token}"}
    with urllib.request.urlopen(
        urllib.request.Request("http://127.0.0.1:8000/review-cases", headers=headers)
    ) as resp:
        cases = json.load(resp)
    items = cases.get("items") or []
    print("list_state", cases.get("state"), "n", len(items))
    reasons: dict[str, int] = {}
    att_nonzero = 0
    unapproved = 0
    for it in items:
        cov = it.get("coverage") or {}
        for r in cov.get("reason_codes") or []:
            reasons[r] = reasons.get(r, 0) + 1
            if r == "attendance_source_unapproved":
                unapproved += 1
        if (cov.get("n_attendance_events") or 0) > 0:
            att_nonzero += 1
    print("reason_hist", reasons)
    print("cases_with_att_events", att_nonzero)
    print("cases_attendance_source_unapproved", unapproved)
    sample = items[0] if items else {}
    cov = sample.get("coverage") or {}
    print(
        "sample",
        {
            "case_id": sample.get("case_id"),
            "band": sample.get("review_priority_band"),
            "n_att": cov.get("n_attendance_events"),
            "status": cov.get("status"),
            "reasons": cov.get("reason_codes"),
            "model_version": sample.get("model_version"),
            "data_state": sample.get("data_state"),
        },
    )
    with urllib.request.urlopen(
        urllib.request.Request(
            "http://127.0.0.1:8000/advisor-handoff-drafts", headers=headers
        )
    ) as resp:
        drafts = json.load(resp)
    print(
        "drafts",
        {k: drafts.get(k) for k in ("state", "status") if k in drafts}
        or {"keys": list(drafts)[:6]},
    )
    ok = unapproved == 0 and att_nonzero > 0 and cases.get("state") == "ok"
    print("smoke_ok" if ok else "smoke_partial")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
