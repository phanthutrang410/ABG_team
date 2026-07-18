"""ML eval synthetic package — decision #26 / M09 (eval lane only).

Not on MVP H20 / source-gate allowlist. Do not feed public ReviewCase.
"""

from __future__ import annotations

from app.ml.eval_synthetic.eda import summarize_eval_package
from app.ml.eval_synthetic.eval_report import run_baseline_eval
from app.ml.eval_synthetic.generate import generate_eval_package
from app.ml.eval_synthetic.io import package_content_hash, write_eval_package
from app.ml.eval_synthetic.load import load_eval_dir, records_from_package
from app.ml.eval_synthetic.models import EvalPackage

__all__ = [
    "EvalPackage",
    "generate_eval_package",
    "load_eval_dir",
    "package_content_hash",
    "records_from_package",
    "run_baseline_eval",
    "summarize_eval_package",
    "write_eval_package",
]
