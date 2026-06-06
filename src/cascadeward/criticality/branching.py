"""Branching ratio n and its 3-level classification.

n is reported as a level + CI, never as a bare point scalar (a single proxy
number invites overconfident verdicts). The point estimate is kept for the
report but the *verdict* is driven by the CI relative to the critical value 1.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

SUB = "sub_critical"
NEAR = "near_critical"
SUPER = "super_critical"


@dataclass
class BranchingResult:
    n: float
    ci_lo: float
    ci_hi: float
    level: str
    endogeneity: float


def classify(n: float, ci_lo: float, ci_hi: float) -> str:
    if math.isnan(ci_lo) or math.isnan(ci_hi):
        return NEAR
    if ci_lo < 1.0 < ci_hi:
        return NEAR
    if ci_hi < 1.0:
        return SUB
    if ci_lo >= 1.0:
        return SUPER
    return NEAR
