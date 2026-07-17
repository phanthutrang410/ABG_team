"""FE / Agent integration envelopes (H11a).

Semantics: docs/04-engineering/10-fe-agent-integration-contract.md.
Builds on H06a ReviewCase — does not widen the public field set.
"""

from __future__ import annotations

from typing import FrozenSet, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.contracts.review_case import ReviewCase

#: Public + agent display allowlist — mirrors ReviewCase fields (H06a).
ALLOWED_DISPLAY_FIELDS: FrozenSet[str] = frozenset(ReviewCase.model_fields.keys())

#: Must never appear on list/detail/agent fixtures or responses.
FORBIDDEN_PUBLIC_FIELDS: FrozenSet[str] = frozenset(
    {
        "model_score",
        "risk_score",
        "raw_score",
        "probability",
        "weight",
        "weights",
        "is_dropout_outcome",
        "advisor_ref",
        "mssv",
        "student_id",
        "full_name",
        "name",
        "date_of_birth",
        "email",
        "phone",
        "phone_number",
        "token",
        "ethnicity",
        "socioeconomic_status",
        "protected_group",
        "audit_group",
    }
)

ProblemCode = Literal[
    "not_found",
    "unauthorized",
    "validation_error",
    "upstream_unavailable",
    "stale_snapshot",
    "insufficient_data",
    "empty",
    "refused",
]

ListState = Literal["ok", "empty", "stale", "error"]
DetailState = Literal["ok", "empty", "stale", "insufficient_data", "error"]
Freshness = Literal["fresh", "stale"]
AgentStatus = Literal[
    "ready", "empty", "insufficient_data", "refused", "unavailable"
]
AgentIntent = Literal["explain_case", "neutral_draft"]


class IntegrationProblem(BaseModel):
    """Machine-readable problem — no long Vietnamese prose (H12a owns copy)."""

    model_config = ConfigDict(extra="forbid")

    code: ProblemCode
    reason_codes: List[str] = Field(default_factory=list)
    message_key: Optional[str] = None


class CaseListResponse(BaseModel):
    """Public list envelope for G05 / future H02."""

    model_config = ConfigDict(extra="forbid")

    items: List[ReviewCase] = Field(default_factory=list)
    state: ListState
    problem: Optional[IntegrationProblem] = None

    @model_validator(mode="after")
    def _consistent(self) -> "CaseListResponse":
        if self.state == "ok" and not self.items:
            raise ValueError("state=ok đòi hỏi items không rỗng")
        if self.state == "empty" and self.items:
            raise ValueError("state=empty đòi hỏi items=[]")
        if self.state == "error":
            if self.items:
                raise ValueError("state=error đòi hỏi items=[]")
            if self.problem is None:
                raise ValueError("state=error đòi hỏi problem")
        if self.state == "stale" and self.problem is None:
            # Allow stale without problem, but recommend stale_snapshot — enforce code if present.
            pass
        if self.problem is not None and self.problem.code in FORBIDDEN_PUBLIC_FIELDS:
            raise ValueError("problem.code không hợp lệ")
        return self


class CaseDetailResponse(BaseModel):
    """Public detail envelope for G05 / future H02."""

    model_config = ConfigDict(extra="forbid")

    case: Optional[ReviewCase] = None
    state: DetailState
    freshness: Freshness = "fresh"
    problem: Optional[IntegrationProblem] = None

    @model_validator(mode="after")
    def _consistent(self) -> "CaseDetailResponse":
        if self.state == "ok":
            if self.case is None:
                raise ValueError("state=ok đòi hỏi case")
            if self.freshness != "fresh":
                raise ValueError("state=ok đòi hỏi freshness=fresh")
        if self.state == "empty" and self.case is not None:
            raise ValueError("state=empty đòi hỏi case=null")
        if self.state == "error":
            if self.case is not None:
                raise ValueError("state=error đòi hỏi case=null")
            if self.problem is None:
                raise ValueError("state=error đòi hỏi problem")
        if self.state == "stale":
            if self.case is None:
                raise ValueError("state=stale đòi hỏi case")
            if self.freshness != "stale":
                raise ValueError("state=stale đòi hỏi freshness=stale")
        if self.state == "insufficient_data":
            if self.case is not None and self.case.data_state != "insufficient_data":
                raise ValueError(
                    "state=insufficient_data với case đòi hỏi data_state=insufficient_data"
                )
            if self.case is None and self.problem is None:
                raise ValueError(
                    "state=insufficient_data không có case đòi hỏi problem"
                )
        return self


class AgentContextResponse(BaseModel):
    """Safe agent context for T03 — same ReviewCase allowlist, no transitions."""

    model_config = ConfigDict(extra="forbid")

    status: AgentStatus
    case: Optional[ReviewCase] = None
    problem: Optional[IntegrationProblem] = None
    allowed_intents: List[AgentIntent] = Field(
        default_factory=lambda: ["explain_case", "neutral_draft"]
    )

    @model_validator(mode="after")
    def _consistent(self) -> "AgentContextResponse":
        if self.status == "ready":
            if self.case is None:
                raise ValueError("status=ready đòi hỏi case")
            if self.problem is not None:
                raise ValueError("status=ready không kèm problem")
        if self.status in ("empty", "refused", "unavailable"):
            if self.case is not None:
                raise ValueError(f"status={self.status} đòi hỏi case=null")
            if self.status == "refused" and self.problem is None:
                raise ValueError("status=refused đòi hỏi problem")
            if self.status == "unavailable" and self.problem is None:
                raise ValueError("status=unavailable đòi hỏi problem")
        if self.status == "insufficient_data":
            if self.case is not None and self.case.data_state not in (
                "insufficient_data",
                "partial",
            ):
                raise ValueError(
                    "agent insufficient_data chỉ cho phép case data_state "
                    "insufficient_data|partial"
                )
            if self.case is None and self.problem is None:
                raise ValueError(
                    "status=insufficient_data không có case đòi hỏi problem"
                )
        return self


def assert_no_forbidden_keys(payload: object, *, path: str = "$") -> None:
    """Recursively reject forbidden public field names in decoded JSON-like trees."""
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in FORBIDDEN_PUBLIC_FIELDS:
                raise ValueError(f"forbidden field {key!r} at {path}")
            assert_no_forbidden_keys(value, path=f"{path}.{key}")
    elif isinstance(payload, list):
        for i, item in enumerate(payload):
            assert_no_forbidden_keys(item, path=f"{path}[{i}]")
