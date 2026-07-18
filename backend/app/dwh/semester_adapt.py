"""Adapt approved raw V59-shaped semester export → M06 `build_semester_dataset` records.

Runs only in the controlled import environment. Pseudonyms are deterministic hashes
of source identifiers; the MSSV↔student_ref map is never written to disk/git.
PII field names are stripped before the domain transform (EPU §3.4).
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional


def _pseudo(prefix: str, value: str) -> str:
    digest = hashlib.sha256(f"silent-shield|{prefix}|{value}".encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:12]}"


def _as_float(value: object) -> Optional[float]:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace(",", ".")
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def _course_ref(grade: dict) -> str:
    raw = grade.get("Mã lớp") or grade.get("Tên môn học") or ""
    if not isinstance(raw, str) or not raw.strip():
        return ""
    # Stable pseudonym for course section codes (may embed identifiable patterns).
    cleaned = re.sub(r"\s+", "", raw.strip())
    return _pseudo("c", cleaned)


def adapt_v59_records(raw_records: List[dict]) -> List[dict]:
    """Map raw V59 list → M06 semester records (pseudonymous, no PII keys)."""
    out: List[dict] = []
    for item in raw_records:
        if not isinstance(item, dict):
            continue
        info = item.get("student_info")
        if not isinstance(info, dict):
            continue
        mssv = info.get("MSSV")
        if not isinstance(mssv, str) or not mssv.strip():
            continue
        student_ref = _pseudo("s", mssv.strip())

        advisor_raw = info.get("Cố vấn học tập")
        advisor_ref = (
            _pseudo("a", advisor_raw.strip())
            if isinstance(advisor_raw, str) and advisor_raw.strip()
            else None
        )

        grades_out: List[Dict[str, Any]] = []
        for grade in item.get("grades") or []:
            if not isinstance(grade, dict):
                continue
            course_ref = _course_ref(grade)
            final_grade = _as_float(grade.get("Điểm tổng kết"))
            term_code = grade.get("Học kỳ")
            if not course_ref or final_grade is None or not isinstance(term_code, str):
                # Keep a stub so M06 can reject with the correct reason code.
                grades_out.append(
                    {
                        "term_code": term_code if isinstance(term_code, str) else None,
                        "course_ref": course_ref or None,
                        "credits": _as_float(grade.get("TC")),
                        "final_grade": final_grade,
                        "grade_status": grade.get("Ghi chú")
                        if isinstance(grade.get("Ghi chú"), str)
                        else None,
                    }
                )
                continue
            grades_out.append(
                {
                    "term_code": term_code,
                    "course_ref": course_ref,
                    "credits": _as_float(grade.get("TC")),
                    "final_grade": final_grade,
                    "grade_status": grade.get("Ghi chú")
                    if isinstance(grade.get("Ghi chú"), str) and grade.get("Ghi chú")
                    else (
                        grade.get("Xếp loại")
                        if isinstance(grade.get("Xếp loại"), str)
                        else None
                    ),
                }
            )

        out.append(
            {
                "student_ref": student_ref,
                "cohort": info.get("Khóa") if isinstance(info.get("Khóa"), str) else None,
                "department": info.get("Khoa") if isinstance(info.get("Khoa"), str) else None,
                "program": info.get("Ngành") if isinstance(info.get("Ngành"), str) else None,
                "major": (
                    info.get("Chuyên ngành")
                    if isinstance(info.get("Chuyên ngành"), str)
                    else (info.get("Ngành") if isinstance(info.get("Ngành"), str) else None)
                ),
                "class_code": info.get("Lớp") if isinstance(info.get("Lớp"), str) else None,
                "status_raw": info.get("Trạng thái")
                if isinstance(info.get("Trạng thái"), str)
                else None,
                "status_observed_at": None,
                "advisor_ref": advisor_ref,
                "scope_source": "v59-empty-program-students",
                "grades": grades_out,
            }
        )
    return out
