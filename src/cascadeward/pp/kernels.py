"""Excitation kernel(s).

Exponential kernel only in v0.1 (O(N) Ogata recursion + analytic compensator).
The Omori power-law kernel is deferred to v0.2 (O(N^2) and worse identifiability).
"""

from __future__ import annotations

import numpy as np


class ExpKernel:
    r"""phi(u) = alpha * beta * exp(-beta * u).

    The integral over [0, inf) is ``alpha``; for the unmarked process this is the
    branching ratio ``n``. ``beta`` is the decay rate (1/timescale).
    """

    name = "exp"

    @staticmethod
    def phi(u, alpha: float, beta: float):
        u = np.asarray(u, dtype=float)
        return alpha * beta * np.exp(-beta * u)

    @staticmethod
    def integral(u, alpha: float, beta: float):
        """int_0^u phi = alpha * (1 - exp(-beta u))  (right-censored mass)."""
        u = np.asarray(u, dtype=float)
        return alpha * (1.0 - np.exp(-beta * u))
