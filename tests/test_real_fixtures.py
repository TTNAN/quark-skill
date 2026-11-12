"""用 WorkBuddy 里真实跑出来的官方 CLI 输出做回归测试（2026-11-12，官方 Skill 1.0.25）。

固件已脱敏（昵称、头像、uptoken、share_fid_token、用户目录名、剩余容量）。
官方一改返回结构，这里会先红。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skills", "quark-search-save", "scripts"))

import check_links as cl  # noqa: E402

FX = os.path.join(HERE, "fixtures", "workbuddy")
# 这批固件来自哪个官方版本。官方升级后重跑真机、刷新固件，并同步改这里、README 和 CONTRIBUTING。
VERIFIED_OFFICIAL_VERSION = "1.0.25"


def read(name):
    with open(os.path.join(FX, name), encoding="utf-8") as f:
        return f.read()


def lines(name):
    return [json.loads(l) for l in read(name).splitlines() if l.strip()]


def test_valid_share_detail_shape():
    first = lines("share-detail-valid.jsonl")[0]
    assert cl.last_result(read("share-detail-valid.jsonl").splitlines()[0]) == first
    status, info = cl.classify(first)
    assert status == "valid"
    assert info["share_title"] == "机器学习的数学基础（53集 高等数学 线性代数 概率论 数理统计）"
    assert info["file_num"] == 1 and info["folders"] == 1  # 一个顶层文件夹，file_type 是字符串 "0"
    assert info["total_files"] == 53
    assert info["total_size"].endswith("GB")


def test_subfolder_listing_is_valid():
    sub = lines("share-detail-valid.jsonl")[1]
    status, info = cl.classify(sub)
    assert status == "valid"
    assert info["folders"] == 5
    assert all(isinstance(f["fid"], str) and f["fid"] for f in sub["data"]["files"])


def test_dead_link_passthrough_code():
    dead = lines("share-detail-dead.jsonl")[0]
    assert dead["code"] == 41006  # 服务端 errno 直接作为 code 透传，msg 里没有 errno=
    status, info = cl.classify(dead)
    assert status == "invalid" and info["errno"] == 41006


def test_saveas_shape():
    r = lines("saveas.jsonl")[0]
    assert r["code"] == 0 and r["action"] == "saveas"
    assert r["data"]["save_path"] == "来自：分享"
    assert r["data"]["save_as"]["save_as_top_fids"]


def test_search_verify_has_result_then_artifact():
    rs = lines("search-verify.jsonl")
    assert [r["type"] for r in rs] == ["result", "artifact"]
    assert cl.last_result(read("search-verify.jsonl")) == rs[0]  # 回查要取 result 行，不是 artifact
    assert rs[0]["data"]["file_list"][0]["filename"] == "第3章-线性代数"


def test_update_files_no_change():
    r = lines("get-share-update-files.jsonl")[0]
    assert r["code"] == 0 and r["data"]["total"] == 0 and r["data"]["files"] == []


def test_fixtures_match_verified_version():
    assert json.loads(read("install.json"))["version"] == VERIFIED_OFFICIAL_VERSION
    root = os.path.join(HERE, "..")
    # 钉住声明验证版本的那一行本身，不是全文子串（README 的下载地址里也带版本号）
    for doc, marker in (("README.md", "已实测验证"), ("README.en.md", "Verified end to end"),
                        ("CONTRIBUTING.md", "当前验证版本")):
        with open(os.path.join(root, doc), encoding="utf-8") as f:
            lines = [ln for ln in f if marker in ln]
        assert len(lines) == 1 and VERIFIED_OFFICIAL_VERSION in lines[0], doc


def test_install_output_shape():
    r = json.loads(read("install.json"))
    assert r["ok"] and r["setup"]["verified"] == "exit0+cli+help"
    assert r["setup"]["install_result"]["type"] == "install_result"


def test_share_search_hit_shape():
    r = lines("share-search-hit.jsonl")[0]
    assert r["code"] == 0 and r["action"] == "share-search"
    f = r["data"]["files"][0]
    assert r["data"]["file_count"] == 1
    assert f["filename"] == "第3章-线性代数"
    assert f["file_type"] == "0"  # 和 share-detail 的 files[] 一样是字符串
    assert f["fid"]  # saveas --fid-list 要用的就是它


def test_share_search_empty_is_success_not_error():
    r = lines("share-search-empty.jsonl")[0]
    assert r["code"] == 0 and r["data"] == {"file_count": 0, "files": []}
