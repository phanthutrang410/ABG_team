"""Unit tests for the non-destructive class-roster overlay (app.cases.class_scope)."""

from __future__ import annotations

from collections import Counter

from app.cases.class_scope import (
    LECTURER_CLASS_SCOPES,
    build_class_scope_map,
    class_scope_for_student,
)


def _refs(n: int) -> list[str]:
    # Zero-padded so lexical sort == numeric rank (mirrors real student_ref order).
    return [f"stu-{i:04d}" for i in range(n)]


def test_split_460_is_four_balanced_classes_of_115() -> None:
    mapping = build_class_scope_map(_refs(460))
    assert len(mapping) == 460
    counts = Counter(mapping.values())
    assert set(counts) == set(LECTURER_CLASS_SCOPES)
    assert all(counts[scope] == 115 for scope in LECTURER_CLASS_SCOPES)


def test_split_is_contiguous_in_sorted_order() -> None:
    refs = _refs(460)
    mapping = build_class_scope_map(refs)
    # First 115 -> class-01, next 115 -> class-02, ... — contiguous blocks.
    for rank, ref in enumerate(refs):
        expected = LECTURER_CLASS_SCOPES[rank // 115]
        assert mapping[ref] == expected


def test_split_is_deterministic_regardless_of_input_order() -> None:
    refs = _refs(460)
    forward = build_class_scope_map(refs)
    reverse = build_class_scope_map(list(reversed(refs)))
    assert forward == reverse


def test_split_dedups_and_ignores_blank_refs() -> None:
    mapping = build_class_scope_map(["b", "a", "a", "", "c"])
    assert set(mapping) == {"a", "b", "c"}


def test_uneven_split_front_loads_earlier_classes() -> None:
    # 10 students, 4 classes -> earlier classes may hold one extra, total preserved.
    mapping = build_class_scope_map(_refs(10))
    counts = Counter(mapping.values())
    assert sum(counts.values()) == 10
    assert max(counts.values()) - min(counts.values()) <= 1


def test_empty_inputs_return_empty_map() -> None:
    assert build_class_scope_map([]) == {}
    assert build_class_scope_map(_refs(5), scopes=()) == {}


def test_class_scope_for_student_matches_map() -> None:
    refs = _refs(460)
    mapping = build_class_scope_map(refs)
    assert class_scope_for_student(refs, refs[0]) == mapping[refs[0]]
    assert class_scope_for_student(refs, refs[200]) == mapping[refs[200]]
    assert class_scope_for_student(refs, "not-a-student") is None
    assert class_scope_for_student(refs, "") is None
