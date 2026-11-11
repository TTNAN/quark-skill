#!/usr/bin/env python3
"""找到夸克官方 Skill（quarkclouddrive）的 CLI 入口 quark-drive.cjs。

用法：
    python3 find_quark_cli.py          # 找到就打印绝对路径，退出码 0
    python3 find_quark_cli.py --json   # {"ok": true, "cli": ..., "skill_dir": ...}

查找顺序：
1. 环境变量 QUARK_SKILL_DIR（官方 Skill 的安装目录）
2. 本 Skill 的兄弟目录（同一个 skills/ 目录下装的 quarkclouddrive）
3. 当前项目和用户目录下常见的 skills 目录
找不到时退出码 1，并列出查过的位置，方便告诉用户。
"""

import argparse
import glob
import json
import os
import sys

SKILL_NAME = "quarkclouddrive"
CLI_REL = os.path.join("scripts", "quark-drive.cjs")

COMMON_ROOTS = [
    ".claude/skills", ".agents/skills", ".codex/skills", ".cursor/skills",
    ".trae/skills", ".qoder/skills", ".opencode/skills", ".config/opencode/skills",
    ".openclaw/skills", ".skills",
]


def candidates():
    env = os.environ.get("QUARK_SKILL_DIR")
    if env:
        yield os.path.expanduser(env)
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yield os.path.join(os.path.dirname(here), SKILL_NAME)
    for base in (os.getcwd(), os.path.expanduser("~")):
        for root in COMMON_ROOTS:
            yield os.path.join(base, root, SKILL_NAME)
    # 兜底：用户目录下两层内任意 skills/quarkclouddrive
    for path in sorted(glob.glob(os.path.expanduser("~/.*/skills/" + SKILL_NAME))):
        yield path
    for path in sorted(glob.glob(os.path.expanduser("~/.*/*/skills/" + SKILL_NAME))):
        yield path


def find():
    checked = []
    for skill_dir in candidates():
        skill_dir = os.path.abspath(skill_dir)
        if skill_dir in checked:
            continue
        checked.append(skill_dir)
        cli = os.path.join(skill_dir, CLI_REL)
        if os.path.isfile(cli):
            return skill_dir, cli, checked
    return None, None, checked


def main(argv=None):
    parser = argparse.ArgumentParser(description="定位夸克官方 Skill 的 quark-drive.cjs")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    skill_dir, cli, checked = find()
    if args.json:
        out = {"ok": bool(cli), "cli": cli, "skill_dir": skill_dir}
        if not cli:
            out["checked"] = checked
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif cli:
        print(cli)
    else:
        print("没找到夸克官方 Skill（{}）。查过这些位置：".format(SKILL_NAME), file=sys.stderr)
        for c in checked:
            print("  " + c, file=sys.stderr)
        print("装好后可用环境变量 QUARK_SKILL_DIR 指定安装目录。", file=sys.stderr)
    return 0 if cli else 1


if __name__ == "__main__":
    raise SystemExit(main())
