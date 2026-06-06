import json

import pytest

from cascadeward.cli import main


def test_version():
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0


@pytest.mark.slow
def test_selftest_passes():
    assert main(["selftest", "--boot", "60", "--seed", "0"]) == 0


def test_score_input_error_exit_2(tmp_path):
    assert main(["score", str(tmp_path / "nope.jsonl")]) == 2


@pytest.mark.slow
def test_score_jsonl_exit_code(tmp_path, capsys):
    # build a sub-critical synthetic trace as jsonl, score it
    from cascadeward.ingest import generate

    s = generate(alpha=0.5, beta=2.0, T=1200, mu=0.5, seed=21)
    p = tmp_path / "t.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for e in s.events:
            f.write(json.dumps({"t": e.t, "type": e.type.value}) + "\n")
    code = main(["score", str(p), "--boot", "50", "--seed", "21", "--format", "json"])
    assert code in (0, 10, 20)
    out = capsys.readouterr().out
    doc = json.loads(out)
    assert doc["schema_version"] == "cascadeward-report/1"
    assert "disclaimer" in doc


def test_score_writes_json_file(tmp_path):
    from cascadeward.ingest import generate

    s = generate(alpha=0.4, beta=2.0, T=800, mu=0.6, seed=22)
    p = tmp_path / "t.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for e in s.events:
            f.write(json.dumps({"t": e.t}) + "\n")
    outp = tmp_path / "report.json"
    main(["score", str(p), "--boot", "40", "--seed", "22", "--json", str(outp)])
    assert outp.exists()
    doc = json.loads(outp.read_text(encoding="utf-8"))
    assert "verdict" in doc
