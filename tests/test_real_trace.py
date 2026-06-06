"""H6: behaviour on real-format traces.

Honest withhold on a sparse captured-format trace; no spurious veto on adequate
data (the veto must not cry wolf). These guard against both failure modes of an
identifiability gate: certifying garbage, and refusing everything.
"""

import pathlib

import pytest

import cascadeward as cw
from cascadeward.ingest import generate, parse_vllm_log

EX = pathlib.Path(__file__).resolve().parent.parent / "examples" / "sample_vllm.log"


def test_real_format_sparse_trace_withholds_honestly():
    # the shipped vLLM scheduler-log example has only a handful of preemptions:
    # the instrument must withhold (too few events), not fabricate a branching ratio.
    stream = parse_vllm_log(str(EX))
    r = cw.score(stream, boot=10, seed=0)
    assert r.verdict == "UNIDENTIFIED"
    assert any("too_few_events" in v for v in r.identifiability["vetoes"])
    assert r.exit_code == 20


@pytest.mark.slow
def test_adequate_trace_veto_does_not_fire_spuriously():
    # complement of the veto tests: an adequate, healthy sub-critical trace must
    # pass the identifiability gate cleanly (no crying wolf).
    stream = generate(alpha=0.5, beta=2.0, T=1500, mu=0.6, seed=12)
    r = cw.score(stream, boot=50, seed=12)
    assert r.identifiability["ok"], r.identifiability["vetoes"]
    assert r.verdict == "SUB_CRITICAL"
