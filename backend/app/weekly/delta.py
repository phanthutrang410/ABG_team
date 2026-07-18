"""H33b — deterministic delta engine + durable case reconcile.

Semantics locked in Decision #23 item 1 / architecture doc 13 §7.2. Delta
classification is a pure function of two observation snapshots (`prev`/
`curr`) plus their run versions — no case-repository lookups — so it stays
easy to unit test and cannot itself mutate durable state.
`reconcile()` is the only place that touches `CaseRepository`, and it never
auto-closes/dismisses/resolves an episode: `no_longer_detected` only adds an
event, and human states (`pending_review`/`approved`/`assigned`/
`monitoring`) are left untouched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Tuple

from app.weekly.cases_durable import CaseRepository
from app.weekly.observations import SignalObservation

DeltaType = Literal[
    "initial_baseline",
    "newly_detected",
    "ongoing",
    "changed",
    "no_longer_detected",
    "resurfaced",
    "comparison_unavailable",
]

_ObsKey = Tuple[str, str]  # (student_ref, branch)


@dataclass(frozen=True)
class RunVersions:
    """Comparability handle (Decision #23 item 1) — model/threshold/namespace."""

    model_version: str
    threshold_config_version: str
    pseudonym_namespace_version: str


@dataclass(frozen=True)
class TerminalFingerprint:
    """Last eligible observation recorded before an episode went terminal."""

    review_priority_band: Optional[str]
    factor_codes: Tuple[str, ...]


@dataclass
class DeltaItem:
    """One (student_ref, branch) row of the weekly delta — report-ready."""

    student_ref: str
    branch: str
    delta_type: DeltaType
    curr_observation: Optional[SignalObservation] = None
    prev_observation: Optional[SignalObservation] = None
    significant_change: bool = False
    reason_codes: List[str] = field(default_factory=list)


def _key(obs: SignalObservation) -> _ObsKey:
    return (obs.student_ref, obs.branch)


def _significant(
    prev_band: Optional[str],
    prev_factors: List[str] | Tuple[str, ...],
    curr_band: Optional[str],
    curr_factors: List[str] | Tuple[str, ...],
) -> bool:
    """Decision #23 item 1: band change OR factor-set change (set equality)."""
    return prev_band != curr_band or set(prev_factors) != set(curr_factors)


def compute_delta(
    prev_obs: List[SignalObservation],
    curr_obs: List[SignalObservation],
    *,
    prev_versions: Optional[RunVersions],
    curr_versions: Optional[RunVersions],
    prior_terminal_fingerprints: Optional[Dict[_ObsKey, TerminalFingerprint]] = None,
) -> List[DeltaItem]:
    """Classify every `(student_ref, branch)` seen in `prev_obs` ∪ `curr_obs`.

    - `prev_versions is None` → no comparable prior run at all: every
      eligible current observation is `initial_baseline` (not "new").
    - Both version sets present but different → `comparison_unavailable`
      for every current observation; never claim "new" across an
      incompatible model/threshold/namespace change.
    - Otherwise compare per key; `prior_terminal_fingerprints` (optional,
      supplied by the caller from durable case history) distinguishes a
      first-time `newly_detected` from a `resurfaced` detection after a
      terminal episode.
    """
    curr_map: Dict[_ObsKey, SignalObservation] = {_key(o): o for o in curr_obs}

    if prev_versions is None:
        items: List[DeltaItem] = []
        for key, curr in curr_map.items():
            if not curr.eligible:
                continue
            items.append(
                DeltaItem(
                    student_ref=key[0],
                    branch=key[1],
                    delta_type="initial_baseline",
                    curr_observation=curr,
                    prev_observation=None,
                    significant_change=True,
                )
            )
        return items

    if curr_versions is None or prev_versions != curr_versions:
        return [
            DeltaItem(
                student_ref=key[0],
                branch=key[1],
                delta_type="comparison_unavailable",
                curr_observation=curr,
                prev_observation=None,
                significant_change=False,
                reason_codes=["version_changed"],
            )
            for key, curr in curr_map.items()
        ]

    prev_map: Dict[_ObsKey, SignalObservation] = {_key(o): o for o in prev_obs}
    terminal = prior_terminal_fingerprints or {}
    all_keys = set(prev_map) | set(curr_map)
    items = []
    for key in sorted(all_keys):
        prev = prev_map.get(key)
        curr = curr_map.get(key)
        prev_eligible = prev is not None and prev.eligible
        curr_eligible = curr is not None and curr.eligible

        if curr_eligible and not prev_eligible:
            term = terminal.get(key)
            if term is not None:
                items.append(
                    DeltaItem(
                        student_ref=key[0],
                        branch=key[1],
                        delta_type="resurfaced",
                        curr_observation=curr,
                        prev_observation=prev,
                        significant_change=_significant(
                            term.review_priority_band,
                            term.factor_codes,
                            curr.review_priority_band,
                            curr.factor_codes,
                        ),
                    )
                )
            else:
                items.append(
                    DeltaItem(
                        student_ref=key[0],
                        branch=key[1],
                        delta_type="newly_detected",
                        curr_observation=curr,
                        prev_observation=prev,
                        significant_change=True,
                    )
                )
        elif curr_eligible and prev_eligible:
            if prev.evidence_fingerprint == curr.evidence_fingerprint:
                items.append(
                    DeltaItem(
                        student_ref=key[0],
                        branch=key[1],
                        delta_type="ongoing",
                        curr_observation=curr,
                        prev_observation=prev,
                        significant_change=False,
                    )
                )
            else:
                items.append(
                    DeltaItem(
                        student_ref=key[0],
                        branch=key[1],
                        delta_type="changed",
                        curr_observation=curr,
                        prev_observation=prev,
                        significant_change=_significant(
                            prev.review_priority_band,
                            prev.factor_codes,
                            curr.review_priority_band,
                            curr.factor_codes,
                        ),
                    )
                )
        elif prev_eligible and not curr_eligible:
            items.append(
                DeltaItem(
                    student_ref=key[0],
                    branch=key[1],
                    delta_type="no_longer_detected",
                    curr_observation=curr,
                    prev_observation=prev,
                    significant_change=False,
                )
            )
        # else: neither eligible in this pair — nothing worth reporting.

    return items


def reconcile(repo: CaseRepository, deltas: List[DeltaItem]) -> None:
    """Apply delta effects to durable episodes — never overrides human state.

    - `initial_baseline` / `newly_detected` open a candidate episode when
      none is active yet.
    - `resurfaced` only opens a new episode when `significant_change` is
      True (Decision #23 item 1); otherwise it is recorded as a
      non-authoritative event with no case effect.
    - `ongoing` / `changed` / `no_longer_detected` / `comparison_unavailable`
      never create or transition an episode — they only append an audit
      event onto whatever active episode already exists, so
      `pending_review`/`approved`/`assigned`/`monitoring` are preserved and
      `no_longer_detected` never auto-dismisses/resolves.
    """
    for delta in deltas:
        curr = delta.curr_observation
        snapshot_id = curr.snapshot_id if curr is not None else None
        effect_key = f"{delta.delta_type}:{snapshot_id}:{delta.student_ref}:{delta.branch}"
        if not repo.mark_effect_applied(effect_key):
            continue

        active = repo.get_active_for(delta.student_ref, delta.branch)

        if delta.delta_type in ("initial_baseline", "newly_detected"):
            if active is None:
                repo.create_episode(
                    delta.student_ref,
                    delta.branch,
                    detail={"delta_type": delta.delta_type, "snapshot_id": snapshot_id},
                )
            else:
                repo.append_event(
                    active.episode_id,
                    f"observation_{delta.delta_type}",
                    detail={"snapshot_id": snapshot_id},
                )
        elif delta.delta_type == "resurfaced":
            if active is None and delta.significant_change:
                repo.create_episode(
                    delta.student_ref,
                    delta.branch,
                    detail={"delta_type": "resurfaced", "snapshot_id": snapshot_id},
                )
            elif active is not None:
                repo.append_event(
                    active.episode_id,
                    "observation_resurfaced",
                    detail={"snapshot_id": snapshot_id, "significant_change": delta.significant_change},
                )
            # No active episode and not significant: no case effect — do
            # not claim a new detection the policy does not support.
        elif delta.delta_type == "ongoing":
            if active is not None:
                repo.append_event(
                    active.episode_id, "observation_ongoing", detail={"snapshot_id": snapshot_id}
                )
        elif delta.delta_type == "changed":
            if active is not None:
                repo.append_event(
                    active.episode_id,
                    "observation_changed",
                    detail={
                        "snapshot_id": snapshot_id,
                        "significant_change": delta.significant_change,
                    },
                )
        elif delta.delta_type == "no_longer_detected":
            if active is not None:
                repo.append_event(
                    active.episode_id,
                    "observation_no_longer_detected",
                    detail={"snapshot_id": snapshot_id},
                )
            # Never auto-dismiss/resolve — a human decides (Process §4).
        elif delta.delta_type == "comparison_unavailable":
            if active is not None:
                repo.append_event(
                    active.episode_id,
                    "observation_comparison_unavailable",
                    detail={"snapshot_id": snapshot_id, "reason_codes": delta.reason_codes},
                )
