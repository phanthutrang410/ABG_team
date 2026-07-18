"""Serialize / hash / write eval packages under data/eval/."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

from app.ml.eval_synthetic.constants import PROVENANCE_LANE
from app.ml.eval_synthetic.models import EvalPackage


def _json_default(obj: Any) -> Any:
    if hasattr(obj, "isoformat"):
        return obj.isoformat().replace("+00:00", "Z")
    raise TypeError(f"Object of type {type(obj)!r} is not JSON serializable")


def dumps_stable(payload: dict) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    )


def content_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def package_content_hash(package: EvalPackage) -> str:
    """Hash of the full EvalPackage dump (determinism check)."""
    return content_sha256(dumps_stable(package.model_dump(mode="json")))


def write_eval_package(package: EvalPackage, out_dir: Path) -> Dict[str, str]:
    """Write semester_package.json, attendance_package.json, PACKAGE_META.json."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    semester_path = out_dir / "semester_package.json"
    attendance_path = out_dir / "attendance_package.json"
    meta_path = out_dir / "PACKAGE_META.json"

    semester_body = dumps_stable(package.semester.model_dump(mode="json")) + "\n"
    attendance_body = dumps_stable(package.attendance.model_dump(mode="json")) + "\n"
    semester_path.write_text(semester_body, encoding="utf-8")
    attendance_path.write_text(attendance_body, encoding="utf-8")

    sem_sha = content_sha256(semester_body)
    att_sha = content_sha256(attendance_body)
    meta = {
        "dataset_version": package.dataset_version,
        "provenance_lane": package.provenance_lane or PROVENANCE_LANE,
        "source_id": package.semester.source_manifest.source_id,
        "seed": package.seed,
        "n_students": package.n_students,
        "files": {
            "semester_package.json": sem_sha,
            "attendance_package.json": att_sha,
        },
    }
    meta_body = dumps_stable(meta) + "\n"
    meta_path.write_text(meta_body, encoding="utf-8")
    return {
        "semester_package.json": sem_sha,
        "attendance_package.json": att_sha,
        "PACKAGE_META.json": content_sha256(meta_body),
    }
