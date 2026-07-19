# M10 shadow + local materialization evidence

> Date: 2026-07-19 · source: local approved Reality-460 DWH.

## Shadow gate

| Item | Result |
|:--|--:|
| OOF cases | 49 / 460 |
| OOF TP / FP / TN / FN | 33 / 16 / 398 / 13 |
| OOF precision | 67.35% |
| OOF recall | 71.74% |
| OOF FPR | 3.86% |
| OOF selection rate | 10.65% |
| Coefficient sign stability | 100% |

All promotion gates passed. The previous heuristic evidence was 35 cases, TP=22, FP=13, TN=401, FN=24.

## Final-model application to the same cohort

The final model was refit on all 460 rows after OOF evaluation and then applied for runtime materialization:

- 460 `dwh.ml_term_snapshot` rows.
- 51 surfaced cases: 29 `uu_tien_som`, 22 `can_ra_soat`.
- 409 below the case threshold.
- 0 surfaced cases without a model-backed factor.
- Approved training package SHA-256: `73274079b30487f066cb2e1751c7ec70e2737ff794d6ae76e3e26ec4cf86df24`.
- Canonical artifact digest: `099265d2d7917014d7622685bf7fbe06a50cd41d726746d805a01ffb4b19febe`.

The 51 final-fit cases are application output, not evaluation evidence; official metrics remain the OOF results above.
