import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skills", "quark-search-save", "scripts"))

import find_quark_cli as fq  # noqa: E402


def test_finds_via_env(tmp_path, monkeypatch, capsys):
    cli = tmp_path / "quarkclouddrive" / "scripts" / "quark-drive.cjs"
    cli.parent.mkdir(parents=True)
    cli.write_text("// stub")
    monkeypatch.setenv("QUARK_SKILL_DIR", str(tmp_path / "quarkclouddrive"))
    assert fq.main(["--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] and out["cli"] == str(cli)


def test_reports_checked_when_missing(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("QUARK_SKILL_DIR", str(tmp_path / "nope"))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    assert fq.main(["--json"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False and out["checked"]
