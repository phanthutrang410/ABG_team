"""H22 — AdvisorHandoffDraftBundle public envelope (FR-12).

Exception vs H11a: `advisor_ref` is allowed here as pseudonym routing only.
Still forbids PII, scores, outcomes, and audit-group attrs.
Semantics: docs/04-engineering/11-advisor-batch-mail-draft.md.
"""

from __future__ import annotations

from typing import FrozenSet, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.contracts.integration import FORBIDDEN_PUBLIC_FIELDS, IntegrationProblem

#: H22 forbid list = H11a public forbids minus advisor_ref (routing exception).
FORBIDDEN_HANDOFF_DRAFT_FIELDS: FrozenSet[str] = frozenset(
    k for k in FORBIDDEN_PUBLIC_FIELDS if k != "advisor_ref"
)

HandoffDraftListState = Literal["ok", "empty", "error"]


class HandoffDraftCaseLine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    student_ref: str = Field(min_length=1)
    review_priority_band: Optional[Literal["uu_tien_som", "can_ra_soat"]] = None
    contributing_factor_codes: List[str] = Field(default_factory=list)
    coverage_status: str = Field(min_length=1)
    coverage_reason_codes: List[str] = Field(default_factory=list)
    case_state: str = Field(min_length=1)
    class_code: Optional[str] = None


class AdvisorHandoffDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)
    requires_human_approval: Literal[True] = True


class AdvisorHandoffDraftBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    advisor_ref: str = Field(min_length=1)
    case_count: int = Field(ge=0)
    cases: List[HandoffDraftCaseLine] = Field(default_factory=list)
    draft: AdvisorHandoffDraft
    limitations: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _counts_match(self) -> "AdvisorHandoffDraftBundle":
        if self.case_count != len(self.cases):
            raise ValueError("case_count must equal len(cases)")
        if self.draft.requires_human_approval is not True:
            raise ValueError("requires_human_approval must be true")
        return self


class MappingRepairBucket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_count: int = Field(ge=0)
    cases: List[HandoffDraftCaseLine] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _counts_match(self) -> "MappingRepairBucket":
        if self.case_count != len(self.cases):
            raise ValueError("case_count must equal len(cases)")
        return self


class AdvisorHandoffDraftListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: HandoffDraftListState
    bundles: List[AdvisorHandoffDraftBundle] = Field(default_factory=list)
    mapping_repair: MappingRepairBucket = Field(
        default_factory=lambda: MappingRepairBucket(case_count=0, cases=[], limitations=[])
    )
    problem: Optional[IntegrationProblem] = None


def assert_no_handoff_forbidden_keys(payload: object, *, path: str = "$") -> None:
    """Recursively reject H22-forbidden field names (allows advisor_ref)."""
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in FORBIDDEN_HANDOFF_DRAFT_FIELDS:
                raise ValueError(f"forbidden handoff field {key!r} at {path}")
            assert_no_handoff_forbidden_keys(value, path=f"{path}.{key}")
    elif isinstance(payload, list):
        for i, item in enumerate(payload):
            assert_no_handoff_forbidden_keys(item, path=f"{path}[{i}]")
