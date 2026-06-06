"""Filimonov-Sornette identifiability self-veto.

Branching-ratio estimation is famously fragile near n ~ 1, under non-stationarity,
and under kernel misspecification. This layer refuses to emit a point verdict
when any of a set of pre-registered triggers fire. ``UNIDENTIFIED`` is a normal,
honest output -- the alternative (always confidently reporting an n) is the R8
failure mode this whole project exists to avoid.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class IdentifiabilityResult:
    ok: bool
    vetoes: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def self_veto(
    *,
    n: float,
    ci_lo: float,
    ci_hi: float,
    n_events: int,
    fidelity,
    beta: float,
    beta_cv: float,
    ks_p: float,
) -> IdentifiabilityResult:
    vetoes: list[str] = []
    notes: list[str] = []
    fid = getattr(fidelity, "value", str(fidelity))

    # (6) fidelity gating
    if fid == "aggregate":
        vetoes.append("aggregate_fidelity_fit_refused")
    w_max = 0.25 if fid == "reconstructed" else 0.40

    # (1) sample size
    if n_events < 50:
        vetoes.append("too_few_events(<50)")
    elif n_events < 200:
        notes.append("low_event_count(<200): reduced confidence")

    # (2) CI width / critical crossing
    if math.isnan(ci_lo) or math.isnan(ci_hi):
        vetoes.append("bootstrap_ci_unavailable")
    else:
        width = ci_hi - ci_lo
        if width > w_max:
            vetoes.append(f"ci_too_wide(>{w_max})")
        if ci_lo < 1.0 < ci_hi:
            vetoes.append("ci_crosses_critical")
        # (3) near-critical instability
        if not math.isnan(n) and abs(n - 1.0) < 0.1 and width > 0.2:
            vetoes.append("near_critical_unstable(|n-1|<0.1)")

    # (4) timescale identifiability
    if not math.isnan(beta_cv) and beta_cv > 0.5:
        vetoes.append("timescale_unidentified(beta_cv>0.5)")

    # (5) kernel goodness-of-fit
    if not math.isnan(ks_p) and ks_p < 0.05:
        vetoes.append("kernel_misspecified(ks_p<0.05)")

    return IdentifiabilityResult(ok=(len(vetoes) == 0), vetoes=vetoes, notes=notes)
