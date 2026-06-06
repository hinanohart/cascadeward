"""Time-varying background (immigration) rate mu(t).

Piecewise-constant on a partition of [0, T]. A constant mu is the single-block
special case. Time variation is mandatory (not optional) because LLM serving is
strongly non-stationary (diurnal / bursty) and Filimonov & Sornette (2015,
arXiv:1308.6756) show a single *stationary* kernel yields significant branching
bias under non-stationarity.
"""

from __future__ import annotations

import numpy as np


class PiecewiseConstantBackground:
    def __init__(self, edges, rates):
        self.edges = np.asarray(edges, dtype=float)
        self.rates = np.asarray(rates, dtype=float)
        if len(self.edges) != len(self.rates) + 1:
            raise ValueError("edges must have one more element than rates")
        if np.any(self.rates <= 0):
            # rates come from softplus during fitting, so this guards callers
            self.rates = np.clip(self.rates, 1e-9, None)

    def at(self, t):
        t = np.asarray(t, dtype=float)
        idx = np.clip(np.searchsorted(self.edges, t, side="right") - 1, 0, len(self.rates) - 1)
        return self.rates[idx]

    def integral(self, t0: float, t1: float) -> float:
        total = 0.0
        for k in range(len(self.rates)):
            lo = max(t0, self.edges[k])
            hi = min(t1, self.edges[k + 1])
            if hi > lo:
                total += self.rates[k] * (hi - lo)
        return float(total)

    @classmethod
    def stationary(cls, mu: float, T: float) -> PiecewiseConstantBackground:
        return cls([0.0, T], [mu])

    @classmethod
    def uniform_blocks(cls, rates, T: float) -> PiecewiseConstantBackground:
        rates = np.asarray(rates, dtype=float)
        edges = np.linspace(0.0, T, len(rates) + 1)
        return cls(edges, rates)
