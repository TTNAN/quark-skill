import io
import json
import os
import sys
import zipfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "quark-search-save", "scripts"))
import install_quark_skill as iq  # noqa: E402

CFG_URL = "https://pdds.quark.cn/download/stfile/x/quarkclouddrive-9.9.9.zip"


def make_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


GOOD = {
    "SKILL.md": "---\nname: quarkclouddrive\nversion: 9.9.9\n---\n",
    "scripts/quark-drive.cjs": "// cli",
    "scripts/install.sh": "echo ok",
    "references/auth.md": "auth",
}


def fake_fetch(zip_bytes, config=None):
    def fetch(url, timeout):
        if url.startswith(iq.CONFIG_URL):
            if config is None:
                raise OSError("down")
            return json.dumps(config).encode()
        return zip_bytes
    return fetch


def test_parse_config_shapes():
    assert iq.parse_config({"data": {"config": {"qkPanVersion": "1", "qkPan": "u"}}}) == ("1", "u")
    assert iq.parse_config({"config": {"qkPan": "u"}}) == ("", "u")
    assert iq.parse_config({"qkPan": " u "}) == ("", "u")
    assert iq.parse_config(None) == ("", "")


def test_resolve_uses_config_and_falls_back():
    cfg = {"data": {"config": {"qkPanVersion": "9.9.9", "qkPan": CFG_URL}}}
    assert iq.resolve_zip_url(fetch=fake_fetch(b"", cfg)) == ("9.9.9", CFG_URL, "skill_config")
    assert iq.resolve_zip_url(fetch=fake_fetch(b"", None))[1] == iq.FALLBACK_ZIP
    evil = {"data": {"config": {"qkPan": "https://evil.example.com/x.zip"}}}
    assert iq.resolve_zip_url(fetch=fake_fetch(b"", evil))[1] == iq.FALLBACK_ZIP


def test_official_url_check():
    assert iq.is_official_url("https://pdds.quark.cn/a.zip")
    assert not iq.is_official_url("http://pdds.quark.cn/a.zip")
    assert not iq.is_official_url("https://quark.cn.evil.com/a.zip")


def test_install_extracts_and_runs_setup(tmp_path):
    target = tmp_path / "skills" / "quarkclouddrive"
    calls = []
    res = iq.install(str(target), fetch=fake_fetch(make_zip(GOOD)),
                     runner=lambda d: calls.append(d) or {"success": True})
    assert res["ok"] and res["status"] == "installed"
    assert res["version"] == "9.9.9"
    assert (target / "scripts" / "quark-drive.cjs").is_file()
    assert calls == [str(target)]


def test_install_handles_wrapped_zip(tmp_path):
    wrapped = {"quarkclouddrive/" + k: v for k, v in GOOD.items()}
    target = tmp_path / "q"
    iq.install(str(target), setup=False, fetch=fake_fetch(make_zip(wrapped)))
    assert (target / "SKILL.md").is_file()


def test_already_installed_is_noop(tmp_path):
    target = tmp_path / "q"
    (target / "scripts").mkdir(parents=True)
    (target / "scripts" / "quark-drive.cjs").write_text("x")
    res = iq.install(str(target), fetch=lambda *a: pytest.fail("should not download"))
    assert res["status"] == "already_installed"


def test_refuses_foreign_dir(tmp_path):
    target = tmp_path / "q"
    target.mkdir()
    (target / "mine.txt").write_text("x")
    with pytest.raises(iq.InstallError):
        iq.install(str(target), setup=False, fetch=fake_fetch(make_zip(GOOD)))
    assert (target / "mine.txt").exists()


def test_rejects_non_official_zip(tmp_path):
    with pytest.raises(iq.InstallError):
        iq.install(str(tmp_path / "q"), setup=False, fetch=fake_fetch(make_zip({"README": "x"})))
    assert not (tmp_path / "q").exists()


def test_rejects_zip_slip(tmp_path):
    bad = dict(GOOD)
    bad["../evil.txt"] = "x"
    with pytest.raises(iq.InstallError):
        iq.install(str(tmp_path / "q"), setup=False, fetch=fake_fetch(make_zip(bad)))
    assert not (tmp_path / "evil.txt").exists()


class _P:
    def __init__(self, code=0, out="", err=""):
        self.returncode, self.stdout, self.stderr = code, out, err


def _skill(tmp_path, with_cli=True):
    d = tmp_path / "quarkclouddrive"
    (d / "scripts").mkdir(parents=True)
    (d / "scripts" / "install.sh").write_text("echo hi")
    if with_cli:
        (d / "scripts" / "quark-drive.cjs").write_text("//")
    return str(d)


def _which(name):
    return "/usr/bin/" + name


def test_setup_ok_without_install_result_line(tmp_path):
    d = _skill(tmp_path)
    res = iq.run_official_setup(d, run=lambda cmd, t: _P(0, "some new format"), which=_which)
    assert res["success"] and res["install_result"] is None


def test_setup_fails_on_nonzero_exit(tmp_path):
    d = _skill(tmp_path)
    with pytest.raises(iq.InstallError):
        iq.run_official_setup(d, run=lambda cmd, t: _P(1, "", "boom"), which=_which)


def test_setup_fails_when_official_says_false(tmp_path):
    d = _skill(tmp_path)
    line = '{"install_result": true, "success": false}'
    with pytest.raises(iq.InstallError):
        iq.run_official_setup(d, run=lambda cmd, t: _P(0, line), which=_which)


def test_setup_fails_without_cli(tmp_path):
    d = _skill(tmp_path, with_cli=False)
    with pytest.raises(iq.InstallError):
        iq.run_official_setup(d, run=lambda cmd, t: _P(0), which=_which)


def test_setup_fails_when_help_breaks(tmp_path):
    d = _skill(tmp_path)

    def run(cmd, t):
        return _P(0) if cmd[0] == "bash" else _P(2, "", "SyntaxError")
    with pytest.raises(iq.InstallError):
        iq.run_official_setup(d, run=run, which=_which)
