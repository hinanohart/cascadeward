# Changelog

All notable changes to cascadeward are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/); versions use PEP 440.

## [0.1.0a1] - 2026-06-06

First alpha. A measurement instrument, not a control or remediation system.

### Added
- Canonical marked temporal point-process event model (`events.py`) with a
  first-class `Fidelity` enum (`NATIVE_EVENT` / `RECONSTRUCTED` / `AGGREGATE`).
- Marked exponential Hawkes likelihood with a **time-varying piecewise-constant
  background rate μ(t)** and right-censored compensator (`pp/`).
- MLE fit with softplus reparameterisation and multi-start (recovers super-critical
  `n ≥ 1`), exact immigration-birth simulator, and parametric bootstrap CIs.
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
- `watch` live stream detection.
- `vllm_prom` Prometheus counter-diff adapter (RECONSTRUCTED fidelity).
- Omori power-law kernel, full Zhuang EM, mark-contribution decomposition.
- Quantitative QPS / context-length headroom extrapolation.
- SGLang / LMCache / OpenTelemetry adapters.
