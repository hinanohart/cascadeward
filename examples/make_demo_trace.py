"""Generate a runnable demo trace (synthetic ground-truth).

    python examples/make_demo_trace.py            # writes examples/demo_trace.jsonl
    cascadeward score examples/demo_trace.jsonl   # then score it

The trace is sub-critical (n=0.65) with a non-stationary background, i.e. what a
moderately-loaded but self-healing cluster looks like.
"""

import json
import pathlib

from cascadeward.ingest import generate


def main() -> None:
    stream = generate(alpha=0.65, beta=2.0, T=3000.0, mu_blocks=[0.3, 0.7, 0.4, 0.6], seed=0)
    out = pathlib.Path(__file__).parent / "demo_trace.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for e in stream.events:
            f.write(json.dumps({"t": e.t, "type": e.type.value}) + "\n")
    print(f"wrote {stream.n_events} events to {out}")


if __name__ == "__main__":
    main()
