"""cascadeward command line.

Exit-code contract (drop-in for Nagios/CI gates):
    0   SUB_CRITICAL (healthy: bursts absorbed)
    10  SUPER_CRITICAL (a single preemption tends to avalanche)
    20  UNIDENTIFIED (identifiability veto -- a normal, honest output)
    2   input / parse error
    1   internal error
"""

from __future__ import annotations

import argparse
import sys

from .. import __version__


def _cmd_score(args) -> int:
    from ..ingest import load
    from ..report.json_report import report_to_json
    from ..report.text import render_text

    try:
        stream = load(args.trace, adapter=args.adapter, fidelity=args.fidelity)
    except (OSError, ValueError) as e:
        print(f"input error: {e}", file=sys.stderr)
        return 2

    from ..score import score

    report = score(stream, kernel=args.kernel, n_blocks=args.blocks, boot=args.boot, seed=args.seed)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            f.write(report_to_json(report))
    if args.plot:
        try:
            from ..report.plots import save_plot

            save_plot(stream, report, args.plot)
        except Exception as e:  # noqa: BLE001 - plotting is optional
            print(f"warning: plot skipped ({e})", file=sys.stderr)

    if args.format == "json":
        print(report_to_json(report))
    else:
        print(render_text(report))
    return report.exit_code


def _cmd_selftest(args) -> int:
    """Reproduce a ground-truth recovery the way a new user would."""
    from ..ingest.synthetic import generate
    from ..score import score

    alpha_true = 0.6
    stream = generate(alpha=alpha_true, beta=2.0, T=4000.0, mu=0.4, seed=args.seed)
    report = score(stream, boot=args.boot, seed=args.seed)
    br = report.branching_ratio_n
    ci = br["ci"]
    ok = (
        ci[0] is not None
        and ci[1] is not None
        and ci[0] <= alpha_true <= ci[1]
        and report.verdict in ("SUB_CRITICAL", "UNIDENTIFIED")
    )
    print(
        f"selftest: true n={alpha_true}  estimated={br['point']}  CI95={ci}  verdict={report.verdict}"
    )
    print(f"events={report.data['n_events']}  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cascadeward",
        description="Measure preemption/recompute storm criticality in serving traces "
        "(measurement instrument; not a control system).",
    )
    p.add_argument("--version", action="version", version=f"cascadeward {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("score", help="score a trace file")
    s.add_argument("trace")
    s.add_argument("--adapter", default="auto", choices=["auto", "jsonl", "vllm_log"])
    s.add_argument(
        "--fidelity", default=None, choices=["native_event", "reconstructed", "aggregate"]
    )
    s.add_argument("--kernel", default="exp", choices=["exp"])
    s.add_argument("--blocks", type=int, default=1, help="piecewise-constant mu(t) blocks")
    s.add_argument("--boot", type=int, default=200, help="bootstrap replicates")
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--format", default="text", choices=["text", "json"])
    s.add_argument("--json", default=None, help="also write JSON report to this path")
    s.add_argument("--plot", default=None, help="write a plot to this path (needs [viz])")
    s.set_defaults(func=_cmd_score)

    t = sub.add_parser("selftest", help="reproduce a synthetic ground-truth recovery")
    t.add_argument("--seed", type=int, default=0)
    t.add_argument("--boot", type=int, default=200)
    t.set_defaults(func=_cmd_selftest)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as e:  # noqa: BLE001 - top-level guard -> exit 1
        print(f"internal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
