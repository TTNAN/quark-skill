<p align="center">
  <img src="assets/banner.png" alt="quark-skill" width="100%">
</p>

<p align="center">
  <b>一句话，把网盘资源存进夸克。</b><br>
  在 AI 智能体的对话里说一句「帮我存到夸克」，它会去搜、让你挑、自动转存、再回查确认。
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-6D5BFF" alt="MIT"></a>
  <img src="https://img.shields.io/badge/python-3.8%2B-3F7BFF" alt="Python 3.8+">
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
| （第一次用时） | 发现没装夸克官方 Skill，问你一句，同意后从夸克官方地址自动装好并引导登录 |
| 「帮我找一下线性代数的课件，存到夸克」 | 用 PanSou 聚合搜索（主实例没结果自动换备用），只留夸克链接，去重排序 |
| （自动） | 用官方 `share-detail` 逐条验链接，**失效的直接剔掉**，列出能存的前 5 条，附文件数和内容预览 |
| 「要第 1 个，只要 PDF」 | 用官方 `share-search` 在分享里找出 PDF，你挑好后只转存这几个文件 |
| 「要第 2 个」 | 调官方 `saveas`，整个分享一键转存 |
| （自动） | 用官方 `search` 回查，告诉你文件存在了哪个目录 |
| 「这个分享有更新吗？」 | 用官方 `get-share-update-files` 查新增内容，你同意后 `saveas-update` 只补新增的 |

全程不抓 cookie、不逆向接口、不部署服务，只是把两段现成能力接起来：**PanSou 搜索 + 夸克官方转存**。

## 为什么做这个

找学习资料时，常见流程是：去搜索站找链接 → 复制 → 打开夸克 → 粘贴 → 点保存 → 再去网盘里找文件放哪了。来回切五六次窗口，链接还经常是失效的。

这个 Skill 把这套流程收进智能体的一次对话里，而且坚持只用**官方或公开**的能力：

| 做法 | 要不要 cookie | 要不要部署服务 | 转存方式 | 风险 |
| --- | --- | --- | --- | --- |
| 手动搜 + 手动存 | 否 | 否 | 手点 | 费时，容易存错版本 |
| 抓 cookie 的转存脚本 | **要** | 常常要 | 逆向网页接口 | 账号凭据外泄、接口一改就坏 |
| **quark-skill** | 否 | 否（只装一个 Skill） | 夸克官方 Skill `saveas` | 授权走官方 `login`，本仓库碰不到你的凭据 |

**适合**：在 Claude Code、Codex、Cursor 等智能体里工作、经常要存公开课件、开源书、教程资料的人。
**不适合**：批量囤资源、需要百度网盘 / 阿里云盘等其他网盘的场景（目前只支持夸克）。

## 快速开始

**你只需要装这一个 Skill。** 转存要用的夸克官方网盘 Skill，第一次用时会自动帮你装好。

**你需要准备**

- 一个支持 Agent Skill 的智能体（Claude Code、Codex、Cursor 等）
- Python 3.8+（脚本只用标准库，不用 `pip install`）
- 一个夸克网盘账号

Node.js 不用提前装：官方安装脚本会检查，缺了自动装 16+。

**1. 安装**

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

注意要复制**整个** `quark-search-save` 目录（`scripts/` 里有搜索、定位和安装脚本），只拷 `SKILL.md` 用不了。

</details>

**2. 在对话里说一句**

```
帮我找一下《深入理解计算机系统》的课件，存到夸克网盘
```

**第一次用时**会多两步，之后就不用了：

1. 智能体发现你还没装夸克官方 Skill，问你要不要装。你说「装」，它就从夸克官方地址下载最新版，装到同一个 skills 目录下，并运行官方安装脚本。
2. 它弹出夸克的浏览器授权页，你登录确认即可（浏览器打不开时，把页面上的授权码贴给它）。

授权完它会接着搜你刚才要的东西，不用再说一遍。

<details>
<summary>已经装过官方 Skill，或者想自己装</summary>

已经装好的话什么都不用做，本 Skill 会自动找到它（查找顺序见下文）。

