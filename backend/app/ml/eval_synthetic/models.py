"""EvalPackage envelope wrapping M06 semester + attendance datasets."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.ml.domain.models import AttendanceDataset, SemesterDataset
from app.ml.eval_synthetic.constants import PROVENANCE_LANE


class EvalPackage(BaseModel):
    """Linked eval-only package (same student_ref across branches)."""

    model_config = ConfigDict(extra="forbid")

    dataset_version: str = Field(min_length=1)
    provenance_lane: str = Field(default=PROVENANCE_LANE, min_length=1)
    seed: int
    n_students: int = Field(ge=1)
    semester: SemesterDataset
    attendance: AttendanceDataset
