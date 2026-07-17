"""Pydantic contracts — source of truth cho interface giữa các lane (P0.5 H06 / H11a)."""

from app.contracts.coverage import (
    ATTENDANCE_SOURCE_UNAPPROVED,
    Coverage,
    attendance_unapproved_defaults,
)
from app.contracts.integration import (
    ALLOWED_DISPLAY_FIELDS,
    FORBIDDEN_PUBLIC_FIELDS,
    AgentContextResponse,
    CaseDetailResponse,
    CaseListResponse,
    IntegrationProblem,
)
from app.contracts.review_case import ContributingFactor, ReviewCase
from app.contracts.scoring import ScoringFeatures

__all__ = [
    "ALLOWED_DISPLAY_FIELDS",
    "ATTENDANCE_SOURCE_UNAPPROVED",
    "AgentContextResponse",
    "CaseDetailResponse",
    "CaseListResponse",
    "ContributingFactor",
    "Coverage",
    "FORBIDDEN_PUBLIC_FIELDS",
    "IntegrationProblem",
    "ReviewCase",
    "ScoringFeatures",
    "attendance_unapproved_defaults",
]
