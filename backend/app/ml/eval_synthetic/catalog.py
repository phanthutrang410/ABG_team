"""Load weighted program catalog derived from approved EPU/M06 package."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

_CATALOG_PATH = Path(__file__).with_name("epu_program_catalog.json")


def _slug(text: str, *, max_len: int = 24) -> str:
    text = text.replace("Đ", "D").replace("đ", "d")
    ascii_ish = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return (ascii_ish or "x")[:max_len]


@lru_cache(maxsize=1)
def load_program_catalog() -> Dict[str, Any]:
    return json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))


def weighted_programs() -> Tuple[List[Dict[str, Any]], List[float]]:
    catalog = load_program_catalog()
    programs = list(catalog["programs"])
    weights = [float(p["weight"]) for p in programs]
    return programs, weights


def course_bank_for_major(major: str, *, size: int) -> List[Dict[str, Any]]:
    """Stable course templates for a major (shared across students)."""
    major_slug = _slug(major)
    bank: List[Dict[str, Any]] = []
    for i in range(size):
        credits = 3.0 if i % 3 else 2.0
        bank.append(
            {
                "course_ref": f"c-{major_slug}-{i:02d}",
                "credits": credits,
                "label": f"HP-{major_slug}-{i:02d}",
            }
        )
    return bank


def pick_terms(n_terms: int, template: Sequence[str]) -> List[str]:
    if n_terms < 2:
        n_terms = 2
    if n_terms > len(template):
        n_terms = len(template)
    return list(template[-n_terms:])
