#!/usr/bin/env python3
"""转存前先验一遍候选链接（调用夸克官方 CLI 的 share-detail，客态模式无需登录）。

读 pansou_search.py --json 的输出，对每条链接调用：
  node <quark-cli> share-detail --url <链接> [--passcode <提取码>] --size 20 \
       --session-input "<用户原话>" --session-id "<会话 ID>"
然后把明确失效的剔除（只认已知失效码），有效的补上分享标题、文件数和内容预览。
拿不准的（网络抖动、限流、未知错误）一律标 unknown 留给用户。进度打到 stderr。

用法：
  python3 pansou_search.py --kw "线性代数" --limit 10 --json > /tmp/qs.json
  python3 check_links.py --cli <quark-cli> --session-input "<用户原话>" \
      --session-id "<会话 ID>" --input /tmp/qs.json --keep 5

只调用官方 CLI，不直接请求任何夸克接口。
"""
import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# 只认已知的「分享本身不可用」错误码；其余一律算 unknown，交给用户决定，不直接判死。
# 41004 文件列表为空/已过期，41006 分享不存在，41007 share not exist（官方文档示例）。
DEAD_ERRNOS = {41004, 41006, 41007}
_ERRNO_RE = re.compile(r"errno\s*[=:]\s*(\d+)")
PREVIEW = 3


def human_size(n):
    try:
        n = float(n)
    except (TypeError, ValueError):
        return ""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return ("%d %s" % (n, unit)) if unit == "B" else ("%.1f %s" % (n, unit))
        n /= 1024.0


