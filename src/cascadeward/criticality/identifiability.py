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

# --- Pre-registered veto thresholds (this is the auditable core contract: the
# whole value of the instrument is that these are fixed, named, and greppable). ---
MIN_EVENTS_VETO = 50  # (1) below this, refuse outright
LOW_EVENTS_NOTE = 200  # (1) below this, note reduced confidence
CI_WIDTH_MAX_NATIVE = 0.40  # (2) max CI width (native/jsonl/synthetic sources)
CI_WIDTH_MAX_RECON = 0.25  # (2) tighter ceiling for reconstructed fidelity
NEAR_CRITICAL_BAND = 0.1  # (3) |n-1| within this is "near critical"
NEAR_CRITICAL_WIDTH = 0.2  # (3) ...and a CI wider than this is unstable
BETA_CV_MAX = 0.5  # (4) timescale identifiability
KS_PVALUE_MIN = 0.05  # (5) kernel goodness-of-fit
EXPLOSION_VETO_FRAC = 0.5  # (7) majority of bootstrap replicates ran away -> CI biased


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
    n_explode: int = 0,
    boot_B: int = 0,
) -> IdentifiabilityResult:
    vetoes: list[str] = []
    notes: list[str] = []
    fid = getattr(fidelity, "value", str(fidelity))

    # (6) fidelity gating
    if fid == "aggregate":
        vetoes.append("aggregate_fidelity_fit_refused")
    w_max = CI_WIDTH_MAX_RECON if fid == "reconstructed" else CI_WIDTH_MAX_NATIVE

    # (1) sample size
    if n_events < MIN_EVENTS_VETO:
        vetoes.append(f"too_few_events(<{MIN_EVENTS_VETO})")
    elif n_events < LOW_EVENTS_NOTE:
        notes.append(f"low_event_count(<{LOW_EVENTS_NOTE}): reduced confidence")

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
        if not math.isnan(n) and abs(n - 1.0) < NEAR_CRITICAL_BAND and width > NEAR_CRITICAL_WIDTH:
            vetoes.append(f"near_critical_unstable(|n-1|<{NEAR_CRITICAL_BAND})")

        # (7) bootstrap explosion bias: the majority of simulated replicates ran
        # away to the event cap, *yet the CI still came back sub-critical*. That
        # CI was taken over the surviving, truncated (low-n) subset, so it is
        # biased downward -- a near/super-critical process laundered into a
        # confident "sub". Refuse. (When the CI is itself >= 1 the super-critical
        # verdict is correct and must stand -- we must NOT suppress the alarm.)
        if boot_B > 0 and n_explode > EXPLOSION_VETO_FRAC * boot_B and ci_hi < 1.0:
            vetoes.append(f"bootstrap_explosion_bias(>{EXPLOSION_VETO_FRAC:.0%}_runaway)")

    # (4) timescale identifiability
    if not math.isnan(beta_cv) and beta_cv > BETA_CV_MAX:
        vetoes.append(f"timescale_unidentified(beta_cv>{BETA_CV_MAX})")

    # (5) kernel goodness-of-fit
    if not math.isnan(ks_p) and ks_p < KS_PVALUE_MIN:
        vetoes.append(f"kernel_misspecified(ks_p<{KS_PVALUE_MIN})")

    return IdentifiabilityResult(ok=(len(vetoes) == 0), vetoes=vetoes, notes=notes)
