"""H35 — advisor draft v2 on durable approved/assigned episodes (server scope only).

Migrates H22's draft-only aggregation (``app.cases.advisor_draft``) onto the
durable ``CaseRepository`` episode ledger (H33a) behind H36 RBAC. Same
boundaries as H22 (Process handoff / Ethics §4):

- Only ``approved``/``assigned`` episodes are ever eligible — pending,
  dismissed, monitoring and resolved episodes never appear here.
- ``can_access_case`` (server-side only, from the resolved ``Principal``)
  gates every episode before it can land in either a bundle or the
  mapping-repair bucket; cross-scope episodes are dropped silently, never
  exposed via an "exists but denied" signal.
- The output envelope carries a pseudonymous ``student_ref`` and case
  metadata only — no email/phone/name field exists anywhere in this module.
- ``requires_human_approval`` is always ``True`` and there is no send
  function/route in this module (Ethics §4 — human decides and sends).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Sequence

from app.auth.principal import Principal
from app.auth.scope import can_access_case
from app.weekly.cases_durable import CaseEpisode, CaseRepository

#: Process §4 durable-episode states eligible for an advisor handoff draft.
ELIGIBLE_STATES = frozenset({"approved", "assigned"})

_FORBIDDEN_VOCAB = ("bỏ học", "nguy cơ", "rủi ro bỏ học", "điểm rủi ro")
_INTRO_VI = (
    "Ban Lãnh đạo gửi danh sách case cần rà soát / theo dõi học vụ "
    "(bản nháp — chưa gửi tự động):"
)
_FOOTER_VI = "Bản nháp — cần Ban Lãnh đạo duyệt trước khi gửi. Không tự động gửi."
_MAPPING_REPAIR_LIMITATION = "mapping_repair"


@dataclass(frozen=True)
class AdvisorDraftV2CaseLine:
    """Draft preview line — pseudonym ``student_ref`` only, no name/email/phone."""

    episode_id: str
    student_ref: str
    branch: str
    case_state: str


@dataclass(frozen=True)
class AdvisorDraftV2Bundle:
    """One advisor's draft bundle — preview text only, never sent from here."""

    advisor_ref: str
    case_count: int
    cases: List[AdvisorDraftV2CaseLine]
    draft_preview_vi: str
    requires_human_approval: Literal[True] = True


@dataclass(frozen=True)
class MappingRepairBucketV2:
    """Episodes with no resolvable advisor — cannot be grouped/drafted yet."""

    case_count: int
    cases: List[AdvisorDraftV2CaseLine]
    limitations: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class AdvisorDraftV2Response:
    """Server-scoped envelope for one report/run — draft-only, no send route."""

    report_id: str
    state: Literal["ok", "empty"]
    bundles: List[AdvisorDraftV2Bundle]
    mapping_repair: MappingRepairBucketV2


def _line(episode: CaseEpisode) -> AdvisorDraftV2CaseLine:
    return AdvisorDraftV2CaseLine(
        episode_id=episode.episode_id,
        student_ref=episode.student_ref,
        branch=episode.branch,
        case_state=episode.state,
    )


def build_draft_preview_vi(cases: Sequence[AdvisorDraftV2CaseLine]) -> str:
    """Deterministic no-send preview text — same forbidden-vocabulary gate as H22."""
    lines: List[str] = ["Kính gửi Thầy/Cô,", "", _INTRO_VI, ""]
    for line in cases:
        lines.append(f"- {line.student_ref} · nhánh {line.branch} · trạng thái {line.case_state}")
    lines.extend(["", _FOOTER_VI])
    body = "\n".join(lines)
    lowered = body.lower()
    for token in _FORBIDDEN_VOCAB:
        if token in lowered:
            raise ValueError(f"draft vocabulary violated: {token!r}")
    return body


def build_advisor_drafts_v2(
    repo: CaseRepository,
    report_id: str,
    principal: Principal,
    *,
    branch: Optional[str] = None,
) -> AdvisorDraftV2Response:
    """Group server-scoped approved/assigned episodes by ``advisor_ref``.

    Only episodes ``principal`` may access (``can_access_case``, server-side
    only — never a client-supplied org/advisor field) are ever bundled or
    surfaced via ``mapping_repair``; cross-scope episodes are dropped before
    grouping, so their existence is never implied by the response.
    """
    episodes = repo.list_active(branch=branch)
    by_advisor: Dict[str, List[AdvisorDraftV2CaseLine]] = defaultdict(list)
    repair_lines: List[AdvisorDraftV2CaseLine] = []

    for episode in episodes:
        if episode.state not in ELIGIBLE_STATES:
            continue
        if not can_access_case(principal, episode.advisor_ref, episode.org_scope or ""):
            continue

        line = _line(episode)
        advisor = (episode.advisor_ref or "").strip()
        if not advisor or episode.mapping_repair_queued:
            repair_lines.append(line)
        else:
            by_advisor[advisor].append(line)

    bundles: List[AdvisorDraftV2Bundle] = []
    for advisor_ref in sorted(by_advisor.keys()):
        cases = by_advisor[advisor_ref]
        bundles.append(
            AdvisorDraftV2Bundle(
                advisor_ref=advisor_ref,
                case_count=len(cases),
                cases=cases,
                draft_preview_vi=build_draft_preview_vi(cases),
            )
        )

    mapping_repair = MappingRepairBucketV2(
        case_count=len(repair_lines),
        cases=repair_lines,
        limitations=[_MAPPING_REPAIR_LIMITATION] if repair_lines else [],
    )

    state: Literal["ok", "empty"] = "ok" if (bundles or repair_lines) else "empty"
    return AdvisorDraftV2Response(
        report_id=report_id,
        state=state,
        bundles=bundles,
        mapping_repair=mapping_repair,
    )
