"""Source gate (M05a) — fail-closed register/hash/PII/provenance gate.

Xem docs/04-engineering/04-epu-data-integration-contract.md §2–§3.
"""

from app.ml.source_gate.gate import (
    SOURCE_ALLOWLIST,
    compute_sha256,
    evaluate_source,
)
from app.ml.source_gate.models import (
    GateReasonCode,
    GateResult,
    SourceManifest,
    SourceRole,
)

__all__ = [
    "SOURCE_ALLOWLIST",
    "GateReasonCode",
    "GateResult",
    "SourceManifest",
    "SourceRole",
    "compute_sha256",
    "evaluate_source",
]
