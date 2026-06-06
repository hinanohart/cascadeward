import numpy as np

from cascadeward.events import Event, EventStream, EventType, Fidelity, normalize


def test_from_times_roundtrip():
    s = EventStream.from_times([10.0, 11.0, 12.5], source="t")
    assert s.n_events == 3
    assert s.t0 == 10.0
    assert s.times() == (10.0, 11.0, 12.5)


def test_normalize_shifts_to_relative():
    s = EventStream.from_times([1000.0, 1001.0, 1003.0], t0=1000.0, t1=1004.0)
    ns, info = normalize(s)
    assert ns.t0 == 0.0
    assert info["t0_shift"] == 1000.0
    assert ns.times()[0] == 0.0
    assert abs(info["duration"] - 4.0) < 1e-9


def test_normalize_jitters_coincident_deterministically():
    # three events at the exact same timestamp must become strictly increasing
    evs = tuple(Event(t=5.0, type=EventType.PREEMPT, seq_id=str(i)) for i in range(3))
    s = EventStream(events=evs, t0=0.0, t1=10.0)
    ns, info = normalize(s)
    ts = np.array(ns.times())
    assert np.all(np.diff(ts) > 0), "times must be strictly increasing after jitter"
    assert info["n_jittered"] == 2  # first stays, two nudged
    # determinism: same input -> same output
    ns2, info2 = normalize(s)
    assert ns.times() == ns2.times()
    assert info2["n_jittered"] == 2


def test_aggregate_fidelity_preserved():
    s = EventStream.from_times([1.0, 2.0], fidelity=Fidelity.AGGREGATE)
    assert s.fidelity == Fidelity.AGGREGATE
