# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：iMato 桌面端后端（main_ai_edu 入口）。

构建（在 backend/ 目录下执行）：
    G:\\Python312\\python.exe -m PyInstaller main_ai_edu.spec --distpath dist --workpath build --noconfirm

产物：
    backend/dist/main_ai_edu/main_ai_edu.exe
    backend/dist/main_ai_edu/_internal/...        （依赖 + 数据）

设计要点：
1. onedir 模式（不是 onefile）：启动快、缺少 DLL 时能定位到具体文件。
2. 保留 console=True：Electron 需要读取 stdout/stderr 转发到 splash
   （spawn 时已是 windowsHide: true，不会弹出黑窗）。
3. 排除项均已在 1.2 阶段验证为「不在启动路径上」或「有 try/except 保护」
   —— 详见 tmp/desktop-pyinstaller.md 的依赖分析结论。
   - torch：仅由 transformers.utils.generic 在 `if is_torch_available():` 内导入
   - transformers：仅由 langchain_core.language_models.base 在 try/except ImportError 内导入
   - faiss/chromadb/sentence_transformers：仅 services/*.py 内部按需使用，不在启动路径
     注意：这些是「可选能力降级」，若后续要在桌面端启用本地向量检索，
     需移除对应 excludes 并重新打包（体积 +~150MB）。
4. SQLAlchemy 的 sqlite+aiosqlite 方言必须显式声明，否则运行时报
   `ModuleNotFoundError: sqlalchemy.dialects.sqlite.aiosqlite`。
"""

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

BACKEND_DIR = Path(SPECPATH).resolve()  # noqa: F821 - SPECPATH 由 PyInstaller 注入

# ---------------------------------------------------------------- 数据文件
# 只收集运行时真正读取的目录；backend/venv（3.7GB）与 marketing_api/venv 绝不收集。
_DATA_DIRS = ["data", "templates", "static", "configs", "migrations"]

datas = []
for _rel in _DATA_DIRS:
    _src = BACKEND_DIR / _rel
    if not _src.is_dir():
        continue
    for _root, _dirs, _files in os.walk(_src):
        _dirs[:] = [d for d in _dirs if d not in ("__pycache__", "venv", ".venv")]
        for _fn in _files:
            if _fn.endswith((".pyc", ".pyo")):
                continue
            _full = Path(_root) / _fn
            _target = str(_full.relative_to(BACKEND_DIR).parent)
            datas.append((str(_full), _target))

# 应用配置文件模板（不含真实 .env，避免把 SECRET_KEY 打进安装包）
# 冻结态的真实配置由 config/settings.py 在首次启动时写入用户数据目录：
#   %APPDATA%\\imato-desktop\\.env（SECRET_KEY + 绝对 DATABASE_URL）
_env_example = BACKEND_DIR / ".env.example"
if _env_example.exists():
    datas.append((str(_env_example), "."))

# ------------------------------------------------------------ 隐式依赖（动态导入）
hiddenimports = [
    # uvicorn：loops / protocols / lifespan 全部靠 import 字符串动态选择
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.http.httptools_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.protocols.websockets.websockets_impl",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    # SQLAlchemy 方言（sqlite+aiosqlite 是本项目默认 DATABASE_URL）
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.dialects.sqlite.aiosqlite",
    "sqlalchemy.dialects.sqlite.pysqlite",
    "sqlalchemy.ext.asyncio",
    "aiosqlite",
    "greenlet",
    # pydantic / pydantic-settings
    "pydantic_settings",
    "dotenv",
    # 认证：passlib 通过 registry 动态加载 handler，jose 动态选择 backend
    "passlib.handlers.bcrypt",
    "passlib.handlers.pbkdf2",
    "passlib.handlers.sha2_crypt",
    "bcrypt",
    "jose.backends.cryptography_backend",
    "cryptography",
    # multipart / form 解析
    "python_multipart",
    "multipart",
    # anyio 后端
    "anyio._backends._asyncio",
    # 首启建库/种子（main_ai_edu 里通过 __import__(字符串) 动态导入，
    # PyInstaller 静态分析看不到，必须显式声明）
    "database.db",
    "database.legacy_base_compat",
    "database.package_base_compat",
    "database.shadow_registry",
    "models.achievement",
    "models.leaderboard",
    "models.content_store",
    "models.finance",
    "models.hardware_module",
    "models.course",
    "models.learning_source",
    "models.organization",
    "models.recommendation",
    "models.unified_learning_record",
    "models.user_organization",
    "scripts.seed_initial_data",
    "scripts.seed_demo_data",
    # Phase1 新增扁平化查询路由（main_ai_edu 直接 import，显式声明防漏）
    "routes.achievement_catalog_routes",
    "routes.course_catalog_routes",
]

# 【PR #68 回归修复】main_ai_edu 改为 core.router_registry 单一事实源后，路由模块只以
# 字符串 module_path 形式出现（importlib.import_module），PyInstaller 静态分析不可见，
# 导致冻结态 22+ 路由注册失败（No module named 'routes.xxx'，含 /ws/ai-edu）。
# 这里整包收集 routes 子模块，避免以后新增路由再次漏打包。
hiddenimports += collect_submodules("routes")

# --------------------------------------------------------------------- 排除项
excludes = [
    # 机器学习栈（不在启动路径）
    "torch",
    "torchvision",
    "torchaudio",
    "torchgen",
    "tensorflow",
    "keras",
    "tensorboard",
    "transformers",
    "tokenizers",
    "safetensors",
    "huggingface_hub",
    "sentence_transformers",
    "faiss",
    "chromadb",
    "cv2",
    "mediapipe",
    # 科学计算中未被启动路径使用的（scipy/sklearn/numpy/pandas 必须保留）
    "sympy",
    "numba",
    "llvmlite",
    "matplotlib",
    "mpl_toolkits",
    # 【体积门禁】下列重依赖不在 63 个 router_registry 模块的模块级 import 链上
    # （tmp/_dep_probe.py 静态验证：190 个可达模块，均不命中），仅被函数内懒加载使用。
    # 不排除则安装包 219MiB > 200MiB 门槛；相关功能在桌面端降级为不可用（Phase 2 再说）。
    "fitz",
    "pymupdf",
    "skimage",
    "grpc",
    "grpc_tools",
    "pyphen",
    "lxml",
    "reportlab",
    "weasyprint",
    # 开发/测试/文档工具链
    "pytest",
    "_pytest",
    "pytest_asyncio",
    "sphinx",
    "docutils",
    "IPython",
    "ipykernel",
    "jupyter",
    "jupyter_client",
    "jupyter_core",
    "notebook",
    "nbconvert",
    "nbformat",
    "tkinter",
    "PyQt5",
    "PySide6",
]

block_cipher = None

a = Analysis(  # noqa: F821
    ["main_ai_edu.py"],
    pathex=[str(BACKEND_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="main_ai_edu",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="main_ai_edu",
)
