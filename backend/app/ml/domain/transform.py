"""M06 semester transform — raw student record → domain tables (fail-closed).

Input contract (M06 handoff, không PII): mỗi phần tử `records` là dict:

    {
      "student_ref": "s-0001",              # pseudonym bắt buộc
      "cohort"/"department"/"program"/"major"/"class_code": str | None,
      "status_raw": "Đang học" | None,      # `Trạng thái` gốc (EPU §3.3)
      "status_observed_at": ISO str | None,
      "advisor_ref": "a-01" | None,         # pseudonym cố vấn
      "scope_source": str | None,
      "grades": [
        {"term_code": "HK1 (2022-2023)" | "2022-2023-T1",
         "course_ref": "c-001", "credits": 3, "final_grade": 7.5,
         "grade_status": "passed" | None},
        ...
      ],
    }

Adapter raw-EPU → contract này nằm ngoài M06 (chạy tại vị trí có kiểm soát cùng
file external M05b); logic taxonomy/chuẩn hóa/validate — phần chịu test — ở đây.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app.ml.domain.models import (
    GRADE_MAX,
    GRADE_MIN,
    TERM_MIN_FOR_TREND,
    AcademicStatusRow,
    AdvisorAssignmentRow,
    CoverageReasonCode,
    DataQualityReport,
    DomainSourceManifest,
    DropoutOutcome,
    RejectReason,
    SemesterDataset,
    StudentDimensionRow,
    StudentTermCoverage,
    TermGradeRow,
)

# --- PII / token guard (fail-closed, độc lập với source_gate) --------------
_FORBIDDEN_PII_TOKENS = (
    "ho va ten",
    "ho ten",
    "hoten",
    "hovaten",
    "mssv",
    "ma so sinh vien",
    "ngay sinh",
    "ngaysinh",
    "email",
    "so dien thoai",
    "sodienthoai",
    "dien thoai",
    "sdt",
    "phone",
    "cccd",
    "cmnd",
    "token",
)


def _normalize_key(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", stripped.lower()).strip()


def _forbidden_field_names(*payloads: object) -> List[str]:
    """Union tên field vi phạm PII/token ở mọi cấp dict lồng nhau."""
    found: List[str] = []
    seen: set = set()

    def _scan(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                norm = _normalize_key(str(key))
                if any(tok in norm for tok in _FORBIDDEN_PII_TOKENS) and key not in seen:
                    seen.add(key)
                    found.append(str(key))
                _scan(value)
        elif isinstance(node, list):
            for item in node:
                _scan(item)

    for payload in payloads:
        _scan(payload)
    return found


class PiiFieldError(ValueError):
    """Fail-closed: input M06 chứa field PII/token bị cấm."""


# --- term_code normalization (EPU §3.2) -----------------------------------
_TERM_HK_RE = re.compile(r"^\s*HK\s*([1-3])\s*\(\s*(\d{4})\s*-\s*(\d{4})\s*\)\s*$", re.IGNORECASE)
_TERM_CANONICAL_RE = re.compile(r"^(\d{4})-(\d{4})-T([1-3])$")


def normalize_term_code(raw: object) -> Optional[str]:
    """`HK1 (2022-2023)` → `2022-2023-T1`; canonical giữ nguyên; sai → None."""
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    canonical = _TERM_CANONICAL_RE.match(text)
    if canonical:
        return text
    hk = _TERM_HK_RE.match(text)
    if hk:
        term, start, end = hk.group(1), hk.group(2), hk.group(3)
        return f"{start}-{end}-T{term}"
    return None


# --- Trạng thái taxonomy (decision #17) -----------------------------------
_STATUS_MAP: Dict[str, Tuple[str, DropoutOutcome]] = {
    "thoi hoc": ("thoi_hoc", "true"),
    "buoc thoi hoc": ("buoc_thoi_hoc", "true"),
    "dang hoc": ("dang_hoc", "false"),
    "rut hoc phi": ("rut_hoc_phi", "unknown"),
    "bao luu": ("bao_luu", "unknown"),
}


def map_academic_status(raw: object) -> Tuple[str, DropoutOutcome]:
    """Trả `(status_code, is_dropout_outcome)`; giá trị lạ/thiếu → `(other|—, unknown)`.

    `unknown` KHÔNG gộp vào positive và bị loại khỏi mẫu số evaluation (Data-ML §5).
    """
    if not isinstance(raw, str) or not raw.strip():
        return ("unknown", "unknown")
    return _STATUS_MAP.get(_normalize_key(raw), ("other", "unknown"))


def _grade_in_domain(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and (
        GRADE_MIN <= float(value) <= GRADE_MAX
    )


def _iso(value: object) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return datetime.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def build_semester_dataset(
    records: List[dict],
    *,
    manifest: DomainSourceManifest,
    report_version: str,
    generated_at: datetime,
) -> SemesterDataset:
    """Chuẩn hóa records → 4 bảng domain + quality report (deterministic).

    Fail-closed: field PII/token ⇒ raise ``PiiFieldError`` (zero output). Bản ghi
    điểm thiếu field bắt buộc / term sai / điểm ngoài miền / khóa trùng ⇒ reject
    vào report, không nạp. Output sắp xếp theo khóa để cùng snapshot ⇒ cùng bytes.
    """
    forbidden = _forbidden_field_names(records)
    if forbidden:
        raise PiiFieldError(f"forbidden PII/token fields in M06 input: {sorted(set(forbidden))}")

    source_id = manifest.source_id
    student_dim: Dict[str, StudentDimensionRow] = {}
    academic: Dict[str, AcademicStatusRow] = {}
    advisor: Dict[str, AdvisorAssignmentRow] = {}
    term_rows: Dict[Tuple[str, str, str], TermGradeRow] = {}
    reject_reasons: Dict[str, int] = {}
    reject_count = 0
    n_advisor_missing = 0

    def _reject(reason: RejectReason) -> None:
        nonlocal reject_count
        reject_count += 1
        reject_reasons[reason] = reject_reasons.get(reason, 0) + 1

    for record in records:
        student_ref = record.get("student_ref")
        if not isinstance(student_ref, str) or not student_ref:
            # SV không có pseudonym: toàn bộ bản ghi điểm của record này bị reject.
            for _ in record.get("grades", []) or []:
                _reject("missing_required_field")
            continue

        # student_dimension (một dòng/SV; trùng student_ref → giữ dòng đầu).
        student_dim.setdefault(
            student_ref,
            StudentDimensionRow(
                source_id=source_id,
                student_ref=student_ref,
                cohort=record.get("cohort"),
                department=record.get("department"),
                program=record.get("program"),
                major=record.get("major"),
                class_code=record.get("class_code"),
            ),
        )

        # academic_status (evaluation nội bộ).
        status_code, outcome = map_academic_status(record.get("status_raw"))
        academic.setdefault(
            student_ref,
            AcademicStatusRow(
                source_id=source_id,
                student_ref=student_ref,
                status_code=status_code,
                status_observed_at=_iso(record.get("status_observed_at")),
                is_dropout_outcome=outcome,
            ),
        )

        # advisor_assignment (routing sau approve; thiếu ⇒ mapping-repair ở H08).
        advisor_ref = record.get("advisor_ref")
        if not advisor_ref:
            n_advisor_missing += 1
        advisor.setdefault(
            student_ref,
            AdvisorAssignmentRow(
                source_id=source_id,
                student_ref=student_ref,
                advisor_ref=advisor_ref if isinstance(advisor_ref, str) and advisor_ref else None,
                scope_source=record.get("scope_source"),
            ),
        )

        # term_grade rows.
        for grade in record.get("grades", []) or []:
            term_code = normalize_term_code(grade.get("term_code"))
            course_ref = grade.get("course_ref")
            final_grade = grade.get("final_grade")
            if not isinstance(course_ref, str) or not course_ref or final_grade is None:
                _reject("missing_required_field")
                continue
            if term_code is None:
                _reject("invalid_term_code")
                continue
            if not _grade_in_domain(final_grade):
                _reject("grade_out_of_domain")
                continue
            key = (student_ref, term_code, course_ref)
            if key in term_rows:
                _reject("duplicate_key")
                continue
            credits = grade.get("credits")
            term_rows[key] = TermGradeRow(
                source_id=source_id,
                student_ref=student_ref,
                term_code=term_code,
                course_ref=course_ref,
                credits=float(credits) if isinstance(credits, (int, float))
                and not isinstance(credits, bool) else None,
                final_grade=float(final_grade),
                grade_status=grade.get("grade_status")
                if isinstance(grade.get("grade_status"), str) else None,
            )

    # --- Coverage/reason theo student (Data-ML §2.1/§3) --------------------
    term_coverage: List[StudentTermCoverage] = []
    source_reasons: set = set()
    for student_ref in sorted(student_dim):
        rows = [r for (s, _t, _c), r in term_rows.items() if s == student_ref]
        terms = sorted({r.term_code for r in rows})
        reasons: List[CoverageReasonCode] = []
        if not rows:
            reasons.append("grade_coverage_insufficient")
        elif len(terms) < TERM_MIN_FOR_TREND:
            reasons.append("single_term")
        if academic[student_ref].is_dropout_outcome == "unknown":
            reasons.append("status_unknown")
        source_reasons.update(reasons)
        term_coverage.append(
            StudentTermCoverage(
                student_ref=student_ref,
                n_valid_terms=len(terms),
                n_courses=len(rows),
                last_term_code=terms[-1] if terms else None,
                reason_codes=reasons,
            )
        )

    ordered_terms = sorted(term_rows)
    last_term = ordered_terms[-1][1] if ordered_terms else None

    report = DataQualityReport(
        source_id=source_id,
        report_version=report_version,
        generated_at=generated_at,
        row_count=len(term_rows),
        reject_count=reject_count,
        reject_reasons=dict(sorted(reject_reasons.items())),
        term_coverage=term_coverage,
        missingness={
            "advisor_ref_missing": n_advisor_missing,
            "students_without_valid_grade": sum(
                1 for c in term_coverage if c.n_valid_terms == 0
            ),
        },
        freshness={"last_term_code": last_term, "n_students": len(student_dim)},
        reason_codes=sorted(source_reasons),
    )

    return SemesterDataset(
        source_manifest=manifest,
        student_dimension=[student_dim[s] for s in sorted(student_dim)],
        term_grade=[term_rows[k] for k in ordered_terms],
        academic_status=[academic[s] for s in sorted(academic)],
        advisor_assignment=[advisor[s] for s in sorted(advisor)],
        data_quality_report=report,
    )
