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


def test_parse_urls():
    assert ps.parse_urls("https://a/, https://b  https://a") == ["https://a", "https://b"]
    assert ps.parse_urls("") == []


def test_search_many_falls_back_on_empty_and_error():
    calls = []

    def fake_search(kw, url, token, retries, timeout, sleep=None, log=None, **kw2):
        calls.append((url, retries))
        if url == "https://a":
            return [], retries + 1
        if url == "https://b":
            raise ps.SearchError("down")
        return ps.clean_links(LINKS), 1

    orig = ps.search
    ps.search = fake_search
    try:
        items, attempts, inst, errors = ps.search_many(
            "x", "https://a,https://b,https://c", retries=3, sleep=lambda s: None)
    finally:
        ps.search = orig
    assert inst == "https://c" and len(items) == 3
    assert calls == [("https://a", 3), ("https://b", 1), ("https://c", 1)]
    assert attempts == 5 and errors and "https://b" in errors[0]


def test_search_many_all_fail_raises(monkeypatch):
    def boom(*a, **k):
        raise ps.SearchError("down")
    monkeypatch.setattr(ps, "search", boom)
    with pytest.raises(ps.SearchError):
        ps.search_many("x", "https://a,https://b")


def test_search_many_empty_everywhere(monkeypatch):
    monkeypatch.setattr(ps, "search", lambda *a, **k: ([], 1))
    items, attempts, inst, errors = ps.search_many("x", "https://a,https://b")
    assert items == [] and inst == "https://b" and attempts == 2


def test_search_stops_retrying_at_deadline():
    clock = [0.0]
    sleeps = []

    def fake_fetch(url, token=None, timeout=None):
        clock[0] += timeout  # 模拟每次请求都跑满超时
        return {"code": 0, "data": {"merged_by_type": {}}}

    def sleep(s):
        sleeps.append(s)
        clock[0] += s
    items, attempts = ps.search("x", retries=3, timeout=15, fetch=fake_fetch, sleep=sleep,
                                deadline=40, now=lambda: clock[0])
    # 0s 请求→15s；+5 等待+15 请求=35s；再 +10+15 会超 40，停
    assert attempts == 2 and sleeps == [5] and items == []


def test_search_many_worst_case_is_bounded():
    clock = [0.0]

    def fake_fetch(url, token=None, timeout=None):
        clock[0] += timeout
        return {"code": 0, "data": {"merged_by_type": {}}}
    orig = ps.fetch_json
    ps.fetch_json = fake_fetch
    try:
        # search 的 fetch 默认参数在定义时就绑定了，这里直接包一层
        real = ps.search

        def wrapped(*a, **k):
            k["fetch"] = fake_fetch
            k["sleep"] = lambda s: clock.__setitem__(0, clock[0] + s)
            return real(*a, **k)
        ps.search = wrapped
        ps.search_many("x", "https://a,https://b", now=lambda: clock[0])
    finally:
        ps.search = real
        ps.fetch_json = orig
    # 默认：超时 15 秒、预算 60 秒、两个实例 → 最坏不超过 60 + 2×15
    assert clock[0] <= ps.DEFAULT_MAX_WAIT + 2 * ps.DEFAULT_TIMEOUT
