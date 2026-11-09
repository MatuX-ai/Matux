"""路由契约快照测试（PR-C1 —— parity 重设计第一步）。

背景
----
PR-B commit 3（PR #28）落地的 ``test_router_parity.py`` 以「入口源码里的
``include_router`` 调用列表」为断言对象。该对象在 PR-B commit 4 把三个入口
收敛到 ``register_all_routers`` 之后即失效 —— 源码里不再有 include_router 列表，
「表 ↔ 源码」这类静态断言随之失去意义。

因此 PR-C1 引入**行为层**的断言对象：入口实际暴露的 ``(method, path)`` 集合。
这一断言对象与入口的实现方式解耦：无论入口是手写 include_router 还是
``register_all_routers``，只要对外暴露的路径不变，契约就不算漂移。

三个层次
--------
======  ==============================================  ==========================
编号    层级                                            CI
======  ==============================================  ==========================
T10     单元层：mock app + register_all_routers 的        默认执行
        注册路径集 == 基线
T8      集成层：真实启动入口后的路径集 == 基线           ``-m "not integration"``
                                                     跳过
T4      入口接线：AST 断言入口已改用                    默认执行
        ``register_all_routers``
======  ==============================================  ==========================

基线来源
--------
基线由 **origin/main 的 backend/ 快照**（``git archive`` 导出，纯 LF）真实启动
三个入口采集而成，**不使用工作区文件** —— 工作区文件可能带 CRLF，且叠加了
2357 项未提交 WIP，两者都会让基线失真。

口径
----
* **只断言 ``(method, path)``，不断言 ``tags``**。tags 是 OpenAPI 的展示用
  元数据，不是功能契约；历史累积的 6 处 tags 漂移属于 commit 4 的清理范围，
  不应在纯新增测试的 PR 里顺手修改。
* **pending_integration 条目的路径单独记账**。``register_all_routers``
  按设计跳过它们（``status="pending_integration"``），因此：

      真实入口路径集  ==  基线路径集 ∪ 该入口的 pending 路径

  基线本身只含「当前实际生效」的路径（pending 路径被剔除），
  ``pending.json`` 记录 pending 条目的全部路径，供 T8 反算。
* **条件开关按基线生成时的取值固定**（4 个 ``ENABLE_*_*_ROUTES`` 默认关闭），
  测试内显式覆写，避免本机 ``.env`` 影响判定。
* **三组互斥**。``ROUTER_TABLE`` 的 ``mode`` 把条目分为 both / lazy / legacy
  三组，三组的路径集互不相交，因此：

      入口等价路径集(main_ai_edu) == both ∪ lazy
      入口等价路径集(main_legacy) == both ∪ legacy
      两者交集                  == both

用法::

    cd backend && pytest tests/test_router_contract_snapshot.py -v
    cd backend && pytest tests/test_router_contract_snapshot.py -v -m integration
"""

import ast
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Dict, List, Set, Tuple

import pytest

# 确保 backend 目录在 sys.path 中（pytest.ini 的 pythonpath = . 已覆盖，
# 这里保留兜底以便从任意目录直接调用 pytest）
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

BACKEND_DIR = Path(_BACKEND_DIR)
BASELINE_DIR = Path(__file__).resolve().parent / "parity_baseline"

#: 基线文件名 -> 入口标识
BASELINE_FILES = {
    "main_ai_edu": "main-ai-edu.json",
    "main_legacy": "main-legacy.json",
    "main_lazy": "main-lazy.json",
}

#: pending_integration 条目的路径集文件名
PENDING_FILE = "pending.json"

PathPair = Tuple[str, str]


# ==================== 子进程采集脚本 ====================
#
# 采集必须在独立进程中完成：
# 1. 真实导入 50+ 个路由模块会污染 pytest 进程的 sys.modules；
# 2. 入口模块（main / main_ai_edu）是「一次性」的，import 副作用不可逆；
# 3. 入口通过环境变量 ENABLE_LAZY_LOADING 切换分支，同进程内无法切换。
#
# 未入库模块以 sys.modules 注入 stub（不落盘），与基线生成时的口径保持一致：
#   services.ai_teacher_live_settings / services.ai_teacher_event_bus
#   / cache.ai_teacher_persistence（均为 issue #26 的未入库依赖）

