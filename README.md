<p align="center">
  <img src="assets/banner.png" alt="quark-skill" width="100%">
</p>

<p align="center">
  <b>一句话，把网盘资源存进夸克。</b><br>
  在 AI 智能体的对话里说一句「帮我存到夸克」，它会去搜、让你挑、自动转存、再回查确认。
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-6D5BFF" alt="MIT"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-3F7BFF" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/依赖-仅标准库-1FC8F2" alt="no deps">
  <img src="https://img.shields.io/badge/Agent%20Skill-quark--search--save-334155" alt="skill">
  <a href="https://github.com/TTNAN/quark-skill/actions/workflows/ci.yml"><img src="https://github.com/TTNAN/quark-skill/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
</p>

<p align="center">简体中文 · <a href="README.en.md">English</a></p>

<p align="center">
  <img src="assets/demo.gif" alt="演示：一句话搜索并转存到夸克网盘" width="760">
</p>

---

## 它能做什么

| 你说 | 它做 |
| --- | --- |
| 「帮我找一下线性代数的课件，存到夸克」 | 用 PanSou 聚合搜索，只留夸克链接，去重后按日期从新到旧列前 5 条 |
| 「要第 1 个」 | 调夸克官方 Skill 的 `saveas`，整个分享一键转存 |
| （自动） | 用官方 `search` 回查，告诉你文件存在了哪个目录 |

全程不抓 cookie、不逆向接口、不部署服务，只是把两段现成能力接起来：**PanSou 搜索 + 夸克官方转存**。

## 为什么做这个

找学习资料时，常见流程是：去搜索站找链接 → 复制 → 打开夸克 → 粘贴 → 点保存 → 再去网盘里找文件放哪了。来回切五六次窗口，链接还经常是失效的。

这个 Skill 把这套流程收进智能体的一次对话里，而且坚持只用**官方或公开**的能力：

| 做法 | 要不要 cookie | 要不要部署服务 | 转存方式 | 风险 |
| --- | --- | --- | --- | --- |
| 手动搜 + 手动存 | 否 | 否 | 手点 | 费时，容易存错版本 |
| 抓 cookie 的转存脚本 | **要** | 常常要 | 逆向网页接口 | 账号凭据外泄、接口一改就坏 |
| **quark-skill** | 否 | 否 | 夸克官方 Skill `saveas` | 授权走官方 `login`，本仓库碰不到你的凭据 |

**适合**：在 Claude Code、Codex、Cursor 等智能体里工作、经常要存公开课件、开源书、教程资料的人。
**不适合**：批量囤资源、需要百度网盘 / 阿里云盘等其他网盘的场景（目前只支持夸克）。

## 快速开始

**你需要准备**

- 一个支持 Agent Skill 的智能体（Claude Code、Codex、Cursor 等）
- Python 3.10+（搜索脚本，只用标准库，不用 `pip install`）
- Node.js 16+（夸克官方 Skill 的 CLI 要用；没有的话官方安装脚本会自动装）
- 一个夸克网盘账号

**1. 装好夸克官方 Skill 并登录**

