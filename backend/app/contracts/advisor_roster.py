"""Public contract for GET /advisor/roster (pseudonymous student list)."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AdvisorRosterStudent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_ref: str
    class_code: Optional[str] = None
    cohort: Optional[str] = None
    case_id: Optional[str] = None
    case_state: Optional[str] = None


class AdvisorRosterClass(BaseModel):
    model_config = ConfigDict(extra="forbid")

    roster_class_label: str
    student_count: int = Field(ge=0)
    students: List[AdvisorRosterStudent]


class AdvisorRosterResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Literal["ok", "empty", "error"]
    classes: List[AdvisorRosterClass] = Field(default_factory=list)
    problem: Optional[dict] = None
