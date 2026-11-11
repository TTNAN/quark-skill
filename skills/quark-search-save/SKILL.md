---
name: quark-search-save
description: >-
  对话里找网盘资源并一句话转存到夸克网盘。先调 PanSou 聚合搜索找夸克分享链接，再调夸克官方 Skill 的 saveas 全自动转存，全程不抓 cookie、不手动点、不部署新应用。触发词：找资源、搜课件、找一下 XX、帮我存到夸克、帮我把 XX 存到夸克网盘、把 XX 保存到夸克、quark search / save。Find cloud-drive resources in chat and save them to Quark Drive: search PanSou for Quark share links, then transfer them with the official Quark Drive skill's saveas. Use when the user asks to find a resource and save it to Quark Drive.
license: MIT
metadata:
  version: "1.2.0"
  repository: https://github.com/TTNAN/quark-skill
---

# Quark Search & Save（夸克搜索转存）

用户在对话里说一句“帮我把 XX 存到夸克网盘”，你去搜、让他挑版本、用夸克官方 Skill 直接转存进他的夸克网盘，存完回查确认。

下文 `<本 Skill 目录>` 指这个 SKILL.md 所在的目录；脚本都在它的 `scripts/` 下，不要去仓库根目录或当前工作目录找。

## 前置条件（缺一不可，缺了先停下来告诉用户）

1. **夸克官方 Skill（`quarkclouddrive`）已安装并已登录授权。** 没装的话由你帮用户装，不要让他自己去折腾。
   先定位它的 CLI，不要凭经验猜路径：

   ```bash
   python3 <本 Skill 目录>/scripts/find_quark_cli.py --json
   ```

   - `ok: true`：记下 `cli`（即 `<quark-cli>`）和 `skill_dir`（即 `<quark-skill-dir>`），本次对话复用。
   - `ok: false`：告诉用户“转存要用夸克官方的网盘 Skill，你还没装”，**问他要不要现在从夸克官方地址帮他装**。他同意后运行：

     ```bash
     python3 <本 Skill 目录>/scripts/install_quark_skill.py --json
     ```

     脚本会向夸克官方接口查最新版下载地址（只接受 `quark.cn` 的地址），下载官方 zip，解压到本 Skill 的同级目录 `quarkclouddrive`，再运行官方的 `scripts/install.sh`（检查并安装 Node.js 16+、安装 CLI、自检）。本仓库不附带任何夸克的文件。
     - `ok: true`：用返回的 `cli`、`skill_dir` 作为 `<quark-cli>`、`<quark-skill-dir>`。然后**先读一遍 `<quark-skill-dir>/SKILL.md` 和 `<quark-skill-dir>/references/auth.md`**（官方 Skill 是刚装的，你还没加载它的规则），按官方规则输出首次安装的欢迎语，并用 `node <quark-cli> login` 引导用户登录授权（浏览器打不开时按官方流程让用户把授权码贴进对话，再 `login --token`）。登录成功后接着做用户原来的请求，不要让他再说一遍。
     - `ok: false`：把 `error` 原文告诉用户，附上 `official_page` 让他按官方页面手动安装，然后停下。
     - 用户想装到别的位置（例如 Codex 的 `~/.codex/skills`）时，加 `--dir <目录>/quarkclouddrive`。官方要求装在智能体的**全局** skills 目录，不要装进项目目录。
     - 用户不同意安装：停下，告诉他转存这一步需要官方 Skill；也可以设置环境变量 `QUARK_SKILL_DIR` 指向已有的安装目录。
2. **搜索用 PanSou。** 默认公共实例 `https://s.panhunt.com`，不用 key；只有用户自部署时才用 `PANSOU_URL` / `PANSOU_TOKEN`。

## 工作流（4 步，缺一步都不算完成）

### 第 1 步：搜索

```bash
python3 <本 Skill 目录>/scripts/pansou_search.py --kw "<关键词>" --limit 5 --json
```

**关键词怎么取：** 从用户原话里取出资源的核心名称本身——片名、书名、课程名。

- 去掉书名号《》、引号，去掉“帮我找”“存到夸克”这类指令词。
- 去掉版本号、年份、出版社、清晰度等修饰词（例如“第五版”“2024”“4K”），这些放到第 2 步挑选时再用。
- 不要加用户没说过的词，不要换同义词、不要翻译。

