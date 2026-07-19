"""Build scoped advisor roster from DWH + optional care case overlay."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.principal import Principal
from app.auth.rbac import DEFAULT_CASE_ORG_SCOPE, principal_can_view_care_case
from app.cases.store import CaseStorePort
from app.contracts.advisor_roster import (
    AdvisorRosterClass,
    AdvisorRosterResponse,
    AdvisorRosterStudent,
)
from app.dwh.importer import SEMESTER_SOURCE_ID
from app.dwh.models import AdvisorAssignment, StudentDimension
from app.dwh.partition_demo import roster_class_label


def build_advisor_roster(
    session: Session,
    principal: Principal,
    store: CaseStorePort,
    *,
    source_id: str = SEMESTER_SOURCE_ID,
) -> AdvisorRosterResponse:
    role = principal.active_role
    if role not in ("gvcn", "ban_quan_ly"):
        return AdvisorRosterResponse(
            state="error",
            classes=[],
            problem={"code": "forbidden_role", "message": "roster requires gvcn or ban_quan_ly"},
        )

    if role == "gvcn" and not (principal.advisor_scope or "").strip():
        return AdvisorRosterResponse(
            state="error",
            classes=[],
            problem={"code": "missing_advisor_scope", "message": "gvcn requires advisor_scope"},
        )

    stmt = (
        select(
            StudentDimension.student_ref,
            StudentDimension.class_code,
            StudentDimension.cohort,
            AdvisorAssignment.advisor_ref,
        )
        .join(
            AdvisorAssignment,
            (AdvisorAssignment.source_id == StudentDimension.source_id)
            & (AdvisorAssignment.student_ref == StudentDimension.student_ref),
        )
        .where(StudentDimension.source_id == source_id)
    )
    if role == "gvcn":
        stmt = stmt.where(AdvisorAssignment.advisor_ref == principal.advisor_scope)

    rows = session.execute(stmt).all()
    if not rows:
        return AdvisorRosterResponse(state="empty", classes=[])

    case_by_student: Dict[str, Tuple[str, Optional[str]]] = {}
    for snap in store.list_snapshots():
        if not snap.student_ref:
            continue
        if not principal_can_view_care_case(
            principal,
            case_advisor_ref=snap.advisor_ref,
            case_state=snap.state,
            case_org=DEFAULT_CASE_ORG_SCOPE,
        ):
            continue
        case_by_student[snap.student_ref] = (snap.case_id, snap.state)

    buckets: Dict[str, List[AdvisorRosterStudent]] = {}
    for student_ref, class_code, cohort, advisor_ref in rows:
        if not advisor_ref:
            continue
        label = roster_class_label(advisor_ref)
        case_id, case_state = case_by_student.get(student_ref, (None, None))
        buckets.setdefault(label, []).append(
            AdvisorRosterStudent(
                student_ref=student_ref,
                class_code=class_code,
                cohort=cohort,
                case_id=case_id,
                case_state=case_state,
            )
        )

    classes: List[AdvisorRosterClass] = []
    for label in sorted(buckets.keys()):
        students = sorted(buckets[label], key=lambda s: s.student_ref)
        classes.append(
            AdvisorRosterClass(
                roster_class_label=label,
                student_count=len(students),
                students=students,
            )
        )

    if not classes:
        return AdvisorRosterResponse(state="empty", classes=[])
    return AdvisorRosterResponse(state="ok", classes=classes)
