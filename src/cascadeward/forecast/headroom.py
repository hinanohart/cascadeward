"""Qualitative headroom only (v0.1).

A *quantitative* "QPS-to-critical" number is deliberately NOT produced. For the
exponential kernel the branching ratio n = alpha is independent of the background
rate mu, so naively scaling arrival load does not move n toward 1. A faithful
quantitative headroom needs alpha modelled as a function of cache pressure,
alpha(gpu_cache_usage), fitted across several load points -- that is the v0.2
roadmap. Emitting a number here would be theatre.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Headroom:
    status: str
    sensitivity_sign: str
    note: str


def qualitative_headroom(verdict) -> Headroom:
    if verdict.label == "UNIDENTIFIED":
        return Headroom(
            status="unknown",
            sensitivity_sign="n/a",
            note=(
                "Identifiability veto active: headroom is not estimated "
                "(doing so would fabricate a number the data cannot support)."
            ),
        )
    endo = verdict.endogeneity
    if verdict.level == "sub_critical":
        return Headroom(
            status="estimated_qualitative",
            sensitivity_sign="positive",
            note=(
                f"Sub-critical: preemption bursts are absorbed (endogeneity {endo:.2f}). "
                "Quantitative QPS-to-critical is intentionally not estimated in v0.1 "
                "(n is mu-independent under the exp kernel; see README 'Why no number')."
            ),
        )
    return Headroom(
        status="estimated_qualitative",
        sensitivity_sign="negative",
        note=(
            f"Super-critical: one preemption tends to avalanche (endogeneity {endo:.2f}). "
            "The actionable lever is self-excitation (scheduler/config), not arrival load alone."
        ),
    )
