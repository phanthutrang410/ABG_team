"""H39a — idempotent auth account seed CLI (not run from migrations).

Usage (from backend/):

    set AUTH_SEED_PASSWORD=...
    python -m app.auth.cli seed
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from app.auth.models import AuthAccount, AuthAccountRole
from app.auth.passwords import hash_password
from app.cases.class_scope import LECTURER_CLASS_SCOPES
from app.config import get_settings
from app.database import get_session_factory, init_schemas

SEED_ORG_SCOPE = "org-demo"
SEED_ADVISOR_SCOPE = "a-240eb01d2805"

# (username, actor_id, display_name, roles, advisor_scope, password_env)
# ``password_env``: optional env var holding this account's own password; falls
# back to AUTH_SEED_PASSWORD when unset. Never hard-code plaintext (RULES §3).
_AccountRow = Tuple[str, str, str, Tuple[str, ...], Optional[str], Optional[str]]

_SEED_ACCOUNTS: Tuple[_AccountRow, ...] = (
    (
        "quanly",
        "acct:quanly",
        "TS. Nam — Giám sát học tập",
        ("ban_quan_ly",),
        None,
        None,
    ),
    (
        "gvcn",
        "acct:gvcn",
        "CVHT Lan — K66-CNTT-A",
        ("gvcn",),
        SEED_ADVISOR_SCOPE,
        None,
    ),
    (
        "demo",
        "acct:demo",
        "Admin hệ thống",
        ("ban_quan_ly", "gvcn"),
        SEED_ADVISOR_SCOPE,
        None,
    ),
)

# Four lecturer (gvcn) accounts — one class each. ``advisor_scope`` maps to the
# class-roster overlay scope (app.cases.class_scope), so each lecturer sees only
# the ~115 students in their own class on /review-cases. Login username is a
# non-PII handle (``gv-<name>``); no real email/contact info in the repo (RULES §2-3).
_LECTURER_ACCOUNTS: Tuple[_AccountRow, ...] = (
    (
        "gv-duy",
        "acct:gv-duy",
        "GVCN — Lớp 01",
        ("gvcn",),
        LECTURER_CLASS_SCOPES[0],
        "AUTH_LECTURER_PW_DUY",
    ),
    (
        "gv-hoang",
        "acct:gv-hoang",
        "GVCN — Lớp 02",
        ("gvcn",),
        LECTURER_CLASS_SCOPES[1],
        "AUTH_LECTURER_PW_HOANG",
    ),
    (
        "gv-trang",
        "acct:gv-trang",
        "GVCN — Lớp 03",
        ("gvcn",),
        LECTURER_CLASS_SCOPES[2],
        "AUTH_LECTURER_PW_TRANG",
    ),
    (
        "gv-giang",
        "acct:gv-giang",
        "GVCN — Lớp 04",
        ("gvcn",),
        LECTURER_CLASS_SCOPES[3],
        "AUTH_LECTURER_PW_GIANG",
    ),
)

ALL_SEED_ACCOUNTS: Tuple[_AccountRow, ...] = _SEED_ACCOUNTS + _LECTURER_ACCOUNTS


def _resolve_password(default_password: str, password_env: Optional[str]) -> str:
    """Per-account password from env when present, else the shared seed password."""
    if password_env:
        override = os.environ.get(password_env, "").strip()
        if override:
            return override
    return default_password


def seed_accounts(db: Session, password: str) -> list[str]:
    """Upsert all seed + lecturer accounts idempotently. Returns usernames touched."""
    if not password:
        raise ValueError("AUTH_SEED_PASSWORD is required (non-empty)")

    now = datetime.now(timezone.utc)
    touched: list[str] = []

    for username, actor_id, display_name, roles, advisor_scope, password_env in (
        ALL_SEED_ACCOUNTS
    ):
        password_hash = hash_password(_resolve_password(password, password_env))
        account = db.get(AuthAccount, actor_id)
        if account is None:
            account = AuthAccount(
                actor_id=actor_id,
                username=username,
                display_name=display_name,
                password_hash=password_hash,
                org_scope=SEED_ORG_SCOPE,
                advisor_scope=advisor_scope,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            db.add(account)
            db.flush()
        else:
            account.username = username
            account.display_name = display_name
            account.password_hash = password_hash
            account.org_scope = SEED_ORG_SCOPE
            account.advisor_scope = advisor_scope
            account.is_active = True
            account.updated_at = now
            # Replace roles
            for existing in list(account.roles):
                db.delete(existing)
            db.flush()

        for role in roles:
            db.add(AuthAccountRole(actor_id=actor_id, role=role))
        touched.append(username)

    db.commit()
    return touched


def _cmd_seed(_: argparse.Namespace) -> int:
    settings = get_settings()
    password = settings.auth_seed_password.get_secret_value()
    if not password.strip():
        print("ERROR: AUTH_SEED_PASSWORD is empty", file=sys.stderr)
        return 2
    init_schemas()
    db = get_session_factory()()
    try:
        touched = seed_accounts(db, password)
    except Exception as exc:  # noqa: BLE001 — CLI surface
        db.rollback()
        print(f"ERROR: seed failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()
    print(f"Seeded accounts: {', '.join(touched)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.auth.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    seed_p = sub.add_parser("seed", help="Idempotent demo auth accounts")
    seed_p.set_defaults(func=_cmd_seed)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
