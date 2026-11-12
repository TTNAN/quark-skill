#!/usr/bin/env python3
"""找到夸克官方 Skill（quarkclouddrive）的 CLI 入口 quark-drive.cjs。

用法：
    python3 find_quark_cli.py          # 找到就打印绝对路径，退出码 0
    python3 find_quark_cli.py --json   # {"ok": true, "cli": ..., "skill_dir": ...}

查找规则：
1. 环境变量 QUARK_SKILL_DIR 指定时只认它（用户明确指定，不再比较）。
2. 否则查本 Skill 的兄弟目录、用户目录和当前项目下常见的 skills 目录，
   每个找到的 quark-drive.cjs 都跑一次 `node quark-drive.cjs --help` 验证能运行，
   在能运行的里面取版本号（官方 SKILL.md 的 version）最高的；同版本按上面的顺序。
   这样项目里残留的旧版不会盖过全局新装的版本，文件被截断的半成品也不会被当成“找到”。
找不到能运行的就退出码 1，列出查过的位置和跑不起来的原因。
`--no-verify` 跳过运行验证，只看文件在不在。
"""

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys

SKILL_NAME = "quarkclouddrive"
CLI_REL = os.path.join("scripts", "quark-drive.cjs")

COMMON_ROOTS = [
    ".claude/skills", ".agents/skills", ".codex/skills", ".cursor/skills",
    ".trae/skills", ".qoder/skills", ".opencode/skills", ".config/opencode/skills",
    ".openclaw/skills", ".workbuddy/skills", ".codebuddy/skills", ".skills",
]


def candidates():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yield os.path.join(os.path.dirname(here), SKILL_NAME)
    for base in (os.path.expanduser("~"), os.getcwd()):
        for root in COMMON_ROOTS:
            yield os.path.join(base, root, SKILL_NAME)
    # 兜底：用户目录下两层内任意 skills/quarkclouddrive
    for path in sorted(glob.glob(os.path.expanduser("~/.*/skills/" + SKILL_NAME))):
        yield path
    for path in sorted(glob.glob(os.path.expanduser("~/.*/*/skills/" + SKILL_NAME))):
        yield path


def read_version(skill_dir):
    """官方 SKILL.md frontmatter 里的 version，读不到返回空串。"""
    try:
        with open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("version:"):
                    return line.split(":", 1)[1].strip().strip("'\"")
    except OSError:
        pass
    return ""


def version_key(v):
    return tuple(int(x) for x in re.findall(r"\d+", v or "")) or (-1,)


def verify_cli(cli, timeout=10):
    """跑一次 node <cli> --help，返回 None 表示能用，否则返回原因。"""
    node = shutil.which("node")
    if not node:
        return "找不到 node（需要 Node.js 16+）"
    try:
        p = subprocess.run([node, cli, "--help"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return "--help 超时"
    except OSError as e:
        return "无法运行：%s" % e
    if p.returncode != 0:
        tail = ((p.stderr or "") + (p.stdout or "")).strip().splitlines()[-1:]
        return "--help 退出码 %s %s" % (p.returncode, " ".join(tail))
    return None


def find(verify=verify_cli, env=None):
    """返回 (skill_dir, cli, checked, broken)。"""
    env = os.environ.get("QUARK_SKILL_DIR") if env is None else env
    checked, broken, good = [], [], []
    dirs = [os.path.expanduser(env)] if env else list(candidates())
    for skill_dir in dirs:
        skill_dir = os.path.abspath(skill_dir)
        if skill_dir in checked:
            continue
        checked.append(skill_dir)
        cli = os.path.join(skill_dir, CLI_REL)
        if not os.path.isfile(cli):
            continue
        why = verify(cli) if verify else None
        if why:
            broken.append({"skill_dir": skill_dir, "reason": why})
            continue
        good.append((skill_dir, cli, read_version(skill_dir)))
    if not good:
        return None, None, checked, broken
    best = max(enumerate(good), key=lambda x: (version_key(x[1][2]), -x[0]))[1]
    return best[0], best[1], checked, broken


def main(argv=None):
    parser = argparse.ArgumentParser(description="定位夸克官方 Skill 的 quark-drive.cjs")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-verify", action="store_true", help="不跑 --help 验证，只看文件在不在")
    args = parser.parse_args(argv)
    skill_dir, cli, checked, broken = find(verify=None if args.no_verify else verify_cli)
    if args.json:
        out = {"ok": bool(cli), "cli": cli, "skill_dir": skill_dir,
               "version": read_version(skill_dir) if skill_dir else ""}
        if broken:
            out["broken"] = broken
        if not cli:
            out["checked"] = checked
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif cli:
        print(cli)
    else:
        print("没找到夸克官方 Skill（{}）。查过这些位置：".format(SKILL_NAME), file=sys.stderr)
        for c in checked:
            print("  " + c, file=sys.stderr)
        for b in broken:
            print("找到了但跑不起来：{}（{}）".format(b["skill_dir"], b["reason"]), file=sys.stderr)
        print("装好后可用环境变量 QUARK_SKILL_DIR 指定安装目录。", file=sys.stderr)
    return 0 if cli else 1


if __name__ == "__main__":
    raise SystemExit(main())
