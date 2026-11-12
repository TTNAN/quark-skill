#!/usr/bin/env python3
"""从夸克官方地址安装「夸克网盘 Skill」（quarkclouddrive）。

本仓库不附带任何夸克的文件：这里只是替用户执行官方安装步骤——
向夸克官方接口查询最新版本的下载地址，下载官方 zip，解压到智能体的
skills 目录，再运行官方自带的 scripts/install.sh（检查 Node.js、安装 CLI、自检）。

用法：
  python3 install_quark_skill.py --json            # 装到本 Skill 的同级目录
  python3 install_quark_skill.py --dir ~/.codex/skills/quarkclouddrive --json
"""
import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from urllib.parse import urlparse

SKILL_NAME = "quarkclouddrive"
CLI_REL = os.path.join("scripts", "quark-drive.cjs")
CONFIG_URL = "https://open-api-drive.quark.cn/agent/v1/skill_config"
# 官方配置接口不可用时的兜底地址（官方页面公布的 1.0.25 版）
FALLBACK_ZIP = "https://pdds.quark.cn/download/stfile/eekkigineefiegmgo/quarkclouddrive-1.0.25.zip"
OFFICIAL_PAGE = "https://b.quark.cn/apps/quarkcloud_skill_info/routes/V-sc7gOBT"
UA = "quark-search-save-skill"


class InstallError(Exception):
    pass


def default_target():
    """本 Skill 的同级目录：两个 Skill 装在同一个 skills 目录下。"""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(os.path.dirname(here), SKILL_NAME)


def is_official_url(url):
    p = urlparse(url)
    host = (p.hostname or "").lower()
    return p.scheme == "https" and (host == "quark.cn" or host.endswith(".quark.cn"))


