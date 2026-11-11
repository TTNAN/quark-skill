# Changelog

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
