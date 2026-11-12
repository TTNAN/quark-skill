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
    monkeypatch.setattr(fq, "verify_cli", lambda cli: None)
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


def make(root, version, name="quarkclouddrive"):
    d = root / name
    (d / "scripts").mkdir(parents=True)
    (d / "scripts" / "quark-drive.cjs").write_text("// stub")
    (d / "SKILL.md").write_text("---\nname: quarkclouddrive\nmetadata:\n  version: %s\n---\n" % version)
    return str(d)


def test_picks_highest_version_over_stale_project_copy(tmp_path, monkeypatch):
    home, proj = tmp_path / "home", tmp_path / "proj"
    new = make(home / ".workbuddy" / "skills", "1.0.25")
    old = make(proj / ".agents" / "skills", "1.0.9")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(proj)
    monkeypatch.setattr(fq, "candidates", lambda: [old, new])
    skill_dir, cli, checked, broken = fq.find(verify=lambda c: None, env="")
    assert skill_dir == new and not broken


def test_skips_cli_that_does_not_run(tmp_path, monkeypatch):
    bad = make(tmp_path / "a", "1.0.30")
    ok = make(tmp_path / "b", "1.0.25")
    monkeypatch.setattr(fq, "candidates", lambda: [bad, ok])
    verify = lambda c: "SyntaxError" if c.startswith(bad) else None
    skill_dir, cli, checked, broken = fq.find(verify=verify, env="")
    assert skill_dir == ok and broken[0]["skill_dir"] == bad


def test_nothing_runs_means_not_found(tmp_path, monkeypatch):
    bad = make(tmp_path / "a", "1.0.25")
    monkeypatch.setattr(fq, "candidates", lambda: [bad])
    skill_dir, cli, checked, broken = fq.find(verify=lambda c: "找不到 node", env="")
    assert cli is None and broken


def test_env_is_exclusive(tmp_path, monkeypatch):
    newer = make(tmp_path / "a", "9.9.9")
    mine = make(tmp_path / "b", "1.0.0")
    monkeypatch.setattr(fq, "candidates", lambda: [newer])
    skill_dir, *_ = fq.find(verify=lambda c: None, env=mine)
    assert skill_dir == mine


def test_version_key():
    assert fq.version_key("1.0.25") > fq.version_key("1.0.9")
    assert fq.version_key("") < fq.version_key("0.0.1")
