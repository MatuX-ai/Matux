"""ROUTER_TABLE 与双入口的静态一致性校验（PR-B commit 3 / PR-C2 兼容性重设计）。

纯校验测试：只读 core/router_registry.py 的静态表，用 AST 反向解析
backend/legacy_routes.py 与 backend/main_ai_edu.py 两个入口源码中的接线形态，
校验「表 ↔ 入口」双向无漂移。
零行为变更，不修改任何源码。

与 tests/test_router_registry.py 的分工：
- test_router_registry.py：校验 router_registry 自身的表结构与失败策略
- test_router_parity.py（本文件）：校验 ROUTER_TABLE 与两个入口**源码**的一致性

入口形态与兼容性（PR-C2）
------------------------
入口的接线形态会随 PR-B commit 4（4a / 4b）演进：

===========  ==========================  ==========================
阶段         legacy_routes.py            main_ai_edu.py
===========  ==========================  ==========================
4a 之前      legacy_inline               legacy_inline
4a 之后      legacy_inline               registry
4b 之后      registry                    registry
===========  ==========================  ==========================

- legacy_inline：入口源码里手写 ``app.include_router(...)``
- registry     ：入口源码里调用 ``register_all_routers(app, mode=...)``

因此本文件不再把「源码里的 include_router 列表」当作唯一断言对象，而是先由
:func:`detect_entry_form` 判定入口当前形态，再按形态选择断言口径：

- legacy_inline：断言源码的 include_router 集合 == 该侧表内条目集合
- registry     ：断言入口调用了 ``register_all_routers(mode=<该侧模式>)``
- mixed        ：两种调用并存 -> 重复注册，**必须失败**
- unknown      ：两种调用都没有 -> 入口接线被破坏，**必须失败**

兼容性分支的行为由 tests/test_router_parity_compat.py 用 mock 源码覆盖四种形态验证。

与 PR-C1 的 test_router_contract_snapshot.py 的分工：
- test_router_contract_snapshot.py（T8 / T10）：**行为层**权威验证 —— 入口对外暴露的
  ``(method, path)`` 集合 vs 快照基线
- test_router_parity.py（T1 / T2 / T3，本文件）：**源码层**一致性检查 ——
  入口有没有绕过 ROUTER_TABLE 手工接线

口径（对齐 issue #21「并集 61」）::

    legacy 侧       : 52 个模块（mode ∈ {legacy, both}）
    main_ai_edu 侧 : 19 个模块（mode ∈ {lazy, both}）
    交集            : 10 个模块
    并集            : 52 + 19 - 10 = 61 个模块  == len(ROUTER_TABLE)

白名单（issue #26）分两类，本文件分别校验其「缺失形态」：

    模块未入库 PENDING_MODULE_MISSING（入口源码里本就找不到，属预期）:
        routes.share_routes
    依赖未入库 PENDING_DEPENDENCY（入口源码里有 include_router，注册期跳过）:
        routes.ai_edu_websocket_routes
        routes.ai_teacher_routes

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

#: 入口侧标识
SIDE_LEGACY = "legacy"
SIDE_AI_EDU = "ai_edu"

#: 入口形态
FORM_LEGACY_INLINE = "legacy_inline"
FORM_REGISTRY = "registry"
FORM_MIXED = "mixed"
FORM_UNKNOWN = "unknown"

#: 注册模式 -> 该模式下预期注册的 mode 归属集合
#: 与 core.router_registry._select_specs 的契约一致：
#:   mode="legacy" 注册全量条目（legacy 模式提供完整路由集）
#:   mode="lazy"   只注册懒加载归属与两侧共用的条目
MODE_SCOPE = {
    MODE_LEGACY: (MODE_LEGACY, MODE_LAZY, MODE_BOTH),
    MODE_LAZY: (MODE_LAZY, MODE_BOTH),
}

#: 白名单（一）：模块在 WIP 树中存在，origin/main 尚未入库 -> 入口源码里找不到
PENDING_MODULE_MISSING = frozenset(
    {
        "routes.share_routes",
    }
)
#: 白名单（二）：模块已入库，但依赖尚未入库 -> 入口源码里有，注册期跳过
PENDING_DEPENDENCY = frozenset(
    {
        "routes.ai_edu_websocket_routes",
        "routes.ai_teacher_routes",
    }
)
#: 白名单全集（issue #26 拍板 + PR #27 commit 2 修正为 4 项 + PR-E 修正为 3 项）
EXPECTED_PENDING = PENDING_MODULE_MISSING | PENDING_DEPENDENCY

#: legacy 侧「表里有、入口源码里找不到」的固定基线（全部属于模块未入库白名单）
EXPECTED_LEGACY_MISSING = frozenset(
    {
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
                if alias.name == "*":
                    continue
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


def _has_include_router_call(tree: ast.Module) -> bool:
    """源码里是否存在任意 include_router(...) 调用（不要求 import 可解析）。

    与 :func:`_include_router_pairs` 的区别：后者要求第一个实参能追溯到 import 语句，
    才能算出 (模块, 属性)；本函数只用于判定「入口是不是 legacy_inline 形态」，
    因此只要出现调用即算命中，避免 ``app.include_router(局部变量)`` 被漏判。
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "include_router":
            return True
    return False


