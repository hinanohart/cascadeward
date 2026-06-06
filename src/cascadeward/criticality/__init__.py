"""Interpretation layer: turn a fit into a guarded verdict.

Fitting and judgement are deliberately separated -- the self-veto can refuse to
issue a verdict even when the optimiser 'converged', which is the whole point of
an honest criticality instrument.
"""

from .branching import BranchingResult, classify
from .identifiability import IdentifiabilityResult, self_veto
from .verdict import Verdict, decide

__all__ = [
    "BranchingResult",
    "classify",
    "IdentifiabilityResult",
    "self_veto",
    "Verdict",
    "decide",
]
