import json

import pytest

from cascadeward.events import Fidelity
from cascadeward.ingest import load, parse_jsonl, parse_vllm_log

VLLM_LOG = """\
INFO 06-06 08:30:00 engine.py:100] Starting up
WARNING 06-06 08:30:01 scheduler.py:1680] Sequence group 42 is preempted by PreemptionMode.RECOMPUTE mode because there is not enough KV cache space. This can affect the end-to-end performance.
WARNING 06-06 08:30:01 scheduler.py:1680] Sequence group 43 is preempted by PreemptionMode.SWAP mode because there is not enough KV cache space.
INFO 06-06 08:30:02 metrics.py:50] Avg generation throughput: 12 tokens/s
WARNING 06-06 08:30:03 scheduler.py:1680] Sequence group 44 is preempted by PreemptionMode.RECOMPUTE mode because there is not enough KV cache space.
"""


def test_vllm_log_parses_preemptions(tmp_path):
    p = tmp_path / "server.log"
    p.write_text(VLLM_LOG, encoding="utf-8")
    s = parse_vllm_log(str(p))
    assert s.n_events == 3
    assert s.fidelity == Fidelity.NATIVE_EVENT
    modes = {e.mode for e in s.events}
    assert modes == {"RECOMPUTE", "SWAP"}
    sids = {e.seq_id for e in s.events}
    assert sids == {"42", "43", "44"}


def test_vllm_log_no_preemptions_raises(tmp_path):
    p = tmp_path / "quiet.log"
    p.write_text("INFO 06-06 08:30:00 engine.py:100] all good\n", encoding="utf-8")
    with pytest.raises(ValueError):
        parse_vllm_log(str(p))


def test_jsonl_parses(tmp_path):
    p = tmp_path / "trace.jsonl"
    lines = [
        {"t": 0.0, "type": "preempt", "marks": {"seq_id": "a", "freed_blocks": 3}},
        {"t": 1.5, "type": "recompute"},
        {"t": 2.0},
    ]
    p.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")
    s = parse_jsonl(str(p))
    assert s.n_events == 3
    assert s.events[0].freed_blocks == 3


def test_load_auto_dispatch(tmp_path):
    p = tmp_path / "trace.jsonl"
    p.write_text(json.dumps({"t": 1.0}) + "\n", encoding="utf-8")
    s = load(str(p))
    assert s.n_events == 1