本 Skill 的转存一步依赖夸克官方的「夸克网盘 Skill」（目录名 `quarkclouddrive`）。官方介绍和最新下载地址在 [夸克网盘 Skill 官方页面](https://b.quark.cn/apps/quarkcloud_skill_info/routes/V-sc7gOBT)。

**方式一：让智能体自己装（官方推荐）**

打开官方页面，点「复制技能地址」，然后把下面这段话发给你的智能体（技能地址换成你复制到的最新地址）：

```
请安装 夸克网盘Skill,并授权账号
技能地址：https://pdds.quark.cn/download/stfile/eekkigineefiegmgo/quarkclouddrive-1.0.25.zip
```

智能体会下载、解压、运行官方安装脚本，再引导你登录授权。上面的地址是写这份 README 时的 1.0.25 版，版本更新后以官方页面为准。

**方式二：手动安装**

```bash
# 以 Claude Code 为例；Codex 换成 ~/.codex/skills，其他智能体换成它的全局 skills 目录
mkdir -p ~/.claude/skills/quarkclouddrive && cd ~/.claude/skills/quarkclouddrive
curl -L -o /tmp/quarkclouddrive.zip "https://pdds.quark.cn/download/stfile/eekkigineefiegmgo/quarkclouddrive-1.0.25.zip"
unzip -o /tmp/quarkclouddrive.zip      # 压缩包里直接是 SKILL.md、scripts/、references/
bash scripts/install.sh                # 检查并安装 Node.js 16+、安装 CLI、自检
node scripts/quark-drive.cjs --help    # 能打印帮助就说明装好了
```

官方要求装在智能体的**全局** skills 目录，不要装进某个项目目录，否则换个项目就找不到了。

**然后登录授权**

在智能体里说一句「登录夸克网盘」，按提示完成官方 Skill 的 `login`（浏览器授权）。授权由官方 Skill 管理，本仓库不经手。

装好后本 Skill 会自动找到它；装在非常规目录时，设置环境变量 `QUARK_SKILL_DIR` 指过去即可。

**2. 安装本 Skill**

```bash
npx skills add TTNAN/quark-skill -g -y
```

<details>
<summary>手动安装（以 Claude Code 为例）</summary>

```bash
git clone https://github.com/TTNAN/quark-skill.git
mkdir -p ~/.claude/skills
cp -r quark-skill/skills/quark-search-save ~/.claude/skills/
```

注意要复制**整个** `quark-search-save` 目录（`scripts/` 里有搜索和定位脚本），只拷 `SKILL.md` 用不了。

</details>

**3. 在对话里说一句**

```
帮我找一下《深入理解计算机系统》的课件，存到夸克网盘
```

想先看看官方 Skill 本身能做什么，见 [官方 Skill 演示](examples/official-skill-demo.md)。

## 一次完整的对话

下面是一次真实流程的样子（结果条目为示意）：

```
你：帮我找一下线性代数的课件，存到夸克

智能体：搜到 95 条夸克链接，按日期从新到旧列前 5 条：

  | # | 标题                                   | 日期       | 提取码 |
  |---|----------------------------------------|------------|--------|
  | 1 | 线性代数（带源码课件）                 | 2026-11-11 | 无     |
  | 2 | 机器学习的数学基础（含线性代数）       | 2026-11-11 | 无     |
  | 3 | ……                                     | ……         | ……     |

  要存哪一条？

你：第 1 个

智能体：已转存，保存在「/来自：分享/线性代数（带源码课件）」，回查确认文件已在网盘里。
```

如果第 1 条的分享已经失效，它会先把夸克返回的原始报错告诉你，再问你要不要换第 2 条，你同意了才换。

## 工作流

```
你的一句话
   │
   ▼
① 搜索   pansou_search.py --kw "关键词"      只留夸克链接，去重排序，冷启动自动重试
   │
   ▼
② 挑选   前 5 条列成表格，等你点头           没选中不转存
   │
   ▼
③ 转存   quark-drive.cjs saveas --url ...    夸克官方接口
   │
   ▼
④ 回查   quark-drive.cjs search              告诉你保存目录
```

每一步具体做了什么：

1. **搜索**：从你的话里取出资源名本身（去掉书名号、「帮我找」、版本号、年份），调 PanSou 的 `cloud_types=quark&res=merge` 接口。结果只留 `pan.quark.cn` 链接，按链接去重（重复时保留较新的、补齐提取码），按日期从新到旧排序。空结果时用**同一个关键词**按 5、10、15 秒退避重试，不换词。
2. **挑选**：最多列 5 条。你提过的版本、年份等条件只用来帮你标出最匹配的一条，最终还是你说了算。
3. **转存**：调官方 CLI 的 `saveas`。带提取码的链接自动加 `--passcode`；你没指定目录就不传目录参数，用夸克默认位置。
4. **回查**：用官方 `search` 按文件名查一遍，用返回的 `save_path` 原文告诉你存在哪。

## 配置

搜索默认用 PanSou 公共实例 `https://s.panhunt.com`，不需要 key。自部署实例时用环境变量覆盖：

| 环境变量 | 说明 | 默认值 |
| --- | --- | --- |
| `PANSOU_URL` | PanSou 实例地址 | `https://s.panhunt.com` |
| `PANSOU_TOKEN` | 实例开启认证时的 JWT | 空 |
| `QUARK_SKILL_DIR` | 夸克官方 Skill 的安装目录（找不到时才需要） | 自动查找 |

也可以单独跑搜索脚本调试：

```bash
python3 skills/quark-search-save/scripts/pansou_search.py --kw "线性代数" --limit 5
python3 skills/quark-search-save/scripts/pansou_search.py --kw "线性代数" --json
python3 skills/quark-search-save/scripts/find_quark_cli.py      # 看看官方 CLI 在哪
```

### 搜索脚本参数

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--kw` | 关键词（书名、课程名本身），必填 | — |
| `--limit` | 最多输出几条 | `5` |
| `--retries` | 结果为空时用同一关键词重试几次，`0` 表示不重试 | `3`（约 30 秒） |
| `--timeout` | 单次请求超时秒数 | `30` |
| `--url` / `--token` | 覆盖 `PANSOU_URL` / `PANSOU_TOKEN` | 见上表 |
| `--json` | 以 JSON 输出，给智能体读 | 关 |

`--json` 的输出长这样：

```json
{
  "ok": true,
  "keyword": "线性代数",
  "quark_total": 95,
  "attempts": 1,
  "quark_links": [
    {
      "title": "机器学习的数学基础（53集 高等数学 线性代数 概率论 数理统计）",
      "date": "2026-11-11",
      "url": "https://pan.quark.cn/s/5edcfe70200c",
      "password": "",
      "source": "plugin:yunso",
      "needs_passcode": false
    }
  ]
}
```

| 字段 | 含义 |
| --- | --- |
| `quark_total` | 去重后的夸克链接总数（`quark_links` 只是其中前 `--limit` 条） |
| `attempts` | 实际请求了几次（冷启动重试时大于 1） |
| `password` | 搜索源给出的提取码，没有则为空 |
| `needs_passcode` | 有提取码且链接里没带 `?pwd=` 时为 `true`，转存要加 `--passcode` |
| `source` | 结果来自 PanSou 的哪个频道或插件 |

出错时输出 `{"ok": false, "error": "..."}`，比如实例被限流返回了网页而不是 JSON。

### 官方 Skill 是怎么被找到的

`find_quark_cli.py` 按这个顺序找 `quarkclouddrive`，找到第一个就停：

1. 环境变量 `QUARK_SKILL_DIR`
2. 和本 Skill 同级的 `quarkclouddrive` 目录（两个 Skill 装在同一个 skills 目录下时最常见）
3. 当前目录和家目录下的常见位置：`.claude/skills`、`.agents/skills`、`.codex/skills`、`.cursor/skills`、`.trae/skills`、`.qoder/skills`、`.opencode/skills`、`.config/opencode/skills`、`.openclaw/skills`、`.skills`
4. 兜底：`~/.*/skills/quarkclouddrive` 和 `~/.*/*/skills/quarkclouddrive`

找不到时，`--json` 会列出所有查过的路径（`checked` 字段），方便你判断装到哪去了。

### 自部署 PanSou

公共实例 `s.panhunt.com` 是别人维护的，收录范围和稳定性都不受本项目控制。需要更稳定的搜索时，可以按 [fish2018/pansou](https://github.com/fish2018/pansou) 的说明用 Docker 自己起一个实例，再设置：

```bash
export PANSOU_URL="http://你的实例地址:端口"
export PANSOU_TOKEN="..."   # 实例开启认证时才需要
```

## 行为约定

为了让结果可预期，这个 Skill 刻意保守：

- **不乱改词**：只用你说的关键词搜，搜不到就直说，不编链接。
- **不替你做主**：没有你明确选中的那一条，就不转存。
- **不乱放文件**：你没指定目录时用夸克默认位置；指定了才传目录参数。
- **失败就停**：`saveas` 报错时原样告诉你 `msg`，不静默重试、不绕路。
- **链接失效会问你**：分享已失效时，把下一条候选推荐给你，你同意了才换，不会自动连试。
- **授权问题走官方**：遇到未授权，引导你重新走官方 Skill 的 `login`。

## 数据与隐私

- **发给 PanSou 的**：只有搜索关键词。
- **发给夸克的**：由官方 Skill 的 CLI 发出，内容是分享链接、提取码，以及官方 CLI 要求的会话参数（你的原始提问、会话 ID）。这部分行为由夸克官方 Skill 决定。
- **本仓库不读、不存**任何 cookie、token 或账号信息，也不把数据发到第三方服务器。

## 已知限制

- 只支持夸克网盘链接；百度、阿里等网盘的结果会被过滤掉。
- 搜得到什么取决于 PanSou 实例的收录。公共实例对部分冷门词（例如一些课程名）可能一直返回空，这时换个说法或自部署实例更有效。
- 一次只转存一条分享，不做批量转存。
- 只能转存到你自己的夸克网盘，转存后的文件管理（重命名、移动）请用夸克官方 Skill 或客户端。

## 支持哪些智能体

能跑夸克官方 Skill 的智能体都能用。官方页面目前列出的已支持平台是千问办公助理、Codex 和 OpenClaw；Claude Code、Cursor 等能加载 Agent Skill、能执行 `node` 的智能体，按上面的手动方式装好后一般也能用。以 [官方页面](https://b.quark.cn/apps/quarkcloud_skill_info/routes/V-sc7gOBT) 为准。

## 常见问题

<details>
<summary>提示找不到夸克官方 Skill 的 CLI？</summary>

确认官方 Skill 已安装，并先跑一次它自带的 `bash <官方 Skill 目录>/scripts/install.sh` 自检。目录以实际安装位置为准，例如 `~/.claude/skills/quarkclouddrive`。

</details>

<details>
<summary>明明有资源却说搜不到？</summary>

PanSou 对新关键词是边搜边聚合的，第一次请求常常返回空。搜索脚本已经会用同一关键词自动重试 3 次（共约 30 秒）。仍然没有时，多半是关键词太长：只说书名、课程名本身，别带版本号、年份、出版社。

</details>

<details>
<summary>链接带提取码怎么办？</summary>

链接里已有 `?pwd=xxxx` 时直接转存；提取码单独给出时，Skill 会自动带上 `--passcode`。

</details>

<details>
<summary>想存到指定文件夹？</summary>

直接在话里说，比如「存到夸克的 /学习/数学 里」。目录已存在时直接传路径；不存在时，Skill 会先用官方 `search` 找目录。你没说目录时，它不会自作主张传目录参数。

</details>

<details>
<summary>提示未授权、token 过期？</summary>

这是夸克官方 Skill 的登录状态问题。在智能体里重新走一次官方 Skill 的 `login` 授权，再让它转存即可。本 Skill 不会绕过授权重试。

</details>

<details>
<summary>能一次存好几条吗？</summary>

目前不行，一次只转存你选中的那一条。这是刻意的：每次转存都要你点头，避免存进一堆用不上的东西。

</details>

## 开发

```
quark-skill/
├── skills/quark-search-save/
│   ├── SKILL.md                 智能体读的说明书（触发词、工作流、失败处理）
│   └── scripts/
│       ├── pansou_search.py     PanSou 搜索、过滤、去重、排序、冷启动重试
│       └── find_quark_cli.py    定位夸克官方 Skill 的 CLI
├── tests/                       离线单元测试（不联网）
├── examples/                    官方 Skill 能力演示
├── tools/make_demo_gif.py       生成 README 演示动图
└── assets/                      logo、banner、演示动图
```

```bash
pip install pytest pyyaml
python -m pytest -q                 # 单元测试，不联网
python tools/make_demo_gif.py       # 重新生成演示动图（需要 Pillow 和中文字体）
```

改动记录见 [CHANGELOG](CHANGELOG.md)，参与贡献见 [CONTRIBUTING](CONTRIBUTING.md)。

## 合规声明

本项目不提供、不存储、不托管任何资源，只调用 PanSou 公开搜索 API 与夸克官方转存接口。请只转存你有权保存的内容（公开课程、开源资料、自己的分享等），因使用本项目产生的版权问题由使用者自行负责。

## 协议

[MIT](LICENSE) © TTNAN
