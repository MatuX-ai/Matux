"""ROUTER_TABLE 与双入口的静态一致性校验（PR-B commit 3）。

纯校验测试：只读 core/router_registry.py 的静态表，用 AST 反向解析
backend/legacy_routes.py 与 backend/main_ai_edu.py 两个入口源码中的
include_router(...) 调用，校验「表 ↔ 入口」双向无漂移。
零行为变更，不修改任何源码。

与 tests/test_router_registry.py 的分工：
- test_router_registry.py：校验 router_registry 自身的表结构与失败策略
- test_router_parity.py（本文件）：校验 ROUTER_TABLE 与两个入口**源码**的一致性

口径（对齐 issue #21「并集 61」）::

    legacy 侧       : 52 个模块（mode ∈ {legacy, both}）
    main_ai_edu 侧 : 20 个模块（mode ∈ {lazy, both}）
    交集            : 11 个模块
    并集            : 52 + 20 - 11 = 61 个模块  == len(ROUTER_TABLE)

白名单（issue #26；desktop-p3-batch1 后剩 3 项）分两类，本文件分别校验其「缺失形态」：

    模块未入库 PENDING_MODULE_MISSING（入口源码里本就找不到，属预期）:
        routes.share_routes
        routes.gamification_websocket_routes
    依赖未入库 PENDING_DEPENDENCY（入口源码里有 include_router，注册期跳过）:
        routes.ai_edu_websocket_routes

注：routes.ai_teacher_routes 已随 backend/cache/ 入库，双入口均已注册，
     不再属于白名单。

用法::

    cd backend && pytest tests/test_router_parity.py -v
"""

import ast
import os
from pathlib import Path
import sys
from typing import Dict, Iterable, List, Optional, Set, Tuple

from core import router_registry
from core.router_registry import (
    MODE_BOTH,
    MODE_LAZY,
    MODE_LEGACY,
    ROUTER_TABLE,
    STATUS_ACTIVE,
    STATUS_PENDING_INTEGRATION,
    RouterSpec,
    pending_integration_modules,
    register_all_routers,
)
import pytest

# 确保 backend 目录在 sys.path 中
_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, os.path.abspath(_backend_dir))


# ==================== 常量 ====================

BACKEND_DIR = Path(__file__).resolve().parent.parent
LEGACY_ROUTES_FILE = BACKEND_DIR / "legacy_routes.py"
AI_EDU_MAIN_FILE = BACKEND_DIR / "main_ai_edu.py"
SETTINGS_FILE = BACKEND_DIR / "config" / "settings.py"

#: legacy 侧归属的 mode 组合（legacy_routes.py 负责注册的模块）
LEGACY_SIDE_MODES = (MODE_LEGACY, MODE_BOTH)
#: main_ai_edu 侧归属的 mode 组合（main_ai_edu.py 负责注册的模块）
AI_EDU_SIDE_MODES = (MODE_LAZY, MODE_BOTH)

#: 白名单（一）：模块在 WIP 树中存在，origin/main 尚未入库 -> 入口源码里找不到
PENDING_MODULE_MISSING = frozenset(
    {
        "routes.share_routes",
        "routes.gamification_websocket_routes",
    }
)
#: 白名单（二）：模块已入库，但依赖尚未入库 -> 入口源码里有，注册期跳过
PENDING_DEPENDENCY = frozenset(
    {
        "routes.ai_edu_websocket_routes",
    }
)
#: 白名单全集（issue #26 拍板；ai_teacher 入库后剩 3 项）
EXPECTED_PENDING = PENDING_MODULE_MISSING | PENDING_DEPENDENCY

#: legacy 侧「表里有、入口源码里找不到」的固定基线（全部属于模块未入库白名单）
EXPECTED_LEGACY_MISSING = frozenset(
    {
        ("routes.gamification_websocket_routes", "router"),
        ("routes.share_routes", "api_router"),
        ("routes.share_routes", "page_router"),
    }
)
#: main_ai_edu 侧「表里有、入口源码里找不到」的固定基线（依赖类白名单在源码里存在）
EXPECTED_AI_EDU_MISSING = frozenset()

