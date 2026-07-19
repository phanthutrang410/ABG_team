"""Demo overlay: partition 460 students into 4 advisor scopes (115 each).

Does **not** rewrite approved package bytes or ``source_manifest.snapshot_sha256``.
Only updates ``dwh.advisor_assignment`` rows with ``scope_source=demo-class-partition-v1``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dwh.importer import SEMESTER_SOURCE_ID
from app.dwh.models import AdvisorAssignment, SourceManifest, StudentDimension

SCOPE_SOURCE = "demo-class-partition-v1"
EXPECTED_STUDENTS = 460
CHUNK_SIZE = 115

# Stable demo advisor scopes (auth seed + roster RBAC key).
DEMO_ADVISOR_PARTITIONS: Tuple[Tuple[str, str], ...] = (
    ("a-gvcn-duy-01", "Lop-GVCN-Duy"),
    ("a-gvcn-hoang-02", "Lop-GVCN-Hoang"),
    ("a-gvcn-trang-03", "Lop-GVCN-Trang"),
    ("a-gvcn-giang-04", "Lop-GVCN-Giang"),
)

ADVISOR_REFS: Tuple[str, ...] = tuple(ref for ref, _ in DEMO_ADVISOR_PARTITIONS)
ROSTER_LABEL_BY_ADVISOR: Dict[str, str] = {ref: label for ref, label in DEMO_ADVISOR_PARTITIONS}


@dataclass(frozen=True)
class PartitionResult:
    status: str
    source_id: str
    scope_source: str
    counts_by_advisor: Dict[str, int]
    total_students: int
    manifest_sha256: str | None
    reason_codes: Tuple[str, ...]
    detail: str


def roster_class_label(advisor_ref: str) -> str:
    return ROSTER_LABEL_BY_ADVISOR.get(advisor_ref, advisor_ref)


def assign_advisor_chunks(
    student_refs: Sequence[str],
    *,
    chunk_size: int = CHUNK_SIZE,
    partitions: Sequence[Tuple[str, str]] = DEMO_ADVISOR_PARTITIONS,
) -> Dict[str, str]:
    """Map student_ref → advisor_ref for sorted refs (deterministic)."""
    ordered = sorted(student_refs)
    if not ordered:
        return {}
    mapping: Dict[str, str] = {}
    for index, student_ref in enumerate(ordered):
        part_index = min(index // chunk_size, len(partitions) - 1)
        mapping[student_ref] = partitions[part_index][0]
    return mapping


def partition_advisor_assignments(
    session: Session,
    *,
    source_id: str = SEMESTER_SOURCE_ID,
) -> PartitionResult:
    """Idempotent overlay on ``advisor_assignment``; leaves manifest hash untouched."""
    manifest = session.get(SourceManifest, source_id)
    manifest_sha = manifest.snapshot_sha256 if manifest else None

    students = list(
        session.scalars(
            select(StudentDimension.student_ref).where(StudentDimension.source_id == source_id)
        ).all()
    )
    if not students:
        return PartitionResult(
            status="skipped",
            source_id=source_id,
            scope_source=SCOPE_SOURCE,
            counts_by_advisor={},
            total_students=0,
            manifest_sha256=manifest_sha,
            reason_codes=("no_students",),
            detail="no student_dimension rows for source",
        )

    mapping = assign_advisor_chunks(students)
    assignments = list(
        session.scalars(
            select(AdvisorAssignment).where(AdvisorAssignment.source_id == source_id)
        ).all()
    )
    by_student = {row.student_ref: row for row in assignments}

    for student_ref, advisor_ref in mapping.items():
        row = by_student.get(student_ref)
        if row is None:
            session.add(
                AdvisorAssignment(
                    source_id=source_id,
                    student_ref=student_ref,
                    advisor_ref=advisor_ref,
                    scope_source=SCOPE_SOURCE,
                )
            )
        else:
            row.advisor_ref = advisor_ref
            row.scope_source = SCOPE_SOURCE

    session.flush()

    counts: Dict[str, int] = {ref: 0 for ref in ADVISOR_REFS}
    for advisor_ref in mapping.values():
        counts[advisor_ref] = counts.get(advisor_ref, 0) + 1

    # Re-read manifest to prove we did not mutate hash.
    manifest_after = session.get(SourceManifest, source_id)
    sha_after = manifest_after.snapshot_sha256 if manifest_after else None
    if manifest_sha and sha_after and manifest_sha != sha_after:
        return PartitionResult(
            status="error",
            source_id=source_id,
            scope_source=SCOPE_SOURCE,
            counts_by_advisor=counts,
            total_students=len(mapping),
            manifest_sha256=sha_after,
            reason_codes=("manifest_hash_changed",),
            detail="source_manifest.snapshot_sha256 changed unexpectedly",
        )

    reason: List[str] = []
    if len(mapping) != EXPECTED_STUDENTS:
        reason.append("unexpected_student_count")
    for ref in ADVISOR_REFS:
        if counts.get(ref, 0) != CHUNK_SIZE and len(mapping) == EXPECTED_STUDENTS:
            reason.append(f"bad_chunk:{ref}")

    return PartitionResult(
        status="partitioned",
        source_id=source_id,
        scope_source=SCOPE_SOURCE,
        counts_by_advisor=counts,
        total_students=len(mapping),
        manifest_sha256=sha_after or manifest_sha,
        reason_codes=tuple(reason),
        detail="advisor_assignment overlay applied",
    )


def counts_by_advisor(session: Session, *, source_id: str = SEMESTER_SOURCE_ID) -> Mapping[str, int]:
    rows = session.scalars(
        select(AdvisorAssignment).where(AdvisorAssignment.source_id == source_id)
    ).all()
    out: Dict[str, int] = {}
    for row in rows:
        if not row.advisor_ref:
            continue
        out[row.advisor_ref] = out.get(row.advisor_ref, 0) + 1
    return out