def _has_register_all_routers_call(tree: ast.Module) -> bool:
    """源码里是否存在 register_all_routers(...) 调用。

    兼容两种写法：
    - ``register_all_routers(app, ...)``
    - ``router_registry.register_all_routers(app, ...)``
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "register_all_routers":
            return True
        if isinstance(func, ast.Attribute) and func.attr == "register_all_routers":
            return True
    return False


def detect_entry_form(entry_file: Path) -> str:
    """检测入口文件的接线形态（纯 AST，不执行入口代码）。

    返回：
    - ``legacy_inline``：只有 include_router 调用
    - ``registry``     ：只有 register_all_routers 调用
    - ``mixed``        ：两者都有（重复注册，必须失败）
    - ``unknown``      ：两者都没有（入口接线被破坏，必须失败）
    """
    tree = _parse_module(entry_file)
    has_include = _has_include_router_call(tree)
    has_register = _has_register_all_routers_call(tree)
    if has_include and has_register:
        return FORM_MIXED
    if has_include:
        return FORM_LEGACY_INLINE
    if has_register:
        return FORM_REGISTRY
    return FORM_UNKNOWN


def _register_modes(entry_file: Path) -> List[Optional[str]]:
    """提取入口源码中 register_all_routers(...) 的 mode 参数列表。

    未显式传 mode 时按 register_all_routers 的默认值 MODE_LEGACY 处理；
    mode 参数不是字面量时返回其源码文本。
    """
    tree = _parse_module(entry_file)
    modes: List[Optional[str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
        else:
            continue
        if name != "register_all_routers":
            continue
        mode: Optional[str] = MODE_LEGACY
        for keyword in node.keywords:
            if keyword.arg != "mode":
                continue
            if isinstance(keyword.value, ast.Constant):
                mode = keyword.value.value
            else:
                mode = ast.unparse(keyword.value)
        modes.append(mode)
    return modes


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


def _table_pairs(
    modes: Iterable[str], status: str = STATUS_ACTIVE
) -> Set[Tuple[str, str]]:
    """按 mode 与 status 过滤 ROUTER_TABLE 并展开为 (模块, 属性) 集合。"""
    return _spec_pairs(
        spec for spec in ROUTER_TABLE if spec.status == status and spec.mode in modes
    )


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


# ==================== 入口侧口径 ====================


def side_modes(side: str) -> Tuple[str, ...]:
    """该侧归属的 mode 组合。"""
    return LEGACY_SIDE_MODES if side == SIDE_LEGACY else AI_EDU_SIDE_MODES


def side_table_pairs(side: str) -> Set[Tuple[str, str]]:
    """该侧表内条目（active + pending）的 (模块, 属性) 集合。"""
    modes = side_modes(side)
    return _table_pairs(modes, status=STATUS_ACTIVE) | _table_pairs(
        modes, status=STATUS_PENDING_INTEGRATION
    )


def side_expected_missing(side: str) -> Set[Tuple[str, str]]:
    """该侧「表里有、入口源码里找不到」的固定基线。"""
    if side == SIDE_LEGACY:
        return set(EXPECTED_LEGACY_MISSING)
    return set(EXPECTED_AI_EDU_MISSING)


def side_entry_mode(side: str) -> str:
    """该侧入口在 registry 形态下应使用的注册模式。"""
    return MODE_LEGACY if side == SIDE_LEGACY else MODE_LAZY


# ==================== 兼容性断言 ====================


def _assert_form_supported(entry_file: Path, form: str) -> None:
    """混合形态 / 未知形态必须直接失败。"""
    assert form != FORM_MIXED, (
        "%s 同时存在 include_router 与 register_all_routers 调用（混合形态）："
        "同一批路由会被重复注册，必须二选一。" % entry_file.name
    )
    assert form != FORM_UNKNOWN, (
        "%s 中既没有 include_router 也没有 register_all_routers 调用（未知形态）："
        "入口接线已被破坏。" % entry_file.name
    )


def _assert_registry_mode(entry_file: Path, side: str) -> None:
    """registry 形态：入口必须以该侧的注册模式调用 register_all_routers。"""
    expected_mode = side_entry_mode(side)
    modes = _register_modes(entry_file)
    assert modes, "%s 中找不到 register_all_routers 调用" % entry_file.name
    assert expected_mode in modes, "%s 的 register_all_routers 缺少 mode=%r，实际为: %r" % (
        entry_file.name,
        expected_mode,
        modes,
    )


def assert_entry_covers_table(entry_file: Path, side: str) -> None:
    """正向断言：表内条目在入口里都有对应注册。

    - legacy_inline：源码的 include_router 集合必须覆盖该侧表内条目
      （缺失项恰好等于已知缺失基线）
    - registry     ：入口必须调用 register_all_routers(mode=<该侧模式>)
    """
    form = detect_entry_form(entry_file)
    _assert_form_supported(entry_file, form)
    if form == FORM_REGISTRY:
        _assert_registry_mode(entry_file, side)
        return
    table_pairs = side_table_pairs(side)
    source_pairs = _include_router_pairs(_parse_module(entry_file))
    missing = table_pairs - source_pairs
    assert missing == side_expected_missing(
        side
    ), "%s 侧 include_router 与 ROUTER_TABLE 漂移：\n%s" % (
        side,
        _format_diff(table_pairs, source_pairs),
    )


def assert_entry_has_no_extra(entry_file: Path, side: str) -> None:
    """反向断言：入口里没有表外注册（防止有人绕过 ROUTER_TABLE）。

    - legacy_inline：源码的 include_router 集合不得超出该侧表内条目
    - registry     ：入口必须调用 register_all_routers(mode=<该侧模式>)
    """
    form = detect_entry_form(entry_file)
    _assert_form_supported(entry_file, form)
    if form == FORM_REGISTRY:
        _assert_registry_mode(entry_file, side)
        return
    table_pairs = side_table_pairs(side)
    source_pairs = _include_router_pairs(_parse_module(entry_file))
    extra = source_pairs - table_pairs
    assert not extra, "%s 存在 ROUTER_TABLE 之外的注册：\n%s" % (
        entry_file.name,
        _format_diff(set(), extra),
    )


def assert_active_set_consistent(entry_file: Path, side: str) -> None:
    """T3：active 集合与入口一致（按入口当前形态选断言口径）。

    - legacy_inline：active 集合 == 源码 include_router 集合 - 源码中出现的 pending 集合
    - registry     ：register_all_routers(mode=...) 实际会注册的 active 模块集合
      == 表内该模式下的 active 模块集合
    """
    form = detect_entry_form(entry_file)
    _assert_form_supported(entry_file, form)
    if form == FORM_REGISTRY:
        mode = side_entry_mode(side)
        selected = router_registry._select_specs(mode, None, None)
        registered = {
            spec.module_path for spec in selected if spec.status == STATUS_ACTIVE
        }
        expected = {
            spec.module_path
            for spec in ROUTER_TABLE
            if spec.status == STATUS_ACTIVE and spec.mode in MODE_SCOPE[mode]
        }
        assert (
            registered == expected
        ), "%s 在 mode=%r 下注册的 active 模块集合与 ROUTER_TABLE 漂移：\n%s" % (
            entry_file.name,
            mode,
            _format_diff(expected, registered),
        )
        return
    modes = side_modes(side)
    source_pairs = _include_router_pairs(_parse_module(entry_file))
    active = _table_pairs(modes, status=STATUS_ACTIVE)
    pending_in_source = (
        _table_pairs(modes, status=STATUS_PENDING_INTEGRATION) & source_pairs
    )
    expected = source_pairs - pending_in_source
    assert active == expected, "%s 侧 active 集合与源码不一致：\n%s" % (
        side,
        _format_diff(expected, active),
    )


def effective_source_modules(entry_file: Path, side: str) -> Set[str]:
    """入口「实际覆盖」的模块集合（按入口当前形态取源码集合或注册模式范围）。"""
    form = detect_entry_form(entry_file)
    if form == FORM_REGISTRY:
        mode = side_entry_mode(side)
        selected = router_registry._select_specs(mode, None, None)
        return {spec.module_path for spec in selected}
    return {module for module, _ in _include_router_pairs(_parse_module(entry_file))}


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


# ==================== T1 / T2：入口源码一致性 ====================


class TestEntrySourceParity:
    """T1/T2：ROUTER_TABLE 与两个入口源码的双向一致性（兼容两种入口形态）。"""

    def test_t1_legacy_routes_matches_table(self):
        """T1：legacy 侧，表内条目在 legacy_routes.py 中都能找到对应注册。"""
        assert_entry_covers_table(LEGACY_ROUTES_FILE, SIDE_LEGACY)

    def test_t1_legacy_routes_has_no_extra_modules(self):
        """T1 反向：legacy_routes.py 里没有表外模块（防止有人绕过 ROUTER_TABLE）。"""
        assert_entry_has_no_extra(LEGACY_ROUTES_FILE, SIDE_LEGACY)

    def test_t2_main_ai_edu_matches_table(self):
        """T2：main_ai_edu 侧，表内条目在 main_ai_edu.py 中都能找到对应注册。"""
        assert_entry_covers_table(AI_EDU_MAIN_FILE, SIDE_AI_EDU)

    def test_t2_main_ai_edu_has_no_extra_modules(self):
        """T2 反向：main_ai_edu.py 里没有表外模块（防止有人绕过 ROUTER_TABLE）。"""
        assert_entry_has_no_extra(AI_EDU_MAIN_FILE, SIDE_AI_EDU)

    def test_legacy_side_covers_52_modules(self, legacy_pairs):
        """legacy 侧口径：52 个模块（52 + 19 - 10 = 61）。"""
        table_modules = {
            spec.module_path for spec in ROUTER_TABLE if spec.mode in LEGACY_SIDE_MODES
        }
        assert len(table_modules) == 52

    def test_aiedu_side_covers_19_modules(self, aiedu_pairs):
        """main_ai_edu 侧口径：19 个模块。"""
        table_modules = {
            spec.module_path for spec in ROUTER_TABLE if spec.mode in AI_EDU_SIDE_MODES
        }
        assert len(table_modules) == 19


# ==================== T3：parity 三方一致 ====================


class TestParitySets:
    """T3：active 集合与入口一致（兼容两种入口形态）。"""

    def test_t3_active_legacy_set_equals_source_minus_pending(self):
        """T3：legacy 侧 active 集合 = 源码集合 - 源码中出现的 pending 集合。"""
        assert_active_set_consistent(LEGACY_ROUTES_FILE, SIDE_LEGACY)

    def test_t3_active_aiedu_set_equals_source_minus_pending(self):
        """T3：main_ai_edu 侧 active 集合 = 源码集合 - 源码中出现的 pending 集合。"""
        assert_active_set_consistent(AI_EDU_MAIN_FILE, SIDE_AI_EDU)

    def test_t3_union_of_sources_covers_table(self):
        """T3 全局：两侧入口覆盖的模块并集 + 模块未入库白名单 == ROUTER_TABLE 的 61 个模块。"""
        table_modules = {spec.module_path for spec in ROUTER_TABLE}
        source_modules = effective_source_modules(
            LEGACY_ROUTES_FILE, SIDE_LEGACY
        ) | effective_source_modules(AI_EDU_MAIN_FILE, SIDE_AI_EDU)
        assert len(table_modules) == 61
        assert (
            source_modules | set(PENDING_MODULE_MISSING) == table_modules
        ), "两侧入口覆盖的模块并集与 ROUTER_TABLE 漂移：\n" + _format_diff(
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
        """白名单恰好 3 项。"""
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
