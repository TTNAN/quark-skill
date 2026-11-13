<p align="center">
  <img src="assets/banner.png" alt="quark-skill" width="100%">
</p>

<p align="center">
  <b>Save cloud-drive resources to Quark Drive with one sentence.</b><br>
  Tell your AI agent "save X to my Quark Drive" — it searches, checks the links, lets you pick, transfers, and verifies.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-6D5BFF" alt="MIT"></a>
  <img src="https://img.shields.io/badge/python-3.9%2B-3F7BFF" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/deps-stdlib%20only-1FC8F2" alt="no deps">
  <a href="https://github.com/TTNAN/quark-skill/actions/workflows/ci.yml"><img src="https://github.com/TTNAN/quark-skill/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
</p>

<p align="center"><a href="README.md">简体中文</a> · English</p>

<p align="center">
  <img src="assets/demo.gif" alt="Demo: search and save to Quark Drive in one sentence" width="760">
</p>

## What it does

`quark-search-save` is an [Agent Skill](https://github.com/vercel-labs/skills) that glues two existing pieces together — [PanSou](https://github.com/fish2018/pansou) search and the **official** Quark Drive skill (`quarkclouddrive`):

| You say | It does |
| --- | --- |
| (first use) | Notices the official Quark skill is missing, asks you, then installs it from Quark's own servers and walks you through login |
| "Find linear algebra slides and save them to Quark" | Searches PanSou (tries the next instance in `PANSOU_URL` when one has nothing), keeps only Quark links, dedupes, newest first |
| (automatic) | Checks every candidate with the official `share-detail`, **drops dead links**, shows the top 5 with file count and a content preview |
| "Number 1, only the PDFs" | Finds the PDFs inside the share with the official `share-search` and saves only the files you pick |
| "Number 2" | Saves the whole share with the official `saveas` |
| (automatic) | Looks the files up with the official `search` and tells you which folder they landed in |
| "Has this share been updated?" | Lists new files with `get-share-update-files`; after your OK, `saveas-update` saves only what's new |

No cookie scraping, no reverse engineering, no servers to deploy, and this repo ships none of Quark's files.

## Install

**You only install this one skill:**

```bash
npx skills add TTNAN/quark-skill -g -y
```

You need an Agent-Skill-capable agent (Claude Code, Codex, Cursor, …), Python 3.9+ (stdlib only; the python3 that ships with macOS works) and a Quark Drive account. Node.js is installed by the official setup script if missing.

**First use** adds two one-time steps:

1. The agent finds the official Quark skill missing and asks whether to install it. Say yes: it fetches the latest package URL from Quark's official endpoint, downloads it from `pdds.quark.cn`, installs it next to this skill and runs the official `install.sh` (checks/installs Node.js 16+, installs the CLI, self-test).
2. It opens Quark's browser authorization page. Log in and confirm (if the browser doesn't open, paste the code shown on the page into the chat).

Then it carries on with your original request.

<details>
<summary>Install the official Quark skill yourself</summary>

