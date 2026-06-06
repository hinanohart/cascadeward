"""cascadeward -- preemption/recompute storm criticality for LLM serving traces.

A measurement instrument: it fits a self-exciting point process to serving
preemption events and reports a guarded criticality verdict. It does not make
serving faster and does not prevent cascades.
"""

from __future__ import annotations

__version__ = "0.1.0a1"

from .events import Event, EventStream, EventType, Fidelity, normalize
from .score import CriticalityReport, score

__all__ = [
    "__version__",
    "score",
    "CriticalityReport",
    "Event",
    "EventStream",
    "EventType",
    "Fidelity",
    "normalize",
]
