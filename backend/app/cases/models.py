"""SQLAlchemy models for durable care CaseStore (``app.review_case`` / ``case_event``)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import APP_SCHEMA, AppBase


class CareReviewCase(AppBase):
    __tablename__ = "review_case"

    case_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    state: Mapped[str] = mapped_column(String(64), nullable=False)
    student_ref: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    advisor_ref: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    review_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reason_code: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    monitoring_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    mapping_repair_queued: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class CareCaseEvent(AppBase):
    __tablename__ = "case_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey(f"{APP_SCHEMA}.review_case.case_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="human")
    action: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    from_state: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    to_state: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    detail_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