Get the latest link from the [official page](https://b.quark.cn/apps/quarkcloud_skill_info/routes/V-sc7gOBT) and either tell your agent:

```
请安装 夸克网盘Skill,并授权账号
技能地址：<the zip link copied from the official page>
```

or install it by hand into your agent's **global** skills directory:

```bash
mkdir -p ~/.claude/skills/quarkclouddrive && cd ~/.claude/skills/quarkclouddrive
curl -L -o /tmp/quarkclouddrive.zip "https://pdds.quark.cn/download/stfile/eekkigineefiegmgo/quarkclouddrive-1.0.25.zip"
unzip -o /tmp/quarkclouddrive.zip && bash scripts/install.sh   # needs/installs Node.js 16+
```

Or let this repo's helper do the same thing: `python3 ~/.claude/skills/quark-search-save/scripts/install_quark_skill.py --json`.

</details>

<details>
<summary>Manual install of this skill</summary>

Copy the **whole** skill folder, not just `SKILL.md`:

```bash
git clone https://github.com/TTNAN/quark-skill.git
cp -r quark-skill/skills/quark-search-save ~/.claude/skills/
```

</details>

## Workflow

```
⓪ prepare   find_quark_cli.py → install_quark_skill.py (with your consent)
① search    pansou_search.py       Quark links only, deduped, newest first; cold-cache retry; multi-instance fallback
② check     check_links.py         official share-detail; dead links dropped, file count + preview added
③ pick      top 5 as a table       nothing is saved without your explicit choice
④ files     share-search / share-detail   (optional) pick only some files inside the share
⑤ save      saveas [--fid-list]    official Quark transfer
⑥ verify    search                 tells you where the files landed
later:      get-share-update-files → saveas-update   save only what's new
```

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `PANSOU_URL` | PanSou instance(s); comma-separated, the next one is tried when one errors or returns nothing | `https://so.252035.xyz` (`s.panhunt.com` requires an auth token since Nov 2026) |
| `PANSOU_TOKEN` | JWT for instances with auth enabled | empty |
| `QUARK_SKILL_DIR` | Install dir of the official Quark skill (only if auto-detect fails; when set, it is the only place checked) | auto: every copy found is run with `--help`, the highest working version wins |

```bash
python3 skills/quark-search-save/scripts/pansou_search.py --kw "linear algebra" --limit 10 --json > /tmp/qs.json
python3 skills/quark-search-save/scripts/check_links.py --cli <official CLI path> \
    --session-input "<your original request>" --session-id "<session id>" --input /tmp/qs.json --keep 5
python3 skills/quark-search-save/scripts/find_quark_cli.py --json
```

`check_links.py` must run inside an agent (the official CLI checks its environment). When the CLI refuses, it returns `check_skipped: true` and the flow continues without the check.

For self-hosting PanSou, see [fish2018/pansou](https://github.com/fish2018/pansou).

## Behaviour

- Searches only with the words you gave; never invents links or rewrites your query.
- Retries the **same** keyword when PanSou's cache is cold, then tries the next instance if you configured more than one.
- Asks before installing anything; installs only from Quark's official servers.
- Never saves without your explicit pick; uses Quark's default folder unless you name one.
- Stops and shows the raw error message when a transfer fails.
- If a link dies at transfer time, suggests the next candidate and waits for your OK — never tries several on its own.

## Privacy

- PanSou receives only the search keyword.
- Quark receives share links, passcodes and the session parameters the official CLI requires — sent by the official CLI itself.
- On first install, `open-api-drive.quark.cn` and `pdds.quark.cn` are contacted; the official script may install Node.js from NodeSource.
- This repo never reads or stores cookies, tokens or account data.

## Limitations

- Quark Drive only; other drives are filtered out.
- Results depend on PanSou's coverage; some niche terms return nothing on the public instance.
- One share per transfer (you can save just some of its files).
- The pre-check tells you a share opens *now*; it can still be withdrawn before you save it.
- Update tracking only works for shares you saved with `saveas`.

## Supported agents

Any agent that can run the official Quark skill. The official page currently lists Qwen Office Assistant, WorkBuddy, Codex and OpenClaw; Claude Code, Cursor and other agents that load Agent Skills and can run `node` usually work too.

**Verified end to end** with official skill **1.0.25** in WorkBuddy (Windows) on 2026-11-12: install, search, pre-check, list files, save selected files, verify, check for updates. Raw official outputs live in `tests/fixtures/workbuddy/`.

## Development

```bash
pip install pytest pyyaml && python -m pytest -q
```

See [CONTRIBUTING](CONTRIBUTING.md) (Chinese) for project rules and release steps, and [CHANGELOG](CHANGELOG.md) for history.

## Legal

This project hosts no content. It only calls PanSou's public search API and Quark's official skill. Only save content you have the right to keep.

## License

[MIT](LICENSE) © TTNAN