_STUB_AND_PATCH = r'''
import sys
import types


def _install_stubs():
    live = types.ModuleType("services.ai_teacher_live_settings")

    class _LiveSettings:
        def get_settings(self, user_id):
            return None

        def update_settings(self, user_id, payload):
            return None

    live.ai_teacher_live_settings = _LiveSettings()
    sys.modules["services.ai_teacher_live_settings"] = live

    bus = types.ModuleType("services.ai_teacher_event_bus")

    class _LiveBus:
        def publish(self, *args, **kwargs):
            return None

        async def publish_async(self, *args, **kwargs):
            return None

    bus.ai_teacher_live_bus = _LiveBus()
    sys.modules["services.ai_teacher_event_bus"] = bus

    persist = types.ModuleType("cache.ai_teacher_persistence")

    class _Repo:
        def get(self, key):
            return None

        def set(self, key, value):
            return None

        def clear(self):
            return None

    def _repo_factory():
        return _Repo()

    for _name in (
        "get_memories_repo",
        "get_personas_repo",
        "get_profiles_repo",
        "get_sessions_repo",
        "get_live_settings_repo",
        "get_event_history_repo",
        "get_user_history_repo",
        "flush_all_repos",
        "reset_all_repos_for_testing",
        "register_persistence_hooks",
    ):
        setattr(persist, _name, _repo_factory)

    class _Profile:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    persist.AITeacherProfile = _Profile

    if "cache" not in sys.modules:
        cache_pkg = types.ModuleType("cache")
        cache_pkg.__path__ = []
        sys.modules["cache"] = cache_pkg
    sys.modules["cache.ai_teacher_persistence"] = persist


def _patch_include_router():
    """patch FastAPI.include_router，记录每次注册带来的 (method, path)。"""
    import fastapi

    collected = []
    original = fastapi.FastAPI.include_router

    def patched(self, router, **kwargs):
        before = {id(r) for r in self.routes}
        result = original(self, router, **kwargs)
        for route in self.routes:
            if id(route) in before:
                continue
            path = getattr(route, "path", None)
            if path is None:
                continue
            methods = getattr(route, "methods", None)
            for method in sorted(methods) if methods else ["WEBSOCKET"]:
                collected.append((method, path))
        return result

    fastapi.FastAPI.include_router = patched
    return collected
'''

#: 采集 register_all_routers 在各 mode / 各分组下的注册路径集（单元层 / T10 用）
_COLLECT_REGISTRY_SCRIPT = (
    _STUB_AND_PATCH
    + r"""
import json
import pathlib
import sys
import tempfile

_install_stubs()
collected = _patch_include_router()

from fastapi import FastAPI

from core import router_registry
from core.router_registry import (
    MODE_LAZY,
    MODE_LEGACY,
    ROUTER_TABLE,
    register_all_routers,
)

# 报告与失败计数写到一次性目录：避免污染 backend/logs，
# 也避免跨进程失败计数触发 L2 熔断而影响重复运行
router_registry.LOG_DIR = pathlib.Path(tempfile.mkdtemp())

lazy_names = [spec.name for spec in ROUTER_TABLE if spec.mode == MODE_LAZY]
group_names = {
    "both": [s.name for s in ROUTER_TABLE if s.mode == "both"],
    "lazy": list(lazy_names),
    "legacy": [s.name for s in ROUTER_TABLE if s.mode == MODE_LEGACY],
}


def _snapshot():
    return sorted({tuple(item) for item in collected})


result = {}

for key, names in group_names.items():
    collected.clear()
    register_all_routers(FastAPI(), mode=MODE_LEGACY, only=names)
    result[key] = [list(item) for item in _snapshot()]

collected.clear()
register_all_routers(FastAPI(), mode=MODE_LAZY)
result["entry_lazy"] = [list(item) for item in _snapshot()]

collected.clear()
register_all_routers(FastAPI(), mode=MODE_LEGACY, exclude=lazy_names)
result["entry_legacy"] = [list(item) for item in _snapshot()]

sys.stdout.write("<<<RESULT>>>" + json.dumps(result))
"""
)

