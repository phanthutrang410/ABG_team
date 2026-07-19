"""Reality-460 training dataset loader.

Outcome is joined only inside this offline module.  Runtime ``ScoringFeatures``
continues to exclude outcome/status fields.
"""

from __future__ import annotations

import math
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from app.contracts.normalized import NormalizedTermGrade
from app.dwh.import_gate import evaluate_domain_package, evaluate_snapshot_bytes
from app.dwh.importer import SEMESTER_APPROVAL
from app.ml.domain.models import SemesterDataset
from app.ml.scoring.estimator import (
    compute_failed_credits,
    compute_grade_trend_slope,
    compute_latest_term_gpa,
)

EXPECTED_STUDENTS = 460
EXPECTED_GRADE_ROWS = 3680
EXPECTED_POSITIVES = 46
EXPECTED_NEGATIVES = 414
EXPECTED_LAST_TERM = "2022-2023-T2"


@dataclass(frozen=True)
class TrainingRow:
    student_ref: str
    latest_term_gpa: float
    failed_credits_log1p: float
    grade_trend_slope: float
    outcome: int

    def vector(self, feature_set: str) -> List[float]:
        values = [self.latest_term_gpa, self.failed_credits_log1p]
        if feature_set == "B":
            values.append(self.grade_trend_slope)
        return values


@dataclass(frozen=True)
class TrainingDataset:
    dataset_version: str
    source_snapshot_sha256: str
    training_package_sha256: str
    rows: List[TrainingRow]

    @property
    def labels(self) -> List[int]:
        return [row.outcome for row in self.rows]


def _grade(row: object) -> NormalizedTermGrade:
    return NormalizedTermGrade(
        term_code=row.term_code,
        course_ref=row.course_ref,
        credits=row.credits,
        final_grade=row.final_grade,
        grade_status=row.grade_status,
    )


def load_reality460(path: Path) -> TrainingDataset:
    raw_bytes = path.read_bytes()
    canonical_bytes = raw_bytes.replace(b"\r\n", b"\n")
    package = SemesterDataset.model_validate_json(raw_bytes)
    snapshot_gate = evaluate_snapshot_bytes(
        canonical_bytes,
        SEMESTER_APPROVAL,
        observed_record_count=len(package.student_dimension),
    )
    if not snapshot_gate.admitted:
        raise ValueError(f"training_package_gate_failed:{','.join(snapshot_gate.reason_codes)}")
    domain_gate = evaluate_domain_package(
        package.model_dump(mode="json"),
        source_id=SEMESTER_APPROVAL.source_id,
        role="primary",
    )
    if not domain_gate.admitted:
        raise ValueError(f"training_domain_gate_failed:{','.join(domain_gate.reason_codes)}")
    manifest = package.source_manifest
    if manifest.source_id != "v59-empty-program-students":
        raise ValueError("unexpected_training_source")
    if not manifest.provenance_approved:
        raise ValueError("training_source_unapproved")
    if len(package.student_dimension) != EXPECTED_STUDENTS:
        raise ValueError("unexpected_student_count")
    if len(package.term_grade) != EXPECTED_GRADE_ROWS:
        raise ValueError("unexpected_grade_row_count")

    dims = {row.student_ref: row for row in package.student_dimension}
    if len(dims) != EXPECTED_STUDENTS:
        raise ValueError("duplicate_student_ref")

    grades_by_ref: Dict[str, List[NormalizedTermGrade]] = {}
    for row in package.term_grade:
        if row.source_id != manifest.source_id or row.student_ref not in dims:
            raise ValueError("grade_source_or_student_mismatch")
        grades_by_ref.setdefault(row.student_ref, []).append(_grade(row))

    outcomes: Dict[str, int] = {}
    for row in package.academic_status:
        if row.source_id != manifest.source_id or row.student_ref not in dims:
            raise ValueError("outcome_source_or_student_mismatch")
        if row.is_dropout_outcome == "unknown":
            raise ValueError("unknown_outcome_not_allowed")
        if row.status_code not in {"dang_hoc", "thoi_hoc", "buoc_thoi_hoc"}:
            raise ValueError("unsupported_status_taxonomy")
        outcomes[row.student_ref] = 1 if row.is_dropout_outcome == "true" else 0
    if len(outcomes) != EXPECTED_STUDENTS:
        raise ValueError("missing_or_duplicate_outcomes")
    positives = sum(outcomes.values())
    if positives != EXPECTED_POSITIVES or len(outcomes) - positives != EXPECTED_NEGATIVES:
        raise ValueError("unexpected_label_distribution")

    training_rows: List[TrainingRow] = []
    for student_ref in sorted(dims):
        grades = grades_by_ref.get(student_ref, [])
        terms = sorted({grade.term_code for grade in grades if grade.final_grade is not None})
        if len(terms) != 2 or terms[-1] != EXPECTED_LAST_TERM:
            raise ValueError("two_term_cutoff_gate_failed")
        latest = compute_latest_term_gpa(grades)
        failed = compute_failed_credits(grades)
        trend = compute_grade_trend_slope(grades)
        if latest is None or failed is None or trend is None:
            raise ValueError("required_feature_missing")
        training_rows.append(
            TrainingRow(
                student_ref=student_ref,
                latest_term_gpa=float(latest),
                failed_credits_log1p=math.log1p(float(failed)),
                grade_trend_slope=float(trend),
                outcome=outcomes[student_ref],
            )
        )

    return TrainingDataset(
        dataset_version=(
            f"{manifest.source_id}:{SEMESTER_APPROVAL.normalized_sha256[:8]}:"
            f"{manifest.schema_version}"
        ),
        source_snapshot_sha256=manifest.snapshot_sha256,
        training_package_sha256=hashlib.sha256(canonical_bytes).hexdigest(),
        rows=training_rows,
    )
