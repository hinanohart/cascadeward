"""Point-process layer: pure math, no serving vocabulary.

Kept lexically separate from survival/hazard language on purpose: this is a
self-exciting *branching* process (immigration + offspring), not a hazard /
risk-set model.
"""

from .background import PiecewiseConstantBackground
from .bootstrap import bootstrap_ci
from .decluster import endogeneity_fraction, ks_goodness_of_fit
from .kernels import ExpKernel
from .likelihood import HawkesParams, compensator_at_events, intensity_at_events, neg_loglik
from .mle import fit_hawkes, simulate_hawkes

__all__ = [
    "ExpKernel",
    "PiecewiseConstantBackground",
    "HawkesParams",
    "neg_loglik",
    "intensity_at_events",
    "compensator_at_events",
    "fit_hawkes",
    "simulate_hawkes",
    "bootstrap_ci",
    "endogeneity_fraction",
    "ks_goodness_of_fit",
]
