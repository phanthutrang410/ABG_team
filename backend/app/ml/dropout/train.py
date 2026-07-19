"""Deterministic nested-CV training for the Reality-460 model.

Scikit-learn is imported only by this offline module.  Production loads the
resulting JSON artifact through ``runtime.py``.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from app.ml.dropout.artifact import finalized_artifact, write_artifact
from app.ml.dropout.dataset import TrainingDataset, load_reality460

RANDOM_SEED = 20260719
C_GRID = (0.01, 0.1, 1.0, 10.0)
FEATURE_SETS = {
    "A": ["latest_term_gpa", "failed_credits_log1p"],
    "B": ["latest_term_gpa", "failed_credits_log1p", "grade_trend_slope"],
}
EXPECTED_SIGNS = {
    "latest_term_gpa": -1,
    "failed_credits_log1p": 1,
    "grade_trend_slope": -1,
}


@dataclass(frozen=True)
class Config:
    feature_set: str
    regularization_c: float


@dataclass(frozen=True)
class Metrics:
    threshold: float
    tp: int
    fp: int
    tn: int
    fn: int
    precision: float
    recall: float
    fpr: float
    selection_rate: float


def _imports():
    try:
        import numpy as np
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import average_precision_score, brier_score_loss
        from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedKFold
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:  # pragma: no cover - exercised by CLI environment
        raise RuntimeError("install the backend 'ml' optional dependencies") from exc
    return (
        np,
        LogisticRegression,
        average_precision_score,
        brier_score_loss,
        RepeatedStratifiedKFold,
        StratifiedKFold,
        StandardScaler,
    )


def _matrix(dataset: TrainingDataset, feature_set: str):
    np, *_rest = _imports()
    return np.asarray([row.vector(feature_set) for row in dataset.rows], dtype=float)


def _valid_signs(feature_names: Sequence[str], coefficients: Sequence[float]) -> bool:
    return all(float(coef) * EXPECTED_SIGNS[name] > 0 for name, coef in zip(feature_names, coefficients))


def _fit_predict(
    x_train,
    y_train,
    x_test,
    config: Config,
):
    np, LogisticRegression, *_middle, StandardScaler = _imports()
    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(x_train)
    model = LogisticRegression(
        penalty="l2",
        C=config.regularization_c,
        solver="liblinear",
        max_iter=2000,
        random_state=RANDOM_SEED,
        class_weight=None,
    )
    model.fit(train_scaled, y_train)
    probabilities = model.predict_proba(scaler.transform(x_test))[:, 1]
    return np.asarray(probabilities), scaler, model


def _inner_select(dataset: TrainingDataset, train_indices, outer_number: int) -> Config:
    (
        np,
        _LogisticRegression,
        average_precision_score,
        _brier,
        _Repeated,
        StratifiedKFold,
        _Scaler,
    ) = _imports()
    labels = np.asarray(dataset.labels, dtype=int)
    candidates: list[tuple[float, Config]] = []
    inner = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=RANDOM_SEED + outer_number,
    )
    for feature_set, feature_names in FEATURE_SETS.items():
        matrix = _matrix(dataset, feature_set)[train_indices]
        inner_labels = labels[train_indices]
        for c_value in C_GRID:
            fold_scores: List[float] = []
            valid = True
            config = Config(feature_set=feature_set, regularization_c=c_value)
            for inner_train, inner_valid in inner.split(matrix, inner_labels):
                probabilities, _scaler, model = _fit_predict(
                    matrix[inner_train],
                    inner_labels[inner_train],
                    matrix[inner_valid],
                    config,
                )
                if not _valid_signs(feature_names, model.coef_[0]):
                    valid = False
                    break
                fold_scores.append(
                    float(average_precision_score(inner_labels[inner_valid], probabilities))
                )
            if valid:
                candidates.append((float(np.mean(fold_scores)), config))
    if not candidates:
        raise ValueError("no_candidate_with_valid_coefficient_signs")
    best_score = max(score for score, _config in candidates)
    shortlist = [(score, config) for score, config in candidates if score >= best_score - 0.01]
    shortlist.sort(
        key=lambda item: (
            len(FEATURE_SETS[item[1].feature_set]),
            item[1].regularization_c,
            -item[0],
        )
    )
    return shortlist[0][1]


def _confusion(labels: Sequence[int], scores: Sequence[float], threshold: float) -> Metrics:
    tp = fp = tn = fn = 0
    for label, score in zip(labels, scores):
        predicted = score >= threshold
        if predicted and label:
            tp += 1
        elif predicted:
            fp += 1
        elif label:
            fn += 1
        else:
            tn += 1
    selected = tp + fp
    return Metrics(
        threshold=float(threshold),
        tp=tp,
        fp=fp,
        tn=tn,
        fn=fn,
        precision=tp / selected if selected else 0.0,
        recall=tp / (tp + fn) if tp + fn else 0.0,
        fpr=fp / (fp + tn) if fp + tn else 0.0,
        selection_rate=selected / len(labels) if labels else 0.0,
    )


def select_thresholds(labels: Sequence[int], scores: Sequence[float]) -> Tuple[Metrics, Metrics]:
    thresholds = sorted({float(score) for score in scores}, reverse=True)
    case_candidates = []
    for threshold in thresholds:
        metric = _confusion(labels, scores, threshold)
        if (
            metric.recall >= 0.70
            and metric.precision >= 0.50
            and metric.fpr <= 0.10
            and metric.selection_rate <= 0.15
        ):
            case_candidates.append(metric)
    if not case_candidates:
        raise ValueError("no_tau_case_meets_acceptance_gate")
    case_candidates.sort(
        key=lambda metric: (-metric.precision, metric.tp + metric.fp, -metric.threshold)
    )
    tau_case = case_candidates[0]

    high_candidates = []
    for threshold in thresholds:
        if threshold < tau_case.threshold:
            continue
        metric = _confusion(labels, scores, threshold)
        if metric.precision >= 0.80 and metric.tp + metric.fp >= 10:
            high_candidates.append(metric)
    if high_candidates:
        high_candidates.sort(key=lambda metric: (-metric.recall, metric.fp, -metric.threshold))
        tau_high = high_candidates[0]
    else:
        tau_high = _confusion(labels, scores, 1.0)
    return tau_case, tau_high


def _bootstrap_intervals(
    labels: Sequence[int],
    scores: Sequence[float],
    threshold: float,
    *,
    iterations: int = 2000,
) -> Dict[str, float]:
    np, *_rest = _imports()
    rng = np.random.default_rng(RANDOM_SEED)
    n = len(labels)
    values: Dict[str, list[float]] = {"precision": [], "recall": [], "fpr": []}
    for _ in range(iterations):
        indices = rng.integers(0, n, size=n)
        sampled_labels = [labels[int(index)] for index in indices]
        sampled_scores = [scores[int(index)] for index in indices]
        metric = _confusion(sampled_labels, sampled_scores, threshold)
        values["precision"].append(metric.precision)
        values["recall"].append(metric.recall)
        values["fpr"].append(metric.fpr)
    result: Dict[str, float] = {}
    for name, samples in values.items():
        result[f"{name}_ci_low"] = float(np.quantile(samples, 0.025))
        result[f"{name}_ci_high"] = float(np.quantile(samples, 0.975))
    return result


def train(dataset: TrainingDataset):
    (
        np,
        _LogisticRegression,
        average_precision_score,
        brier_score_loss,
        RepeatedStratifiedKFold,
        _Stratified,
        _Scaler,
    ) = _imports()
    labels = np.asarray(dataset.labels, dtype=int)
    splitter = RepeatedStratifiedKFold(
        n_splits=5,
        n_repeats=10,
        random_state=RANDOM_SEED,
    )
    score_sum = np.zeros(len(labels), dtype=float)
    score_count = np.zeros(len(labels), dtype=int)
    selected_counts: Counter[Config] = Counter()
    outer_ap_by_config: Dict[Config, list[float]] = defaultdict(list)
    sign_valid_fits = 0

    split_matrix = _matrix(dataset, "A")
    for outer_number, (train_indices, valid_indices) in enumerate(
        splitter.split(split_matrix, labels)
    ):
        config = _inner_select(dataset, train_indices, outer_number)
        matrix = _matrix(dataset, config.feature_set)
        probabilities, _scaler, model = _fit_predict(
            matrix[train_indices],
            labels[train_indices],
            matrix[valid_indices],
            config,
        )
        if _valid_signs(FEATURE_SETS[config.feature_set], model.coef_[0]):
            sign_valid_fits += 1
        score_sum[valid_indices] += probabilities
        score_count[valid_indices] += 1
        selected_counts[config] += 1
        outer_ap_by_config[config].append(
            float(average_precision_score(labels[valid_indices], probabilities))
        )
    if not np.all(score_count == 10):
        raise AssertionError("each student must receive ten OOF predictions")
    oof_scores = score_sum / score_count

    max_count = max(selected_counts.values())
    finalists = [config for config, count in selected_counts.items() if count == max_count]
    finalists.sort(
        key=lambda config: (
            -float(np.mean(outer_ap_by_config[config])),
            len(FEATURE_SETS[config.feature_set]),
            config.regularization_c,
        )
    )
    final_config = finalists[0]
    tau_case, tau_high = select_thresholds(labels.tolist(), oof_scores.tolist())
    ap = float(average_precision_score(labels, oof_scores))
    brier = float(brier_score_loss(labels, oof_scores))
    bootstrap = _bootstrap_intervals(labels.tolist(), oof_scores.tolist(), tau_case.threshold)
    promoted = (
        tau_case.recall >= 0.70
        and tau_case.precision >= 0.50
        and tau_case.fpr <= 0.10
        and tau_case.selection_rate <= 0.15
        and ap > 0.10
        and sign_valid_fits / 50 >= 0.90
    )

    final_matrix = _matrix(dataset, final_config.feature_set)
    _probabilities, scaler, model = _fit_predict(
        final_matrix,
        labels,
        final_matrix,
        final_config,
    )
    names = FEATURE_SETS[final_config.feature_set]
    metrics = {
        "n_students": float(len(labels)),
        "n_positive": float(sum(labels)),
        "n_negative": float(len(labels) - sum(labels)),
        "oof_average_precision": ap,
        "oof_brier": brier,
        "oof_tp": float(tau_case.tp),
        "oof_fp": float(tau_case.fp),
        "oof_tn": float(tau_case.tn),
        "oof_fn": float(tau_case.fn),
        "oof_precision": tau_case.precision,
        "oof_recall": tau_case.recall,
        "oof_fpr": tau_case.fpr,
        "oof_selection_rate": tau_case.selection_rate,
        "coefficient_sign_stability": sign_valid_fits / 50,
        **bootstrap,
    }
    artifact = finalized_artifact(
        {
            "dataset_version": dataset.dataset_version,
            "source_snapshot_sha256": dataset.source_snapshot_sha256,
            "training_package_sha256": dataset.training_package_sha256,
            "feature_set": final_config.feature_set,
            "feature_order": names,
            "transforms": {
                name: ("log1p" if name == "failed_credits_log1p" else "identity")
                for name in names
            },
            "means": {name: float(scaler.mean_[i]) for i, name in enumerate(names)},
            "scales": {name: float(scaler.scale_[i]) for i, name in enumerate(names)},
            "coefficients": {name: float(model.coef_[0][i]) for i, name in enumerate(names)},
            "intercept": float(model.intercept_[0]),
            "regularization_c": final_config.regularization_c,
            "random_seed": RANDOM_SEED,
            "tau_case": tau_case.threshold,
            "tau_high": tau_high.threshold,
            "promoted": promoted,
            "aggregate_metrics": metrics,
            "limitations": ["grade_only_model", "two_term_history"],
        }
    )
    report = {
        "status": "promoted" if promoted else "not_promoted",
        "artifact_sha256": artifact.artifact_sha256,
        "model_version": artifact.model_version,
        "threshold_config_version": artifact.threshold_config_version,
        "dataset_version": artifact.dataset_version,
        "training_package_sha256": artifact.training_package_sha256,
        "label_rule_version": artifact.label_rule_version,
        "feature_set": final_config.feature_set,
        "regularization_c": final_config.regularization_c,
        "thresholds": {"tau_case": artifact.tau_case, "tau_high": artifact.tau_high},
        "metrics": metrics,
        "baseline": {
            "cases": 35,
            "tp": 22,
            "fp": 13,
            "tn": 401,
            "fn": 24,
            "precision": 22 / 35,
            "recall": 22 / 46,
            "fpr": 13 / 414,
        },
        "disclaimers": [
            "OOF metrics on one 460-student cohort; no external validation cohort.",
            "Final model is fit on all 460 rows; in-sample metrics are not reported.",
            "Grade-only two-term model; generated attendance is excluded.",
        ],
    }
    return artifact, report


def train_to_files(dataset_path: Path, artifact_path: Path, report_path: Path) -> dict:
    dataset = load_reality460(dataset_path)
    artifact, report = train(dataset)
    write_artifact(artifact, artifact_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
