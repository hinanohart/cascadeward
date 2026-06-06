"""Versioned JSON serialisation of a CriticalityReport."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from typing import Any


def report_to_dict(report: Any) -> dict:
    # ``is_dataclass`` is True for dataclass *types* too; we only want instances.
    if is_dataclass(report) and not isinstance(report, type):
        return asdict(report)
    if isinstance(report, Mapping):
        return dict(report)
    raise TypeError(f"report_to_dict expects a dataclass instance or mapping, got {type(report)!r}")


def report_to_json(report, indent: int = 2) -> str:
    return json.dumps(report_to_dict(report), indent=indent, sort_keys=False)
