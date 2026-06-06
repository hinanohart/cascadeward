"""The honest-marketing gate must pass on this repo and catch real violations."""

from pathlib import Path

from cascadeward._claims import REQUIRED_IN_README, main, scan_text

REPO = Path(__file__).resolve().parent.parent


def test_repo_passes_honest_marketing_gate():
    # run the gate over README + src + CHANGELOG as CI does
    rc = main([str(REPO / "README.md"), str(REPO / "src"), str(REPO / "CHANGELOG.md")])
    assert rc == 0


def test_gate_catches_performance_claim():
    hits = scan_text("cascadeward makes serving faster and gives a 10x speedup!")
    assert hits, "must flag performance hype"


def test_gate_catches_guarantee():
    hits = scan_text("It guarantees no cascades will ever happen.")
    assert hits


def test_clean_text_passes():
    assert scan_text("cascadeward measures preemption storm criticality from traces.") == []


def test_readme_has_required_disclaimers():
    text = (REPO / "README.md").read_text(encoding="utf-8")
    for sentinel in REQUIRED_IN_README:
        assert sentinel in text, f"README missing disclaimer sentinel: {sentinel!r}"
