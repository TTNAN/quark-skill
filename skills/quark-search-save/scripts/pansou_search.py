#!/usr/bin/env python3
"""PanSou 网盘搜索客户端（只用 Python 标准库，Python 3.9+）。

查询 PanSou 聚合搜索 API，返回去重、按日期倒序排好的夸克网盘（quark）分享链接。

用法：
    python3 pansou_search.py --kw "关键词" [--limit 5] [--json]
                             [--url https://so.252035.xyz] [--token <TOKEN>]
                             [--retries 3] [--timeout 25] [--max-wait 60]

说明：
- 默认使用 PanSou 公共实例 https://so.252035.xyz （PanSou 作者的演示站），不带 key 就能用。
  （s.panhunt.com 自 2026-11 起要求认证令牌，已不在默认列表里；有令牌可用 --url + --token。）
- 自部署实例用 --url（或环境变量 PANSOU_URL），可以用逗号写多个，前一个出错或没结果时按顺序换下一个；实例开了认证
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

__version__ = "1.3.6"

DEFAULT_URL = "https://so.252035.xyz"
# 默认实例列表：第一个没结果或出错时依次尝试后面的。
# s.panhunt.com 2026-11-13 实测不带令牌一律返回 AUTH_TOKEN_MISSING，已移出默认列表。
DEFAULT_URLS = (DEFAULT_URL,)
FALLBACK_RETRIES = 1  # 备用实例只重试 1 次，避免总耗时过长
DEFAULT_TIMEOUT = 25  # 单次请求超时（秒）。公共实例实测单次 6–18 秒才返回，别再往下调
DEFAULT_MAX_WAIT = 60  # 重试总预算（秒）：最坏约 60 + 实例数 × 25 ≈ 110 秒
RETRY_DELAYS = (5, 10, 15)  # 第 n 次重试前等待的秒数（PanSou 冷启动实测需 10–30 秒）
_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


class SearchError(RuntimeError):
    """搜索请求失败（网络、HTTP、响应格式）。"""


class AuthError(SearchError):
    """实例要求认证令牌：重试没用，直接换实例或报错。"""


def _auth_error(code, detail):
    return AuthError(
        "PanSou 搜索失败：这个实例需要认证令牌（{}：{}），"
        "请用 --token 或环境变量 PANSOU_TOKEN 传入，或换一个实例".format(code, detail))


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
        if e.code in (401, 403) and "AUTH_" in body:
            try:
                err = json.loads(body)
            except ValueError:
                err = {}
            raise _auth_error(err.get("code") or e.code, err.get("error") or body) from e
        raise SearchError("PanSou 搜索失败：HTTP {} {}".format(e.code, " ".join(body.split())[:200])) from e
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
    code = payload.get("code")
    if code != 0:
        detail = payload.get("message") or payload.get("error") or payload
        if isinstance(code, str) and code.startswith("AUTH_"):
            raise _auth_error(code, detail)
        raise SearchError("PanSou 搜索失败：{}".format(detail))
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


def search(keyword, base_url=DEFAULT_URL, token=None, retries=3, timeout=DEFAULT_TIMEOUT,
           sleep=time.sleep, fetch=fetch_json, log=None, deadline=None, now=time.monotonic):
    """搜索夸克链接。结果为空或临时出错（超时、HTTP 5xx/400 等）时用同一关键词退避重试 retries 次。

    deadline（time.monotonic 时刻）到了就不再重试，但至少请求一次。
    认证错误（AuthError）不重试。重试用完仍出错时抛最后一次的 SearchError；
    只要有一次请求成功（哪怕为空），就返回 (items, attempts)。
    """
    url = build_url(base_url, keyword)
    attempts = 0
    items = []
    last_error = None
    for attempt in range(retries + 1):
        if attempt:
            delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
            if deadline is not None and now() + delay + timeout > deadline:
                if log:
                    log("已经等了很久，不再重试 {}。".format(base_url))
                break
            if log:
                if last_error is not None:
                    log("请求出错（{}），{} 秒后用同一关键词重试（第 {}/{} 次）…".format(
                        last_error, delay, attempt, retries))
                else:
                    log("暂无结果，PanSou 可能还在聚合，{} 秒后用同一关键词重试（第 {}/{} 次）…".format(
                        delay, attempt, retries))
            sleep(delay)
        attempts += 1
        try:
            items = clean_links(parse_payload(fetch(url, token=token, timeout=timeout)))
        except AuthError:
            raise
        except SearchError as e:
            last_error = e
            continue
        last_error = None
        if items:
            break
    if last_error is not None:
        raise last_error
    return items, attempts


def parse_urls(value):
    """把逗号或空白分隔的实例地址拆成列表，去掉空项和重复项。"""
    if isinstance(value, (list, tuple)):
        parts = list(value)
    else:
        parts = re.split(r"[,\s]+", value or "")
    out = []
    for u in parts:
        u = (u or "").strip().rstrip("/")
        if u and u not in out:
            out.append(u)
    return out


def search_many(keyword, urls=DEFAULT_URLS, token=None, retries=3, timeout=DEFAULT_TIMEOUT,
                sleep=time.sleep, log=None, max_wait=DEFAULT_MAX_WAIT, now=time.monotonic):
    """按顺序在多个 PanSou 实例上搜索，拿到结果就停。

    第一个实例用完整的 retries；后面的备用实例最多重试 FALLBACK_RETRIES 次。
    返回 (items, attempts, instance, errors)：instance 是给出结果（或最后成功响应）的实例。
    所有实例都请求失败时抛 SearchError。
    max_wait 是重试的总时间预算（秒）：超出后不再重试，但每个实例至少请求一次。
    最坏耗时约 max_wait + 实例数 × timeout。
    """
    deadline = now() + max_wait if max_wait else None
    urls = parse_urls(urls) or list(DEFAULT_URLS)
    attempts = 0
    errors = []
    answered = None
    for i, url in enumerate(urls):
        n = retries if i == 0 else min(retries, FALLBACK_RETRIES)
        if log:
            if i:
                log("{} 没有结果，换备用实例 {} 再试…".format(urls[i - 1], url))
            else:
                log("正在搜索「{}」（{}）…".format(keyword, url))
        try:
            items, used = search(keyword, url, token, n, timeout, sleep=sleep, log=log,
                                 deadline=deadline, now=now)
        except SearchError as e:
            errors.append("{}: {}".format(url, e))
            continue
        attempts += used
        answered = url
        if items:
            return items, attempts, url, errors
    if answered is None:
        raise SearchError("；".join(errors) if errors else "PanSou 搜索失败")
    return [], attempts, answered, errors


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
    parser.add_argument("--url", default=os.environ.get("PANSOU_URL", ",".join(DEFAULT_URLS)),
                        help="PanSou 实例地址，逗号分隔可写多个，按顺序尝试（默认 {}）".format(
                            ",".join(DEFAULT_URLS)))
    parser.add_argument("--token", default=os.environ.get("PANSOU_TOKEN", ""),
                        help="自部署实例开启认证时的 JWT（默认不填）")
    parser.add_argument("--limit", type=int, default=5, help="最多输出几条（默认 5）")
    parser.add_argument("--retries", type=int, default=3,
                        help="结果为空时用同一关键词重试几次（默认 3，0 表示不重试）")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help="单次请求超时秒数（默认 {}）".format(DEFAULT_TIMEOUT))
    parser.add_argument("--max-wait", type=float, default=DEFAULT_MAX_WAIT,
                        help="重试的总时间预算秒数，超出就不再重试（默认 {}，0 表示不限）".format(
                            DEFAULT_MAX_WAIT))
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
        items, attempts, instance, errors = search_many(
            kw, args.url, args.token or None, args.retries, args.timeout, log=log,
            max_wait=args.max_wait)
    except SearchError as e:
        if args.json:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        else:
            print(str(e), file=sys.stderr)
        return 1

    shown = items[: args.limit]
    if args.json:
        print(json.dumps({"ok": True, "keyword": kw, "quark_total": len(items),
                          "attempts": attempts, "instance": instance,
                          "instance_errors": errors, "quark_links": shown},
                         ensure_ascii=False, indent=2))
    else:
        print(format_text(shown, len(items), attempts), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
