"""Endogeneity (Zhuang background probability) and goodness-of-fit.

endogeneity = 1 - mean_i( mu(t_i) / lambda(t_i) ) is the fraction of events
attributable to self-excitation rather than the exogenous arrival rate -- the
operator's lever (a high-n cluster driven by endogeneity points at config, not
traffic).
"""

from __future__ import annotations

import numpy as np
from scipy import stats

from .likelihood import HawkesParams, compensator_at_events, intensity_at_events


def endogeneity_fraction(times, params: HawkesParams) -> float:
    times = np.asarray(times, dtype=float)
    if len(times) == 0:
        return float("nan")
    lam, _ = intensity_at_events(times, params)
    mu = params.background.at(times)
    rho_bg = np.clip(mu / lam, 0.0, 1.0)
    return float(1.0 - np.mean(rho_bg))


def ks_goodness_of_fit(times, T: float, params: HawkesParams) -> float:
    """Time-rescaling KS p-value.

    Under a correct model the compensator-rescaled inter-event gaps are i.i.d.
    Exp(1); a small p-value flags kernel misspecification (veto trigger).
    """
    times = np.asarray(times, dtype=float)
    if len(times) < 20:
        return float("nan")
    Lam = compensator_at_events(times, T, params)
    dtau = np.diff(Lam)
    dtau = dtau[dtau >= 0]
    if len(dtau) < 10:
        return float("nan")
    res = stats.kstest(dtau, "expon", args=(0, 1))
    return float(res.pvalue)
