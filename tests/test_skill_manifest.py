"""SKILL.md 的 frontmatter 必须是合法 YAML，否则 `npx skills add` 会直接跳过这个 Skill。"""
import os
import re

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(HERE, "..", "skills", "quark-search-save", "SKILL.md")


def load_frontmatter():
    text = open(SKILL, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "SKILL.md 必须以 --- 包裹的 frontmatter 开头"
    return yaml.safe_load(m.group(1))


def test_frontmatter_is_valid_yaml():
    fm = load_frontmatter()
    assert fm["name"] == "quark-search-save"
    assert isinstance(fm["description"], str) and len(fm["description"]) > 20


def test_version_matches_script():
    import sys
    sys.path.insert(0, os.path.join(HERE, "..", "skills", "quark-search-save", "scripts"))
    import pansou_search
    assert str(load_frontmatter()["metadata"]["version"]) == pansou_search.__version__
