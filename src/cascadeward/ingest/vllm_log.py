"""vLLM scheduler-log adapter -- the only NATIVE per-event preemption source.

vLLM exposes preemptions per-event ONLY as a scheduler WARNING log line; the
Prometheus metric ``vllm:num_preemptions_total`` is a cumulative Counter, not a
per-event stream (that path is RECONSTRUCTED fidelity, deferred to v0.2). So this
adapter scrapes lines like:

    WARNING 06-06 08:30:01 scheduler.py:1680] Sequence group 42 is preempted by
    PreemptionMode.RECOMPUTE mode because there is not enough KV cache space ...

Timestamps lack a year; we map MM-DD HH:MM:SS to a monotonic relative-seconds
axis (exact within a month, which is all a preemption storm needs).
"""

from __future__ import annotations

import re

from ..events import Event, EventStream, EventType, Fidelity

_PREEMPT_RE = re.compile(
    r"Sequence group (?P<sid>\S+) is preempted by PreemptionMode\.(?P<mode>RECOMPUTE|SWAP)"
)
_TS_RE = re.compile(
    r"(?P<mon>\d{2})-(?P<day>\d{2})\s+(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2})(?:[.,](?P<ms>\d+))?"
)


def _ts_to_seconds(m: re.Match) -> float:
    mon = int(m.group("mon"))
    day = int(m.group("day"))
    h = int(m.group("h"))
    mi = int(m.group("m"))
    s = int(m.group("s"))
    ms = m.group("ms")
    frac = float("0." + ms) if ms else 0.0
    # month*31 is a calendar-free monotonic surrogate; exact within a month.
    return ((mon * 31 + day) * 86400) + h * 3600 + mi * 60 + s + frac


def parse_vllm_log(path: str) -> EventStream:
    events: list[Event] = []
    times: list[float] = []
    for line in open(path, encoding="utf-8"):
        pm = _PREEMPT_RE.search(line)
        if not pm:
            continue
        tm = _TS_RE.search(line)
        if not tm:
            continue
        t = _ts_to_seconds(tm)
        times.append(t)
        events.append(
            Event(
                t=t,
                type=EventType.PREEMPT,
                seq_id=pm.group("sid"),
                mode=pm.group("mode"),
            )
        )
    if not events:
        raise ValueError(
            f"no vLLM preemption lines found in {path} "
            "(need scheduler WARNING lines; ensure disable_log_stats=False)"
        )
    # The MM-DD surrogate axis (see _ts_to_seconds) is monotone within a year but
    # jumps backwards by ~a year of seconds at a Dec->Jan rollover. Detect that
    # large backward step and refuse, rather than silently emitting negative
    # inter-event gaps that normalisation would launder into a garbage fit.
    for prev, cur in zip(times, times[1:], strict=False):
        if cur < prev - 86400.0:
            raise ValueError(
                f"non-monotonic vLLM timestamps in {path}: {prev:.1f} -> {cur:.1f} "
                "(>1 day backwards). The year-free MM-DD axis cannot span a year "
                "boundary; split the log so each file stays within one calendar year."
            )
    return EventStream(
        events=tuple(events),
        t0=min(times),
        t1=max(times),
        fidelity=Fidelity.NATIVE_EVENT,
        source=f"vllm_log:{path}",
    )
