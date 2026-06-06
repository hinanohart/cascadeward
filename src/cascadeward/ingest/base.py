"""Adapter contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..events import EventStream


class Adapter(ABC):
    name: str = "base"

    @abstractmethod
    def parse(self, src: str) -> EventStream:  # pragma: no cover - interface
        ...
