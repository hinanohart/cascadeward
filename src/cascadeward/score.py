"""Top-level orchestration: EventStream -> guarded CriticalityReport.

This wires the layers together: normalize -> fit (exp Hawkes + mu(t)) ->
bootstrap CI -> endogeneity + goodness-of-fit -> identifiability veto -> verdict
-> qualitative headroom -> versioned report. Fit and judgement stay separate so a
'converged' optimiser can still be refused a verdict.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np

from ._claims import DISCLAIMER
from .criticality.branching import BranchingResult, classify
from .criticality.identifiability import self_veto
from .criticality.verdict import decide
from .events import EventStream, Fidelity, normalize
from .forecast.headroom import qualitative_headroom
from .pp.bootstrap import bootstrap_ci
from .pp.decluster import endogeneity_fraction, ks_goodness_of_fit
from .pp.mle import fit_hawkes

SCHEMA = "cascadeward-report/1"


@dataclass
class CriticalityReport:
    verdict: str
    branching_ratio_n: dict
    endogeneity: float
    kernel: dict
    identifiability: dict
    forecast: dict
    data: dict
    determinism: dict
    disclaimer: str = DISCLAIMER
    schema_version: str = SCHEMA
    _exit_code: int = field(default=1, repr=False)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("_exit_code", None)
        return d

    @property
    def exit_code(self) -> int:
        return self._exit_code


def _aggregate_refusal(stream: EventStream, info: dict) -> CriticalityReport:
    return CriticalityReport(
        verdict="UNIDENTIFIED",
        branching_ratio_n={"point": None, "ci": [None, None], "level": "n/a", "boot_B": 0},
        endogeneity=float("nan"),
        kernel={"type": "exp", "beta": None, "beta_cv": None, "n_blocks": 0},
        identifiability={
            "ok": False,
            "vetoes": ["aggregate_fidelity_fit_refused"],
            "notes": [
                "AGGREGATE fidelity: only binned counts available; a point-process fit is refused."
            ],
            "ks_pvalue": None,
        },
        forecast={"status": "unknown", "sensitivity_sign": "n/a", "note": "No fit performed."},
        data={
            "n_events": stream.n_events,
            "fidelity": stream.fidelity.value,
            "source": stream.source,
            "window_s": round(float(stream.duration), 4),
            "n_jittered": 0,
        },
        determinism={"seed": None, "reproducible": True},
        _exit_code=20,
    )


def score(
    stream: EventStream,
    *,
    kernel: str = "exp",
    n_blocks: int = 1,
    boot: int = 200,
    seed: int = 0,
) -> CriticalityReport:
    if kernel != "exp":
        raise ValueError("v0.1 supports only kernel='exp' (Omori is v0.2)")
    if stream.fidelity == Fidelity.AGGREGATE:
        ns, info = normalize(stream)
        return _aggregate_refusal(stream, info)

    ns, info = normalize(stream)
    times = np.asarray(ns.times(), dtype=float)
    T = float(ns.t1)

    params, diag = fit_hawkes(times, T, n_blocks=n_blocks, seed=seed)
    boot_res = bootstrap_ci(params, T, B=boot, n_blocks=n_blocks, seed=seed + 1)
    endo = endogeneity_fraction(times, params)
    ks_p = ks_goodness_of_fit(times, T, params)

    ident = self_veto(
        n=params.n,
        ci_lo=boot_res["lo"],
        ci_hi=boot_res["hi"],
        n_events=len(times),
        fidelity=stream.fidelity,
        beta=params.beta,
        beta_cv=boot_res["beta_cv"],
        ks_p=ks_p,
    )
    if not diag["converged"]:
        ident.vetoes.append("optimizer_not_converged")
        ident.ok = False

    level = classify(params.n, boot_res["lo"], boot_res["hi"])
    branch = BranchingResult(
        n=params.n, ci_lo=boot_res["lo"], ci_hi=boot_res["hi"], level=level, endogeneity=endo
    )
    verdict = decide(branch, ident)
    head = qualitative_headroom(verdict)

    def _round(x):
        return None if x is None or (isinstance(x, float) and x != x) else round(float(x), 4)

    return CriticalityReport(
        verdict=verdict.label,
        branching_ratio_n={
            "point": _round(params.n),
            "ci": [_round(boot_res["lo"]), _round(boot_res["hi"])],
            "level": level,
            "boot_B": boot_res["B_effective"],
            "n_explode": boot_res["n_explode"],
        },
        endogeneity=_round(endo),
        kernel={
            "type": kernel,
            "beta": _round(params.beta),
            "beta_cv": _round(boot_res["beta_cv"]),
            "n_blocks": n_blocks,
        },
        identifiability={
            "ok": ident.ok,
            "vetoes": ident.vetoes,
            "notes": ident.notes,
            "ks_pvalue": _round(ks_p),
        },
        forecast={
            "status": head.status,
            "sensitivity_sign": head.sensitivity_sign,
            "note": head.note,
        },
        data={
            "n_events": int(len(times)),
            "fidelity": stream.fidelity.value,
            "source": stream.source,
            "window_s": round(T, 4),
            "n_jittered": info["n_jittered"],
        },
        determinism={"seed": seed, "reproducible": True},
        _exit_code=verdict.exit_code,
    )
