"""Canonical event model for cascadeward.

A *domain-agnostic* marked temporal point process. Only the ``ingest`` layer
knows about vLLM / SGLang / Prometheus; every layer downstream speaks this
vocabulary. The data model is deliberately stdlib-only (no numpy) so it stays a
pure, importable contract that other tools can produce without pulling our
solver in.

Numerical landmines handled here (see ``normalize``):
  1. epoch seconds -> t0-relative (``exp(-beta * epoch)`` underflows to 0).
  2. coincident timestamps -> deterministic micro-jitter (ties break a point
     process likelihood and the Ogata recursion).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

SCHEMA_VERSION = "cw-event/1"


class EventType(StrEnum):
    PREEMPT = "preempt"
    RECOMPUTE = "recompute"
    EVICT = "evict"
    SWAP_OUT = "swap_out"
    SWAP_IN = "swap_in"


class Fidelity(StrEnum):
    """How faithfully the event times reflect reality.

    NATIVE_EVENT   true per-event source (a scheduler log line per preemption).
    RECONSTRUCTED  a cumulative counter was differenced and the events were
                   placed probabilistically within scrape intervals -> the
                   identifiability veto is tightened (see criticality layer).
    AGGREGATE      only binned counts are available -> a point-process fit is
                   refused rather than fabricated.
    """

    NATIVE_EVENT = "native_event"
    RECONSTRUCTED = "reconstructed"
    AGGREGATE = "aggregate"


@dataclass(frozen=True, slots=True)
class Event:
    t: float
    type: EventType
    seq_id: str | None = None
    freed_blocks: int | None = None
    recompute_tokens: int | None = None
    mode: str | None = None  # "RECOMPUTE" | "SWAP"
    meta: dict | None = None


@dataclass(frozen=True, slots=True)
class EventStream:
    events: tuple[Event, ...]
    t0: float
    t1: float  # observation-window end; required so the right-censored
    #            compensator Lambda(t1) is well defined (omitting it inflates
    #            alpha/beta).
    fidelity: Fidelity = Fidelity.NATIVE_EVENT
    source: str = "unknown"
    schema_version: str = SCHEMA_VERSION

    @property
    def n_events(self) -> int:
        return len(self.events)

    @property
    def duration(self) -> float:
        return self.t1 - self.t0

    def times(self) -> tuple[float, ...]:
        return tuple(e.t for e in self.events)

    @classmethod
    def from_times(
        cls,
        times,
        *,
        t0: float | None = None,
        t1: float | None = None,
        type: EventType = EventType.PREEMPT,
        fidelity: Fidelity = Fidelity.NATIVE_EVENT,
        source: str = "synthetic",
        marks: list[dict] | None = None,
    ) -> EventStream:
        ts = [float(t) for t in times]
        if t0 is None:
            t0 = min(ts) if ts else 0.0
        if t1 is None:
            t1 = max(ts) if ts else (t0 + 1.0)
        evs = []
        for i, t in enumerate(ts):
            m = (marks[i] if marks else None) or {}
            evs.append(
                Event(
                    t=t,
                    type=type,
                    seq_id=m.get("seq_id"),
                    freed_blocks=m.get("freed_blocks"),
                    recompute_tokens=m.get("recompute_tokens"),
                    mode=m.get("mode"),
                )
            )
        return cls(events=tuple(evs), t0=float(t0), t1=float(t1), fidelity=fidelity, source=source)


def normalize(stream: EventStream, jitter_eps: float = 1e-6) -> tuple[EventStream, dict]:
    """Return a t0-relative, strictly-increasing copy of ``stream`` plus info.

    Events are ordered by (time, deterministic tie key) and any non-increasing
    timestamp is nudged forward by ``jitter_eps`` so the resulting times are
    strictly monotonic. The number of nudges is reported so the caller can
    surface it (heavy jitter == coarse timestamps == lower fidelity).
    """
    evs = list(stream.events)
    t0 = stream.t0

    def tie_key(i: int):
        e = evs[i]
        h = (hash(e.seq_id) & 0xFFFFFFFF) if e.seq_id is not None else 0
        return (e.t, h, i)

    order = sorted(range(len(evs)), key=tie_key)

    norm: list[tuple[float, Event]] = []
    n_jittered = 0
    for idx in order:
        e = evs[idx]
        rt = e.t - t0
        if norm and rt <= norm[-1][0]:
            rt = norm[-1][0] + jitter_eps
            n_jittered += 1
        norm.append((rt, e))

    out_events = tuple(replace(e, t=rt) for rt, e in norm)
    new_t1 = stream.t1 - t0
    if out_events and out_events[-1].t > new_t1:
        new_t1 = out_events[-1].t + jitter_eps

    info = {
        "n_events": len(out_events),
        "n_jittered": n_jittered,
        "t0_shift": t0,
        "duration": new_t1,
    }
    ns = EventStream(
        events=out_events,
        t0=0.0,
        t1=new_t1,
        fidelity=stream.fidelity,
        source=stream.source,
    )
    return ns, info
