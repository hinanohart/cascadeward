"""Plain-text terminal summary (colour-free, CI-safe, utf-8)."""

from __future__ import annotations


def render_text(report) -> str:
    d = report if isinstance(report, dict) else report.to_dict()
    br = d["branching_ratio_n"]
    ident = d["identifiability"]
    lines = []
    lines.append(f"cascadeward {d['schema_version']}  source={d['data']['source']}")
    lines.append(
        f"  events={d['data']['n_events']}  fidelity={d['data']['fidelity']}  window_s={d['data']['window_s']}"
    )
    lines.append(f"  VERDICT: {d['verdict']}")
    ci = br["ci"]
    ci_str = "[nan, nan]" if ci[0] is None or _isnan(ci[0]) else f"[{ci[0]:.3f}, {ci[1]:.3f}]"
    lines.append(f"  branching ratio n: {br['point']}  CI95={ci_str}  level={br['level']}")
    lines.append(f"  endogeneity: {d['endogeneity']}")
    lines.append(f"  kernel: {d['kernel']['type']}  beta={d['kernel']['beta']}")
    if ident["vetoes"]:
        lines.append(f"  identifiability vetoes: {', '.join(ident['vetoes'])}")
    if ident["notes"]:
        lines.append(f"  notes: {', '.join(ident['notes'])}")
    lines.append(f"  forecast: {d['forecast']['status']} ({d['forecast']['sensitivity_sign']})")
    lines.append(f"    {d['forecast']['note']}")
    lines.append(f"  {d['disclaimer']}")
    return "\n".join(lines)


def _isnan(x) -> bool:
    try:
        return x != x
    except Exception:
        return False
