import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "quark-search-save", "scripts"))
import check_links as cl  # noqa: E402

OK = {"code": 0, "msg": "成功", "type": "result", "action": "share-detail",
      "data": {"token_info": {"title": "线代课件"}, "share_info": {"file_num": 4}, "file_count": 4,
               "files": [{"fid": "d", "filename": "习题", "size": 0, "file_type": "0"},
                         {"fid": "a", "filename": "第1章.pdf", "size": 1048576, "file_type": "1"},
                         {"fid": "b", "filename": "第2章.pdf", "size": 524288, "file_type": "1"},
                         {"fid": "c", "filename": "第3章.pdf", "size": 1, "file_type": "1"}]}}
DEAD = {"code": -803, "msg": "获取分享详情失败: errno=41007, message=share not exist", "type": "result"}
ODD = {"code": -1, "msg": "网络异常", "type": "result"}
RUNTIME = {"code": -104, "msg": "无法识别当前 Agent 环境，禁止继续使用", "action": "runtime", "type": "result"}


def links(n):
    return [{"title": "t%d" % i, "url": "https://pan.quark.cn/s/%d" % i, "password": "",
             "needs_passcode": False} for i in range(n)]


def fake(mapping):
    def call(cli, link, si, sid, upd):
        return mapping[link["url"]]
    return call


def test_human_size():
    assert cl.human_size(1572864) == "1.5 MB"
    assert cl.human_size(10) == "10 B"


def test_last_result_picks_result_line():
    out = '{"type":"progress"}\nnoise\n' + json.dumps(OK)
    assert cl.last_result(out)["code"] == 0


def test_classify():
    s, info = cl.classify(OK)
    assert s == "valid" and info["file_num"] == 4 and info["folders"] == 1
    assert info["preview"] == ["习题", "第1章.pdf", "第2章.pdf"] and info["listed_size"] == "1.5 MB"
    assert cl.classify(DEAD)[0] == "invalid"
    assert cl.classify(ODD)[0] == "unknown"
    assert cl.classify(RUNTIME)[0] == "runtime"
    assert cl.classify(None)[0] == "unknown"


def test_check_drops_dead_keeps_order_and_limit():
    ls = links(4)
    m = {ls[0]["url"]: DEAD, ls[1]["url"]: OK, ls[2]["url"]: ODD, ls[3]["url"]: OK}
    res = cl.check(ls, "cli", "q", "s", keep=2, call=fake(m))
    assert [x["url"] for x in res["shown"]] == [ls[1]["url"], ls[2]["url"]]
    assert res["invalid"][0]["url"] == ls[0]["url"]
    assert res["valid_count"] == 2 and not res["check_skipped"]


def test_check_skipped_when_cli_unusable():
    ls = links(3)
    res = cl.check(ls, "cli", "q", "s", call=fake({l["url"]: RUNTIME for l in ls}))
    assert res["check_skipped"] and len(res["shown"]) == 3 and res["invalid"] == []


def test_notices_deduped():
    ok = dict(OK, notice={"kind": "skill_updated", "text": "已升级"})
    ls = links(2)
    res = cl.check(ls, "cli", "q", "s", call=fake({l["url"]: ok for l in ls}))
    assert res["notices"] == ["已升级"]


def test_run_cli_builds_command():
    seen = {}

    class P:
        stdout = json.dumps(OK)

    def runner(cmd, **kw):
        seen["cmd"] = cmd
        return P()
    link = {"url": "https://pan.quark.cn/s/x", "password": "ab12", "needs_passcode": True}
    cl.run_cli("/c.cjs", link, "原话", "1-abc", skill_updated=True, runner=runner)
    c = seen["cmd"]
    assert c[:4] == ["node", "/c.cjs", "share-detail", "--url"]
    assert "--passcode" in c and "ab12" in c and "--skill-updated" in c
    assert c[c.index("--session-input") + 1] == "原话"
