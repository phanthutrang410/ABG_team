# M10 Reality-460 model card

## Model and intended use

- Version: `m10-reality460-logreg-1.0`.
- Artifact schema: `ml-linear-artifact-v1`.
- Purpose: prioritize human review; never diagnose, discipline, or auto-contact a student.
- Public output: review band, model-backed factor codes, coverage, limitations, and versions. Raw score and coefficients remain internal.

## Training data and feature boundary

- Reality source: 460 pseudonymous students, two terms, 3,680 grade rows.
- Approved package SHA-256: `73274079b30487f066cb2e1751c7ec70e2737ff794d6ae76e3e26ec4cf86df24`.
- Label: 46 positive / 414 negative under `gt-epu-status-after-t2-v1`.
- Selected feature set A: latest-term credit-weighted GPA and `log1p(failed_credits)`.
- Grade trend was evaluated but did not earn inclusion under the nested-CV simplicity rule.
- Grade volatility and generated attendance are excluded from scoring.

## Training and evaluation

- L2 logistic regression, standardized inside each fold, no class weighting.
- Nested repeated stratified CV: outer 5×10, inner 5 folds, seed `20260719`.
- Final hyperparameter: `C=0.01`.
- OOF threshold selection targets recall ≥70%, precision ≥50%, FPR ≤10%, selection ≤15%.

| Metric | OOF result |
|:--|--:|
| Average precision | 0.7951 |
| Precision | 0.6735 |
| Recall | 0.7174 |
| FPR | 0.0386 |
| Selection rate | 0.1065 |
| TP / FP / TN / FN | 33 / 16 / 398 / 13 |

The committed aggregate evaluation report is [`25-m10-reality460-evaluation.json`](../03-project/25-m10-reality460-evaluation.json). Metrics are OOF; the deployment model is refit on all 460 rows and in-sample metrics are not reported as evidence.

## Explainability and limitations

- Factors are derived from positive log-odds contributions relative to GPA 5.0 and failed credits 0.
- Public factor values/weights are not exposed.
- Limitations: `grade_only_model`, `two_term_history`.
- No approved audit attribute is available; fairness remains `insufficient_data`.
- There is no independent external or prospective validation cohort.

## Rollback

Operator-only rollback selects `m02-baseline-0.2` and re-materializes. Artifact errors fail closed and never trigger an automatic heuristic fallback.
