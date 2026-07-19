# M10 — Reality-460 label cutoff decision

> **Status:** Approved for the M10 implementation requested on 2026-07-19.
> **Owner:** Data/ML lane (Giang); source approval remains with the existing M05b owner.

## Decision

- Feature observation ends at `2022-2023-T2`.
- `thoi_hoc` and `buoc_thoi_hoc` map to `is_dropout_outcome=true`.
- `dang_hoc` maps to `is_dropout_outcome=false`.
- The supervised label is treated as observed after the feature cutoff for this retrospective short-horizon baseline.
- Label rule version: `gt-epu-status-after-t2-v1`.

## Locked dataset

- Approved primary source: `v59-empty-program-students`.
- 460 pseudonymous students; 3,680 term-grade rows; two terms.
- 46 positive, 414 negative, zero unknown.
- Generated linked attendance is excluded from training and evaluation.

## Claim boundary

This is a retrospective, two-term, grade-only early-warning baseline. OOF metrics on this cohort do not establish prospective or cross-cohort effectiveness. A future external/time-forward cohort is required before production institutional claims.
