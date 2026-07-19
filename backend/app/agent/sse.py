"""SSE helpers for Global Agent turn streaming (status + faux token deltas)."""

from __future__ import annotations

import json
from typing import Any, Iterator, Mapping


def format_sse(event: str, data: Mapping[str, Any] | dict[str, Any]) -> str:
    """Encode one SSE message: ``event:`` + ``data:`` JSON + blank line."""
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n"


def chunk_text(text: str, size: int = 16) -> Iterator[str]:
    """Split validated answer into faux-token chunks (post output_guard only)."""
    if size < 1:
        raise ValueError("chunk size must be >= 1")
    if not text:
        return
    for i in range(0, len(text), size):
        yield text[i : i + size]
