"""Class-roster overlay — partition approved semester students into lecturer classes.

Non-destructive by design: this NEVER mutates the hash-gated approved domain
package (``data/approved/semester/domain_package.json``, decision #18). It
deterministically splits the *sorted* set of ``student_ref`` into balanced,
contiguous classes, one per lecturer ``gvcn`` account, and is used only to widen
that lecturer's ``/review-cases`` visibility to their own class roster.

The overlay is a parallel scope dimension: it does not touch the DWH
``advisor_assignment`` rows (still all ``a-240eb01d2805``), so legacy
handoff/assign routing and the existing demo ``gvcn`` account are unaffected.
Each lecturer account carries one of :data:`LECTURER_CLASS_SCOPES` as its
``advisor_scope``; a student is visible to that lecturer iff the student's
overlay class equals the lecturer's ``advisor_scope``.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

#: Advisor-scope value for each of the four lecturer classes. These MUST match
#: the ``advisor_scope`` seeded on the four ``gvcn`` lecturer accounts
#: (see ``app.auth.cli._LECTURER_ACCOUNTS``). Order defines class 01..04.
LECTURER_CLASS_SCOPES: Tuple[str, ...] = (
    "class-01",
    "class-02",
    "class-03",
    "class-04",
)


def build_class_scope_map(
    student_refs: Iterable[str],
    scopes: Tuple[str, ...] = LECTURER_CLASS_SCOPES,
) -> Dict[str, str]:
    """Map each ``student_ref`` to exactly one class scope (balanced, contiguous).

    The split is deterministic in the sorted, de-duplicated ``student_ref`` set:
    with ``N`` students and ``K`` classes, student at 0-based rank ``r`` lands in
    class ``r * K // N``. For ``N`` divisible by ``K`` every class holds ``N/K``
    students (460 → 4 × 115); otherwise the earlier classes may hold one more.

    Returns an empty map when there are no students or no scopes.
    """
    refs: List[str] = sorted({r for r in student_refs if r})
    n = len(refs)
    k = len(scopes)
    if n == 0 or k == 0:
        return {}
    out: Dict[str, str] = {}
    for rank, ref in enumerate(refs):
        idx = rank * k // n
        if idx >= k:  # guard against float-free edge at the last element
            idx = k - 1
        out[ref] = scopes[idx]
    return out


def class_scope_for_student(
    student_refs: Iterable[str],
    student_ref: str,
    scopes: Tuple[str, ...] = LECTURER_CLASS_SCOPES,
) -> Optional[str]:
    """Return the overlay class scope for ``student_ref`` (or ``None`` if absent)."""
    ref = (student_ref or "").strip()
    if not ref:
        return None
    return build_class_scope_map(student_refs, scopes).get(ref)
