"""Provider-neutral text model protocol (H29)."""

from __future__ import annotations

from typing import Protocol


class ModelUnavailable(RuntimeError):
    """The inference service did not return a usable response."""


class TextModel(Protocol):
    def complete(self, *, system: str, user: str) -> str: ...
