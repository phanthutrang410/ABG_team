"""Deterministic generator for ml-eval-feature-complete packages.

Program mix (khoa/ngành/lớp) is sampled from weights derived from the approved
EPU/M06 `domain_package.json` catalog — not inventing a single fake faculty.
"""

from __future__ import annotations

import hashlib
import random
from datetime import timedelta
from typing import Dict, List, Tuple

from app.ml.domain.models import (
    ATTENDANCE_MIN_EVENTS,
    AcademicStatusRow,
    AdvisorAssignmentRow,
    AttendanceDataset,
    AttendanceEventRow,
    DataQualityReport,
    DomainSourceManifest,
    SemesterDataset,
    StudentAttendanceCoverage,
    StudentDimensionRow,
    StudentTermCoverage,
    TermGradeRow,
)
from app.ml.eval_synthetic.catalog import (
    course_bank_for_major,
    load_program_catalog,
    pick_terms,
    weighted_programs,
)
from app.ml.eval_synthetic.constants import (
    ADVISORS_PER_DEPT,
    ATTENDANCE_EVENT_COUNT,
    DEFAULT_SEED,
    EXTRACTED_AT,
    PROVENANCE_LANE,
    REPORT_VERSION,
    RISK_FRACTION,
    SCHEMA_VERSION,
    SOURCE_ID,
)
from app.ml.eval_synthetic.models import EvalPackage


def _dataset_version(seed: int, n: int) -> str:
    return f"ml-eval-feature-complete-v1-seed{seed}-n{n}"


def _placeholder_sha(seed: int, n: int, role: str) -> str:
    raw = f"{SOURCE_ID}:{role}:{seed}:{n}:{PROVENANCE_LANE}".encode()
    return hashlib.sha256(raw).hexdigest()


def _grade_status_for(score: float, force_fail: bool) -> str:
    if force_fail or score < 4.0:
        return "Không đạt"
    if score >= 8.5:
        return "[A - ]"
    if score >= 7.0:
        return "[B - ]"
    if score >= 5.5:
        return "[C - ]"
    return "[D - ]"


def _advisor_for(department: str, rng: random.Random) -> str:
    dept_key = hashlib.sha256(department.encode("utf-8")).hexdigest()[:6]
    slot = rng.randrange(ADVISORS_PER_DEPT)
    return f"adv-{dept_key}-{slot:02d}"


def _class_code(seed_code: str, cohort: str, index: int, rng: random.Random) -> str:
    """Expand observed class seeds into multiple sections for large n."""
    section = rng.randint(1, 8)
    if seed_code:
        return f"{seed_code}-S{section:02d}"
    return f"K{cohort[-2:]}-EVAL-A{section:02d}-{index % 99:02d}"


