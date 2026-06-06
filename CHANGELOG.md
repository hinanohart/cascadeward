# Changelog

All notable changes to cascadeward are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/); versions use PEP 440.

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
