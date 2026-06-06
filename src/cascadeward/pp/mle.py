"""Maximum-likelihood fit and exact simulation of the exp-Hawkes process.

Fitting uses a softplus reparameterisation (mu_k, alpha, beta > 0) and multi-start
L-BFGS-B. ``alpha`` (= branching ratio n) is *not* capped below 1, so the
super-critical regime can be detected. Optimisation is gradient-free
(finite-difference) for robustness; the kernel is exponential so each likelihood
evaluation is O(N).

Simulation uses the exact immigration-birth (cluster) representation, which is
correct for any exp kernel and trivially exposes the branching structure.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from .background import PiecewiseConstantBackground
from .likelihood import HawkesParams, neg_loglik


def _softplus(x):
    return np.logaddexp(0.0, x)


def _inv_softplus(y: float) -> float:
    y = max(float(y), 1e-9)
    return float(np.log(np.expm1(y))) if y < 30 else y


def _unpack(theta, n_blocks: int, edges) -> HawkesParams:
    mu = _softplus(theta[:n_blocks])
    alpha = float(_softplus(theta[n_blocks]))
    beta = max(float(_softplus(theta[n_blocks + 1])), 1e-8)
    bg = PiecewiseConstantBackground(edges, mu)
    return HawkesParams(bg, alpha, beta)


def fit_hawkes(times, T: float, n_blocks: int = 1, n_starts: int = 8, seed: int = 0):
    """Fit a marked-free exp-Hawkes with piecewise-constant mu(t).

    Returns ``(HawkesParams, diag)``. ``diag`` carries convergence info; callers
    must not trust a number whose ``converged`` is False without the veto layer.
    """
    times = np.asarray(times, dtype=float)
    N = len(times)
    edges = np.linspace(0.0, T, n_blocks + 1)
    rng = np.random.default_rng(seed)

    dt = np.diff(times) if N > 1 else np.array([T / max(N, 1)])
    med_dt = float(np.median(dt)) if len(dt) else T
    beta0_base = 1.0 / max(med_dt, 1e-6)
    rate = N / max(T, 1e-9)

    starts = []
    for a in (0.3, 0.6, 0.9, 1.2):
        for bm in (1.0, 4.0):
            mu0 = max(rate * (1.0 - min(a, 0.95)), 1e-6)
            starts.append((np.full(n_blocks, mu0), a, beta0_base * bm))
    while len(starts) < n_starts:
        starts.append(
            (
                np.full(n_blocks, max(rate * 0.5 * (1.0 + rng.random()), 1e-6)),
                0.3 + rng.random(),
                beta0_base * (0.5 + 2.0 * rng.random()),
            )
        )
    starts = starts[:n_starts]

    best = None
    for mu0, a0, b0 in starts:
        theta0 = np.concatenate(
            [[_inv_softplus(m) for m in mu0], [_inv_softplus(a0), _inv_softplus(b0)]]
        )
        try:
            res = minimize(
                lambda th: neg_loglik(times, T, _unpack(th, n_blocks, edges)),
                theta0,
                method="L-BFGS-B",
            )
        except Exception:
            continue
        if not np.isfinite(res.fun):
            continue
        if best is None or res.fun < best.fun:
            best = res

    if best is None:
        raise RuntimeError("Hawkes MLE failed to converge from any start")

    params = _unpack(best.x, n_blocks, edges)
    diag = {
        "nll": float(best.fun),
        "converged": bool(best.success),
        "n_starts": n_starts,
        "n_events": int(N),
        "edges": edges.tolist(),
    }
    return params, diag


def simulate_hawkes(
    background: PiecewiseConstantBackground,
    alpha: float,
    beta: float,
    T: float,
    seed: int = 0,
    max_events: int = 200000,
):
    """Exact immigration-birth simulation. Returns (sorted_times, truncated)."""
    rng = np.random.default_rng(seed)
    edges = background.edges
    rates = background.rates

    times: list[float] = []
    for k in range(len(rates)):
        w = float(edges[k + 1] - edges[k])
        lam = float(rates[k]) * w
        if lam <= 0:
            continue
        n_imm = rng.poisson(lam)
        if n_imm:
            times.extend((edges[k] + w * rng.random(n_imm)).tolist())

    queue = list(times)
    truncated = False
    while queue:
        if len(times) > max_events:
            truncated = True
            break
        tp = queue.pop()
        n_off = rng.poisson(alpha)
        for _ in range(int(n_off)):
            child = tp + rng.exponential(1.0 / beta)
            if child <= T:
                times.append(float(child))
                queue.append(float(child))

    arr = np.sort(np.array([t for t in times if 0.0 <= t <= T], dtype=float))
    return arr, truncated
