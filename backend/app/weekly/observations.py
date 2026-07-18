"""H32 — Mode B linked-bundle adapter → immutable signal observations.

Decision #23 item 2: there is no approved canonical linked namespace yet, so
semester and attendance stay in separate branches (Mode B). A `"combined"`
branch request must fail loudly instead of falling back to a heuristic
cross-source join on `student_ref`.

Each observation is immutable output for one `(snapshot_id, student_ref,
branch)`; it never carries `model_score`, PII, or `is_dropout_outcome` —
only the same public-safe projection fields as `ReviewCase`
(`review_priority_band` + factor codes + coverage).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.dwh.models import DatasetSnapshot
from app.dwh.read_adapter import ReadAdapterError, list_normalized_students
from app.ml.scoring import (
    DEFAULT_THRESHOLDS,
    MODEL_VERSION,
    ThresholdConfig,
    band_for_score,
    compute_model_score,
    contributing_factors,
    score_student,
)
from app.ml.source_gate.gate import SOURCE_ALLOWLIST

#: Mode B branch -> expected `app.ml.source_gate.gate.SOURCE_ALLOWLIST` role.
#: No `"combined"` entry — see `build_observations_mode_b`.
BRANCH_ROLES: Dict[str, str] = {"semester": "primary", "attendance": "attendance"}


class NamespaceMismatchError(ValueError):
    """Resolved `source_id` role does not match the requested branch."""


@dataclass(frozen=True)
class SignalObservation:
    """Immutable H32 output for one student/branch/run — not a public envelope."""

    snapshot_id: str
    student_ref: str
    branch: str
    review_priority_band: Optional[str]
    factor_codes: List[str] = field(default_factory=list)
    coverage_status: str = "insufficient"
    extracted_at: Optional[datetime] = None
    evidence_fingerprint: str = ""
    model_version: str = MODEL_VERSION

    @property
    def eligible(self) -> bool:
        """Data-ML §3 eligibility: a ready branch produced a band (H28a §7.1)."""
        return self.coverage_status != "insufficient" and self.review_priority_band is not None


def evidence_fingerprint(
    *,
    student_ref: str,
    branch: str,
    review_priority_band: Optional[str],
    factor_codes: List[str],
    coverage_status: str,
) -> str:
    """Deterministic sha256 over the signal-identity fields only.

    Excludes `snapshot_id`/`extracted_at` on purpose: those change every run
    even when the signal itself is unchanged, which would make `ongoing`
    unrecognizable to the H33b delta engine.
    """
    payload = {
        "student_ref": student_ref,
        "branch": branch,
        "review_priority_band": review_priority_band,
        "factor_codes": sorted(factor_codes),
        "coverage_status": coverage_status,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def resolve_source_id(snapshot: DatasetSnapshot, branch: str) -> str:
    """Resolve the dwh `source_id` backing a Mode B branch — no fuzzy join.

    Uses `legacy_source_id` when the H30 snapshot carries one (bridging the
    H19/H20 `source_manifest` bytes), otherwise falls back to `dataset_key`.
    Either way the resolved id's `SOURCE_ALLOWLIST` role must match the
    requested branch; a mismatch fails closed.
    """
    expected_role = BRANCH_ROLES.get(branch)
    if expected_role is None:
        raise ValueError(f"unknown_branch:{branch}")

    source_id = snapshot.legacy_source_id or snapshot.dataset_key
    role = SOURCE_ALLOWLIST.get(source_id)
    if role != expected_role:
        raise NamespaceMismatchError(
            f"namespace_mismatch: branch={branch} source_id={source_id} role={role!r}"
        )
    return source_id


def _insufficient_observation(
    *, snapshot_id: str, student_ref: str, branch: str, extracted_at: Optional[datetime], model_version: str
) -> SignalObservation:
    return SignalObservation(
        snapshot_id=snapshot_id,
        student_ref=student_ref,
        branch=branch,
        review_priority_band=None,
        factor_codes=[],
        coverage_status="insufficient",
        extracted_at=extracted_at,
        evidence_fingerprint=evidence_fingerprint(
            student_ref=student_ref,
            branch=branch,
            review_priority_band=None,
            factor_codes=[],
            coverage_status="insufficient",
        ),
        model_version=model_version,
    )


def build_observations_mode_b(
    session: Session,
    snapshot_id: str,
    branch: str,
    *,
    thresholds: ThresholdConfig = DEFAULT_THRESHOLDS,
    model_version: str = MODEL_VERSION,
) -> List[SignalObservation]:
    """Normalize one approved snapshot's own branch into immutable observations.

    Mode B only (Decision #23 item 2): `branch` must be `"semester"` or
    `"attendance"`. A `"combined"` request means the canonical linked
    namespace is not approved yet — refuse instead of joining semester and
    attendance rows heuristically by `student_ref`.
    """
    if branch == "combined":
        raise ValueError("linked_namespace_pending")
    if branch not in BRANCH_ROLES:
        raise ValueError(f"unknown_branch:{branch}")

    snapshot = session.get(DatasetSnapshot, snapshot_id)
    if snapshot is None:
        raise ValueError(f"snapshot_not_found:{snapshot_id}")

    source_id = resolve_source_id(snapshot, branch)

    try:
        records = list_normalized_students(session, source_id)
    except ReadAdapterError:
        # Structural source problem (unapproved/not allowlisted) — fail
        # closed rather than fabricate per-student rows.
        raise

    observations: List[SignalObservation] = []
    for record in records:
        if record.coverage.status == "insufficient":
            observations.append(
                _insufficient_observation(
                    snapshot_id=snapshot_id,
                    student_ref=record.student_ref,
                    branch=branch,
                    extracted_at=snapshot.extracted_at,
                    model_version=model_version,
                )
            )
            continue

        features = score_student(
            record,
            calculated_at=snapshot.extracted_at,
            model_version=model_version,
            threshold_config_version=thresholds.version,
        )
        score = compute_model_score(features)
        band = band_for_score(score, thresholds)
        factors = [f.code for f in contributing_factors(features)] if band is not None else []
        observations.append(
            SignalObservation(
                snapshot_id=snapshot_id,
                student_ref=record.student_ref,
                branch=branch,
                review_priority_band=band,
                factor_codes=factors,
                coverage_status=record.coverage.status,
                extracted_at=snapshot.extracted_at,
                evidence_fingerprint=evidence_fingerprint(
                    student_ref=record.student_ref,
                    branch=branch,
                    review_priority_band=band,
                    factor_codes=factors,
                    coverage_status=record.coverage.status,
                ),
                model_version=model_version,
            )
        )
    return observations
