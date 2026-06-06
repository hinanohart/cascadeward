"""Single source of truth for cascadeward's honest-marketing boundary.

cascadeward is a *measurement instrument*. It must never claim to make serving
faster, to prevent or guarantee against cascades, or to be a causal model of the
scheduler. This module both documents the allowed framing (``DISCLAIMER``) and
provides a runnable checker used by CI:

    python -m cascadeward._claims README.md src CHANGELOG.md

Exit 0 == clean, exit 1 == a banned token was found or a required disclaimer is
missing. Using Python (not raw grep) avoids the BRE/ERE footgun and is testable.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DISCLAIMER = (
    "cascadeward is a measurement instrument: it measures preemption/recompute "
    "storm criticality from serving traces. It does NOT make serving faster, does "
    "NOT prevent or guarantee against cascades, and is NOT a causal model of the "
    "scheduler. All headline numbers in this project are validated on synthetic "
    "ground-truth only."
)

# Tier 1: unambiguous promotional tokens that never appear in an honest
# disclaimer -- always flagged.
HARD_BANNED: list[tuple[str, str]] = [
    (r"\bspeed\s*ups?\b", "performance hype"),
    (r"\bblazing(ly)?\b", "hype"),
    (r"\bSOTA\b", "benchmark hype"),
    (r"state[- ]of[- ]the[- ]art", "benchmark hype"),
    (r"\bout[- ]?perform", "benchmark hype"),
    (r"\bbest[- ]in[- ]class\b", "hype"),
    (r"\d+\s*x\s*faster", "performance claim"),
    (r"\d+\s*%\s*faster", "performance claim"),
    (r"\bfirst[- ]ever\b", "novelty over-claim"),
]

# Tier 2: claims that DO legitimately appear in disclaimers as negations
# ("does NOT make serving faster"). Flagged ONLY when the line is not negated.
CLAIM_BANNED: list[tuple[str, str]] = [
    (r"\bmakes? (serving|inference|it) faster", "performance claim"),
    (r"\bguarantees?\b", "guarantee over-claim"),
    (r"\bprevents? (all )?cascad", "remediation over-claim"),
    (r"\bcausal model of (the )?scheduler", "causal over-claim"),
    (r"\bpredicts? (all|every) ", "prediction over-claim"),
    (r"\bsolves? (the )?reproducibilit", "scope over-claim"),
]

_NEG_CUES = (" not ", "n't", "never", "without", "cannot", "no longer")

# README must contain these sentinels (proves the disclaimer is present).
# Compared case-insensitively.
REQUIRED_IN_README = [
    "measurement instrument",
    "does not make serving faster",
    "synthetic ground-truth",
]


def _negated(line: str) -> bool:
    low = " " + line.lower() + " "
    return any(cue in low for cue in _NEG_CUES)


def scan_text(text: str) -> list[tuple[int, str, str]]:
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        for pat, why in HARD_BANNED:
            if re.search(pat, line, flags=re.IGNORECASE):
                hits.append((i, pat, why))
        if not _negated(line):
            for pat, why in CLAIM_BANNED:
                if re.search(pat, line, flags=re.IGNORECASE):
                    hits.append((i, pat, why))
    return hits


def _iter_files(paths: list[str]):
    for p in paths:
        path = Path(p)
        if path.is_dir():
            yield from path.rglob("*.py")
            yield from path.rglob("*.md")
        elif path.exists():
            yield path


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        argv = ["README.md", "src", "CHANGELOG.md"]
    violations = 0
    readme_text = ""
    for path in _iter_files(argv):
        # the canonical claim definitions live in this file -> don't scan it
        if path.name == "_claims.py":
            continue
        text = path.read_text(encoding="utf-8")
        if path.name == "README.md":
            readme_text = text
        for lineno, pat, why in scan_text(text):
            print(f"BANNED [{why}] {path}:{lineno}  /{pat}/")
            violations += 1
    if readme_text:
        low = readme_text.lower()
        for sentinel in REQUIRED_IN_README:
            if sentinel.lower() not in low:
                print(f"MISSING required disclaimer sentinel in README: {sentinel!r}")
                violations += 1
    if violations:
        print(f"\nhonest-marketing gate FAILED: {violations} issue(s)")
        return 1
    print("honest-marketing gate OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
