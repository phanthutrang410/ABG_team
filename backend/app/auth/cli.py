"""H39a — idempotent auth account seed CLI (not run from migrations).

Usage (from backend/):

    set AUTH_SEED_PASSWORD=demo123
    set AUTH_LECTURER_SEEDS=[{"username":"duy.bk","password":"..."},...]
    python -m app.auth.cli seed

``AUTH_SEED_PASSWORD`` seeds quanly / legacy demo accounts.
Lecturer passwords come from ``AUTH_LECTURER_SEEDS`` JSON (preferred) or fall
back to ``AUTH_SEED_PASSWORD`` for local/dev only.

Live ops: SSM ``/silent-shield/d460/AUTH_SEED_PASSWORD`` +
``/silent-shield/d460/AUTH_LECTURER_SEEDS``.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Dict, Mapping, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from app.auth.models import AuthAccount, AuthAccountRole
from app.auth.passwords import hash_password
from app.config import get_settings
from app.database import get_session_factory, init_schemas
from app.dwh.partition_demo import ADVISOR_REFS

SEED_ORG_SCOPE = "org-demo"
# Legacy single-advisor scope kept only for historical fixtures; seed remaps
# gvcn/demo onto the first demo partition so they never see all 460.
LEGACY_ADVISOR_SCOPE = "a-240eb01d2805"
DEFAULT_LECTURER_SCOPE = ADVISOR_REFS[0]

# (username, actor_id, display_name, roles, advisor_scope)
_CORE_SEED_ACCOUNTS: Tuple[Tuple[str, str, str, Tuple[str, ...], str | None], ...] = (
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
        "CVHT Lan — Lop-GVCN-Duy (legacy)",
        ("gvcn",),
        DEFAULT_LECTURER_SCOPE,
    ),
    (
        "demo",
        "acct:demo",
        "Tài khoản trình diễn (2 vai)",
        ("ban_quan_ly", "gvcn"),
        DEFAULT_LECTURER_SCOPE,
    ),
)

# Four GVCN lecturers — display names only (no emails in repo).
_LECTURER_SEED_ACCOUNTS: Tuple[Tuple[str, str, str, str], ...] = (
    ("duy.bk", "acct:duy.bk", "Bùi Khánh Duy", ADVISOR_REFS[0]),
    ("hoang.nv", "acct:hoang.nv", "Nguyễn Việt Hoàng", ADVISOR_REFS[1]),
    ("trang.pt", "acct:trang.pt", "Phan Thu Trang", ADVISOR_REFS[2]),
    ("giang.nt", "acct:giang.nt", "Nguyễn Trường Giang", ADVISOR_REFS[3]),
)


def parse_lecturer_passwords(raw: str) -> Dict[str, str]:
    """Parse AUTH_LECTURER_SEEDS JSON → username → password."""
    text = (raw or "").strip()
    if not text:
        return {}
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("AUTH_LECTURER_SEEDS must be a JSON array")
    out: Dict[str, str] = {}
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("AUTH_LECTURER_SEEDS items must be objects")
        username = str(item.get("username") or "").strip()
        password = str(item.get("password") or "")
        if not username or not password:
            raise ValueError("each lecturer seed needs username and password")
        out[username] = password
    return out


def _upsert_account(
    db: Session,
    *,
    username: str,
    actor_id: str,
    display_name: str,
    roles: Sequence[str],
    advisor_scope: Optional[str],
    password_hash: str,
    now: datetime,
) -> str:
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
        for existing in list(account.roles):
            db.delete(existing)
        db.flush()

    for role in roles:
        db.add(AuthAccountRole(actor_id=actor_id, role=role))
    return username


def seed_accounts(
    db: Session,
    password: str,
    *,
    lecturer_passwords: Optional[Mapping[str, str]] = None,
) -> list[str]:
    """Upsert core + lecturer seed accounts. Returns usernames touched."""
    if not password:
        raise ValueError("AUTH_SEED_PASSWORD is required (non-empty)")

    now = datetime.now(timezone.utc)
    touched: list[str] = []
    core_hash = hash_password(password)

    for username, actor_id, display_name, roles, advisor_scope in _CORE_SEED_ACCOUNTS:
        touched.append(
            _upsert_account(
                db,
                username=username,
                actor_id=actor_id,
                display_name=display_name,
                roles=roles,
                advisor_scope=advisor_scope,
                password_hash=core_hash,
                now=now,
            )
        )

    lecturer_pw = dict(lecturer_passwords or {})
    for username, actor_id, display_name, advisor_scope in _LECTURER_SEED_ACCOUNTS:
        pw = lecturer_pw.get(username) or password
        touched.append(
            _upsert_account(
                db,
                username=username,
                actor_id=actor_id,
                display_name=display_name,
                roles=("gvcn",),
                advisor_scope=advisor_scope,
                password_hash=hash_password(pw),
                now=now,
            )
        )

    db.commit()
    return touched


def _cmd_seed(_: argparse.Namespace) -> int:
    settings = get_settings()
    password = settings.auth_seed_password.get_secret_value()
    if not password.strip():
        print("ERROR: AUTH_SEED_PASSWORD is empty", file=sys.stderr)
        return 2
    lecturer_raw = settings.auth_lecturer_seeds.get_secret_value()
    try:
        lecturer_passwords = parse_lecturer_passwords(lecturer_raw)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: AUTH_LECTURER_SEEDS invalid: {exc}", file=sys.stderr)
        return 2
    init_schemas()
    db = get_session_factory()()
    try:
        touched = seed_accounts(db, password, lecturer_passwords=lecturer_passwords)
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