def _get(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_config(payload):
    """兼容 {data:{config}} / {config} / {data} / 裸对象，返回 (version, zip_url)。"""
    j = payload if isinstance(payload, dict) else {}
    data = j.get("data") if isinstance(j.get("data"), dict) else {}
    cfg = data.get("config") or j.get("config") or data or j
    if not isinstance(cfg, dict):
        cfg = {}
    return str(cfg.get("qkPanVersion") or ""), str(cfg.get("qkPan") or "").strip()


def resolve_zip_url(fetch=_get, timeout=30):
    """向官方接口要最新下载地址；失败或地址不是 quark.cn 时用兜底地址。"""
    try:
        raw = fetch("%s?req_id=%d" % (CONFIG_URL, int(time.time() * 1000)), timeout)
        version, url = parse_config(json.loads(raw.decode("utf-8")))
        if url and is_official_url(url):
            return version, url, "skill_config"
    except Exception:
        pass
    return "", FALLBACK_ZIP, "fallback"


def extract(zip_bytes, target):
    """校验并解压官方 zip。拒绝缺文件或路径越界的包。"""
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        raise InstallError("下载到的不是有效的 zip 包")
    names = zf.namelist()
    # 有的包外面多套一层目录
    prefix = ""
    if "SKILL.md" not in names:
        tops = {n.split("/", 1)[0] for n in names if n.strip("/")}
        if len(tops) == 1:
            prefix = tops.pop() + "/"
    if prefix + "SKILL.md" not in names or prefix + "scripts/quark-drive.cjs" not in names:
        raise InstallError("zip 包里没有 SKILL.md 或 scripts/quark-drive.cjs，不像官方 Skill")
    real_target = os.path.realpath(target)
    os.makedirs(target, exist_ok=True)
    for info in zf.infolist():
        if not info.filename.startswith(prefix):
            continue
        rel = info.filename[len(prefix):]
        if not rel:
            continue
        dest = os.path.realpath(os.path.join(target, rel))
        if dest != real_target and not dest.startswith(real_target + os.sep):
            raise InstallError("zip 包含越界路径: " + info.filename)
        if info.is_dir():
            os.makedirs(dest, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with zf.open(info) as src, open(dest, "wb") as out:
                shutil.copyfileobj(src, out)


def read_version(skill_dir):
    try:
        for line in open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8"):
            if line.startswith("version:"):
                return line.split(":", 1)[1].strip().strip("'\"")
    except OSError:
        pass
    return ""


def _run(cmd, timeout):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def run_official_setup(skill_dir, timeout=600, run=_run, which=shutil.which):
    """运行官方 install.sh，并自己验证结果。

    成功标准不依赖官方脚本的输出格式：install.sh 退出码为 0、
    scripts/quark-drive.cjs 存在、`node quark-drive.cjs --help` 能正常运行。
    官方脚本若输出了 install_result 且明确 success:false，也按失败处理。
    """
    script = os.path.join(skill_dir, "scripts", "install.sh")
    cli = os.path.join(skill_dir, CLI_REL)
    if not os.path.isfile(script):
        raise InstallError("官方包里没有 scripts/install.sh")
    if not which("bash"):
        raise InstallError("没有找到 bash，请手动运行官方 scripts/install.sh")
    try:
        proc = run(["bash", script], timeout)
    except subprocess.TimeoutExpired:
        raise InstallError("官方 install.sh 超时")

    def tail(p):
        return " | ".join(((p.stderr or "") + "\n" + (p.stdout or "")).strip().splitlines()[-5:])

    result = None  # 官方脚本的 install_result 只作参考
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("{") and "install_result" in line:
            try:
                result = json.loads(line)
            except ValueError:
                pass
    if proc.returncode != 0:
        raise InstallError("官方 install.sh 执行失败（退出码 %s）: %s" % (proc.returncode, tail(proc)))
    if isinstance(result, dict) and result.get("success") is False:
        raise InstallError("官方 install.sh 报告失败: %s" % tail(proc))
    if not os.path.isfile(cli):
        raise InstallError("安装后没有找到官方 CLI：%s" % cli)
    node = which("node")
    if not node:
        raise InstallError("安装后仍找不到 node，请检查 Node.js 16+ 是否装好")
    try:
        check = run([node, cli, "--help"], 60)
    except subprocess.TimeoutExpired:
        raise InstallError("官方 CLI --help 超时")
    if check.returncode != 0:
        raise InstallError("官方 CLI 无法运行: %s" % tail(check))
    return {"success": True, "verified": "exit0+cli+help", "install_result": result}


def install(target, setup=True, force=False, fetch=_get, timeout=60, runner=run_official_setup):
    target = os.path.expanduser(target)
    cli = os.path.join(target, CLI_REL)
    if os.path.isfile(cli) and not force:
        return {"ok": True, "status": "already_installed", "skill_dir": target, "cli": cli,
                "version": read_version(target)}
    if os.path.isdir(target) and os.listdir(target) and not force:
        raise InstallError("目标目录已存在且不是官方 Skill：%s（换个 --dir，或确认后加 --force）" % target)

    version, url, via = resolve_zip_url(fetch=fetch, timeout=timeout)
    try:
        data = fetch(url, timeout * 2)
    except Exception as e:
        raise InstallError("下载官方 zip 失败（%s）: %s" % (url, e))

    # 先解压到临时目录再移过去，失败不留半成品
    parent = os.path.dirname(os.path.abspath(target)) or "."
    os.makedirs(parent, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix=".quarkclouddrive-", dir=parent)
    try:
        extract(data, tmp)
        if os.path.isdir(target):
            shutil.rmtree(target)
        os.replace(tmp, target)
    finally:
        if os.path.isdir(tmp):
            shutil.rmtree(tmp, ignore_errors=True)

    out = {"ok": True, "status": "installed", "skill_dir": target, "cli": cli,
           "version": read_version(target) or version, "source": url, "via": via}
    if setup:
        out["setup"] = runner(target)
        out["version"] = read_version(target) or out["version"]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="从夸克官方地址安装夸克网盘 Skill（quarkclouddrive）")
    ap.add_argument("--dir", default=None, help="安装目录（默认：本 Skill 的同级 quarkclouddrive 目录）")
    ap.add_argument("--no-setup", action="store_true", help="只下载解压，不运行官方 install.sh")
    ap.add_argument("--force", action="store_true", help="目标目录已存在时覆盖")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = ap.parse_args(argv)
    target = args.dir or default_target()
    try:
        res = install(target, setup=not args.no_setup, force=args.force)
    except InstallError as e:
        res = {"ok": False, "error": str(e), "skill_dir": target, "official_page": OFFICIAL_PAGE}
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif res["ok"]:
        print("夸克网盘 Skill %s：%s（%s）" % (
            "已安装" if res["status"] == "already_installed" else "安装完成",
            res["skill_dir"], res.get("version") or "版本未知"))
    else:
        print("安装失败：%s\n可以按官方页面手动安装：%s" % (res["error"], OFFICIAL_PAGE), file=sys.stderr)
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
