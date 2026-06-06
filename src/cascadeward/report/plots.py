"""Optional plotting (requires the ``viz`` extra; matplotlib is lazily imported)."""

from __future__ import annotations

import numpy as np


def save_plot(stream, report, path: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from ..events import normalize

    ns, _ = normalize(stream)
    times = np.asarray(ns.times(), dtype=float)

    fig, axes = plt.subplots(2, 1, figsize=(8, 6))
    # cumulative count (Omori-style "aftershock" accumulation visible as kinks)
    axes[0].step(times, np.arange(1, len(times) + 1), where="post")
    axes[0].set_xlabel("time (s, relative)")
    axes[0].set_ylabel("cumulative preemptions")
    d = report.to_dict()
    axes[0].set_title(f"cascadeward: {d['verdict']}  (n={d['branching_ratio_n']['point']})")

    # inter-event intervals
    if len(times) > 1:
        axes[1].plot(times[1:], np.diff(times), ".", ms=2)
        axes[1].set_xlabel("time (s, relative)")
        axes[1].set_ylabel("inter-event interval (s)")
        axes[1].set_yscale("log")

    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
