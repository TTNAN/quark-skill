# Changelog

## 1.2.0 — 2026-11-11

### Added
- 只装一个 Skill 就能用：没装夸克官方 Skill 时，智能体会先问用户，同意后用新脚本 `install_quark_skill.py` 从夸克官方接口取最新下载地址、下载官方 zip、装到同级目录并运行官方 `install.sh`，再按官方流程引导登录，登录后接着完成原请求。本仓库不附带任何夸克的文件。
  - 只接受 `quark.cn` 的 https 下载地址；校验包内容、拒绝路径越界；先解压到临时目录再移动；不覆盖已有的非官方目录；已安装时不做任何事。
- `tests/test_install_quark_skill.py`：安装脚本的离线测试。

### Docs
- README 按「只装一个」重写快速开始；补充自动安装原理、首次使用流程、数据去向、为什么不打包官方 Skill；夸克官方 Skill 的手动安装方法（官方页面、提示词、命令）收进折叠区。
- README 大幅扩充：做法对比、完整对话示例、每步细节、搜索脚本参数与 JSON 字段、官方 Skill 查找顺序、自部署 PanSou、数据与隐私、已知限制、更多常见问题、项目结构。支持平台按官方页面更正。

## 1.1.2 — 2026-11-11

### Changed
- 转存遇到“分享已失效 / 已取消 / 不存在 / 提取码错误”时，不再直接结束：先报 `msg` 原文，再把表格里的下一条候选推荐给用户，等他同意才换。一次只推荐一条，不自动连试、不重新搜索。

### Added
- `CONTRIBUTING.md`：项目原则、目录结构、本地开发与发版约定。
- Issue 模板（Bug 报告、功能建议）和 PR 模板。

## 1.1.1 — 2026-11-11

### Fixed
- SKILL.md 的 `description` 里有英文冒号加空格（`Quark Drive: search`），YAML 解析失败，`npx skills add` 会报 `No valid skills found` 直接跳过。改用 `>-` 块标量。1.0.0 起就存在这个问题。

### Added
- `tests/test_skill_manifest.py`：校验 frontmatter 是合法 YAML、版本号与脚本一致；CI 安装 `pyyaml`。

## 1.1.0 — 2026-11-11

### Fixed
- 搜索脚本搬进 `skills/quark-search-save/scripts/`，`npx skills add` 和手动安装后都能找到。
- PanSou 冷启动第一次返回 0 条时，会用同一关键词自动退避重试（默认 3 次，约 30 秒），不再误报“搜不到”。
- 实例返回非 JSON（限流、拦截页）时给出清晰错误，不再抛 traceback；`--json` 模式下输出 `{"ok": false, "error": ...}`。
- `install.sh` 统一写成官方 Skill 目录下的路径，避免和本仓库混淆。

### Changed
- 改用 PanSou `res=merge`，直接读取 `merged_by_type.quark`。
- 按链接去重（保留日期较新的一条，补齐提取码），按日期从新到旧排序。
- 日期统一为 `YYYY-MM-DD`，空值和 `0001-01-01` 不显示。
- 输出改为“共找到 N 条夸克链接”，不再显示容易误解的全网盘总数。
- 新增 `needs_passcode` 字段，智能体据此决定是否传 `--passcode`。
- SKILL.md 写明关键词提取规则：只取资源核心名称，修饰词留到挑选时用。
- SKILL.md frontmatter 增加 `license` 和 `metadata.version`。

### Added
- `scripts/find_quark_cli.py`：自动定位夸克官方 Skill 的 `quark-drive.cjs`，支持 `QUARK_SKILL_DIR`。
- 单元测试（`tests/`）和 GitHub Actions CI（Python 3.10 / 3.12）。
- 新 README、英文 README、logo、横幅和演示动图（`assets/`），动图生成脚本 `tools/make_demo_gif.py`。

## 1.0.0

- 首个版本：PanSou 搜索 + 夸克官方 `saveas` 转存 + 回查。