def generate_eval_package(*, n: int = 12, seed: int = DEFAULT_SEED) -> EvalPackage:
    """Build a linked semester+attendance eval package (decision #26)."""
    if n < 1:
        raise ValueError("n must be >= 1")

    catalog = load_program_catalog()
    programs, weights = weighted_programs()
    terms_template = list(catalog.get("terms_template") or [])
    courses_per_term = int(catalog.get("courses_per_term") or 5)
    bank_size = int(catalog.get("course_bank_size_per_major") or 20)

    rng_students = random.Random(seed)
    rng_grades = random.Random(seed + 1)
    rng_att = random.Random(seed + 2)
    rng_outcome = random.Random(seed + 3)

    # Cache course banks per major for stability within a run.
    banks: Dict[str, List[dict]] = {}

    student_dimension: List[StudentDimensionRow] = []
    term_grade: List[TermGradeRow] = []
    academic_status: List[AcademicStatusRow] = []
    advisor_assignment: List[AdvisorAssignmentRow] = []
    attendance_event: List[AttendanceEventRow] = []
    term_coverage: List[StudentTermCoverage] = []
    att_coverage: List[StudentAttendanceCoverage] = []

    width = max(4, len(str(n - 1)))

    for i in range(n):
        student_ref = f"s-eval-{i:0{width}d}"
        is_risk = rng_students.random() < RISK_FRACTION
        prog = rng_students.choices(programs, weights=weights, k=1)[0]
        department = prog["department"]
        program = prog["program"]
        major = prog["major"]
        cohort = str(prog.get("cohort") or "2022")
        class_code = _class_code(prog.get("class_code_seed") or "", cohort, i, rng_students)

        student_dimension.append(
            StudentDimensionRow(
                source_id=SOURCE_ID,
                student_ref=student_ref,
                cohort=cohort,
                department=department,
                program=program,
                major=major,
                class_code=class_code,
            )
        )
        advisor_assignment.append(
            AdvisorAssignmentRow(
                source_id=SOURCE_ID,
                student_ref=student_ref,
                advisor_ref=_advisor_for(department, rng_students),
                scope_source="eval_lane",
            )
        )

        drop_p = 0.35 if is_risk else 0.05
        is_drop = rng_outcome.random() < drop_p
        academic_status.append(
            AcademicStatusRow(
                source_id=SOURCE_ID,
                student_ref=student_ref,
                status_code="buoc_thoi_hoc" if is_drop else "dang_hoc",
                status_observed_at=None,
                is_dropout_outcome="true" if is_drop else "false",
            )
        )

        if major not in banks:
            banks[major] = course_bank_for_major(major, size=bank_size)
        bank = banks[major]

        # 2–4 terms from EPU-like template (richer than smoke-only 2).
        n_terms = 2 if rng_grades.random() < 0.35 else (3 if rng_grades.random() < 0.5 else 4)
        terms = pick_terms(n_terms, terms_template)
        n_courses = 0
        for term_idx, term_code in enumerate(terms):
            if is_risk:
                base = 4.8 - term_idx * 0.55
            else:
                base = 7.0 + term_idx * 0.12
            # Distinct courses from bank for this term.
            start = (term_idx * courses_per_term) % max(1, bank_size - courses_per_term + 1)
            term_courses = bank[start : start + courses_per_term]
            if len(term_courses) < courses_per_term:
                term_courses = bank[:courses_per_term]
            force_fail_slot = rng_grades.randrange(len(term_courses)) if is_risk else -1
            for c_idx, course in enumerate(term_courses):
                credits = float(course["credits"])
                noise = rng_grades.uniform(-1.2, 1.2)
                score = max(0.0, min(10.0, round(base + noise, 2)))
                force_fail = is_risk and c_idx == force_fail_slot
                if force_fail:
                    score = round(rng_grades.uniform(1.0, 3.5), 2)
                status = _grade_status_for(score, force_fail=force_fail)
                term_grade.append(
                    TermGradeRow(
                        source_id=SOURCE_ID,
                        student_ref=student_ref,
                        term_code=term_code,
                        course_ref=course["course_ref"],
                        credits=credits,
                        final_grade=score,
                        grade_status=status,
                    )
                )
                n_courses += 1

        term_coverage.append(
            StudentTermCoverage(
                student_ref=student_ref,
                n_valid_terms=len(terms),
                n_courses=n_courses,
                last_term_code=terms[-1],
                reason_codes=[],
            )
        )

        course_ref = bank[i % len(bank)]["course_ref"]
        present_target = 0.45 if is_risk else 0.9
        last_at = None
        n_present = 0
        n_excused = 0
        for w in range(ATTENDANCE_EVENT_COUNT):
            observed = EXTRACTED_AT - timedelta(days=12 * (ATTENDANCE_EVENT_COUNT - w))
            excused = False
            if rng_att.random() < 0.05:
                excused = True
                n_excused += 1
                presence = "absent"
            elif rng_att.random() < present_target:
                presence = "present"
                n_present += 1
            else:
                presence = "absent"
            attendance_event.append(
                AttendanceEventRow(
                    source_id=SOURCE_ID,
                    student_ref=student_ref,
                    observed_at=observed,
                    course_ref=course_ref,
                    presence_status=presence,
                    excused=excused if excused else False,
                )
            )
            last_at = observed

        n_events = ATTENDANCE_EVENT_COUNT
        counted = n_events - n_excused
        rate = round(n_present / counted, 6) if counted else None
        att_coverage.append(
            StudentAttendanceCoverage(
                student_ref=student_ref,
                n_attendance_events=n_events,
                n_counted_events=counted,
                n_excused=n_excused,
                attendance_rate_window=rate,
                last_attendance_at=last_at,
                trend_eligible=n_events >= ATTENDANCE_MIN_EVENTS,
                reason_codes=[],
            )
        )

    semester_manifest = DomainSourceManifest(
        source_id=SOURCE_ID,
        snapshot_sha256=_placeholder_sha(seed, n, "semester"),
        provenance_approved=True,
        schema_version=SCHEMA_VERSION,
        record_count=len(student_dimension),
        extracted_at=EXTRACTED_AT,
    )
    attendance_manifest = DomainSourceManifest(
        source_id=SOURCE_ID,
        snapshot_sha256=_placeholder_sha(seed, n, "attendance"),
        provenance_approved=True,
        schema_version=SCHEMA_VERSION,
        record_count=len(attendance_event),
        extracted_at=EXTRACTED_AT,
    )

    semester_dqr = DataQualityReport(
        source_id=SOURCE_ID,
        report_version=REPORT_VERSION,
        generated_at=EXTRACTED_AT,
        row_count=len(term_grade),
        reject_count=0,
        reject_reasons={},
        missingness={},
        term_coverage=term_coverage,
        attendance_coverage=[],
        freshness={"extracted_at": EXTRACTED_AT.isoformat().replace("+00:00", "Z")},
        reason_codes=[],
    )
    attendance_dqr = DataQualityReport(
        source_id=SOURCE_ID,
        report_version=REPORT_VERSION,
        generated_at=EXTRACTED_AT,
        row_count=len(attendance_event),
        reject_count=0,
        reject_reasons={},
        missingness={},
        term_coverage=[],
        attendance_coverage=att_coverage,
        freshness={"extracted_at": EXTRACTED_AT.isoformat().replace("+00:00", "Z")},
        reason_codes=[],
    )

    semester = SemesterDataset(
        source_manifest=semester_manifest,
        student_dimension=student_dimension,
        term_grade=term_grade,
        academic_status=academic_status,
        advisor_assignment=advisor_assignment,
        data_quality_report=semester_dqr,
    )
    attendance = AttendanceDataset(
        source_manifest=attendance_manifest,
        attendance_event=attendance_event,
        data_quality_report=attendance_dqr,
    )
    return EvalPackage(
        dataset_version=_dataset_version(seed, n),
        provenance_lane=PROVENANCE_LANE,
        seed=seed,
        n_students=n,
        semester=semester,
        attendance=attendance,
    )


def risk_branch_stats(package: EvalPackage) -> Tuple[int, int]:
    from collections import defaultdict

    fails: dict[str, float] = defaultdict(float)
    for g in package.semester.term_grade:
        if g.grade_status and g.grade_status.strip().casefold() == "không đạt":
            if g.credits and g.credits > 0:
                fails[g.student_ref] += g.credits
    n_risk = sum(1 for v in fails.values() if v > 0)
    return n_risk, package.n_students