**结果怎么读：**

- 脚本已经只保留夸克链接、按 URL 去重、按日期从新到旧排好序。
- 脚本在结果为空时会**自动用同一关键词退避重试**（PanSou 对新关键词是异步聚合的，第一次常返回 0）。你不需要、也不允许再自己换词重搜。
- `ok: false`：把 `error` 原文告诉用户，停下。
- `quark_links` 为空：直接告诉用户搜不到。**不许换词重搜、不许编链接。** 可以建议他换个说法后再让你搜。

### 第 2 步：挑一个，让用户确认

把结果做成表格给用户看：序号、标题、日期、链接，最多 5 条。

- 没有用户明确选中的那一条就不要转存。用户说“就第一个”“要带课件的那个”时按他说的来。
- 用户提过的版本、年份、清晰度等修饰条件，用来在结果里帮他标出最匹配的一条，推荐后等他点头。

### 第 3 步：转存（全自动）

用户确认后，用官方 Skill 的 `saveas` 转存整个分享链接：

```bash
node <quark-cli> saveas --url "<分享链接>" --session-input "<用户原始提问，逐字复制>" --session-id "<unix 秒>-<6 位随机字母数字>"
```

- `--session-input` 和 `--session-id` 是官方 CLI 所有子命令的公共参数，**每次调用都必传**。
  `--session-input` 逐字复制用户原始提问，禁止改写或摘要；
  `--session-id` 在本次对话第一次调 CLI 时生成（如 `1784035443-a1b2c3`），同一对话后续复用。
- 每次用户输入后，第一次调官方 CLI 前先跑一次官方自检：`bash <quark-skill-dir>/scripts/install.sh`。
  返回 `success: true` 且 `updated: true` 时，本次业务命令额外带 `--skill-updated`，否则不带。
  （`install.sh` 是官方 Skill 的脚本，本仓库没有这个文件。）
- 提取码：结果里 `needs_passcode: true` 时加 `--passcode "<password>"`；URL 里已有 `?pwd=` 时不用传。
- 用户没有明确指定目录时，**严禁**传 `--to-pdir-path`、`--to-pdir-fid` 或 `"0"`，必须省略，让 CLI 用默认位置。
  用户明确说了目录才传 `--to-pdir-path "<目录路径>"`；目录不存在就先用官方 `search` 定位目录 fid 再传 `--to-pdir-fid`。

### 第 4 步：回查确认

转存成功（`code: 0`）后，用官方 Skill 的 `search` 按文件名查一遍，确认文件真的进了网盘，再告诉用户保存位置（用成功结果里 `data.save_path` 的原文）。

## 失败处理

- `saveas` 返回 `code != 0`：把 `msg` 原文告诉用户，停下来，不许静默重试、不许换办法绕过去。
- **例外：分享链接本身不可用**（`msg` 表明分享已失效、已取消、不存在、被封禁或提取码错误）：
  1. 先把 `msg` 原文告诉用户，说明是这条分享的问题，不是他的账号问题。
  2. 如果第 1 步的表格里还有其他候选，把**下一条**（标题、日期、链接）推荐给他，问他要不要换这条。
  3. 等用户明确同意后，再用新链接走第 3 步；用户不同意就停下。
  - 一次只推荐一条，不许自动连续尝试多条，不许重新搜索、不许换关键词。
  - 候选用完了就直说“这几条都失效了”，可以建议他换个说法后再让你搜。
- 报错是未授权 / 认证 / token 问题：先展示 `msg`，再引导用户重新走官方 Skill 的 `login`，不要直接重跑 `saveas`。
- 转存同一链接的“更新内容”才用 `saveas-update`；首次转存一律用 `saveas`。
- 官方 CLI 每次返回的非空 `notice.text`，在业务结果之后另起一段原样展示，不得省略、概括或改写。

## 明确不做的事

- 不抓浏览器 cookie、不逆向夸克网页接口、不绕过官方 Skill 的环境检测。
- 不附带、不修改夸克官方 Skill 的任何文件；只在用户同意后，从夸克官方地址下载安装官方 Skill。
- 不部署应用、不跑 Docker、不开常驻服务。本 Skill 只是两段现成能力的拼接：PanSou 搜索 + 夸克官方转存。
- 不提供、不托管任何资源。请只转存用户有权保存的内容。
