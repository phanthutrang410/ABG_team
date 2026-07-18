"""Load eval packages into NormalizedStudentRecord (linked join — eval lane only)."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.contracts.coverage import Coverage
from app.contracts.normalized import (
    NormalizedAttendanceEvent,
    NormalizedStudentRecord,
    NormalizedTermGrade,
)
from app.ml.domain.models import AttendanceDataset, SemesterDataset
from app.ml.domain.models import ATTENDANCE_MIN_EVENTS, TERM_MIN_FOR_TREND
from app.ml.eval_synthetic.constants import SCHEMA_VERSION, SOURCE_ID
from app.ml.eval_synthetic.models import EvalPackage


def _coverage_for(
    term_grades: List[NormalizedTermGrade],
    events: List[NormalizedAttendanceEvent],
) -> Coverage:
    terms = sorted({g.term_code for g in term_grades if g.final_grade is not None})
    n_courses = sum(1 for g in term_grades if g.final_grade is not None)
    n_att = sum(1 for e in events if e.presence_status is not None)
    last_att = max((e.observed_at for e in events), default=None)
    reasons: list = []
    if len(terms) == 0 and n_att < ATTENDANCE_MIN_EVENTS:
        status = "insufficient"
        reasons.append("grade_coverage_insufficient")
        if n_att < ATTENDANCE_MIN_EVENTS:
            reasons.append("attendance_coverage_insufficient")
    elif len(terms) < TERM_MIN_FOR_TREND or n_att < ATTENDANCE_MIN_EVENTS:
        status = "partial"
        if 0 < len(terms) < TERM_MIN_FOR_TREND:
            reasons.append("single_term")
        if 0 < n_att < ATTENDANCE_MIN_EVENTS:
            reasons.append("attendance_coverage_insufficient")
    else:
        status = "ok"
    return Coverage(
        n_valid_terms=len(terms),
        n_courses=n_courses,
        n_attendance_events=n_att,
        last_term_code=terms[-1] if terms else None,
        last_attendance_at=last_att,
        status=status,
        reason_codes=reasons,
    )


def records_from_package(package: EvalPackage) -> List[NormalizedStudentRecord]:
    """Join semester + attendance on student_ref (eval carve-out only)."""
    dim_by_ref = {d.student_ref: d for d in package.semester.student_dimension}
    advisor_by_ref = {a.student_ref: a for a in package.semester.advisor_assignment}
    grades_by: Dict[str, List[NormalizedTermGrade]] = defaultdict(list)
    for g in package.semester.term_grade:
        grades_by[g.student_ref].append(
            NormalizedTermGrade(
                term_code=g.term_code,
                course_ref=g.course_ref,
                credits=g.credits,
                final_grade=g.final_grade,
                grade_status=g.grade_status,
            )
        )
    events_by: Dict[str, List[NormalizedAttendanceEvent]] = defaultdict(list)
    for e in package.attendance.attendance_event:
        events_by[e.student_ref].append(
            NormalizedAttendanceEvent(
                observed_at=e.observed_at,
                course_ref=e.course_ref,
                presence_status=e.presence_status,
                excused=e.excused,
            )
        )

    sha = package.semester.source_manifest.snapshot_sha256
    records: List[NormalizedStudentRecord] = []
    for ref in sorted(dim_by_ref):
        dim = dim_by_ref[ref]
        grades = grades_by.get(ref, [])
        events = events_by.get(ref, [])
        adv = advisor_by_ref.get(ref)
        records.append(
            NormalizedStudentRecord(
                student_ref=ref,
                source_id=SOURCE_ID,
                dataset_version=package.dataset_version,
                schema_version=SCHEMA_VERSION,
                snapshot_sha256=sha,
                provenance_approved=True,
                cohort=dim.cohort,
                department=dim.department,
                program=dim.program,
                major=dim.major,
                class_code=dim.class_code,
                term_grades=grades,
                attendance_events=events,
                advisor_ref=adv.advisor_ref if adv else None,
                mapping_repair=False,
                coverage=_coverage_for(grades, events),
            )
        )
    return records


def outcomes_from_package(package: EvalPackage) -> Dict[str, Optional[bool]]:
    """Map student_ref → dropout label (True/False/None for unknown). Eval only."""
    out: Dict[str, Optional[bool]] = {}
    for row in package.semester.academic_status:
        if row.is_dropout_outcome == "true":
            out[row.student_ref] = True
        elif row.is_dropout_outcome == "false":
            out[row.student_ref] = False
        else:
            out[row.student_ref] = None
    return out


def load_eval_dir(path: Path) -> Tuple[EvalPackage, List[NormalizedStudentRecord]]:
    """Load semester_package.json + attendance_package.json + PACKAGE_META.json."""
    path = Path(path)
    semester = SemesterDataset.model_validate(
        json.loads((path / "semester_package.json").read_text(encoding="utf-8"))
    )
    attendance = AttendanceDataset.model_validate(
        json.loads((path / "attendance_package.json").read_text(encoding="utf-8"))
    )
    meta = json.loads((path / "PACKAGE_META.json").read_text(encoding="utf-8"))
    package = EvalPackage(
        dataset_version=meta["dataset_version"],
        provenance_lane=meta.get("provenance_lane", "ml-eval-synthetic"),
        seed=int(meta["seed"]),
        n_students=int(meta["n_students"]),
        semester=semester,
        attendance=attendance,
    )
    return package, records_from_package(package)