想自己装的话，官方介绍和最新下载地址在 [夸克网盘 Skill 官方页面](https://b.quark.cn/apps/quarkcloud_skill_info/routes/V-sc7gOBT)，两种方式任选：

**让智能体装（官方推荐）**：在官方页面点「复制技能地址」，把下面这段话发给智能体（地址换成你复制到的最新地址）：

```
请安装 夸克网盘Skill,并授权账号
技能地址：https://pdds.quark.cn/download/stfile/eekkigineefiegmgo/quarkclouddrive-1.0.25.zip
```

**手动装**：

```bash
# 以 Claude Code 为例；Codex 换成 ~/.codex/skills，其他智能体换成它的全局 skills 目录
mkdir -p ~/.claude/skills/quarkclouddrive && cd ~/.claude/skills/quarkclouddrive
curl -L -o /tmp/quarkclouddrive.zip "https://pdds.quark.cn/download/stfile/eekkigineefiegmgo/quarkclouddrive-1.0.25.zip"
unzip -o /tmp/quarkclouddrive.zip      # 压缩包里直接是 SKILL.md、scripts/、references/
bash scripts/install.sh                # 检查并安装 Node.js 16+、安装 CLI、自检
node scripts/quark-drive.cjs --help    # 能打印帮助就说明装好了
```

上面的地址是写这份 README 时的 1.0.25 版，以官方页面为准。官方要求装在智能体的**全局** skills 目录，不要装进某个项目目录。装好后在智能体里说「登录夸克网盘」完成授权。

</details>

想先看看官方 Skill 本身能做什么，见 [官方 Skill 演示](examples/official-skill-demo.md)。

## 一次完整的对话

下面是一次真实流程的样子（结果条目为示意）：

```
你：帮我找一下线性代数的课件，存到夸克

智能体：搜到 95 条夸克链接，逐条验过，另有 3 条已失效已略过。能存的前 5 条：

  | # | 标题                             | 日期       | 文件数 | 内容预览                     |
  |---|----------------------------------|------------|--------|------------------------------|
  | 1 | 线性代数（带源码课件）           | 2026-11-11 | 24     | 第1章.pdf、第2章.pdf、习题   |
  | 2 | 机器学习的数学基础（含线性代数） | 2026-11-11 | 53     | 01 导论.mp4、02 矩阵.mp4     |
  | 3 | ……                               | ……         | ……     | ……                           |

  要存哪一条？

你：第 1 个，只要第 3 章

智能体：分享里和「第3章」相关的有 2 个文件：

  | 文件名            | 大小   | 类型 |
  |-------------------|--------|------|
  | 第3章 行列式.pdf  | 2.1 MB | 文档 |
  | 第3章 习题.pdf    | 0.8 MB | 文档 |

  两个都存吗？

你：都存

智能体：已转存，保存在「/来自：分享/线性代数（带源码课件）」，回查确认文件已在网盘里。
        这个分享以后有更新的话，跟我说「看看有没有更新」就能只补新增的。
```

第一次用时，在列结果之前会先问你要不要装夸克官方 Skill，装好、授权后再继续。

预检之后链接仍可能在转存那一刻失效。这时它会先把夸克返回的原始报错告诉你，再问你要不要换下一条，你同意了才换。

## 工作流

```
你的一句话
   │
   ▼
⓪ 准备   find_quark_cli.py                   找官方 Skill；没有就问你，同意后 install_quark_skill.py 从官方地址装
   │
   ▼
① 搜索   pansou_search.py --kw "关键词"      只留夸克链接，去重排序；冷启动自动重试，没结果换备用实例
   │
   ▼
② 预检   check_links.py → share-detail       失效的剔掉，补上文件数和内容预览
   │
   ▼
③ 挑选   前 5 条列成表格，等你点头           没选中不转存
   │
   ▼
④ 选文件（可选）share-search / share-detail  只要一部分时，挑出要的文件
   │
   ▼
⑤ 转存   saveas [--fid-list ...]             夸克官方接口
   │
   ▼
⑥ 回查   search                              告诉你保存目录

之后：get-share-update-files → saveas-update  分享有更新时只补新增的
```

每一步具体做了什么：

1. **搜索**：从你的话里取出资源名本身（去掉书名号、「帮我找」、版本号、年份），调 PanSou 的 `cloud_types=quark&res=merge` 接口。结果只留 `pan.quark.cn` 链接，按链接去重（重复时保留较新的、补齐提取码），按日期从新到旧排序。空结果时用**同一个关键词**按 5、10、15 秒退避重试；主实例还是没结果或出错，就换备用实例再试一次。
2. **预检**：对前 10 条候选逐个调官方 `share-detail`（客态模式，不需要登录），把已失效、已取消、不存在、提取码错误的剔掉，留下最多 5 条，并带上分享标题、文件数和前几个文件名。官方 CLI 当前不可用时跳过这一步，流程照旧。
3. **挑选**：表格里有文件数和内容预览，你不用点开链接也知道里面是什么。你提过的版本、年份等条件只用来帮你标出最匹配的一条，最终还是你说了算。
4. **选文件**（只在你提出时）：「只要第 3 章」「只要 PDF」时用 `share-search` 在分享里搜；想先看看时用 `share-detail` 浏览目录。挑好的文件记下 `fid`。
5. **转存**：调官方 `saveas`，整个分享或只传 `--fid-list`。带提取码的链接自动加 `--passcode`；你没指定目录就不传目录参数，用夸克默认位置。
6. **回查**：用官方 `search` 按文件名查一遍，用返回的 `save_path` 原文告诉你存在哪。

**追更**：连载课程、每周更新的资料，存过一次之后说「看看有没有更新」，它用 `get-share-update-files` 列出新增文件，你同意后用 `saveas-update` 只补新增的，存进上次的目录。智能体支持定时任务的话，还可以让它每天固定时间帮你查。

## 配置

搜索默认依次用两个 PanSou 公共实例：`https://s.panhunt.com`，没结果或出错时换 `https://so.252035.xyz`（PanSou 作者的演示站），都不需要 key。自部署实例时用环境变量覆盖：

| 环境变量 | 说明 | 默认值 |
| --- | --- | --- |
| `PANSOU_URL` | PanSou 实例地址，逗号分隔可写多个，按顺序尝试 | `https://s.panhunt.com,https://so.252035.xyz` |
| `PANSOU_TOKEN` | 实例开启认证时的 JWT | 空 |
| `QUARK_SKILL_DIR` | 夸克官方 Skill 的安装目录（找不到时才需要） | 自动查找 |

也可以单独跑搜索脚本调试：

```bash
python3 skills/quark-search-save/scripts/pansou_search.py --kw "线性代数" --limit 5
python3 skills/quark-search-save/scripts/pansou_search.py --kw "线性代数" --json
python3 skills/quark-search-save/scripts/find_quark_cli.py      # 看看官方 CLI 在哪
```

预检脚本要在智能体里跑（官方 CLI 会检测运行环境），用法见下文「预检脚本」。

### 搜索脚本参数

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--kw` | 关键词（书名、课程名本身），必填 | — |
| `--limit` | 最多输出几条 | `5` |
| `--retries` | 结果为空时用同一关键词重试几次，`0` 表示不重试 | `3`（约 30 秒） |
| `--timeout` | 单次请求超时秒数 | `30` |
| `--url` / `--token` | 覆盖 `PANSOU_URL` / `PANSOU_TOKEN`；`--url` 也可以逗号分隔写多个 | 见上表 |
| `--json` | 以 JSON 输出，给智能体读 | 关 |

`--json` 的输出长这样：

```json
{
  "ok": true,
  "keyword": "线性代数",
  "quark_total": 95,
  "attempts": 1,
  "instance": "https://s.panhunt.com",
  "instance_errors": [],
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
| `attempts` | 所有实例加起来实际请求了几次（冷启动重试时大于 1） |
| `instance` | 结果来自哪个 PanSou 实例 |
| `instance_errors` | 请求失败的实例和原因（换到备用实例时才会有） |
| `password` | 搜索源给出的提取码，没有则为空 |
| `needs_passcode` | 有提取码且链接里没带 `?pwd=` 时为 `true`，转存要加 `--passcode` |
| `source` | 结果来自 PanSou 的哪个频道或插件 |

所有实例都请求失败时输出 `{"ok": false, "error": "..."}`，比如实例被限流返回了网页而不是 JSON。

### 预检脚本

`check_links.py` 读搜索结果，对每条链接调官方 `share-detail`，剔掉失效的：

```bash
python3 skills/quark-search-save/scripts/pansou_search.py --kw "线性代数" --limit 10 --json > /tmp/qs.json
python3 skills/quark-search-save/scripts/check_links.py --cli <官方 CLI 路径> \
    --session-input "<你的原话>" --session-id "<会话 ID>" --input /tmp/qs.json --keep 5
```

| 输出字段 | 含义 |
| --- | --- |
| `shown` | 要给你看的候选（最多 `--keep` 条，顺序不变），每条多一个 `check` |
| `check.status` | `valid` 验过能用；`unknown` 没验出来（原因在 `check.msg`），照样可选 |
| `check.file_num` / `preview` / `listed_size` | 分享里的文件数、前 3 个文件名、首页文件的总大小 |
| `invalid` | 被剔掉的条目和夸克返回的原因 |
| `check_skipped` | 官方 CLI 当前不可用时为 `true`，原样返回候选，流程照旧 |
| `notices` | 官方 CLI 返回的提示，需要原样展示 |

它只调用官方 CLI，不直接请求任何夸克接口；默认 3 个并发。

### 官方 Skill 是怎么被找到的

`find_quark_cli.py` 按这个顺序找 `quarkclouddrive`，找到第一个就停：

1. 环境变量 `QUARK_SKILL_DIR`
2. 和本 Skill 同级的 `quarkclouddrive` 目录（两个 Skill 装在同一个 skills 目录下时最常见）
3. 当前目录和家目录下的常见位置：`.claude/skills`、`.agents/skills`、`.codex/skills`、`.cursor/skills`、`.trae/skills`、`.qoder/skills`、`.opencode/skills`、`.config/opencode/skills`、`.openclaw/skills`、`.skills`
4. 兜底：`~/.*/skills/quarkclouddrive` 和 `~/.*/*/skills/quarkclouddrive`

找不到时，`--json` 会列出所有查过的路径（`checked` 字段），方便你判断装到哪去了。

### 找不到时怎么自动安装

`install_quark_skill.py` 只是替你执行官方安装步骤，本仓库不附带任何夸克的文件：

1. 请求夸克官方接口 `open-api-drive.quark.cn/agent/v1/skill_config` 拿最新版本和下载地址（只接受 `quark.cn` 的 https 地址；接口不可用时用官方页面公布的地址兜底）
2. 下载官方 zip，校验里面有 `SKILL.md` 和 `scripts/quark-drive.cjs`，拒绝路径越界的包
3. 先解压到临时目录，再整体移到本 Skill 的同级目录 `quarkclouddrive`，失败不留半成品；目标目录已有别的东西时不覆盖
4. 运行官方 `scripts/install.sh`（检查并安装 Node.js 16+、安装 CLI、自检）

```bash
python3 skills/quark-search-save/scripts/install_quark_skill.py --json                     # 装到同级目录
python3 skills/quark-search-save/scripts/install_quark_skill.py --dir ~/.codex/skills/quarkclouddrive --json
python3 skills/quark-search-save/scripts/install_quark_skill.py --no-setup                 # 只下载解压，不跑官方脚本
```

已经装好时它什么都不做，直接返回 `already_installed`。智能体只会在你同意后运行它。

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
- **装东西先问你**：官方 Skill 没装时，先问你，同意了才从夸克官方地址安装。
- **不乱放文件**：你没指定目录时用夸克默认位置；指定了才传目录参数。
- **失败就停**：`saveas` 报错时原样告诉你 `msg`，不静默重试、不绕路。
- **链接失效会问你**：分享已失效时，把下一条候选推荐给你，你同意了才换，不会自动连试。
- **授权问题走官方**：遇到未授权，引导你重新走官方 Skill 的 `login`。

## 数据与隐私

- **发给 PanSou 的**：只有搜索关键词（主实例没结果时，备用实例也会收到同一个关键词）。
- **发给夸克的**：由官方 Skill 的 CLI 发出，内容是分享链接、提取码（预检、选文件、转存、查更新时），以及官方 CLI 要求的会话参数（你的原始提问、会话 ID）。这部分行为由夸克官方 Skill 决定。
- **安装官方 Skill 时**（只在第一次、你同意后）：访问夸克官方的 `open-api-drive.quark.cn` 和 `pdds.quark.cn` 下载安装包；官方安装脚本缺 Node.js 时会从 NodeSource 安装。
- **本仓库不读、不存**任何 cookie、token 或账号信息，也不把数据发到第三方服务器。

## 已知限制

- 只支持夸克网盘链接；百度、阿里等网盘的结果会被过滤掉。
- 搜得到什么取决于 PanSou 实例的收录。两个公共实例对部分冷门词（例如一些课程名）都可能返回空，这时换个说法或自部署实例更有效。
- 一次只转存一条分享（可以只存其中几个文件），不做多条分享的批量转存。
- 预检只能看出「这条分享现在能不能打开」，转存那一刻仍可能因为对方取消分享而失败。
- 追更依赖官方的转存记录，只对你用 `saveas` 存过的分享有效。
- 只能转存到你自己的夸克网盘，转存后的文件管理（重命名、移动）请用夸克官方 Skill 或客户端。

## 支持哪些智能体

能跑夸克官方 Skill 的智能体都能用。官方页面目前列出的已支持平台是千问办公助理、Codex 和 OpenClaw；Claude Code、Cursor 等能加载 Agent Skill、能执行 `node` 的智能体，按上面的手动方式装好后一般也能用。以 [官方页面](https://b.quark.cn/apps/quarkcloud_skill_info/routes/V-sc7gOBT) 为准。

## 常见问题

<details>
<summary>提示找不到夸克官方 Skill？</summary>

正常情况下智能体会直接问你要不要自动安装。如果你已经装在别的位置，设置环境变量 `QUARK_SKILL_DIR` 指过去；如果自动安装失败（比如网络连不上夸克），按「已经装过官方 Skill，或者想自己装」里的方式手动装，再跑一次官方的 `bash <官方 Skill 目录>/scripts/install.sh` 自检。

</details>

<details>
<summary>明明有资源却说搜不到？</summary>

PanSou 对新关键词是边搜边聚合的，第一次请求常常返回空。搜索脚本已经会用同一关键词自动重试 3 次（共约 30 秒），还没有就换备用实例再试。仍然没有时，多半是关键词太长：只说书名、课程名本身，别带版本号、年份、出版社。

</details>

<details>
<summary>链接带提取码怎么办？</summary>

链接里已有 `?pwd=xxxx` 时直接转存；提取码单独给出时，Skill 会自动带上 `--passcode`。

</details>

<details>
<summary>为什么不直接把官方 Skill 打包进这个仓库？</summary>

官方 Skill 是夸克的代码，没有授权再分发；打包进来还会很快过时。所以改成第一次用时、你同意后，从夸克官方地址下载最新版。效果一样是「只装一个」，但装上的永远是官方原版。

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

一次只转存你选中的那一条分享，这是刻意的：每次转存都要你点头，避免存进一堆用不上的东西。反过来，一条分享里可以只存你要的那几个文件。

</details>

<details>
<summary>为什么表格里有的条目文件数写着「未验证」？</summary>

那条链接预检时夸克没给出明确结果（比如网络抖动），既不能确定能用，也不能确定失效，所以留着让你决定。明确失效的已经剔掉了。

</details>

<details>
<summary>怎么让它定时帮我追更？</summary>

先正常转存一次。之后在支持定时任务的智能体里说「每天晚上 10 点帮我看看这个分享有没有更新，有就存下来」。智能体不支持定时任务的话，就需要你想起来时说一句「看看有没有更新」。

</details>

## 开发

```
quark-skill/
├── skills/quark-search-save/
│   ├── SKILL.md                 智能体读的说明书（触发词、工作流、失败处理）
│   └── scripts/
│       ├── pansou_search.py     PanSou 搜索、过滤、去重、排序、冷启动重试、备用实例
│       ├── find_quark_cli.py    定位夸克官方 Skill 的 CLI
│       ├── check_links.py       调官方 share-detail 预检候选，剔除失效链接
│       └── install_quark_skill.py  没装时从夸克官方地址安装官方 Skill
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
