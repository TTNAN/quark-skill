# Changelog

## 1.3.4 — 2026-11-12

### Changed
- **`find_quark_cli.py` 会验证 CLI 能跑**：每个找到的 `quark-drive.cjs` 都跑一次 `node quark-drive.cjs --help`，跑不起来的（没装 node、文件被截断）记进 `broken`、不算找到。能跑的有多份时取官方 `SKILL.md` 版本号最高的，项目里残留的旧版不再盖过全局新装的；查找位置补上 `.workbuddy/skills`、`.codebuddy/skills`。`QUARK_SKILL_DIR` 设了就只认它。`--no-verify` 可跳过验证。SKILL.md 写明 `broken` 时如何引导用户重装。
- **最坏耗时有上限，文档口径对齐代码**：新增 `--max-wait`（默认 60 秒）重试总预算，超出就不再重试，每个实例至少请求一次；搜索单次超时 30→25 秒（公共实例实测单次就要 6–18 秒，再低会把正常请求判超时），搜索最坏约两分钟；预检单条超时 30→20 秒，最坏约一分半。SKILL.md 改为“通常半分钟以内，最坏三四分钟”，README 不再写“约 30 秒”。
- 预检：`code: 0`、`files` 为空且 `share_info` 里没有 `file_num` / `file_only_num` 的分享也按失效处理。

### Docs
- README 中英文写明“已实测验证：官方 Skill 1.0.25，WorkBuddy”；CONTRIBUTING 写明官方升级后要重跑真机、刷新固件。测试里的 `VERIFIED_OFFICIAL_VERSION` 和这两处文档不一致时 CI 会红。
- 演示动图从 2.1 MB 压到约 400 KB（滚动改为直接跳转、64 色调色板并固定品牌色），内容不变。

## 1.3.3 — 2026-11-12

### Added
- `share-search` 的真实固件（命中 / 没命中，WorkBuddy 实测），回归测试钉住返回形状。至此 SKILL.md 用到的官方命令都有真实固件。

### Docs
- SKILL.md 第 4 步写明：`file_type` 是字符串，`"0"` 为文件夹；`share-search` 没搜到返回 `code: 0` + 空 `files`，不是报错，改用 `share-detail` 浏览。

## 1.3.2 — 2026-11-12

首次在真实智能体（WorkBuddy，Windows，官方 Skill 1.0.25）里跑通全链路：自动安装 → 搜索 → 预检 → 列文件 → `saveas --fid-list` → 回查 → 查更新。字段名和之前的假设一致。

### Fixed
- **Windows 下预检刷屏报错**：中文 Windows 默认 GBK，官方 CLI 往 stderr 输出的字节让 subprocess 读线程抛 `UnicodeDecodeError`（结果没受影响，但日志全是 traceback）。`check_links.py` 和 `install_quark_skill.py` 调子进程时显式 `encoding="utf-8", errors="replace"`。

### Added
- **真实固件回归测试**：`tests/fixtures/workbuddy/` 存了脱敏后的官方 CLI 原始输出（share-detail 有效 / 失效、saveas、search 回查、get-share-update-files、安装结果），`tests/test_real_fixtures.py` 对着它们断言。官方改返回结构时 CI 会先红。
- 预检结果新增 `total_files` / `total_size`（取自 `share_info.file_only_num` / `size`）。很多分享只有一个顶层文件夹，首层“1 个文件”没意义，现在能显示“53 个文件，2.9 GB”。
- `invalid` 条目带上 `errno`。

### Changed
- 最低 Python 版本定为 **3.9**（macOS 自带的 python3 就是 3.9）。CI 改回 `ubuntu-latest`，在官方 `python:3.9-slim` / `python:3.13-slim` 容器里测，不再依赖 runner 自带哪些 Python 版本，也不再钉死会被 GitHub 退役的 ubuntu-22.04。

## 1.3.1 — 2026-11-12

### Fixed
- **预检不再误杀**：`check_links.py` 不再按报错文字做子串匹配，只认已知失效码 41004 / 41006 / 41007（从 `errno=` 或透传的 `code` 里取），以及“分享里一个文件都没有”；网络抖动、限流、41008 等拿不准的一律标 `unknown`，留给用户决定。
- **自动安装不再依赖官方脚本的输出格式**：成功标准改为 `install.sh` 退出码 0 + `scripts/quark-drive.cjs` 存在 + `node quark-drive.cjs --help` 能跑；官方若明确输出 `success:false` 仍按失败处理。

### Changed
- **等待时有进度**：搜索脚本开头就报“正在搜索哪个实例”；预检每验完一条往 stderr 打 `[n/总数] 标题：可用/已失效/未验证`。每条预检超时从 60 秒降到 30 秒（`--timeout` 可调，`--quiet` 关闭进度）。SKILL.md 要求开始前告诉用户可能要一两分钟，等久了转告最新进度。
- CI 的“Skill 自包含”检查覆盖全部 4 个脚本（文件存在 + SKILL.md 里的引用都相对 `<本 Skill 目录>`）。

### Docs
- README 中英文“支持哪些智能体”补上 WorkBuddy（官方页展示 4 个）。
- 演示动图按 v1.3 流程重做：首次安装 → 搜索 → 预检 → 挑选 → 只存第 3 章 → 转存 → 回查 → 追更提示。

## 1.3.0 — 2026-11-11

### Added
- **转存前预检**：新脚本 `check_links.py` 对候选逐条调官方 `share-detail`（客态模式，无需登录），剔除已失效、已取消、不存在、提取码错误的分享，并给表格补上分享标题、文件数、内容预览。官方 CLI 不可用时自动跳过，流程照旧。搜索改为先取 10 条，预检后保留 5 条。
- **只存需要的文件**：用户说“只要第 3 章 / 只要 PDF”时，用官方 `share-search` 或 `share-detail` 列出分享内的文件，选好后 `saveas --fid-list` 只存这些。
- **追更**：已转存过的分享，用官方 `get-share-update-files` 查新增内容，同意后 `saveas-update` 只补新增的；只要其中几个时走 `get-share-saved-dir` + `saveas --fid-list`。
- **搜索备用实例**：`PANSOU_URL` / `--url` 支持逗号分隔多个实例，按顺序尝试；默认 `https://s.panhunt.com`，没结果或出错时换 `https://so.252035.xyz`（备用实例只重试 1 次）。JSON 输出新增 `instance`、`instance_errors`。
- 测试：`tests/test_check_links.py`、备用实例相关用例。

### Changed
- SKILL.md：官方 CLI 公共规则（`--session-input`、`--session-id`、`install.sh` 自检、`notice.text`）提到工作流之前，统一适用于预检、选文件、转存、追更；工作流改为 6 步。
- Python 版本要求从 3.10+ 改为实际支持的 3.8+；CI 改测 3.8 和 3.12。

### Docs
- README 中英文同步更新：功能表、对话示例、工作流、预检脚本说明、备用实例、追更、限制与常见问题；英文 README 补全到与中文结构一致。

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
