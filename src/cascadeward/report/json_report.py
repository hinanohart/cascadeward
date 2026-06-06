"""Versioned JSON serialisation of a CriticalityReport."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass


def report_to_dict(report) -> dict:
    if is_dataclass(report):
        return asdict(report)
    return dict(report)


def report_to_json(report, indent: int = 2) -> str:
    return json.dumps(report_to_dict(report), indent=indent, sort_keys=False)
