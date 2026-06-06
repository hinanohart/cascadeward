"""Parametric bootstrap confidence interval for the branching ratio.

Simulate B traces from the fitted process, refit each, and take percentiles of
the recovered branching ratio. Also returns the bootstrap CV of beta (used by
the identifiability veto) and how many samples hit the explosion cap (a
super-critical signature, not an error).
"""

from __future__ import annotations

import numpy as np

from .likelihood import HawkesParams
from .mle import fit_hawkes, simulate_hawkes


def bootstrap_ci(
    params: HawkesParams,
    T: float,
    B: int = 200,
    n_blocks: int = 1,
    seed: int = 0,
    ci: tuple[float, float] = (2.5, 97.5),
    max_events: int = 30000,
    refit_starts: int = 2,
):
    rng = np.random.default_rng(seed)
    ns: list[float] = []
    betas: list[float] = []
    n_explode = 0
    for _ in range(B):
        s = int(rng.integers(0, 2**31 - 1))
        times, trunc = simulate_hawkes(
            params.background, params.alpha, params.beta, T, seed=s, max_events=max_events
        )
        if trunc:
            n_explode += 1
        if len(times) < 10:
            continue
        try:
            p, _ = fit_hawkes(times, T, n_blocks=n_blocks, n_starts=refit_starts, seed=s)
        except Exception:
            continue
        ns.append(p.alpha)
        betas.append(p.beta)

    ns_arr = np.asarray(ns, dtype=float)
    betas_arr = np.asarray(betas, dtype=float)
    if len(ns_arr) < 5:
        return {
            "lo": float("nan"),
            "hi": float("nan"),
            "std": float("nan"),
            "beta_cv": float("nan"),
            "n_explode": n_explode,
            "B_effective": int(len(ns_arr)),
            "samples": ns_arr.tolist(),
        }
    lo, hi = np.percentile(ns_arr, ci)
    beta_mean = float(np.mean(betas_arr))
    beta_cv = float(np.std(betas_arr) / beta_mean) if beta_mean > 0 else float("nan")
    return {
        "lo": float(lo),
        "hi": float(hi),
        "std": float(np.std(ns_arr)),
        "beta_cv": beta_cv,
        "n_explode": n_explode,
        "B_effective": int(len(ns_arr)),
        "samples": ns_arr.tolist(),
    }
