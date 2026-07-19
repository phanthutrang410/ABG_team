"""H39a — idempotent auth account seed CLI (not run from migrations).

Usage (from backend/):

    set AUTH_SEED_PASSWORD=demo123
    python -m app.auth.cli seed

Canonical demo password for quanly/gvcn/demo (and future seed accounts): demo123.
Live ops keep the same value in SSM `/silent-shield/d460/AUTH_SEED_PASSWORD`.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from typing import Sequence, Tuple

from sqlalchemy.orm import Session

from app.auth.models import AuthAccount, AuthAccountRole
from app.auth.passwords import hash_password
from app.config import get_settings
from app.database import get_session_factory, init_schemas

SEED_ORG_SCOPE = "org-demo"
SEED_ADVISOR_SCOPE = "a-240eb01d2805"

# (username, actor_id, display_name, roles, advisor_scope)
_SEED_ACCOUNTS: Tuple[Tuple[str, str, str, Tuple[str, ...], str | None], ...] = (
    (
        "quanly",
        "acct:quanly",
        "TS. Nam — Giám sát học tập",
        ("ban_quan_ly",),
        None,
    ),
    (
        "gvcn",
        "acct:gvcn",
        "CVHT Lan — K66-CNTT-A",
        ("gvcn",),
        SEED_ADVISOR_SCOPE,
    ),
    (
        "demo",
        "acct:demo",
        "Tài khoản trình diễn (2 vai)",
        ("ban_quan_ly", "gvcn"),
        SEED_ADVISOR_SCOPE,
    ),
)


def seed_accounts(db: Session, password: str) -> list[str]:
    """Upsert seed accounts idempotently. Returns usernames touched."""
    if not password:
        raise ValueError("AUTH_SEED_PASSWORD is required (non-empty)")

    password_hash = hash_password(password)
    now = datetime.now(timezone.utc)
    touched: list[str] = []

    for username, actor_id, display_name, roles, advisor_scope in _SEED_ACCOUNTS:
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
