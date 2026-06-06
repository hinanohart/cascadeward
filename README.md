# cascadeward

**Measure preemption/recompute *storm criticality* in LLM-serving traces — on the CPU, model-free, from logs alone.**

When a KV-cache-bound server (vLLM / SGLang / LMCache) runs hot, a single
preemption can free blocks that trigger a recompute that evicts another
sequence that preempts again — a self-exciting cascade that vLLM's own docs
describe as serving "cascade into instance lockups." cascadeward fits a
**self-exciting point process (Hawkes / ETAS)** to a trace of preemption events
and answers one question:

> *Is this cluster sub-critical (a burst is absorbed) or super-critical (one
> preemption tends to avalanche)? — and is the data even good enough to say?*

It reports a **branching ratio `n`** as a guarded 3-level verdict with a
confidence interval, an **endogeneity** fraction (is a storm driven by traffic
or by self-excitation / config?), and an **identifiability self-veto** that
returns `UNIDENTIFIED` rather than a confident-but-meaningless number.

> ⚠️ **cascadeward is a measurement instrument.** It measures criticality from
> serving traces. It does not make serving faster, does not prevent or guarantee
> against cascades, and is not a causal model of the scheduler. Every headline
> number in this repository is validated on synthetic ground-truth only; it has
> not been validated against production incidents.

---

## What it is *not* (positioning)

cascadeward is easy to confuse with three neighbours; it is none of them:

| Neighbour | What that does | cascadeward |
|---|---|---|
| **KV token-eviction** (H2O / Scissorhands; our own `cachelens`) | decides *which tokens to drop* | measures the *dynamics of the dropping*, not the policy |
| **Metastable-failure modelling** (MSF-Model, arXiv:2309.16181; HotOS'25) | hand-builds a **CTMC** of the system to predict metastable regions | fits the branching ratio **non-parametrically from logs** — no hand model. *Honest moat:* if you are willing to hand-write a serving CTMC you can get an `n`-equivalent; cascadeward's edge is being model-free and one command. |
| **Survival / competing-risks** (our own `hazardloop`) | *when does a request finish / fail* | a self-exciting **branching** process (immigration + offspring), different vocabulary and different question |

---

## Install

`cascadeward` is an early `v0.1.0a1` pre-release published on GitHub (it is not
on PyPI yet). Install it straight from the tagged release:

```bash
pip install "git+https://github.com/hinanohart/cascadeward@v0.1.0a1"          # core: numpy + scipy, CPU-only
pip install "cascadeward[viz] @ git+https://github.com/hinanohart/cascadeward@v0.1.0a1"   # + matplotlib plots
```

No GPU, no model weights, no network at runtime. It consumes logs/metrics offline.

## Use

```bash
# reproduce a synthetic ground-truth recovery (no data needed)
cascadeward selftest

# score a vLLM scheduler log (NATIVE per-event preemption lines)
cascadeward score server.log --adapter vllm_log

# score a generic JSON-Lines event stream, non-stationary background, JSON out
cascadeward score trace.jsonl --blocks 4 --format json --json report.json
```

```python
import cascadeward as cw
from cascadeward.ingest import generate

stream = generate(alpha=0.7, beta=2.0, T=4000, mu=0.4, seed=0)
report = cw.score(stream)
print(report.verdict, report.branching_ratio_n)
```

### Exit codes (drop-in for CI / Nagios gates)

| code | meaning |
|---|---|
| `0`  | `SUB_CRITICAL` — healthy, bursts absorbed |
| `10` | `SUPER_CRITICAL` — one preemption tends to avalanche |
| `20` | `UNIDENTIFIED` — identifiability veto (a normal, honest output) |
| `2`  | input / parse error |
| `1`  | internal error |

### Input formats (`Fidelity` is first-class)

vLLM exposes preemptions **per event only as a scheduler WARNING log line**; the
Prometheus metric `vllm:num_preemptions_total` is a cumulative *Counter*, not a
per-event stream. cascadeward tracks this in the data model:

- `NATIVE_EVENT` — true per-event source (`vllm_log`, generic `jsonl`, `synthetic`).
- `RECONSTRUCTED` — counter-diff → probabilistic placement → **veto tightened** *(Prometheus adapter is v0.2)*.
- `AGGREGATE` — binned only → **fit refused** (no fabricated point process).

## Why no "QPS-to-critical" number? (a deliberate omission)

For the exponential kernel the branching ratio `n = α` is **independent of the
background rate `μ`**. So naively scaling arrival load does *not* move `n` toward
1, and any "increase QPS by X% to hit criticality" number would be unfounded.
v0.1 reports headroom **qualitatively** (current regime + sensitivity sign). A
quantitative headroom requires modelling `α(cache_pressure)` across several load
points and is on the v0.2 roadmap.

## How it works

1. **Ingest** a trace → canonical marked event stream (`events.py`).
2. **Fit** an exponential Hawkes with a **time-varying piecewise-constant
   background `μ(t)`** by multi-start MLE (the time-varying background matters:
   a single *stationary* kernel is biased under non-stationarity — Filimonov &
   Sornette 2015, arXiv:1308.6756). *v0.1 fits the unmarked process; event marks
   (`freed_blocks`, …) are captured for mark-weighted excitation in v0.2.*
3. **Bootstrap** a CI for `n` by exact immigration-birth simulation + refit.
4. **Decluster** (Zhuang background probability) → endogeneity.
5. **Self-veto** (Filimonov–Sornette) on too-few events, wide/critical-crossing
   CI, near-critical instability, unidentified timescale, kernel
   misspecification (time-rescaling KS), or bootstrap-explosion bias (most
   replicates ran away yet the CI came back sub-critical) → possibly
   `UNIDENTIFIED`.
6. **Report** a versioned JSON / text verdict.

## Honest limits

- Branching-ratio identifiability near `n ≈ 1` is a known minefield; the CI and
  self-veto **mitigate, they do not remove it**. "Cannot certify" is sometimes
  the correct output.
- A memoryless-offspring Hawkes is an **approximation** of a deterministic
  state-machine scheduler — an early-warning / config-ranking instrument, not a
  causal model.
- Trace quality is load-bearing. Coarse timestamps or counter-reconstruction
  lower fidelity and tighten the veto; cascadeward fails loudly rather than
  fabricating.
- Validated on **synthetic ground-truth** only. No production-incident
  validation is claimed.

## Scope of usefulness

cascadeward pays off when you run vLLM/SGLang yourself, preemption is an actual
pain at your load, and your logs are granular enough to fit. That is a
lab-to-mid-scale audience by design.

## License

MIT © 2026 hinanohart. See [LICENSE](LICENSE).
