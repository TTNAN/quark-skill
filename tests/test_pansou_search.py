import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skills", "quark-search-save", "scripts"))

import pansou_search as ps  # noqa: E402


def payload(links):
    return {"code": 0, "message": "success",
            "data": {"total": len(links), "merged_by_type": {"quark": links}}}


LINKS = [
    {"url": "https://pan.quark.cn/s/aaa", "password": "", "note": "线性代数 课件",
     "datetime": "Sun 2025-09-07 2:07 AM (UTC+08:00)", "source": "plugin:x"},
    {"url": "https://pan.quark.cn/s/aaa/", "password": "", "note": "线性代数 课件（重复）",
     "datetime": "Sat 2026-11-07 2:53 PM (UTC+08:00)", "source": "plugin:y"},
    {"url": "https://pan.quark.cn/s/bbb", "password": "ab12", "note": "  几何   讲义 ",
     "datetime": "Mon 0001-01-01 8:00 AM (UTC+08:00)", "source": "tg"},
    {"url": "https://pan.quark.cn/s/ccc?pwd=zz99", "password": "zz99", "note": "",
     "datetime": "Wed 2026-11-11 12:42 PM (UTC+08:00)", "source": "tg"},
    {"url": "https://pan.baidu.com/s/ddd", "password": "", "note": "不是夸克",
     "datetime": "Wed 2026-11-11 12:42 PM (UTC+08:00)", "source": "tg"},
]


def test_normalize_date():
    assert ps.normalize_date("Wed 2026-11-11 12:42 PM (UTC+08:00)") == "2026-11-11"
    assert ps.normalize_date("Mon 0001-01-01 8:00 AM (UTC+08:00)") == ""
    assert ps.normalize_date("") == ""
    assert ps.normalize_date(None) == ""


def test_clean_links_dedupes_sorts_and_filters():
    items = ps.clean_links(LINKS)
    urls = [i["url"] for i in items]
    assert urls == ["https://pan.quark.cn/s/ccc?pwd=zz99",
                    "https://pan.quark.cn/s/aaa/",
                    "https://pan.quark.cn/s/bbb"]
    assert items[1]["date"] == "2026-11-07"   # 重复链接保留较新的
    assert items[2]["title"] == "几何 讲义"      # 空白被规整
    assert items[2]["date"] == ""              # 0001 年视为无日期，排最后
    assert items[0]["title"] == "（无标题）"


def test_needs_passcode():
    items = {i["url"]: i for i in ps.clean_links(LINKS)}
    assert items["https://pan.quark.cn/s/bbb"]["needs_passcode"] is True
    assert items["https://pan.quark.cn/s/ccc?pwd=zz99"]["needs_passcode"] is False
    assert items["https://pan.quark.cn/s/aaa/"]["needs_passcode"] is False


def test_parse_payload_error():
    with pytest.raises(ps.SearchError):
        ps.parse_payload({"code": 1, "message": "rate limited"})
    with pytest.raises(ps.SearchError):
        ps.parse_payload(["not", "a", "dict"])


def test_search_retries_same_keyword_until_results():
    calls, sleeps = [], []
    responses = [payload([]), payload([]), payload(LINKS)]

    def fake_fetch(url, token=None, timeout=30):
        calls.append(url)
        return responses[len(calls) - 1]

    items, attempts = ps.search("线性代数", retries=2, fetch=fake_fetch, sleep=sleeps.append)
    assert attempts == 3 and len(items) == 3
    assert len(set(calls)) == 1          # 每次都是同一个关键词
    assert sleeps == [5, 10]


def test_search_no_retry_when_disabled():
    sleeps = []
    items, attempts = ps.search("x", retries=0, fetch=lambda *a, **k: payload([]),
                                sleep=sleeps.append)
    assert items == [] and attempts == 1 and sleeps == []


def test_build_url_uses_merge():
    url = ps.build_url("https://s.panhunt.com/", "线性 代数")
    assert url.startswith("https://s.panhunt.com/api/search?")
    assert "res=merge" in url and "cloud_types=quark" in url


def test_fetch_json_non_json(monkeypatch):
    class Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b"<html>blocked</html>"

    monkeypatch.setattr(ps.urllib.request, "urlopen", lambda *a, **k: Resp())
    with pytest.raises(ps.SearchError, match="不是 JSON"):
        ps.fetch_json("https://example.invalid")


def test_main_json_output(monkeypatch, capsys):
    monkeypatch.setattr(ps, "fetch_json", lambda *a, **k: payload(LINKS))
    monkeypatch.setattr(ps, "search",
                        lambda *a, **k: (ps.clean_links(LINKS), 1))
    assert ps.main(["--kw", "线性代数", "--json", "--limit", "2"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] and out["quark_total"] == 3 and len(out["quark_links"]) == 2


def test_main_error_exit_code(monkeypatch, capsys):
    def boom(*a, **k):
        raise ps.SearchError("PanSou 搜索失败：网络错误")
    monkeypatch.setattr(ps, "search", boom)
    assert ps.main(["--kw", "x", "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False


def test_main_rejects_bad_args():
    with pytest.raises(SystemExit):
        ps.main(["--kw", "   "])
    with pytest.raises(SystemExit):
        ps.main(["--kw", "x", "--limit", "0"])
