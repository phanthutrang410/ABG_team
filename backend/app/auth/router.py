"""H39a — /auth/login|me|active-role|logout (cookie session)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session, joinedload

from app.auth.models import AuthAccount, AuthSession
from app.auth.passwords import verify_password
from app.auth.principal import (
    SESSION_COOKIE,
    SESSION_TTL_SECONDS,
    VALID_ROLES,
    Principal,
    cookie_secure,
    get_principal,
    principal_from_session,
)
from app.auth.session_tokens import generate_session_token, hash_session_token
from app.config import Settings, get_settings
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class ActiveRoleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str = Field(min_length=1, max_length=32)


class MeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    display_name: str
    roles: List[str]
    active_role: Optional[str]


class LoginResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    display_name: str
    roles: List[str]
    active_role: Optional[str]


def _set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        secure=cookie_secure(settings),
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )


def _clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/",
        httponly=True,
        samesite="lax",
        secure=cookie_secure(settings),
    )


def _me_from_principal(principal: Principal) -> MeResponse:
    return MeResponse(
        account_id=principal.actor_id,
        display_name=principal.display_name,
        roles=list(principal.roles),
        active_role=principal.active_role,
    )


@router.post("/login", response_model=LoginResponse)
def login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    username = body.username.strip()
    account = (
        db.query(AuthAccount)
        .options(joinedload(AuthAccount.roles))
        .filter(AuthAccount.username == username)
        .one_or_none()
    )
    if account is None or not verify_password(account.password_hash, body.password):
        raise HTTPException(
            status_code=401,
            detail={"code": "invalid_credentials", "message": "invalid username or password"},
        )
    if not account.is_active:
        raise HTTPException(
            status_code=403,
            detail={"code": "account_disabled", "message": "account is disabled"},
        )

    role_codes = sorted(r.role for r in account.roles)
    if not role_codes:
        raise HTTPException(
            status_code=403,
            detail={"code": "no_roles", "message": "account has no roles"},
        )

    active_role: Optional[str] = role_codes[0] if len(role_codes) == 1 else None
    if active_role == "gvcn" and not (account.advisor_scope or "").strip():
        raise HTTPException(
            status_code=403,
            detail={
                "code": "missing_advisor_scope",
                "message": "gvcn role requires advisor_scope on account",
            },
        )

    raw_token = generate_session_token()
    now = datetime.now(timezone.utc)
    session_row = AuthSession(
        session_id=uuid.uuid4().hex,
        actor_id=account.actor_id,
        token_hash=hash_session_token(raw_token),
        active_role=active_role,
        expires_at=now + timedelta(seconds=SESSION_TTL_SECONDS),
        revoked_at=None,
        created_at=now,
    )
    db.add(session_row)
    db.commit()
    db.refresh(session_row)
    # Ensure relationship for principal_from_session
    session_row.account = account

    _set_session_cookie(response, raw_token, settings)
    principal = principal_from_session(session_row)
    return LoginResponse(
        account_id=principal.actor_id,
        display_name=principal.display_name,
        roles=list(principal.roles),
        active_role=principal.active_role,
    )


@router.get("/me", response_model=MeResponse)
def me(principal: Principal = Depends(get_principal)) -> MeResponse:
    return _me_from_principal(principal)


@router.post("/active-role", response_model=MeResponse)
def set_active_role(
    body: ActiveRoleRequest,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
) -> MeResponse:
    role = body.role.strip().lower()
    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=403,
            detail={"code": "unknown_role", "message": "role not in canonical set"},
        )
    if role not in principal.roles:
        raise HTTPException(
            status_code=403,
            detail={"code": "role_not_permitted", "message": "role not assigned to account"},
        )
    if role == "gvcn" and not (principal.advisor_scope or "").strip():
        raise HTTPException(
            status_code=403,
            detail={
                "code": "missing_advisor_scope",
                "message": "gvcn role requires advisor_scope on account",
            },
        )
    if not principal.session_id:
        raise HTTPException(
            status_code=401,
            detail={"code": "invalid_session", "message": "session not found"},
        )

    row = db.query(AuthSession).filter(AuthSession.session_id == principal.session_id).one_or_none()
    if row is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "invalid_session", "message": "session not found"},
        )
    row.active_role = role
    db.commit()

    return MeResponse(
        account_id=principal.actor_id,
        display_name=principal.display_name,
        roles=list(principal.roles),
        active_role=role,
    )


@router.post("/logout", status_code=204, response_model=None)
def logout(
    response: Response,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> None:
    if principal.session_id:
        row = (
            db.query(AuthSession)
            .filter(AuthSession.session_id == principal.session_id)
            .one_or_none()
        )
        if row is not None and row.revoked_at is None:
            row.revoked_at = datetime.now(timezone.utc)
            db.commit()
    _clear_session_cookie(response, settings)
