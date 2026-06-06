"""Synthetic ground-truth generator (also used by tests and SHIP GATE).

Wraps the exact immigration-birth simulator so a stream with *known* mu/alpha/beta
can be produced. The branching ratio of the returned stream is exactly ``alpha``
(unmarked), which is what the recovery tests assert.
"""

from __future__ import annotations

import numpy as np

from ..events import EventStream, EventType, Fidelity
from ..pp.background import PiecewiseConstantBackground
from ..pp.mle import simulate_hawkes


def generate(
    *,
    alpha: float,
    beta: float,
    T: float,
    mu=0.5,
    mu_blocks=None,
    seed: int = 0,
    source: str | None = None,
) -> EventStream:
    """Generate a synthetic EventStream.

    ``mu`` is a constant background; pass ``mu_blocks`` (a sequence of rates over
    equal-width blocks on [0, T]) for a non-stationary background.
    """
    if mu_blocks is not None:
        bg = PiecewiseConstantBackground.uniform_blocks(np.asarray(mu_blocks, dtype=float), T)
    else:
        bg = PiecewiseConstantBackground.stationary(float(mu), T)

    times, _ = simulate_hawkes(bg, float(alpha), float(beta), float(T), seed=seed)
    src = source or f"synthetic(alpha={alpha},beta={beta},T={T})"
    return EventStream.from_times(
        times,
        t0=0.0,
        t1=float(T),
        type=EventType.PREEMPT,
        fidelity=Fidelity.NATIVE_EVENT,
        source=src,
    )
