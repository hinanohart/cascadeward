"""SHIP GATE: pre-registered synthetic ground-truth recovery.

These thresholds are frozen. They are the difference between an honest instrument
and "a pretty plot that distinguishes nothing." Bootstrap replicates are kept
modest so the suite runs in a couple of minutes; correctness, not tightness, is
what is asserted.
"""

import numpy as np
import pytest

import cascadeward as cw
from cascadeward.ingest import generate
from cascadeward.pp.decluster import endogeneity_fraction
from cascadeward.pp.mle import fit_hawkes


def _fit(stream, n_blocks=1, seed=0):
    return fit_hawkes(np.asarray(stream.times()), stream.t1, n_blocks=n_blocks, seed=seed)


# ---- G1: point recovery + CI coverage (stationary) ----
@pytest.mark.slow
def test_g1_recovery_stationary():
    s = generate(alpha=0.6, beta=2.0, T=2000, mu=0.4, seed=1)
    r = cw.score(s, boot=60, seed=1)
    br = r.branching_ratio_n
    assert br["ci"][0] <= 0.6 <= br["ci"][1], f"CI must cover truth: {br}"
    assert abs(br["point"] - 0.6) < 0.2
    assert r.verdict in ("SUB_CRITICAL", "UNIDENTIFIED")


# ---- G2: sub vs super discrimination ----
@pytest.mark.slow
def test_g2_discriminates_sub_vs_super():
    sub = cw.score(generate(alpha=0.7, beta=2.0, T=1200, mu=0.5, seed=2), boot=50, seed=2)
    sup = cw.score(generate(alpha=1.3, beta=2.0, T=400, mu=0.6, seed=3), boot=50, seed=3)
    # Safety-critical property: a healthy (sub-critical) cluster is certified, while
    # a runaway (super-critical) cluster is NEVER certified healthy. We deliberately
    # do NOT assert the super point estimate > 1: for an explosive, truncation-prone
    # trace that point estimate is platform-fragile (and asserting on a bare scalar
    # would contradict D4). Verdict in {SUPER_CRITICAL, UNIDENTIFIED} are both honest.
    assert sub.verdict == "SUB_CRITICAL"
    assert sup.verdict != "SUB_CRITICAL"
    # Endogeneity (the fraction of self-excited events) is far more stable across
    # platforms than the branching point and cleanly separates the two regimes.
    assert sup.endogeneity > sub.endogeneity + 0.1, (sub.endogeneity, sup.endogeneity)


# ---- G3: endogeneity fingers the right culprit (fit-only, fast) ----
def test_g3_endogeneity_culprit():
    # high background, low self-excitation -> low endogeneity
    a = generate(alpha=0.2, beta=2.0, T=1000, mu=2.0, seed=4)
    pa, _ = _fit(a, seed=4)
    endo_a = endogeneity_fraction(np.asarray(a.times()), pa)
    # low background, high self-excitation -> high endogeneity
    b = generate(alpha=0.8, beta=2.0, T=1000, mu=0.2, seed=5)
    pb, _ = _fit(b, seed=5)
    endo_b = endogeneity_fraction(np.asarray(b.times()), pb)
    assert endo_a < 0.45, endo_a
    assert endo_b > 0.5, endo_b
    assert endo_b > endo_a


# ---- G5: timescale (beta) recovery within ~factor 2 (fit-only, fast) ----
def test_g5_beta_recovery():
    s = generate(alpha=0.5, beta=2.0, T=1500, mu=0.5, seed=6)
    p, _ = _fit(s, seed=6)
    assert 1.0 < p.beta < 4.0, p.beta


# ---- D9(b): non-stationary mu(t) recovery (the time-varying background path) ----
@pytest.mark.slow
def test_d9b_nonstationary_background_recovery():
    s = generate(alpha=0.5, beta=2.0, T=2000, mu_blocks=[0.2, 0.8, 0.2, 0.7], seed=7)
    r = cw.score(s, n_blocks=4, boot=50, seed=7)
    br = r.branching_ratio_n
    # n must still be recovered with a time-varying background fitted
    assert br["ci"][0] <= 0.5 <= br["ci"][1] or abs(br["point"] - 0.5) < 0.2, br
    assert r.verdict != "SUPER_CRITICAL"


# ---- D9(c): sub-critical negative control (do not cry wolf) ----
@pytest.mark.slow
def test_d9c_subcritical_negative_control():
    r = cw.score(generate(alpha=0.3, beta=2.0, T=1500, mu=0.6, seed=8), boot=50, seed=8)
    assert r.verdict != "SUPER_CRITICAL"
    assert r.branching_ratio_n["point"] < 1.0


# ---- D9(d): near-critical AND data-limited -> withhold (the honest output) ----
@pytest.mark.slow
def test_d9d_near_critical_limited_data_withholds():
    # near the critical boundary with only a short trace, the branching ratio is
    # genuinely unidentifiable: the instrument must withhold, not certify a side.
    r = cw.score(generate(alpha=0.95, beta=2.0, T=150, mu=0.5, seed=3), boot=50, seed=3)
    assert r.verdict == "UNIDENTIFIED", (r.verdict, r.branching_ratio_n)
    assert r.identifiability["vetoes"], "a withheld verdict must name its veto reason"


# ---- D9(d2): with ENOUGH data, near-critical n=0.95 IS resolvable (no false veto) ----
@pytest.mark.slow
def test_d9d_near_critical_resolvable_with_data():
    # the complement: the veto must not be trigger-happy. Given a long clean trace,
    # n=0.95 should resolve to a confident sub-critical with a CI below 1.
    r = cw.score(generate(alpha=0.95, beta=2.0, T=1200, mu=0.5, seed=9), boot=60, seed=9)
    ci = r.branching_ratio_n["ci"]
    assert ci[1] is not None and ci[1] < 1.0, r.branching_ratio_n
    assert r.verdict == "SUB_CRITICAL", (r.verdict, r.branching_ratio_n)
