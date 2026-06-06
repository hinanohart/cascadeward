"""The self-veto must be able to say 'I cannot certify this' -- the core honesty."""

import math

import cascadeward as cw
from cascadeward.criticality.identifiability import self_veto
from cascadeward.events import EventStream, Fidelity
from cascadeward.ingest import generate


def test_g4_too_few_events_unidentified():
    # tiny window -> very few events -> must withhold a verdict
    s = generate(alpha=0.5, beta=2.0, T=40, mu=0.2, seed=11)
    r = cw.score(s, boot=40, seed=11)
    assert r.verdict == "UNIDENTIFIED"
    assert any("too_few_events" in v for v in r.identifiability["vetoes"])


def test_aggregate_fidelity_refuses_fit():
    s = EventStream.from_times([1.0, 2.0, 3.0, 4.0], fidelity=Fidelity.AGGREGATE)
    r = cw.score(s, boot=10, seed=0)
    assert r.verdict == "UNIDENTIFIED"
    assert "aggregate_fidelity_fit_refused" in r.identifiability["vetoes"]
    assert r.exit_code == 20


def test_aggregate_report_has_full_branching_keys():
    # the AGGREGATE refusal report must carry the SAME branching_ratio_n key set as
    # a normal fit (schema "cascadeward-report/1" is a contract): a consumer that
    # reads branching_ratio_n["n_explode"] must not KeyError on a refusal.
    s = EventStream.from_times([1.0, 2.0, 3.0, 4.0], fidelity=Fidelity.AGGREGATE)
    r = cw.score(s, boot=10, seed=0)
    assert set(r.branching_ratio_n) == {
        "point",
        "ci",
        "level",
        "boot_B",
        "boot_requested",
        "n_explode",
    }


def test_bootstrap_explosion_bias_vetoes():
    # when the majority of bootstrap replicates ran away to the event cap, the CI
    # is biased toward sub-critical; the veto must refuse to certify off it.
    quiet = self_veto(
        n=0.6,
        ci_lo=0.5,
        ci_hi=0.7,
        n_events=2000,
        fidelity=Fidelity.NATIVE_EVENT,
        beta=2.0,
        beta_cv=0.05,
        ks_p=0.5,
        n_explode=0,
        boot_B=200,
    )
    runaway = self_veto(
        n=0.6,
        ci_lo=0.5,
        ci_hi=0.7,
        n_events=2000,
        fidelity=Fidelity.NATIVE_EVENT,
        beta=2.0,
        beta_cv=0.05,
        ks_p=0.5,
        n_explode=180,
        boot_B=200,
    )
    assert quiet.ok, quiet.vetoes
    assert not runaway.ok
    assert any("explosion" in v for v in runaway.vetoes)


def test_explosion_does_not_suppress_supercritical_alarm():
    # a fully-runaway bootstrap whose CI is ITSELF super-critical must still report
    # super: the explosion veto must never mute the core runaway alarm.
    res = self_veto(
        n=1.25,
        ci_lo=1.19,
        ci_hi=1.27,
        n_events=2000,
        fidelity=Fidelity.NATIVE_EVENT,
        beta=2.0,
        beta_cv=0.05,
        ks_p=0.5,
        n_explode=200,
        boot_B=200,
    )
    assert not any("explosion" in v for v in res.vetoes), res.vetoes
    assert res.ok, res.vetoes


def test_reconstructed_fidelity_tightens_ci_threshold():
    # same CI width 0.30: native passes width gate, reconstructed vetoes it
    native = self_veto(
        n=0.6,
        ci_lo=0.45,
        ci_hi=0.75,
        n_events=500,
        fidelity=Fidelity.NATIVE_EVENT,
        beta=2.0,
        beta_cv=0.1,
        ks_p=0.5,
    )
    recon = self_veto(
        n=0.6,
        ci_lo=0.45,
        ci_hi=0.75,
        n_events=500,
        fidelity=Fidelity.RECONSTRUCTED,
        beta=2.0,
        beta_cv=0.1,
        ks_p=0.5,
    )
    assert native.ok, native.vetoes
    assert not recon.ok
    assert any("ci_too_wide" in v for v in recon.vetoes)


def test_ci_crossing_critical_vetoes():
    res = self_veto(
        n=1.0,
        ci_lo=0.85,
        ci_hi=1.15,
        n_events=800,
        fidelity=Fidelity.NATIVE_EVENT,
        beta=2.0,
        beta_cv=0.1,
        ks_p=0.5,
    )
    assert not res.ok
    assert "ci_crosses_critical" in res.vetoes


def test_kernel_misspecification_vetoes():
    res = self_veto(
        n=0.6,
        ci_lo=0.55,
        ci_hi=0.65,
        n_events=800,
        fidelity=Fidelity.NATIVE_EVENT,
        beta=2.0,
        beta_cv=0.1,
        ks_p=0.001,
    )
    assert not res.ok
    assert any("kernel_misspecified" in v for v in res.vetoes)


def test_clean_case_passes():
    res = self_veto(
        n=0.6,
        ci_lo=0.55,
        ci_hi=0.65,
        n_events=2000,
        fidelity=Fidelity.NATIVE_EVENT,
        beta=2.0,
        beta_cv=0.05,
        ks_p=0.5,
    )
    assert res.ok
    assert res.vetoes == []


def test_nan_ci_unavailable_vetoes():
    res = self_veto(
        n=0.6,
        ci_lo=math.nan,
        ci_hi=math.nan,
        n_events=800,
        fidelity=Fidelity.NATIVE_EVENT,
        beta=2.0,
        beta_cv=math.nan,
        ks_p=math.nan,
    )
    assert not res.ok
    assert "bootstrap_ci_unavailable" in res.vetoes
