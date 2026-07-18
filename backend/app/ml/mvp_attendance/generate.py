"""Generate MVP linked attendance (decision #27) — session grain, ≥12 events/SV."""

from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

ATTENDANCE_SOURCE_ID = "mvp-attendance-over-time"
SCHEMA_VERSION = "epu-1"
DEFAULT_SEED = 42
EXTRACTED_AT = datetime(2026, 7, 18, 12, 0, 0, tzinfo=timezone.utc)
#: Target sessions per student (session = one course meeting).
SESSIONS_PER_STUDENT = 16
COURSES_PER_STUDENT = 3
SESSIONS_PER_COURSE = 6  # 3×6 = 18; trim to SESSIONS_PER_STUDENT


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _latest_term_courses(
    grades: Sequence[dict],
) -> Tuple[str | None, List[str]]:
    by_term: Dict[str, List[str]] = defaultdict(list)
    for g in grades:
        term = g.get("term_code")
        course = g.get("course_ref")
        if isinstance(term, str) and isinstance(course, str) and course:
            by_term[term].append(course)
    if not by_term:
        return None, []
    latest = max(by_term)
    # Stable unique course list
    seen = sorted(set(by_term[latest]))
    return latest, seen


def _fail_ratio(grades: Sequence[dict]) -> float:
    if not grades:
        return 0.0
    fails = 0
    for g in grades:
        status = (g.get("grade_status") or "").strip().casefold()
        if status == "không đạt":
            fails += 1
    return fails / len(grades)


def build_attendance_payload(
    domain_package: dict,
    *,
    seed: int = DEFAULT_SEED,
) -> dict:
    """Build `{source_id, schema_version, events}` covering all semester students."""
    dims = domain_package.get("student_dimension") or []
    grades = domain_package.get("term_grade") or []
    grades_by: Dict[str, List[dict]] = defaultdict(list)
    for g in grades:
        ref = g.get("student_ref")
        if isinstance(ref, str):
            grades_by[ref].append(g)

    rng = random.Random(seed)
    events: List[dict] = []

    for dim in sorted(dims, key=lambda d: d.get("student_ref") or ""):
        ref = dim.get("student_ref")
        if not isinstance(ref, str) or not ref:
            continue
        student_grades = grades_by.get(ref, [])
        _term, courses = _latest_term_courses(student_grades)
        if not courses:
            courses = [f"c-att-{ref[-6:]}-{i}" for i in range(COURSES_PER_STUDENT)]
        pick = courses[:COURSES_PER_STUDENT]
        while len(pick) < COURSES_PER_STUDENT:
            pick.append(f"c-att-{ref[-6:]}-{len(pick)}")

        risk = _fail_ratio(student_grades)
        present_p = max(0.35, min(0.95, 0.92 - 0.55 * risk))

        # Spread sessions across ~80 days ending at EXTRACTED_AT.
        session_specs: List[Tuple[str, datetime]] = []
        day_cursor = 3
        for course_i, course_ref in enumerate(pick):
            for s in range(SESSIONS_PER_COURSE):
                # Unique timestamp: different day + course-specific hour.
                days_ago = 8 + day_cursor + s * 4 + course_i
                hour = 7 + course_i * 2
                observed = EXTRACTED_AT - timedelta(days=days_ago, hours=(12 - hour))
                # Normalize to timezone-aware datetime with distinct time-of-day
                observed = observed.replace(hour=hour, minute=15 + s, second=0, microsecond=0)
                session_specs.append((course_ref, observed))
            day_cursor += 1

        # Keep most recent SESSIONS_PER_STUDENT sessions
        session_specs.sort(key=lambda x: x[1])
        session_specs = session_specs[-SESSIONS_PER_STUDENT:]

        for course_ref, observed in session_specs:
            excused = False
            if rng.random() < 0.04:
                excused = True
                presence = "absent"
            elif rng.random() < present_p:
                presence = "present"
            else:
                presence = "absent"
            row: Dict[str, Any] = {
                "student_ref": ref,
                "observed_at": observed.isoformat().replace("+00:00", "Z"),
                "presence_status": presence,
                "course_ref": course_ref,
            }
            if excused:
                row["excused"] = True
            else:
                row["excused"] = False
            events.append(row)

    events.sort(key=lambda e: (e["student_ref"], e["observed_at"], e["course_ref"]))
    return {
        "source_id": ATTENDANCE_SOURCE_ID,
        "schema_version": SCHEMA_VERSION,
        "events": events,
    }


def write_attendance_package(
    payload: dict,
    *,
    out_dir: Path | None = None,
) -> Dict[str, str]:
    """Write over_time JSON + manifest + DQR sidecar; return sha256 + counts."""
    out_dir = out_dir or (_repo_root() / "data" / "approved" / "attendance")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "mvp_attendance_over_time.json"
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    raw = body.encode("utf-8")
    sha = _sha256_bytes(raw)
    path.write_bytes(raw)

    n_events = len(payload.get("events") or [])
    n_students = len({e["student_ref"] for e in payload.get("events") or []})
    manifest = {
        "source_id": ATTENDANCE_SOURCE_ID,
        "snapshot_sha256": sha,
        "provenance_approved": True,
        "schema_version": SCHEMA_VERSION,
        "record_count": n_events,
        "extracted_at": EXTRACTED_AT.isoformat().replace("+00:00", "Z"),
        "n_students": n_students,
        "grain": "session",
        "linked_semester_source_id": "v59-empty-program-students",
    }
    (out_dir / "mvp_attendance_source_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    dqr = {
        "source_id": ATTENDANCE_SOURCE_ID,
        "report_version": "h15b-linked-1",
        "generated_at": EXTRACTED_AT.isoformat().replace("+00:00", "Z"),
        "row_count": n_events,
        "reject_count": 0,
        "n_students": n_students,
        "min_events_per_student": SESSIONS_PER_STUDENT,
        "freshness": {"extracted_at": EXTRACTED_AT.isoformat().replace("+00:00", "Z")},
    }
    (out_dir / "mvp_attendance_data_quality_report.json").write_text(
        json.dumps(dqr, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "sha256": sha,
        "n_events": str(n_events),
        "n_students": str(n_students),
        "path": str(path),
    }
