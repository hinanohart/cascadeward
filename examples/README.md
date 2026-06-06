# Examples

```bash
# 1. score a vLLM scheduler log (NATIVE per-event preemption lines)
cascadeward score examples/sample_vllm.log --adapter vllm_log
#   (only 5 events -> expect UNIDENTIFIED: too few events to certify. That is the
#    instrument behaving honestly, not a bug.)

# 2. generate a realistic synthetic trace and score it
python examples/make_demo_trace.py
cascadeward score examples/demo_trace.jsonl --blocks 4 --format json

# 3. reproduce a ground-truth recovery end-to-end
cascadeward selftest
```

Exit codes: `0` SUB_CRITICAL, `10` SUPER_CRITICAL, `20` UNIDENTIFIED, `2` input error.
