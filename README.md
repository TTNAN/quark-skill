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

## 快速开始

**1. 装好夸克官方 Skill 并登录**

本 Skill 的转存一步依赖夸克官方 Skill（`quarkclouddrive`）。先按官方说明安装，并在智能体里完成一次 `login` 授权。Skill 会自动找到它的安装位置；装在非常规目录时，设置环境变量 `QUARK_SKILL_DIR` 指过去即可。

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

## 行为约定

为了让结果可预期，这个 Skill 刻意保守：

- **不乱改词**：只用你说的关键词搜，搜不到就直说，不编链接。
- **不替你做主**：没有你明确选中的那一条，就不转存。
- **不乱放文件**：你没指定目录时用夸克默认位置；指定了才传目录参数。
- **失败就停**：`saveas` 报错时原样告诉你 `msg`，不静默重试、不绕路。
- **授权问题走官方**：遇到未授权，引导你重新走官方 Skill 的 `login`。

## 支持哪些智能体

能跑夸克官方 Skill 的智能体都能用，包括 Claude Code、Codex、Cursor、Trae、Qoder、OpenCode、Cherry Studio、Kimi、豆包、通义等。完整清单以夸克官方 Skill 的环境检测为准。

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

## 开发

```bash
pip install pytest
python -m pytest -q                 # 单元测试，不联网
python tools/make_demo_gif.py       # 重新生成演示动图（需要 Pillow 和中文字体）
```

改动记录见 [CHANGELOG](CHANGELOG.md)。

## 合规声明

本项目不提供、不存储、不托管任何资源，只调用 PanSou 公开搜索 API 与夸克官方转存接口。请只转存你有权保存的内容（公开课程、开源资料、自己的分享等），因使用本项目产生的版权问题由使用者自行负责。

## 协议

[MIT](LICENSE) © TTNAN
