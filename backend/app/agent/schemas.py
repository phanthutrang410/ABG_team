"""Agent I/O contract for the Silent Shield explanation agent (task T03).

Consumer contract built ON TOP of Hoàng's H06a/H11a envelopes — this module
defines only the agent's OUTPUT side (Thu Trang's lane). The INPUT side is
imported verbatim from ``app.contracts.integration`` (source of truth):

- input:  ``AgentContextResponse`` — safe, RBAC-filtered projection. Public
  case carries NO model_score/PII/is_dropout_outcome/audit attrs (H06a).
- output: ``AgentExplanation`` (here) — grounded answer, refusal, or
  fail-closed ``insufficient_data`` / ``unavailable``.

Boundaries (Problems Brief D.1/D.6, PRD §5.4 FR-08, Ethics §8, RULES §3):

- The agent only explains model/API output it was given. It never computes,
  edits, or invents scores; never diagnoses; never speculates about protected
  or personal causes; never transitions a case; never sends anything itself.
- Answers must separate facts (``grounded_facts``), model output
  (``model_factors_used`` — factor *codes* from the case), and limitations.
- Low coverage → fail closed: silence-with-reason, never "ổn định".
"""

from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.contracts.integration import AgentContextResponse, AgentIntent

DEFAULT_DISCLAIMER_VI = (
    "Đây là tín hiệu cần rà soát nhằm hỗ trợ con người ưu tiên sự quan tâm, "
    "không phải kết luận về sinh viên. Quyết định và việc liên hệ do con người thực hiện."
)


class AgentCommand(BaseModel):
    """Public HTTP command body (H23/H24) — browser must not send context.

    Only ``intent`` / ``question`` / ``locale``. Server builds AgentContextResponse.
    """

    model_config = ConfigDict(extra="forbid")

    intent: AgentIntent
    question: str = Field(
        min_length=1,
        max_length=500,
        description="Reviewer question (local policy only; not sent raw to provider)",
    )
    locale: Literal["vi"] = "vi"

    @field_validator("question", mode="before")
    @classmethod
    def _trim_question(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class AgentExplanationRequest(BaseModel):
    """Library input to the explanation agent (T02/H25).

    ``context`` is Hoàng's H11a envelope, passed through unchanged — the agent
    must not widen it, query around it, or fall back when it is not ready.
    Keep this shape for library callers; HTTP uses ``AgentCommand`` + server context.
    """

    model_config = ConfigDict(extra="forbid")

    context: AgentContextResponse
    question: str = Field(min_length=1, description="Reviewer question, vd. 'Vì sao case này cần rà soát?'")
    intent: AgentIntent = "explain_case"
    locale: str = "vi"


class ExplanationStatus(str, Enum):
    """Output status. Mirrors the context outcomes the agent may surface."""

    OK = "ok"
    INSUFFICIENT_DATA = "insufficient_data"
    REFUSED = "refused"
    UNAVAILABLE = "unavailable"


class RefusalReason(str, Enum):
    """Machine-readable agent-side refusal codes (PRD §5.4, Ethics §8).

    These are OUTPUT reason codes for the agent's own guardrails; upstream
    (context-level) refusals arrive as ``IntegrationProblem.reason_codes``.
    """

    INVENT_SCORE = "invent_or_compute_score"
    DIAGNOSE_HEALTH = "diagnose_mental_health"
    SPECULATE_CAUSE = "speculate_protected_or_personal_cause"
    DECIDE_ACTION = "decide_contact_discipline_or_status"
    AUTO_SEND = "auto_send_or_notify"
    OUT_OF_SCOPE_DATA = "access_data_out_of_scope"
    REVEAL_RAW_SCORE = "reveal_raw_score_or_weights"


class GroundedFact(BaseModel):
    """One claim tied to its source so facts stay separable from opinion.

    Ethics §8: answers must distinguish dữ kiện / output model / giới hạn.
    ``ref`` points at a contributing-factor ``code``, an ``evidence_ref``
    (vd. ``term_avg:20251``) or a coverage field — never at raw DWH rows.
    """

    model_config = ConfigDict(extra="forbid")

    statement_vi: str = Field(min_length=1)
    source: Literal["model_factor", "coverage", "case_field"]
    ref: Optional[str] = None


class DraftMessage(BaseModel):
    """Neutral outreach draft (warm check-in). NEVER sent by the agent.

    Ethics §4 / Process §3 step 10–11: agent drafts, human approves and sends.
    Copy must not diagnose, conclude, or mention risk/score.
    """

    model_config = ConfigDict(extra="forbid")

    body_vi: str = Field(min_length=1)
    requires_human_approval: bool = Field(default=True)
    channel: Optional[str] = None


class AgentExplanation(BaseModel):
    """Output of the explanation agent."""

    model_config = ConfigDict(extra="forbid")

    status: ExplanationStatus
    answer_vi: str = Field(min_length=1)
    grounded_facts: List[GroundedFact] = Field(default_factory=list)
    model_factors_used: List[str] = Field(
        default_factory=list,
        description="Factor codes taken verbatim from case.contributing_factors[].code",
    )
    limitation_keys: List[str] = Field(
        default_factory=list,
        description="Machine/copy keys mirrored from case.limitations (H12a maps to VI)",
    )
    limitations_vi: str = ""
    refusal_reason: Optional[RefusalReason] = None
    draft_message: Optional[DraftMessage] = None
    model_version: Optional[str] = Field(
        default=None, description="Echoed from case.model_version; null when no case"
    )
    disclaimer_vi: str = DEFAULT_DISCLAIMER_VI

    @model_validator(mode="after")
    def _check_invariants(self) -> "AgentExplanation":
        if self.status is ExplanationStatus.REFUSED and self.refusal_reason is None:
            raise ValueError("refused status requires a refusal_reason")
        if self.status is not ExplanationStatus.REFUSED and self.refusal_reason is not None:
            raise ValueError("refusal_reason must be null unless status is 'refused'")
        if self.draft_message is not None:
            if self.status is not ExplanationStatus.OK:
                raise ValueError("draft_message only allowed when status is 'ok'")
            if not self.draft_message.requires_human_approval:
                raise ValueError("draft_message.requires_human_approval must always be True")
        if self.status is ExplanationStatus.OK and self.model_version is None:
            raise ValueError("status=ok requires model_version echoed from the case")
        if self.status is ExplanationStatus.UNAVAILABLE and (
            self.grounded_facts or self.model_factors_used or self.draft_message
        ):
            raise ValueError(
                "status=unavailable must carry no facts/factors/draft — "
                "no data was accessible, nothing may be invented"
            )
        return self
