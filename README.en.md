<p align="center">
  <img src="assets/banner.png" alt="quark-skill" width="100%">
</p>

<p align="center">
  <b>Save cloud-drive resources to Quark Drive with one sentence.</b><br>
  Tell your AI agent "save X to my Quark Drive" — it searches, lets you pick, transfers, and verifies.
</p>

<p align="center"><a href="README.md">简体中文</a> · English</p>

<p align="center">
  <img src="assets/demo.gif" alt="Demo: search and save to Quark Drive in one sentence" width="760">
</p>

## What it does

`quark-search-save` is an [Agent Skill](https://github.com/vercel-labs/skills) that glues two existing pieces together:

1. **Search** — queries [PanSou](https://github.com/fish2018/pansou) for Quark Drive share links, deduplicates them and sorts newest first.
2. **Pick** — shows you the top 5 as a table and waits for your choice.
3. **Save** — transfers the share with the official Quark Drive skill's `saveas` command.
4. **Verify** — looks the file up with the official `search` command and tells you where it landed.

No cookie scraping, no reverse engineering, no servers to deploy.

## Install

Prerequisite: install the official Quark Drive skill (`quarkclouddrive`) and complete its `login` once.

```bash
npx skills add TTNAN/quark-skill -g -y
```

Manual install (Claude Code example) — copy the **whole** skill folder, not just `SKILL.md`:

```bash
git clone https://github.com/TTNAN/quark-skill.git
cp -r quark-skill/skills/quark-search-save ~/.claude/skills/
```

> The [Chinese README](README.md) has the full reference: a sample conversation, search script options and JSON fields, how the official skill is located, self-hosting PanSou, privacy, known limitations and FAQ.

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `PANSOU_URL` | PanSou instance | `https://s.panhunt.com` |
| `PANSOU_TOKEN` | JWT for instances with auth enabled | empty |
| `QUARK_SKILL_DIR` | Install dir of the official Quark skill (only if auto-detect fails) | auto |

```bash
python3 skills/quark-search-save/scripts/pansou_search.py --kw "linear algebra" --json
python3 skills/quark-search-save/scripts/find_quark_cli.py
```

## Behaviour

- Searches only with the words you gave; never invents links.
- Retries the **same** keyword automatically when PanSou's cache is cold.
- Never saves without your explicit pick.
- Uses Quark's default folder unless you name one.
- Stops and shows the raw error message when a transfer fails.
- If a share link is dead, suggests the next candidate and waits for your OK — never tries several on its own.

## Development

```bash
pip install pytest pyyaml && python -m pytest -q
```

See [CONTRIBUTING](CONTRIBUTING.md) (Chinese) for project rules and release steps.

## Legal

This project hosts no content. It only calls PanSou's public search API and Quark's official transfer interface. Only save content you have the right to keep.

## License

[MIT](LICENSE) © TTNAN
