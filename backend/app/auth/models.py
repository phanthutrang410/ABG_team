"""H39a — SQLAlchemy models for Postgres schema ``app`` (auth RBAC)."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

APP_SCHEMA = "app"

VALID_ROLE_VALUES = ("ban_quan_ly", "gvcn")


class AppBase(DeclarativeBase):
    metadata = MetaData(schema=APP_SCHEMA)


class AuthAccount(AppBase):
    __tablename__ = "auth_account"

    actor_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    org_scope: Mapped[str] = mapped_column(String(128), nullable=False)
    advisor_scope: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    roles: Mapped[List["AuthAccountRole"]] = relationship(
        "AuthAccountRole", back_populates="account", cascade="all, delete-orphan"
    )
    sessions: Mapped[List["AuthSession"]] = relationship(
        "AuthSession", back_populates="account", cascade="all, delete-orphan"
    )


class AuthAccountRole(AppBase):
    __tablename__ = "auth_account_role"
    __table_args__ = (
        CheckConstraint(
            "role IN ('ban_quan_ly', 'gvcn')",
            name="ck_auth_account_role_valid",
        ),
    )

    actor_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey(f"{APP_SCHEMA}.auth_account.actor_id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(String(32), primary_key=True)

    account: Mapped[AuthAccount] = relationship("AuthAccount", back_populates="roles")


class AuthSession(AppBase):
    __tablename__ = "auth_session"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_auth_session_token_hash"),
        CheckConstraint(
            "active_role IS NULL OR active_role IN ('ban_quan_ly', 'gvcn')",
            name="ck_auth_session_active_role",
        ),
    )

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey(f"{APP_SCHEMA}.auth_account.actor_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    active_role: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    account: Mapped[AuthAccount] = relationship("AuthAccount", back_populates="sessions")


class AccessAuditEventRow(AppBase):
    __tablename__ = "access_audit_event"
    __table_args__ = (
        CheckConstraint(
            "decision IN ('allowed', 'denied')",
            name="ck_access_audit_decision",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_handle: Mapped[str] = mapped_column(String(256), nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
