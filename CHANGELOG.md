# Changelog

All notable changes to cascadeward are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/); versions use PEP 440.

## [0.1.0a2] - 2026-06-06

Post-release audit hardening (three-agent review). No change to the estimator
math or any SHIP GATE verdict; all fixes are additive guards and contract fixes.

### Fixed
- **Report schema contract**: the `AGGREGATE`-refusal report now carries the same
  `branching_ratio_n` key set as a normal fit (it was missing `n_explode`), so a
  consumer reading `branching_ratio_n["n_explode"]` no longer `KeyError`s on a
  refusal. The refusal now also reports the real `n_jittered` count. A new
  `boot_requested` key makes the explosion fraction (`n_explode / boot_requested`)
  computable from JSON — `boot_B` is the *effective* (successfully-refit) sample.
- **`report_to_dict`** no longer treats a dataclass *type* as an instance, and
  raises a clear `TypeError` on unsupported input instead of an obscure failure.
- **vLLM log ingest** refuses a trace whose MM-DD timestamps roll backwards over
  a year boundary (the year-free surrogate axis cannot represent it) rather than
  silently emitting negative inter-event gaps.
- MLE "failed from any start" now surfaces the last optimiser error for diagnosis.

### Added
- **Identifiability trigger (7) — bootstrap explosion bias**: if the majority of
  bootstrap replicates ran away to the event cap *yet the CI still came back
  sub-critical*, the verdict is withheld (`UNIDENTIFIED`) — that CI is taken over
  a truncated, downward-biased subset. A bootstrap that explodes but whose CI is
  itself super-critical still reports `SUPER_CRITICAL`: the alarm is never muted.
- The pre-registered veto thresholds are now named module-level constants
  (auditable/greppable), not inline literals.

### Deferred to v0.2
- A `mypy` type-check CI gate (the package ships `py.typed`).

## [0.1.0a1] - 2026-06-06

First alpha. A measurement instrument, not a control or remediation system.

### Added
- Canonical marked temporal point-process event model (`events.py`) with a
  first-class `Fidelity` enum (`NATIVE_EVENT` / `RECONSTRUCTED` / `AGGREGATE`).
  Marks (`freed_blocks`, `recompute_tokens`) are parsed and carried; the v0.1
  *estimator* is unmarked (see Deferred).
- Exponential Hawkes likelihood (unmarked in v0.1) with a **time-varying
  piecewise-constant background rate μ(t)** and a right-censored compensator (`pp/`).
- MLE fit with softplus reparameterisation and multi-start (recovers super-critical
  `n ≥ 1`), exact immigration-birth simulator, and parametric bootstrap CIs.
  Optimisation is finite-difference (numerically robust; recovers ground truth).
- Endogeneity (Zhuang background probability) and a time-rescaling KS
  goodness-of-fit check.
- Branching ratio `n` reported as a **3-level verdict (SUB / NEAR-CRITICAL / SUPER)
  with a mandatory bootstrap CI** — never as a bare point scalar.
- Filimonov–Sornette identifiability self-veto: `UNIDENTIFIED` is a normal output.
- Qualitative-only headroom (quantitative QPS-to-critical is deliberately deferred;
  see README "Why no number").
- Ingest adapters: `vllm_log` (NATIVE per-event scheduler lines), generic `jsonl`,
  `synthetic` ground-truth generator.
- `cascadeward score` and `cascadeward selftest` CLI with a stable exit-code contract.
- Honest-marketing gate (`_claims.py`) enforced in CI.

### Deferred to v0.2 (explicitly out of scope for a1)
- **Marked excitation weighting** `g(m)` over `freed_blocks` / `recompute_tokens`
  and the `--mark none|blocks` flag. v0.1 fits the unmarked exp-Hawkes; the marks
  are already captured in the data model so weighting can be added without a
  schema change.
- **Analytic gradient** for the exponential kernel. v0.1 uses finite-difference
  (it recovers ground truth in the SHIP GATE); the analytic gradient is a speed
  optimisation, not a correctness one.
- `watch` live stream detection.
- `vllm_prom` Prometheus counter-diff adapter (RECONSTRUCTED fidelity).
- Omori power-law kernel, full Zhuang EM, mark-contribution decomposition.
- Quantitative QPS / context-length headroom extrapolation.
- SGLang / LMCache / OpenTelemetry adapters.
