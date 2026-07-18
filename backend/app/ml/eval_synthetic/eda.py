"""EDA / descriptive stats for an EvalPackage (M09)."""

from __future__ import annotations

import statistics
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.ml.eval_synthetic.load import outcomes_from_package, records_from_package
from app.ml.eval_synthetic.models import EvalPackage
from app.ml.scoring import score_student


def _safe_mean(values: List[float]) -> float | None:
    return round(statistics.mean(values), 4) if values else None


def _safe_stdev(values: List[float]) -> float | None:
    return round(statistics.pstdev(values), 4) if len(values) >= 2 else None


def summarize_eval_package(package: EvalPackage) -> Dict[str, Any]:
    """Return JSON-serializable EDA summary for smoke/full eval packages."""
    records = records_from_package(package)
    outcomes = outcomes_from_package(package)
    calc_at = datetime(2026, 7, 18, tzinfo=timezone.utc)

    gpas: List[float] = []
    vols: List[float] = []
    fails: List[float] = []
    rates: List[float] = []
    trends: List[float] = []
    fail_positive = 0
    status_counts = Counter(
        row.is_dropout_outcome for row in package.semester.academic_status
    )
    grade_status_counts = Counter(
        (g.grade_status or "").strip() for g in package.semester.term_grade
    )
    presence_counts = Counter(
        (e.presence_status or "null") for e in package.attendance.attendance_event
    )
    dept_counts = Counter(d.department for d in package.semester.student_dimension)
    major_counts = Counter(d.major for d in package.semester.student_dimension)
    term_counts = Counter(g.term_code for g in package.semester.term_grade)
    course_n = len({g.course_ref for g in package.semester.term_grade})
    class_n = len({d.class_code for d in package.semester.student_dimension})
    advisor_n = len({a.advisor_ref for a in package.semester.advisor_assignment})

    for record in records:
        f = score_student(record, calculated_at=calc_at)
        if f.latest_term_gpa is not None:
            gpas.append(f.latest_term_gpa)
        if f.grade_volatility is not None:
            vols.append(f.grade_volatility)
        if f.failed_credits is not None:
            fails.append(f.failed_credits)
            if f.failed_credits > 0:
                fail_positive += 1
        if f.attendance_rate_window is not None:
            rates.append(f.attendance_rate_window)
        if f.grade_trend_slope is not None:
            trends.append(f.grade_trend_slope)

    n = package.n_students
    return {
        "dataset_version": package.dataset_version,
        "provenance_lane": package.provenance_lane,
        "n_students": n,
        "n_term_grade_rows": len(package.semester.term_grade),
        "n_attendance_events": len(package.attendance.attendance_event),
        "n_departments": len(dept_counts),
        "n_majors": len(major_counts),
        "n_class_codes": class_n,
        "n_unique_courses": course_n,
        "n_advisors": advisor_n,
        "department_top": dept_counts.most_common(15),
        "major_top": major_counts.most_common(15),
        "term_counts": dict(term_counts),
        "outcome_counts": dict(status_counts),
        "grade_status_top": grade_status_counts.most_common(8),
        "presence_counts": dict(presence_counts),
        "features": {
            "latest_term_gpa": {
                "n": len(gpas),
                "mean": _safe_mean(gpas),
                "stdev": _safe_stdev(gpas),
                "min": round(min(gpas), 4) if gpas else None,
                "max": round(max(gpas), 4) if gpas else None,
            },
            "grade_trend_slope": {
                "n": len(trends),
                "mean": _safe_mean(trends),
                "stdev": _safe_stdev(trends),
            },
            "grade_volatility": {
                "n": len(vols),
                "mean": _safe_mean(vols),
                "stdev": _safe_stdev(vols),
            },
            "failed_credits": {
                "n": len(fails),
                "mean": _safe_mean(fails),
                "stdev": _safe_stdev(fails),
                "pct_positive": round(100.0 * fail_positive / n, 2) if n else 0.0,
            },
            "attendance_rate_window": {
                "n": len(rates),
                "mean": _safe_mean(rates),
                "stdev": _safe_stdev(rates),
                "min": round(min(rates), 4) if rates else None,
                "max": round(max(rates), 4) if rates else None,
            },
        },
        "outcome_positive_rate": round(100.0 * status_counts.get("true", 0) / n, 2)
        if n
        else 0.0,
        "labeled_outcomes": sum(1 for v in outcomes.values() if v is not None),
    }
