"""Generic JSON-Lines adapter (domain-agnostic).

Each line: {"t": <float seconds>, "type": <event type>, "marks": {...}}.
``type`` and ``marks`` are optional. This is also the path for agent-retry storms
and RLVR rollout bursts -- anything expressible as a marked event stream.
"""

from __future__ import annotations

import json

from ..events import Event, EventStream, EventType, Fidelity


def parse_jsonl(path: str, fidelity: str | None = None) -> EventStream:
    events: list[Event] = []
    times: list[float] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            t = float(obj["t"])
            times.append(t)
            etype = obj.get("type", "preempt")
            try:
                et = EventType(etype)
            except ValueError:
                et = EventType.PREEMPT
            marks = obj.get("marks", {}) or {}
            events.append(
                Event(
                    t=t,
                    type=et,
                    seq_id=marks.get("seq_id"),
                    freed_blocks=marks.get("freed_blocks"),
                    recompute_tokens=marks.get("recompute_tokens"),
                    mode=marks.get("mode"),
                )
            )
    if not events:
        raise ValueError(f"no events parsed from {path}")
    t0 = min(times)
    t1 = max(times)
    fid = Fidelity(fidelity) if fidelity else Fidelity.NATIVE_EVENT
    return EventStream(events=tuple(events), t0=t0, t1=t1, fidelity=fid, source=f"jsonl:{path}")
