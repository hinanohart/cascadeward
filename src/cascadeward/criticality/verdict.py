"""Final verdict and exit-code contract."""

from __future__ import annotations

from dataclasses import dataclass

from .branching import SUB, SUPER, BranchingResult
from .identifiability import IdentifiabilityResult

_EXIT = {"SUB_CRITICAL": 0, "SUPER_CRITICAL": 10, "UNIDENTIFIED": 20}


@dataclass
class Verdict:
    label: str  # SUB_CRITICAL | SUPER_CRITICAL | UNIDENTIFIED
    n: float
    ci_lo: float
    ci_hi: float
    level: str
    endogeneity: float
    vetoes: list[str]
    notes: list[str]

    @property
    def exit_code(self) -> int:
        return _EXIT.get(self.label, 1)


def decide(branch: BranchingResult, ident: IdentifiabilityResult) -> Verdict:
    if not ident.ok:
        label = "UNIDENTIFIED"
    elif branch.level == SUB:
        label = "SUB_CRITICAL"
    elif branch.level == SUPER:
        label = "SUPER_CRITICAL"
    else:
        label = "UNIDENTIFIED"
    return Verdict(
        label=label,
        n=branch.n,
        ci_lo=branch.ci_lo,
        ci_hi=branch.ci_hi,
        level=branch.level,
        endogeneity=branch.endogeneity,
        vetoes=ident.vetoes,
        notes=ident.notes,
    )