def last_result(stdout):
    """官方 CLI 输出 JSONL，取最后一行 type=result。"""
    res = None
    for line in (stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if obj.get("type") == "result":
            res = obj
    return res


def classify(result):
    """返回 (status, info)。status: valid / invalid / unknown / runtime。"""
    if not result:
        return "unknown", {"msg": "官方 CLI 没有返回结果"}
    code = result.get("code")
    msg = str(result.get("msg") or "")
    if code == 0:
        data = result.get("data") or {}
        files = data.get("files") or []
        share_info = data.get("share_info") or {}
        token_info = data.get("token_info") or {}
        if not files and share_info.get("file_num") == 0:
            return "invalid", {"msg": "分享里没有文件（可能已被删除或屏蔽）", "errno": None}
        folders = sum(1 for f in files if str(f.get("file_type")) == "0")
        size = sum(int(f.get("size") or 0) for f in files if str(f.get("file_type")) != "0")
        info = {
            "share_title": token_info.get("title") or share_info.get("title") or "",
            "file_num": share_info.get("file_num", data.get("file_count", len(files))),
            "folders": folders,
            "listed_size": human_size(size) if size else "",
            "preview": [f.get("filename") or "" for f in files[:PREVIEW]],
        }
        # 分享常常只有一个顶层文件夹；share_info 里有递归统计，比首页更能说明里面有什么。
        # 字段名来自 WorkBuddy 实测（tests/fixtures/workbuddy/share-detail-valid.jsonl）。
        if isinstance(share_info.get("file_only_num"), int):
            info["total_files"] = share_info["file_only_num"]
        if isinstance(share_info.get("size"), int) and share_info["size"] > 0:
            info["total_size"] = human_size(share_info["size"])
        return "valid", info
    if result.get("action") == "runtime":
        return "runtime", {"msg": msg}
    errno = errno_of(result)
    if errno in DEAD_ERRNOS:
        return "invalid", {"msg": msg, "errno": errno}
    return "unknown", {"msg": msg, "errno": errno}


def errno_of(result):
    """从官方结果里取服务端 errno：msg 里的 errno=NNNNN，或直接透传的 code。"""
    m = _ERRNO_RE.search(str(result.get("msg") or ""))
    if m:
        return int(m.group(1))
    code = result.get("code")
    if isinstance(code, int) and code > 0:
        return code
    return None


def run_cli(cli, link, session_input, session_id, skill_updated=False, timeout=30, runner=subprocess.run):
    cmd = ["node", cli, "share-detail", "--url", link["url"], "--size", "20",
           "--session-input", session_input, "--session-id", session_id]
    if link.get("needs_passcode") and link.get("password"):
        cmd += ["--passcode", link["password"]]
    if skill_updated:
        cmd.append("--skill-updated")
    try:
        # 显式 UTF-8 + replace：Windows 中文系统默认 GBK，node 往 stderr 打的非 UTF-8 字节
        # 会让 subprocess 的读线程抛 UnicodeDecodeError（WorkBuddy 实测）。
        proc = runner(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                      timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"code": -1, "msg": "share-detail 超时", "type": "result"}
    except OSError as e:
        return {"code": -1, "msg": "无法运行 node：%s" % e, "type": "result", "action": "runtime"}
    return last_result(proc.stdout)


STATUS_TEXT = {"valid": "可用", "invalid": "已失效", "unknown": "未验证", "runtime": "CLI 不可用"}


def check(links, cli, session_input, session_id, keep=5, workers=3, skill_updated=False,
          call=run_cli, log=None):
    links = list(links)
    results = [None] * len(links)
    total = len(links)
    if log and total:
        log("正在逐条验证 {} 条链接（{} 个并发）…".format(total, max(1, workers)))
    done = [0]
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futs = {pool.submit(call, cli, l, session_input, session_id, skill_updated): i
                for i, l in enumerate(links)}
        for fut in as_completed(futs):
            i = futs[fut]
            results[i] = fut.result()
            done[0] += 1
            if log:
                log("[{}/{}] {}：{}".format(done[0], total, links[i].get("title", "")[:30],
                                          STATUS_TEXT[classify(results[i])[0]]))

    notices = []
    checked = []
    for link, res in zip(links, results):
        status, info = classify(res)
        notice = ((res or {}).get("notice") or {}).get("text") if res else None
        if notice and notice not in notices:
            notices.append(notice)
        checked.append(dict(link, check=dict(info, status=status)))

    # 官方 CLI 整体不可用（例如环境检测不通过）：不做判断，原样交回，流程照旧
    if checked and all(c["check"]["status"] == "runtime" for c in checked):
        return {"ok": True, "check_skipped": True, "reason": checked[0]["check"]["msg"],
                "shown": links[:keep], "invalid": [], "notices": notices}

    shown = [c for c in checked if c["check"]["status"] != "invalid"][:keep]
    invalid = [{"title": c["title"], "url": c["url"], "msg": c["check"]["msg"],
                "errno": c["check"].get("errno")}
               for c in checked if c["check"]["status"] == "invalid"]
    return {"ok": True, "check_skipped": False, "checked": len(checked),
            "valid_count": sum(1 for c in checked if c["check"]["status"] == "valid"),
            "shown": shown, "invalid": invalid, "notices": notices}


def main(argv=None):
    ap = argparse.ArgumentParser(description="用夸克官方 CLI 的 share-detail 预检候选链接")
    ap.add_argument("--cli", required=True, help="夸克官方 CLI 路径（find_quark_cli.py 返回的 cli）")
    ap.add_argument("--session-input", required=True, help="用户原始提问，逐字复制")
    ap.add_argument("--session-id", required=True, help="本次对话的会话 ID")
    ap.add_argument("--input", default="-", help="pansou_search.py --json 的输出文件（默认读标准输入）")
    ap.add_argument("--keep", type=int, default=5, help="最多保留几条可用链接（默认 5）")
    ap.add_argument("--workers", type=int, default=3, help="并发数（默认 3）")
    ap.add_argument("--timeout", type=float, default=30, help="每条链接的超时秒数（默认 30）")
    ap.add_argument("--quiet", action="store_true", help="不往 stderr 打进度")
    ap.add_argument("--skill-updated", action="store_true", help="官方 install.sh 返回 updated:true 时加上")
    args = ap.parse_args(argv)

    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    try:
        search = json.loads(raw)
    except ValueError:
        print(json.dumps({"ok": False, "error": "输入不是 pansou_search.py --json 的输出"}, ensure_ascii=False))
        return 1
    if not search.get("ok"):
        print(json.dumps({"ok": False, "error": search.get("error") or "搜索失败"}, ensure_ascii=False))
        return 1
    def call(cli, link, si, sid, upd):
        return run_cli(cli, link, si, sid, upd, timeout=args.timeout)

    def log(msg):
        print(msg, file=sys.stderr, flush=True)

    res = check(search.get("quark_links") or [], args.cli, args.session_input, args.session_id,
                keep=args.keep, workers=args.workers, skill_updated=args.skill_updated,
                call=call, log=None if args.quiet else log)
    res["keyword"] = search.get("keyword")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
