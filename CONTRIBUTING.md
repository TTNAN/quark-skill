# 参与贡献

欢迎提 Issue 和 PR！这个项目很小，规则也简单。

## 项目原则

`quark-search-save` 只是两段现成能力的拼接：**PanSou 搜索 + 夸克官方 Skill 转存**。下面这些不会合并：

- 抓浏览器 cookie、逆向夸克网页接口、绕过官方 Skill 的环境检测
- 部署服务、跑 Docker、开常驻进程
- 引入第三方 Python 依赖（脚本只用标准库，兼容 Python 3.9，即 macOS 自带的 python3）
- 绕过官方 CLI、直接请求夸克接口（预检、选文件、追更都必须走官方 CLI 命令）
- 托管或分发任何资源
- 把夸克官方 Skill 的文件打包进本仓库（只能在用户同意后从夸克官方地址下载）

## 目录结构

```
skills/quark-search-save/        ← 安装时整个目录会被拷走，必须自包含
  SKILL.md                       ← 给智能体看的说明（frontmatter 必须是合法 YAML）
  scripts/pansou_search.py       ← PanSou 搜索
  scripts/find_quark_cli.py      ← 定位夸克官方 CLI
  scripts/check_links.py         ← 调官方 share-detail 预检候选链接
  scripts/install_quark_skill.py ← 用户同意后从夸克官方地址安装官方 Skill
tests/                           ← 单元测试，不联网
examples/                        ← 官方 Skill 演示
assets/  tools/                  ← README 素材和动图生成脚本
```

## 本地开发

```bash
pip install pytest pyyaml
python -m pytest -q

# 联网试一下搜索
python3 skills/quark-search-save/scripts/pansou_search.py --kw "线性代数" --json

# 试一下安装（不会影响你自己的 ~/.claude）
HOME=$(mktemp -d) npx -y skills add . -g -y -a claude-code
```

## 改动约定

- **改了 SKILL.md**：注意 `description` 里不要出现未加引号的 `: `，测试会检查 YAML 能否解析。
- **改了行为**：同步更新 `README.md`、`README.en.md` 和 `CHANGELOG.md`。
- **发版本**：同时改 SKILL.md 的 `metadata.version` 和 `pansou_search.py` 的 `__version__`（测试会检查两者一致），然后打 `vX.Y.Z` tag 并发 Release。
- 提交信息用中文或英文都行，说清楚改了什么。

## 报 Bug

请用 Issue 模板，并附上 `pansou_search.py --json` 的输出或 `saveas` 返回的 `code` / `msg`。**不要贴账号、token 或私人分享的提取码。**
