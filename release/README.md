# 桌面端发布产物

本目录由 `npm run electron:build:win`（参见 [electron/package.json](../electron/package.json)）生成。版本演进：

| 版本 | 安装包 | 构建日期 | 备注 |
|---|---|---|---|
| 1.0.0 | `iMato Setup 1.0.0.exe` | 2026-07-01 | 首次对外 |
| 1.0.2 | `iMato Setup 1.0.2.exe` | 2026-08-17 | 修复迭代 |
| 1.0.3 | `iMato Setup 1.0.3.exe` | 2026-08-17 | 上一个稳定版 |
| **1.0.4** | `iMato Setup 1.0.4.exe` | 待构建 | 见阶段一 1.4（[docs/07-产品文档/rfc-2026-v2-ai-collab.md](../docs/07-产品文档/rfc-2026-v2-ai-collab.md)） |

## 不入库的产物

为避免仓库膨胀，下列文件由 `.gitignore` 排除，仅保留在本地分发：

- `release/*.exe`（单文件 ~170 MB，建议走 GitHub Releases / 对象存储）
- `release/*.blockmap`（electron-builder 差分升级描述）
- `release/win-unpacked/`、`release/win-ia32-unpacked/`（解包目录）

仅 `builder-debug.yml` 与本 README 入库，便于追溯构建配置。

## v1.0.4 变更摘要（待 build 后回填）

- `fix(backend)`：4 个新模块注册到 `core/module_registry.py`，修复懒加载与 `legacy_routes.py` 双轨制漂移
- `feat(backend)`：错误日志持久化（`ErrorLog` + `FrontendErrorLog` 双格式）
- `feat(backend)`：AR/VR 课程管理（Admin + 前端课程两条路由 + 种子数据）
- `fix(ux)`：P4 系列体验修复（学习档案 / 教学建议 / AI 导师 / 状态栏 / AR-VR 播放器）
- 三端版本号统一：`matux-desktop` 1.0.4 / Flutter `1.0.4+4`

对应提交链：`11da327` → `52c3e34` → `73386cd` → `90650b0`。