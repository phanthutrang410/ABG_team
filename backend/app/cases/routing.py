"""H03 — resolve advisor_ref from H08 for assign (never trust client)."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.cases.domain import CaseSnapshot
from app.dwh.read_adapter import ReadAdapterError, get_normalized_student


def resolve_advisor_for_assign(session: Session, case: CaseSnapshot) -> Optional[str]:
    """Return H08 advisor_ref for assign, or None → mapping-repair stop.

    Missing case identity, missing/unapproved snapshot, mapping_repair, or empty
    advisor_ref all fail closed (caller queues mapping-repair).
    """
    student_ref = (case.student_ref or "").strip()
    source_id = (case.source_id or "").strip()
    if not student_ref or not source_id:
        return None
    try:
        record = get_normalized_student(session, source_id, student_ref)
    except ReadAdapterError:
        return None
    if record is None:
        return None
    if record.mapping_repair:
        return None
    advisor = (record.advisor_ref or "").strip()
    return advisor or None
