#!/usr/bin/env python3
"""PanSou 网盘搜索客户端（只用 Python 标准库，Python 3.10+）。

查询 PanSou 聚合搜索 API，返回去重、按日期倒序排好的夸克网盘（quark）分享链接。

用法：
    python3 pansou_search.py --kw "关键词" [--limit 5] [--json]
                             [--url https://s.panhunt.com] [--token <TOKEN>]
                             [--retries 3] [--timeout 30]

说明：
- 默认使用 PanSou 公共实例 https://s.panhunt.com ，不带 key 就能用。
- 自部署实例用 --url（或环境变量 PANSOU_URL）；实例开了认证
  （AUTH_ENABLED=true）再用 --token（或 PANSOU_TOKEN）传 JWT。
- PanSou 对新关键词是异步聚合的，第一次请求常常返回 0 条。
  脚本会用【同一个关键词】自动退避重试（默认最多再试 3 次，共约 30 秒），不会改词。
- 本脚本只做搜索，不做转存。转存请走夸克官方 Skill 的 saveas 命令。

退出码：0 = 请求成功（结果可能为空）；1 = 请求失败（网络/HTTP/响应格式）。
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

__version__ = "1.1.2"

DEFAULT_URL = "https://s.panhunt.com"
RETRY_DELAYS = (5, 10, 15)  # 第 n 次重试前等待的秒数（PanSou 冷启动实测需 10–30 秒）
_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


class SearchError(RuntimeError):
    """搜索请求失败（网络、HTTP、响应格式）。"""


def fetch_json(url, token=None, timeout=30):
    """GET 一个 URL 并解析 JSON；任何失败都转成 SearchError。"""
    req = urllib.request.Request(url, method="GET")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "quark-search-save-skill/" + __version__)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:300]
        raise SearchError("PanSou 搜索失败：HTTP {} {}".format(e.code, body)) from e
    except (urllib.error.URLError, OSError) as e:  # 含超时、DNS、连接重置
        raise SearchError("PanSou 搜索失败：网络错误 {}".format(e)) from e
    try:
        return json.loads(raw)
    except ValueError as e:
        snippet = " ".join(raw.split())[:200]
        raise SearchError(
            "PanSou 搜索失败：返回的不是 JSON（可能被限流或拦截）：{}".format(snippet)
        ) from e


def build_url(base_url, keyword):
    params = {"kw": keyword, "cloud_types": "quark", "res": "merge"}
    return base_url.rstrip("/") + "/api/search?" + urllib.parse.urlencode(params)


def parse_payload(payload):
    """从 PanSou 响应里取出夸克链接原始列表；业务错误抛 SearchError。"""
    if not isinstance(payload, dict):
        raise SearchError("PanSou 搜索失败：响应格式不对")
    if payload.get("code") != 0:
        raise SearchError("PanSou 搜索失败：{}".format(payload.get("message") or payload))
    data = payload.get("data") or {}
    merged = data.get("merged_by_type") or {}
    return merged.get("quark") or []


def normalize_date(value):
    """'Wed 2026-11-11 12:42 PM (UTC+08:00)' -> '2026-11-11'；空值/0001 年 -> ''。"""
    m = _DATE_RE.search(value or "")
    if not m or m.group(1) == "0001":
        return ""
    return "-".join(m.groups())


def link_key(url):
    """去重用的键：去掉协议、查询串和末尾斜杠，只留 host + path。"""
    p = urllib.parse.urlsplit((url or "").strip())
    return (p.netloc.lower() + p.path.rstrip("/")) or url


def has_pwd_in_url(url):
    return "pwd" in urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)


def clean_links(raw_links):
    """规整、去重、按日期倒序（无日期的排最后）。"""
    seen = {}
    for item in raw_links:
        url = (item.get("url") or "").strip()
        if "pan.quark.cn" not in url:
            continue
        key = link_key(url)
        entry = {
            "title": " ".join((item.get("note") or "").split()) or "（无标题）",
            "date": normalize_date(item.get("datetime")),
            "url": url,
            "password": (item.get("password") or "").strip(),
            "source": item.get("source") or "",
        }
        old = seen.get(key)
        # 同一链接出现多次：保留日期更新的那条，并补上缺失的提取码
        if old is None or entry["date"] > old["date"]:
            if old and not entry["password"]:
                entry["password"] = old["password"]
            seen[key] = entry
        elif not old["password"] and entry["password"]:
            old["password"] = entry["password"]
    items = list(seen.values())
    items.sort(key=lambda x: x["date"] or "0000-00-00", reverse=True)
    for it in items:
        # 提取码已在 URL 里就不用再单独传 --passcode
        it["needs_passcode"] = bool(it["password"]) and not has_pwd_in_url(it["url"])
    return items


def search(keyword, base_url=DEFAULT_URL, token=None, retries=3, timeout=30,
           sleep=time.sleep, fetch=fetch_json, log=None):
    """搜索夸克链接。结果为空时用同一关键词退避重试 retries 次。

    返回 (items, attempts)。
    """
    url = build_url(base_url, keyword)
    attempts = 0
    items = []
    for attempt in range(retries + 1):
        if attempt:
            delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
            if log:
                log("暂无结果，PanSou 可能还在聚合，{} 秒后用同一关键词重试（第 {}/{} 次）…".format(
                    delay, attempt, retries))
            sleep(delay)
        attempts += 1
        items = clean_links(parse_payload(fetch(url, token=token, timeout=timeout)))
        if items:
            break
    return items, attempts


def format_text(items, total, attempts):
    if not items:
        return "没有搜到夸克网盘链接（同一关键词共请求 {} 次）。\n".format(attempts)
    lines = ["共找到 {} 条夸克网盘链接（已去重，按日期从新到旧），前 {} 条：".format(
        total, len(items)), ""]
    for i, it in enumerate(items, 1):
        lines.append("[{}] {}".format(i, it["title"]))
        if it["date"]:
            lines.append("    日期：{}".format(it["date"]))
        lines.append("    链接：{}".format(it["url"]))
        if it["needs_passcode"]:
            lines.append("    提取码：{}（转存时加 --passcode）".format(it["password"]))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="PanSou 夸克网盘搜索")
    parser.add_argument("--kw", required=True, help="搜索关键词（片名/书名/课程名本身）")
    parser.add_argument("--url", default=os.environ.get("PANSOU_URL", DEFAULT_URL),
                        help="PanSou 实例地址（默认 {}）".format(DEFAULT_URL))
    parser.add_argument("--token", default=os.environ.get("PANSOU_TOKEN", ""),
                        help="自部署实例开启认证时的 JWT（默认不填）")
    parser.add_argument("--limit", type=int, default=5, help="最多输出几条（默认 5）")
    parser.add_argument("--retries", type=int, default=3,
                        help="结果为空时用同一关键词重试几次（默认 3，约 30 秒，0 表示不重试）")
    parser.add_argument("--timeout", type=float, default=30, help="单次请求超时秒数（默认 30）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    args = parser.parse_args(argv)

    kw = args.kw.strip()
    if not kw:
        parser.error("--kw 不能为空")
    if args.limit < 1:
        parser.error("--limit 至少为 1")
    if args.retries < 0:
        parser.error("--retries 不能为负数")

    def log(msg):
        print(msg, file=sys.stderr)

    try:
        items, attempts = search(kw, args.url, args.token or None, args.retries,
                                 args.timeout, log=log)
    except SearchError as e:
        if args.json:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        else:
            print(str(e), file=sys.stderr)
        return 1

    shown = items[: args.limit]
    if args.json:
        print(json.dumps({"ok": True, "keyword": kw, "quark_total": len(items),
                          "attempts": attempts, "quark_links": shown},
                         ensure_ascii=False, indent=2))
    else:
        print(format_text(shown, len(items), attempts), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