#: 真实启动入口并采集其注册路径集（集成层 / T8 用）
_COLLECT_ENTRY_SCRIPT = (
    _STUB_AND_PATCH
    + r"""
import asyncio
import json
import os
import sys

_install_stubs()
collected = _patch_include_router()

entry = sys.argv[1]

if entry == "main_ai_edu":
    import main_ai_edu
elif entry == "main_legacy":
    os.environ["ENABLE_LAZY_LOADING"] = "false"
    import main
elif entry == "main_lazy":
    os.environ["ENABLE_LAZY_LOADING"] = "true"
    import main

    async def _run_lifespan():
        try:
            async with main.app.router.lifespan_context(main.app):
                pass
        except Exception as exc:  # noqa: BLE001 - DB 不可用时保留已注册路径
            print("LIFESPAN_ERROR: %s" % exc, file=sys.stderr)

    asyncio.run(_run_lifespan())
else:
    raise SystemExit("未知入口: %s" % entry)

snapshot = sorted({tuple(item) for item in collected})
sys.stdout.write("<<<RESULT>>>" + json.dumps([list(i) for i in snapshot]))
"""
)

_RESULT_MARKER = "<<<RESULT>>>"


# ==================== 工具函数 ====================


def _run_script(script: str, args: List[str]) -> str:
    """在独立进程中执行采集脚本，返回标记后的 JSON 负载。

    独立进程保证：入口模块的 import 副作用不污染 pytest 进程，
    且 ENABLE_LAZY_LOADING 等环境变量可在 import 前设定。
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(BACKEND_DIR)
    env.setdefault("PYTHONIOENCODING", "utf-8")

    completed = subprocess.run(
        [sys.executable, "-c", script, *args],
        cwd=str(BACKEND_DIR),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    stdout = completed.stdout or ""
    if _RESULT_MARKER not in stdout:
        raise AssertionError(
            "采集脚本未产出结果（exit=%s）\n--- stdout ---\n%s\n--- stderr ---\n%s"
            % (completed.returncode, stdout[-4000:], (completed.stderr or "")[-4000:])
        )
    return stdout.split(_RESULT_MARKER, 1)[1].strip()


def _load_baseline(entry: str) -> Dict[str, object]:
    """读取入口对应的基线文件。"""
    path = BASELINE_DIR / BASELINE_FILES[entry]
    assert path.is_file(), "基线文件缺失: %s" % path
    return json.loads(path.read_text(encoding="utf-8"))


def _as_pairs(items) -> Set[PathPair]:
    """[[method, path], ...] -> {(method, path), ...}"""
    return {(method, path) for method, path in items}


def _baseline_pairs(entry: str) -> Set[PathPair]:
    """基线中的 (method, path) 集合。"""
    return _as_pairs(_load_baseline(entry)["paths"])


def _pending_pairs() -> Set[PathPair]:
    """pending_integration 条目的 (method, path) 集合。"""
    path = BASELINE_DIR / PENDING_FILE
    assert path.is_file(), "pending 基线文件缺失: %s" % path
    return _as_pairs(json.loads(path.read_text(encoding="utf-8"))["paths"])


def _format_diff(expected: Set[PathPair], actual: Set[PathPair]) -> str:
    """生成可读的差异说明：基线有而实际没有 / 实际有而基线没有。"""
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    lines: List[str] = []
    if missing:
        lines.append(
            "基线有而实际没有（%d 条）:\n  " % len(missing)
            + "\n  ".join("%s %s" % item for item in missing)
        )
    if extra:
        lines.append(
            "实际有而基线没有（%d 条）:\n  " % len(extra)
            + "\n  ".join("%s %s" % item for item in extra)
        )
    return "\n".join(lines) if lines else "无差异"


def _find_register_calls(tree: ast.Module) -> List[object]:
    """在 AST 中查找 register_all_routers(...) 调用的 mode 参数。"""
    modes: List[object] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Name) or func.id != "register_all_routers":
            continue
        mode: object = None
        for keyword in node.keywords:
            if keyword.arg != "mode":
                continue
            if isinstance(keyword.value, ast.Constant):
                mode = keyword.value.value
            else:
                mode = ast.unparse(keyword.value)
        modes.append(mode)
    return modes


def _group_names(mode: str) -> List[str]:
    """ROUTER_TABLE 中归属指定 mode 的条目名。"""
    from core.router_registry import ROUTER_TABLE

    return [spec.name for spec in ROUTER_TABLE if spec.mode == mode]


# ==================== fixtures ====================


@pytest.fixture(scope="module")
def registry_paths() -> Dict[str, Set[PathPair]]:
    """register_all_routers 在各 mode / 各分组下注册的 (method, path) 集合。

    采集在独立进程中完成（真实导入 50+ 路由模块，避免污染 pytest 进程）。
    """
    raw = json.loads(_run_script(_COLLECT_REGISTRY_SCRIPT, []))
    return {key: _as_pairs(value) for key, value in raw.items()}


@pytest.fixture(scope="module")
def entry_paths() -> Dict[str, Set[PathPair]]:
    """三个真实入口启动后的 (method, path) 集合。"""
    result: Dict[str, Set[PathPair]] = {}
    for entry in BASELINE_FILES:
        payload = _run_script(_COLLECT_ENTRY_SCRIPT, [entry])
        result[entry] = _as_pairs(json.loads(payload))
    return result


# ==================== T10：单元层快照契约 ====================


class TestContractSnapshot:
    """T10：register_all_routers 的注册路径集必须与基线完全一致。"""

    def test_t10_main_ai_edu_paths_match_baseline(self, registry_paths):
        """T10：main_ai_edu 入口基线 vs register_all_routers(mode=lazy)。"""
        baseline = _baseline_pairs("main_ai_edu")
        actual = registry_paths["entry_lazy"]
        assert actual == baseline, "main_ai_edu 路径契约漂移：\n" + _format_diff(
            baseline, actual
        )

    def test_t10_main_legacy_paths_match_baseline(self, registry_paths):
        """T10：main_legacy 入口基线 vs register_all_routers(mode=legacy)。"""
        baseline = _baseline_pairs("main_legacy")
        actual = registry_paths["entry_legacy"]
        assert actual == baseline, "main_legacy 路径契约漂移：\n" + _format_diff(
            baseline, actual
        )

    def test_t10_baseline_is_union_of_mode_groups(self):
        """T10：基线 == 对应 mode 分组的并集（both ∪ lazy / both ∪ legacy）。"""
        expectations = {
            "main_ai_edu": ("both", "lazy"),
            "main_legacy": ("both", "legacy"),
        }
        for entry, groups in expectations.items():
            data = _load_baseline(entry)
            by_group = data["paths_by_group"]
            union: Set[PathPair] = set()
            for group in groups:
                union |= _as_pairs(by_group[group])
            baseline = _as_pairs(data["paths"])
            assert union == baseline, "%s 基线与 mode 分组并集不一致：\n" % entry + (
                _format_diff(baseline, union)
            )

    def test_t10_mode_groups_are_disjoint(self, registry_paths):
        """T10：both / lazy / legacy 三组的路径集互不相交。

        这是「入口等价路径集 = both ∪ lazy / both ∪ legacy」成立的前提：
        交集必须精确等于 both 组。
        """
        both = registry_paths["both"]
        lazy = registry_paths["lazy"]
        legacy = registry_paths["legacy"]
        assert not (both & lazy), "both 与 lazy 组存在重叠路径"
        assert not (both & legacy), "both 与 legacy 组存在重叠路径"
        assert not (lazy & legacy), "lazy 与 legacy 组存在重叠路径"

    def test_t10_entry_intersection_equals_both_group(self, registry_paths):
        """T10：两个入口等价路径集的交集 == both 组路径集。"""
        intersection = registry_paths["entry_lazy"] & registry_paths["entry_legacy"]
        both = registry_paths["both"]
        assert intersection == both, "两个入口的交集与 both 组不一致：\n" + _format_diff(
            both, intersection
        )

    def test_t10_baseline_metadata_is_consistent(self):
        """T10：基线文件自身的元数据自洽（total 与 paths 长度一致）。"""
        for entry in BASELINE_FILES:
            data = _load_baseline(entry)
            assert data["total"] == len(data["paths"]), (
                "%s 基线的 total 字段与实际路径数不一致" % entry
            )
            assert data["entry"] == entry
            assert data["real_total"] >= data["total"], (
                "%s 基线的 real_total 不应小于 total" % entry
            )

    def test_t10_pending_paths_are_not_in_baseline(self):
        """T10：pending_integration 条目的独占路径不得出现在基线里。

        register_all_routers 会跳过 pending 条目；若基线仍含其独占路径，
        T10 会在 PR-C2 落地后立刻失败。
        """
        pending = _pending_pairs()
        assert pending, "pending 路径集为空，与 issue #26 的记录不符"
        for entry in BASELINE_FILES:
            data = _load_baseline(entry)
            baseline = _as_pairs(data["paths"])
            overlap = pending & baseline
            # 允许 pending 路径与 active 条目路径重合（同一路由被两个模块提供），
            # 但基线必须保证 pending 条目「独占」的路径不在其中
            assert not (
                overlap - set(map(tuple, data["pending_paths"]))
            ), "%s 基线含 pending 条目独占路径：\n" % entry + _format_diff(
                set(), overlap - set(map(tuple, data["pending_paths"]))
            )


# ==================== T8：集成层端到端契约 ====================


@pytest.mark.integration
class TestEntryIntegration:
    """T8：真实启动入口后的路径集必须与基线一致。

    标记为 integration，CI 以 ``-m "not integration"`` 跳过。

    口径：真实入口会注册 pending 条目（只要模块可导入），而 register_all_routers
    会跳过它们，因此：

        真实入口路径集 == 基线路径集 ∪ 该入口的 pending 路径
    """

    def _assert_entry_matches(self, entry: str, actual: Set[PathPair]) -> None:
        data = _load_baseline(entry)
        baseline = _as_pairs(data["paths"])
        pending_paths = _as_pairs(data["pending_paths"])
        expected = baseline | pending_paths
        assert actual == expected, "%s 入口路径漂移：\n" % entry + _format_diff(
            expected, actual
        )

    def test_t8_main_ai_edu_entry_paths_match_baseline(self, entry_paths):
        """T8：main_ai_edu 入口真实启动后的路径集 == 基线 + pending。"""
        self._assert_entry_matches("main_ai_edu", entry_paths["main_ai_edu"])

    def test_t8_main_legacy_entry_paths_match_baseline(self, entry_paths):
        """T8：main_legacy 入口真实启动后的路径集 == 基线 + pending。"""
        self._assert_entry_matches("main_legacy", entry_paths["main_legacy"])

    def test_t8_main_lazy_entry_paths_match_baseline(self, entry_paths):
        """T8：main_lazy 入口真实启动后的路径集 == 基线。

        lazy 模式由 LazyLoader 按 Tier 渐进激活，路径集小于 register_all_routers
        的注册结果，属预期。
        """
        self._assert_entry_matches("main_lazy", entry_paths["main_lazy"])


# ==================== T4：入口接线断言 ====================


class TestEntryWiring:
    """T4：入口必须通过 register_all_routers 接线（替代旧的「源码 include_router 列表」断言）。"""

    def test_t4_main_ai_edu_uses_register_all_routers(self):
        """T4：main_ai_edu.py 必须调用 register_all_routers(mode=...)。"""
        source = (BACKEND_DIR / "main_ai_edu.py").read_text(encoding="utf-8")
        tree = ast.parse(source, filename="main_ai_edu.py")
        modes = _find_register_calls(tree)
        assert modes, "main_ai_edu.py 中找不到 register_all_routers 调用"
        assert "lazy" in modes, (
            'main_ai_edu.py 的 register_all_routers 缺少 mode="lazy"，实际为: %r' % modes
        )

    def test_t4_main_uses_register_all_routers(self):
        """T4：main.py 必须调用 register_all_routers(mode=...)。"""
        source = (BACKEND_DIR / "main.py").read_text(encoding="utf-8")
        tree = ast.parse(source, filename="main.py")
        modes = _find_register_calls(tree)
        assert modes, "main.py 中找不到 register_all_routers 调用"
        assert {"lazy", "legacy"} & set(modes), (
            "main.py 的 register_all_routers 缺少 mode 参数，实际为: %r" % modes
        )