#: 4 个条件开关（与 config/settings.py 中的默认值一一对应）
CONDITION_KEYS = frozenset(
    {
        "ENABLE_AR_VR_ROUTES",
        "ENABLE_AR_VR_MOCK_ROUTES",
        "ENABLE_DIGITAL_TWIN_ROUTES",
        "ENABLE_MODEL_UPDATE_ROUTES",
    }
)


# ==================== AST 解析工具 ====================


def _parse_module(path: Path) -> ast.Module:
    """解析 Python 源文件为 AST。"""
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _import_aliases(tree: ast.Module) -> Dict[str, Tuple[str, Optional[str]]]:
    """收集 import 语句：本地别名 -> (来源模块, 导入名)。

    - ``from pkg import mod``   -> ("pkg", "mod")      mod 通常是子模块
    - ``from pkg.mod import x`` -> ("pkg.mod", "x")    x 通常是模块内对象
    - ``import pkg.mod``        -> ("pkg.mod", None)
    """
    aliases: Dict[str, Tuple[str, Optional[str]]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level or not node.module:
                continue
            for alias in node.names:
                if alias.name == "*":
                    continue
                aliases[alias.asname or alias.name] = (node.module, alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name] = (alias.name, None)
    return aliases


def _include_router_pairs(tree: ast.Module) -> Set[Tuple[str, str]]:
    """提取源码中所有 include_router(...) 的 (模块路径, router 属性名)。

    兼容两种写法：
    - ``app.include_router(mod.router, ...)``   -> ("pkg.mod", "router")
    - ``app.include_router(router_alias, ...)``  -> ("pkg.mod", "router")
    """
    aliases = _import_aliases(tree)
    pairs: Set[Tuple[str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "include_router":
            continue
        if not node.args:
            continue
        target = node.args[0]
        if isinstance(target, ast.Name):
            # 直接引入 router 对象：from pkg.mod import router as alias
            entry = aliases.get(target.id)
            if entry is None:
                continue
            base, imported = entry
            pairs.add((base, imported or "router"))
        elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
            # 引入模块后取属性：from pkg import mod -> mod.router
            entry = aliases.get(target.value.id)
            if entry is None:
                continue
            base, imported = entry
            module = f"{base}.{imported}" if imported else base
            pairs.add((module, target.attr))
    return pairs


def _settings_flag_defaults() -> Dict[str, bool]:
    """从 config/settings.py 解析 Settings 类的布尔开关默认值（不导入 settings）。"""
    tree = _parse_module(SETTINGS_FILE)
    defaults: Dict[str, bool] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != "Settings":
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.AnnAssign):
                continue
            if not isinstance(stmt.target, ast.Name) or stmt.value is None:
                continue
            if isinstance(stmt.value, ast.Constant) and isinstance(
                stmt.value.value, bool
            ):
                defaults[stmt.target.id] = stmt.value.value
    return defaults


def _spec_pairs(specs: Iterable[RouterSpec]) -> Set[Tuple[str, str]]:
    """规格列表展开为 (模块路径, router 属性名) 集合。"""
    return {(spec.module_path, attr) for spec in specs for attr in spec.router_attr}


def _format_diff(expected: Set, actual: Set) -> str:
    """生成可读的差异说明，失败时直接定位漂移方向。"""
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    lines: List[str] = []
    if missing:
        lines.append("缺失（表里有、源码里找不到）:\n  " + "\n  ".join(str(item) for item in missing))
    if extra:
        lines.append("多出（源码里有、表里没有）:\n  " + "\n  ".join(str(item) for item in extra))
    return "\n".join(lines) if lines else "无差异"


# ==================== 测试替身与 fixtures ====================


class MockApp:
    """最小 FastAPI 替身：只记录 include_router 调用。"""

    def __init__(self) -> None:
        self.calls: List[Dict[str, object]] = []

    def include_router(self, router: object, prefix: str = "", tags=None) -> None:
        self.calls.append(
            {"router": router, "prefix": prefix, "tags": list(tags or [])}
        )

    def modules(self) -> List[str]:
        """已注册的模块路径列表（按调用顺序，去重）。"""
        seen: List[str] = []
        for call in self.calls:
            module = str(call["router"]).rsplit(".", 1)[0]
            if module not in seen:
                seen.append(module)
        return seen


@pytest.fixture
def mock_app() -> MockApp:
    """空的 mock FastAPI 应用。"""
    return MockApp()


@pytest.fixture
def isolated_logs(monkeypatch, tmp_path) -> Path:
    """把报告与失败计数隔离到 tmp_path，避免污染 backend/logs。"""
    monkeypatch.setattr(router_registry, "LOG_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def stub_import(monkeypatch):
    """把真实 import 替换为返回可辨识字符串的假实现（避免导入 57 个重依赖模块）。"""

    def _fake(spec: RouterSpec, attr: str) -> str:
        return f"{spec.module_path}.{attr}"

    monkeypatch.setattr(router_registry, "_import_router", _fake)
    return _fake


@pytest.fixture
def conditions_on(monkeypatch):
    """条件路由全部视为已启用。"""
    monkeypatch.setattr(router_registry, "_condition_enabled", lambda key: True)
    return True


@pytest.fixture(scope="module")
def legacy_pairs() -> Set[Tuple[str, str]]:
    """legacy_routes.py 中 include_router 的 (模块, 属性) 集合。"""
    return _include_router_pairs(_parse_module(LEGACY_ROUTES_FILE))


@pytest.fixture(scope="module")
def aiedu_pairs() -> Set[Tuple[str, str]]:
    """main_ai_edu.py 中 include_router 的 (模块, 属性) 集合。"""
    return _include_router_pairs(_parse_module(AI_EDU_MAIN_FILE))


def _table_pairs(
    modes: Iterable[str], status: str = STATUS_ACTIVE
) -> Set[Tuple[str, str]]:
    """按 mode 与 status 过滤 ROUTER_TABLE 并展开为 (模块, 属性) 集合。"""
    return _spec_pairs(
        spec for spec in ROUTER_TABLE if spec.status == status and spec.mode in modes
    )


# ==================== T1 / T2：入口源码一致性 ====================


class TestEntrySourceParity:
    """T1/T2：ROUTER_TABLE 与两个入口源码的 include_router 双向一致性。"""

    def test_t1_legacy_routes_matches_table(self, legacy_pairs):
        """T1：legacy 侧，表内条目在 legacy_routes.py 中都能找到对应注册。"""
        table_pairs = _table_pairs(
            LEGACY_SIDE_MODES, status=STATUS_ACTIVE
        ) | _table_pairs(LEGACY_SIDE_MODES, status=STATUS_PENDING_INTEGRATION)
        missing = table_pairs - legacy_pairs
        assert missing == set(
            EXPECTED_LEGACY_MISSING
        ), "legacy 侧 include_router 与 ROUTER_TABLE 漂移：\n" + _format_diff(
            set(EXPECTED_LEGACY_MISSING), missing
        )

    def test_t1_legacy_routes_has_no_extra_modules(self, legacy_pairs):
        """T1 反向：legacy_routes.py 里没有表外模块（防止有人绕过 ROUTER_TABLE）。"""
        table_pairs = _table_pairs(
            LEGACY_SIDE_MODES, status=STATUS_ACTIVE
        ) | _table_pairs(LEGACY_SIDE_MODES, status=STATUS_PENDING_INTEGRATION)
        extra = legacy_pairs - table_pairs
        assert not extra, "legacy_routes.py 存在 ROUTER_TABLE 之外的注册：\n" + _format_diff(
            set(), extra
        )

    def test_t2_main_ai_edu_matches_table(self, aiedu_pairs):
        """T2：main_ai_edu 侧，表内条目在 main_ai_edu.py 中都能找到对应注册。"""
        table_pairs = _table_pairs(
            AI_EDU_SIDE_MODES, status=STATUS_ACTIVE
        ) | _table_pairs(AI_EDU_SIDE_MODES, status=STATUS_PENDING_INTEGRATION)
        missing = table_pairs - aiedu_pairs
        assert missing == set(
            EXPECTED_AI_EDU_MISSING
        ), "main_ai_edu 侧 include_router 与 ROUTER_TABLE 漂移：\n" + _format_diff(
            set(EXPECTED_AI_EDU_MISSING), missing
        )

    def test_t2_main_ai_edu_has_no_extra_modules(self, aiedu_pairs):
        """T2 反向：main_ai_edu.py 里没有表外模块（防止有人绕过 ROUTER_TABLE）。"""
        table_pairs = _table_pairs(
            AI_EDU_SIDE_MODES, status=STATUS_ACTIVE
        ) | _table_pairs(AI_EDU_SIDE_MODES, status=STATUS_PENDING_INTEGRATION)
        extra = aiedu_pairs - table_pairs
        assert not extra, "main_ai_edu.py 存在 ROUTER_TABLE 之外的注册：\n" + _format_diff(
            set(), extra
        )

    def test_legacy_side_covers_52_modules(self, legacy_pairs):
        """legacy 侧口径：52 个模块（52 + 19 - 10 = 61）。"""
        table_modules = {
            spec.module_path for spec in ROUTER_TABLE if spec.mode in LEGACY_SIDE_MODES
        }
        assert len(table_modules) == 52

    def test_aiedu_side_covers_20_modules(self, aiedu_pairs):
        """main_ai_edu 侧口径：20 个模块。"""
        table_modules = {
            spec.module_path for spec in ROUTER_TABLE if spec.mode in AI_EDU_SIDE_MODES
        }
        assert len(table_modules) == 20


# ==================== T3：parity 三方一致 ====================


class TestParitySets:
    """T3：active 集合 == 入口源码集合 - pending 集合。"""

    def test_t3_active_legacy_set_equals_source_minus_pending(self, legacy_pairs):
        """T3：legacy 侧 active 集合 = 源码集合 - 源码中出现的 pending 集合。"""
        active = _table_pairs(LEGACY_SIDE_MODES, status=STATUS_ACTIVE)
        pending_in_source = (
            _table_pairs(LEGACY_SIDE_MODES, status=STATUS_PENDING_INTEGRATION)
            & legacy_pairs
        )
        expected = legacy_pairs - pending_in_source
        assert active == expected, "legacy 侧 active 集合与源码不一致：\n" + _format_diff(
            expected, active
        )

    def test_t3_active_aiedu_set_equals_source_minus_pending(self, aiedu_pairs):
        """T3：main_ai_edu 侧 active 集合 = 源码集合 - 源码中出现的 pending 集合。"""
        active = _table_pairs(AI_EDU_SIDE_MODES, status=STATUS_ACTIVE)
        pending_in_source = (
            _table_pairs(AI_EDU_SIDE_MODES, status=STATUS_PENDING_INTEGRATION)
            & aiedu_pairs
        )
        expected = aiedu_pairs - pending_in_source
        assert active == expected, "main_ai_edu 侧 active 集合与源码不一致：\n" + _format_diff(
            expected, active
        )

    def test_t3_union_of_sources_covers_table(self, legacy_pairs, aiedu_pairs):
        """T3 全局：两侧源码并集 + 模块未入库白名单 == ROUTER_TABLE 的 61 个模块。"""
        table_modules = {spec.module_path for spec in ROUTER_TABLE}
        source_modules = {module for module, _ in legacy_pairs} | {
            module for module, _ in aiedu_pairs
        }
        assert len(table_modules) == 61
        assert (
            source_modules | set(PENDING_MODULE_MISSING) == table_modules
        ), "两侧入口源码并集与 ROUTER_TABLE 漂移：\n" + _format_diff(
            table_modules, source_modules | set(PENDING_MODULE_MISSING)
        )


# ==================== T4：条件路由 ====================


class TestConditionalRoutes:
    """T4：4 个 ENABLE_* 条件开关默认关闭时，active 集合仍然正确。"""

    def test_t4_condition_keys_are_four(self):
        """条件项恰好 4 条，且开关键与 settings 一致。"""
        actual = {spec.condition_key for spec in ROUTER_TABLE if spec.condition_key}
        assert actual == set(CONDITION_KEYS)

    def test_t4_condition_defaults_are_false(self):
        """config/settings.py 中 4 个开关的代码默认值均为 False。"""
        defaults = _settings_flag_defaults()
        for key in CONDITION_KEYS:
            assert defaults.get(key) is False, f"{key} 的默认值不是 False"

    def test_t4_runtime_condition_is_disabled(self):
        """运行时读取到的开关同样为 False（settings 不可读时按未启用处理）。"""
        for key in CONDITION_KEYS:
            assert router_registry._condition_enabled(key) is False

    def test_t4_conditional_modules_exist_in_legacy_source(self, legacy_pairs):
        """条件路由在 legacy_routes.py 中是静态存在的（位于 if 分支内）。"""
        conditional = {
            (spec.module_path, attr)
            for spec in ROUTER_TABLE
            if spec.condition_key
            for attr in spec.router_attr
        }
        assert conditional
        assert (
            conditional <= legacy_pairs
        ), "条件路由在 legacy_routes.py 中找不到：\n" + _format_diff(
            conditional, conditional & legacy_pairs
        )

    def test_t4_active_set_unaffected_by_flag_defaults(self):
        """开关默认关闭只影响注册期跳过，不影响静态 active 集合的构成。"""
        conditional_modules = {
            spec.module_path for spec in ROUTER_TABLE if spec.condition_key
        }
        active_modules = {
            spec.module_path for spec in ROUTER_TABLE if spec.status == STATUS_ACTIVE
        }
        assert conditional_modules <= active_modules
        assert len(active_modules) == 58


# ==================== T5：白名单 ====================


class TestPendingIntegration:
    """T5：pending_integration_modules() 返回 3 项，且与源码缺失形态一致。"""

    def test_t5_returns_three_modules(self):
        """白名单恰为 3 项。"""
        pending = pending_integration_modules()
        assert len(pending) == 3
        assert set(pending) == set(EXPECTED_PENDING)

    def test_t5_matches_table_status(self):
        """返回值与表内 status 完全一致。"""
        table_pending = {
            spec.module_path
            for spec in ROUTER_TABLE
            if spec.status == STATUS_PENDING_INTEGRATION
        }
        assert set(pending_integration_modules()) == table_pending

    def test_t5_categories_are_disjoint(self):
        """两类白名单互斥且并集为全集。"""
        assert not (PENDING_MODULE_MISSING & PENDING_DEPENDENCY)
        assert PENDING_MODULE_MISSING | PENDING_DEPENDENCY == set(
            pending_integration_modules()
        )

    def test_t5_module_missing_are_absent_from_sources(self, legacy_pairs, aiedu_pairs):
        """模块未入库的白名单：两个入口源码里都找不到。"""
        source_modules = {module for module, _ in legacy_pairs} | {
            module for module, _ in aiedu_pairs
        }
        for module in PENDING_MODULE_MISSING:
            assert module not in source_modules

    def test_t5_dependency_pending_are_present_in_source(self, legacy_pairs):
        """依赖未入库的白名单：源码里存在 include_router，仅在注册期跳过。"""
        source_modules = {module for module, _ in legacy_pairs}
        for module in PENDING_DEPENDENCY:
            assert module in source_modules


# ==================== T6：注册行为 ====================


class TestRegisterAllRoutersParity:
    """T6：register_all_routers 在 mock app 上注册 58 个 active 模块。"""

    def test_t6_registers_58_active_modules(
        self, mock_app, stub_import, isolated_logs, conditions_on
    ):
        """条件开启时：58 项 active 全部注册，3 项 pending 被跳过。"""
        report = register_all_routers(mock_app)

        assert report.total == 61
        assert len(report.succeeded) == 58
        assert not report.failed
        assert not report.disabled
        assert len(report.skipped) == 3
        assert {item["module"] for item in report.skipped} == set(EXPECTED_PENDING)
        assert len(mock_app.calls) == 58

    def test_t6_registered_modules_equal_active_set(
        self, mock_app, stub_import, isolated_logs, conditions_on
    ):
        """注册的模块集合必须恰好等于表内 active 集合。"""
        register_all_routers(mock_app)

        active_modules = {
            spec.module_path for spec in ROUTER_TABLE if spec.status == STATUS_ACTIVE
        }
        assert set(mock_app.modules()) == active_modules

    def test_t6_default_flags_skip_conditional_only(
        self, mock_app, stub_import, isolated_logs, monkeypatch
    ):
        """开关默认关闭：只额外跳过 4 项条件路由，active 集合本身不变。"""
        monkeypatch.setattr(router_registry, "_condition_enabled", lambda key: False)

        report = register_all_routers(mock_app)

        # 3 项 pending + 4 项条件未启用
        assert len(report.skipped) == 7
        assert len(report.succeeded) == 54
        conditional_modules = {
            spec.module_path for spec in ROUTER_TABLE if spec.condition_key
        }
        assert not conditional_modules & set(mock_app.modules())
        reasons = {item["reason"] for item in report.skipped}
        assert any(reason.endswith("=False") for reason in reasons)
