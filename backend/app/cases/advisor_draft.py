"""H22 — aggregate approved/assigned cases into advisor handoff draft bundles."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence

from sqlalchemy.orm import Session

from app.cases.domain import CaseState
from app.cases.review_projection import project_review_case, student_ref_from_case_id
from app.cases.store import CaseStore
from app.contracts.advisor_handoff_draft import (
    AdvisorHandoffDraft,
    AdvisorHandoffDraftBundle,
    AdvisorHandoffDraftListResponse,
    HandoffDraftCaseLine,
    MappingRepairBucket,
)
from app.contracts.integration import IntegrationProblem
from app.contracts.normalized import NormalizedStudentRecord
from app.ml.scoring import DEFAULT_THRESHOLDS, ThresholdConfig

ELIGIBLE_STATES = frozenset(
    {
        CaseState.APPROVED_FOR_FOLLOW_UP,
        CaseState.ASSIGNED,
    }
)

_FORBIDDEN_VOCAB = ("bỏ học", "nguy cơ", "rủi ro bỏ học", "điểm rủi ro")

_SUBJECT = "Danh sách sinh viên cần rà soát / theo dõi học vụ"
_FOOTER = "Bản nháp — cần Ban Lãnh đạo duyệt trước khi gửi."
_LIMITATION_NO_CONTACT = "insufficient_contact_map"


def _line_from_projection(
    *,
    case_id: str,
    case_state: str,
    student_ref: str,
    record: Optional[NormalizedStudentRecord],
    store: CaseStore,
    thresholds: ThresholdConfig,
    calculated_at: datetime,
    session: Optional[Session] = None,
) -> HandoffDraftCaseLine:
    band = None
    factor_codes: List[str] = []
    coverage_status = "insufficient"
    coverage_reason_codes: List[str] = []
    class_code = None

    if record is not None:
        class_code = record.class_code
        coverage_status = record.coverage.status
        coverage_reason_codes = list(record.coverage.reason_codes)
        projected = project_review_case(
            record,
            store,
            thresholds=thresholds,
            calculated_at=calculated_at,
            include_below_threshold=True,
            session=session,
        )
        if projected is not None:
            band = projected.review_priority_band
            factor_codes = [f.code for f in projected.contributing_factors[:2]]
            coverage_status = projected.coverage.status
            coverage_reason_codes = list(projected.coverage.reason_codes)
            student_ref = projected.student_ref
            case_id = projected.case_id

    return HandoffDraftCaseLine(
        case_id=case_id,
        student_ref=student_ref,
        review_priority_band=band,
        contributing_factor_codes=factor_codes,
        coverage_status=coverage_status,
        coverage_reason_codes=coverage_reason_codes,
        case_state=case_state,
        class_code=class_code,
    )


def _case_link(base_url: str, case_id: str) -> Optional[str]:
    base = (base_url or "").rstrip("/")
    if not base:
        return None
    # Login-gated deep link to the secured student detail (GVCN scope). The email
    # body stays pseudonymous; the real data lives behind auth at this link.
    return f"{base}/advisor?case={case_id}"


def build_draft_text(
    cases: Sequence[HandoffDraftCaseLine],
    *,
    base_url: str = "",
) -> AdvisorHandoffDraft:
    lines: List[str] = [
        "Kính gửi Thầy/Cô,",
        "",
        "Ban Lãnh đạo gửi danh sách sinh viên cần rà soát / theo dõi học vụ "
        "(bản nháp — chưa gửi tự động):",
        "",
    ]
    for line in cases:
        class_part = f" · lớp {line.class_code}" if line.class_code else ""
        band = line.review_priority_band or "chưa_xác_định"
        factors = ", ".join(line.contributing_factor_codes) if line.contributing_factor_codes else "—"
        lines.append(
            f"- {line.student_ref}{class_part} · mức ưu tiên: {band} · tín hiệu: {factors}"
        )
        link = _case_link(base_url, line.case_id)
        if link:
            lines.append(f"  Xem chi tiết (đăng nhập): {link}")
    if any(_case_link(base_url, c.case_id) for c in cases):
        lines.extend(
            [
                "",
                "Khoa đề nghị Thầy/Cô đăng nhập theo liên kết để xem thông tin sinh viên "
                "và xác nhận tiếp nhận, nhằm hỗ trợ sinh viên kịp thời.",
            ]
        )
    lines.extend(["", _FOOTER])
    body = "\n".join(lines)
    lower = body.lower()
    for token in _FORBIDDEN_VOCAB:
        if token in lower:
            raise ValueError(f"draft vocabulary violated: {token!r}")
    return AdvisorHandoffDraft(subject=_SUBJECT, body=body, requires_human_approval=True)


def build_advisor_handoff_drafts(
    store: CaseStore,
    records_by_ref: Dict[str, NormalizedStudentRecord],
    *,
    thresholds: ThresholdConfig = DEFAULT_THRESHOLDS,
    calculated_at: Optional[datetime] = None,
    session: Optional[Session] = None,
    advisor_names: Optional[Dict[str, str]] = None,
    base_url: str = "",
) -> AdvisorHandoffDraftListResponse:
    """Group eligible CaseStore snapshots by H08 advisor_ref (server-side)."""
    calc_at = calculated_at or datetime.now(timezone.utc)
    by_advisor: Dict[str, List[HandoffDraftCaseLine]] = defaultdict(list)
    repair_lines: List[HandoffDraftCaseLine] = []

    for snap in store.list_snapshots():
        if snap.state not in ELIGIBLE_STATES:
            continue
        student_ref = (snap.student_ref or "").strip() or (
            student_ref_from_case_id(snap.case_id) or ""
        )
        if not student_ref:
            repair_lines.append(
                HandoffDraftCaseLine(
                    case_id=snap.case_id,
                    student_ref="unknown",
                    review_priority_band=None,
                    contributing_factor_codes=[],
                    coverage_status="insufficient",
                    coverage_reason_codes=["missing_student_ref"],
                    case_state=snap.state.value,
                    class_code=None,
                )
            )
            continue

        record = records_by_ref.get(student_ref)
        line = _line_from_projection(
            case_id=snap.case_id,
            case_state=snap.state.value,
            student_ref=student_ref,
            record=record,
            store=store,
            thresholds=thresholds,
            calculated_at=calc_at,
            session=session,
        )

        advisor = None
        mapping_repair = True
        if record is not None:
            mapping_repair = bool(record.mapping_repair)
            advisor = (record.advisor_ref or "").strip() or None

        if mapping_repair or not advisor:
            repair_lines.append(line)
        else:
            by_advisor[advisor].append(line)

    names = advisor_names or {}
    bundles: List[AdvisorHandoffDraftBundle] = []
    for advisor_ref in sorted(by_advisor.keys()):
        cases = by_advisor[advisor_ref]
        bundles.append(
            AdvisorHandoffDraftBundle(
                advisor_ref=advisor_ref,
                advisor_display_name=names.get(advisor_ref),
                case_count=len(cases),
                cases=cases,
                draft=build_draft_text(cases, base_url=base_url),
                limitations=[_LIMITATION_NO_CONTACT],
            )
        )

    repair_limitations = [_LIMITATION_NO_CONTACT, "mapping_repair"]
    mapping_repair = MappingRepairBucket(
        case_count=len(repair_lines),
        cases=repair_lines,
        limitations=repair_limitations if repair_lines else [],
    )

    if not bundles and not repair_lines:
        return AdvisorHandoffDraftListResponse(
            state="empty",
            bundles=[],
            mapping_repair=mapping_repair,
            problem=IntegrationProblem(code="empty", reason_codes=[]),
        )
    return AdvisorHandoffDraftListResponse(
        state="ok",
        bundles=bundles,
        mapping_repair=mapping_repair,
        problem=None,
    )
