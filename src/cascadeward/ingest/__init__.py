"""Ingest layer: the ONLY place that knows serving-specific formats.

Everything downstream consumes a domain-agnostic EventStream.
"""

from .jsonl import parse_jsonl
from .synthetic import generate
from .vllm_log import parse_vllm_log

__all__ = ["parse_jsonl", "parse_vllm_log", "generate"]


def load(path: str, adapter: str = "auto", fidelity: str | None = None):
    """Dispatch to an adapter. ``auto`` picks by file extension."""
    if adapter == "auto":
        low = path.lower()
        if low.endswith(".jsonl") or low.endswith(".json"):
            adapter = "jsonl"
        elif low.endswith(".log") or low.endswith(".txt"):
            adapter = "vllm_log"
        else:
            adapter = "jsonl"
    if adapter == "jsonl":
        return parse_jsonl(path, fidelity=fidelity)
    if adapter == "vllm_log":
        return parse_vllm_log(path)
    raise ValueError(f"unknown adapter: {adapter}")
