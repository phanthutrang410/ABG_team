"""Constants for ml-eval-feature-complete-v1 (decision #26)."""

from __future__ import annotations

from datetime import datetime, timezone

SOURCE_ID = "ml-eval-feature-complete-v1"
SCHEMA_VERSION = "epu-1"
PROVENANCE_LANE = "ml-eval-synthetic"
REPORT_VERSION = "m09-eval-1"

DEFAULT_SEED = 42
SMOKE_N = 12
#: Target full eval cohort (EPU-scale); write under data/eval/full/ (gitignored).
FULL_N = 2000

#: Fixed extraction clock for determinism (ISO UTC).
EXTRACTED_AT = datetime(2026, 7, 18, 12, 0, 0, tzinfo=timezone.utc)

#: Fraction of students in the latent "risk" branch.
RISK_FRACTION = 0.40

ATTENDANCE_EVENT_COUNT = 6

#: Advisors per department (eval lane pseudonyms).
ADVISORS_PER_DEPT = 3
