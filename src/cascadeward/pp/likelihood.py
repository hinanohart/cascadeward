"""Exponential-Hawkes log-likelihood with time-varying background (unmarked, v0.1).

Intensity:  lambda(t) = mu(t) + sum_{t_i < t} alpha * beta * exp(-beta (t - t_i))
Log-lik:    sum_i log lambda(t_i) - int_{0}^{T} lambda
            = sum_i log lambda(t_i)
              - int mu
              - alpha * sum_i (1 - exp(-beta (T - t_i)))    [right-censored]

The recurrence R_i = sum_{j<i} exp(-beta (t_i - t_j)) makes the event-term O(N).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .background import PiecewiseConstantBackground


@dataclass
class HawkesParams:
    background: PiecewiseConstantBackground
    alpha: float
    beta: float

    @property
    def n(self) -> float:
        """Branching ratio (unmarked exp kernel)."""
        return self.alpha


def _excitation_recursion(times: np.ndarray, beta: float) -> np.ndarray:
    """R_i = sum_{j<i} exp(-beta (t_i - t_j)), computed in O(N).

    Uses math.exp on python floats (not np.exp on scalars): this is the optimiser
    inner loop, called thousands of times, and scalar np.exp is ~10x slower.
    """
    n = len(times)
    if n == 0:
        return np.zeros(0)
    tv = times.tolist() if isinstance(times, np.ndarray) else list(times)
    R = [0.0] * n
    acc = 0.0
    beta = float(beta)
    for i in range(1, n):
        acc = math.exp(-beta * (tv[i] - tv[i - 1])) * (acc + 1.0)
        R[i] = acc
    return np.asarray(R)


def intensity_at_events(times: np.ndarray, params: HawkesParams):
    times = np.asarray(times, dtype=float)
    R = _excitation_recursion(times, params.beta)
    mu = params.background.at(times)
    lam = mu + params.alpha * params.beta * R
    return lam, R


def neg_loglik(times, T: float, params: HawkesParams) -> float:
    times = np.asarray(times, dtype=float)
    if len(times) == 0:
        return params.background.integral(0.0, T)
    lam, _ = intensity_at_events(times, params)
    if np.any(lam <= 0) or not np.all(np.isfinite(lam)):
        return 1e12
    bg_int = params.background.integral(0.0, T)
    comp_excite = params.alpha * np.sum(1.0 - np.exp(-params.beta * (T - times)))
    ll = np.sum(np.log(lam)) - bg_int - comp_excite
    if not np.isfinite(ll):
        return 1e12
    return float(-ll)


def compensator_at_events(times, T: float, params: HawkesParams) -> np.ndarray:
    """Lambda(t_i) for each event, for the time-rescaling goodness-of-fit test."""
    times = np.asarray(times, dtype=float)
    n = len(times)
    if n == 0:
        return np.array([])
    R = _excitation_recursion(times, params.beta)
    counts = np.arange(n)  # prior-event count for 0-indexed i is i
    excite = params.alpha * (counts - R)  # sum_{j<i}(1 - exp(-beta (t_i - t_j)))
    bg = np.array([params.background.integral(0.0, float(t)) for t in times])
    return bg + excite
