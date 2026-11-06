"""core/router_registry.py 单元测试（PR-B commit 1）。

覆盖范围：
- ROUTER_TABLE 静态表结构约束（61 条 / 2 条白名单 / 唯一性 / 合法性）
- register_all_routers 正常路径（mock app 记录 include_router 调用）
- 三级失败策略：L0 致命 / L1 降级 / L2 熔断
- 条件开关与白名单的跳过语义
- 注册报告落盘格式

真实导入校验标记为 integration：CI 单测以 `-m "not integration"` 运行，
不在默认集内。
"""

import importlib
import json
import logging
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

from core import router_registry
from core.router_registry import (
    MODE_LAZY,
    MODE_LEGACY,
    ROUTER_TABLE,
    STATUS_ACTIVE,
    STATUS_PENDING_INTEGRATION,
    RouterRegistrationError,
    RouterSpec,
    active_specs,
    pending_integration_modules,
    register_all_routers,
    specs_by_name,
)
import pytest

# 确保 backend 目录在 sys.path 中
_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, os.path.abspath(_backend_dir))


# ==================== 测试替身 ====================


class MockApp:
    """最小 FastAPI 替身：只记录 include_router 调用。"""

    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def include_router(
        self,
        router: Any,
        prefix: str = "",
        tags: Optional[List[str]] = None,
    ) -> None:
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


# ==================== fixtures ====================


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
    """把真实 import 替换为返回可辨识字符串的假实现。"""

    def _fake(spec: RouterSpec, attr: str) -> str:
        return f"{spec.module_path}.{attr}"

    monkeypatch.setattr(router_registry, "_import_router", _fake)
    return _fake


@pytest.fixture
def conditions_on(monkeypatch):
    """条件路由全部视为已启用。"""
    monkeypatch.setattr(router_registry, "_condition_enabled", lambda key: True)
    return True


# ==================== 静态表结构 ====================


class TestRouterTable:
    """ROUTER_TABLE 静态表结构约束。"""

    def test_table_size_is_61(self):
        """总表必须是 61 条（issue #21 的并集口径）。"""
        assert len(ROUTER_TABLE) == 61

    def test_pending_integration_count_is_2(self):
        """白名单恰好 2 项（issue #26 拍板）。"""
        pending = [
            spec for spec in ROUTER_TABLE if spec.status == STATUS_PENDING_INTEGRATION
        ]
        assert len(pending) == 2

    def test_active_count_is_59(self):
        """其余 59 项为 active。"""
        assert len(active_specs()) == 59

    def test_names_are_unique(self):
        names = [spec.name for spec in ROUTER_TABLE]
        assert len(set(names)) == len(names)

    def test_module_paths_are_unique(self):
        paths = [spec.module_path for spec in ROUTER_TABLE]
        assert len(set(paths)) == len(paths)

    def test_keys_are_unique(self):
        keys = [spec.key for spec in ROUTER_TABLE]
        assert len(set(keys)) == len(keys)

    def test_whitelist_matches_issue26(self):
        """白名单内容与 issue #26 的拍板完全一致。"""
        assert set(pending_integration_modules()) == {
            "routes.ai_teacher_routes",
            "routes.ai_edu_websocket_routes",
        }

    def test_pending_specs_carry_note(self):
        """白名单条目必须写明跳过原因，便于排查。"""
        for spec in ROUTER_TABLE:
            if spec.is_pending_integration:
                assert spec.note, f"{spec.name} 缺少 note 说明"

    def test_all_specs_have_valid_status_and_mode(self):
        for spec in ROUTER_TABLE:
            assert spec.status in router_registry.STATUS_VALUES
            assert spec.mode in router_registry.MODE_VALUES
            assert spec.router_attr

    def test_share_routes_uses_per_attr_tags(self):
        """share_routes 一条携带两个 router，标签必须逐 attr 区分。"""
        share = specs_by_name()["share"]
        assert share.router_attr == ("api_router", "page_router")
        assert len(share.attr_tags) == 2
        assert share.attr_tags[0] != share.attr_tags[1]

    def test_condition_keys_are_known_settings(self):
        """条件开关键必须是 settings 中真实存在的 4 个。"""
        expected = {
            "ENABLE_AR_VR_ROUTES",
            "ENABLE_AR_VR_MOCK_ROUTES",
            "ENABLE_DIGITAL_TWIN_ROUTES",
            "ENABLE_MODEL_UPDATE_ROUTES",
        }
        actual = {spec.condition_key for spec in ROUTER_TABLE if spec.condition_key}
        assert actual == expected

    def test_specs_by_name_covers_all(self):
        mapping = specs_by_name()
        assert len(mapping) == 61
        assert mapping["auth"].module_path == "routes.auth_routes"


# ==================== 正常注册路径 ====================


class TestRegisterAllRouters:
    """register_all_routers 的正常注册与过滤语义。"""

    def test_registers_every_active_spec(
        self, mock_app, stub_import, isolated_logs, conditions_on
    ):
        report = register_all_routers(mock_app)

        assert report.total == 61
        assert len(report.succeeded) == 59
        assert not report.failed
        assert not report.disabled
        # share_routes 贡献 2 个 router 对象 -> 60 次 include_router
        assert len(mock_app.calls) == 60

    def test_pending_specs_are_skipped_with_warning(
        self, mock_app, stub_import, isolated_logs, conditions_on, caplog
    ):
        with caplog.at_level(logging.WARNING, logger="core.router_registry"):
            report = register_all_routers(mock_app)

        assert len(report.skipped) == 2
        skipped_modules = {item["module"] for item in report.skipped}
        assert skipped_modules == set(pending_integration_modules())
        assert "待集成" in caplog.text
        # 白名单模块不得被注册
        assert "routes.ai_teacher_routes" not in mock_app.modules()
        assert "routes.ai_edu_websocket_routes" not in mock_app.modules()

    def test_condition_disabled_is_skipped(
        self, mock_app, stub_import, isolated_logs, monkeypatch
    ):
        monkeypatch.setattr(router_registry, "_condition_enabled", lambda key: False)

        report = register_all_routers(mock_app)

        # 2 条白名单 + 4 条条件未启用
        assert len(report.skipped) == 6
        reasons = {item["reason"] for item in report.skipped}
        assert any(reason.endswith("=False") for reason in reasons)

    def test_only_filter_limits_registration(
        self, mock_app, stub_import, isolated_logs, conditions_on
    ):
        report = register_all_routers(mock_app, only=["auth", "exam"])

        assert report.total == 2
        assert len(mock_app.calls) == 2
        assert set(mock_app.modules()) == {"routes.auth_routes", "routes.exam_routes"}

    def test_exclude_filter_skips_specs(
        self, mock_app, stub_import, isolated_logs, conditions_on
    ):
        report = register_all_routers(mock_app, exclude=["auth"])

        assert "routes.auth_routes" not in mock_app.modules()
        assert len(report.succeeded) == 58

    def test_lazy_mode_only_registers_lazy_and_both(
        self, mock_app, stub_import, isolated_logs, conditions_on
    ):
        report = register_all_routers(mock_app, mode=MODE_LAZY)

        expected = [spec for spec in ROUTER_TABLE if spec.mode in ("lazy", "both")]
        assert report.total == len(expected)
        for spec in expected:
            if spec.status == STATUS_ACTIVE:
                assert spec.module_path in mock_app.modules()

    def test_invalid_mode_raises_value_error(self, mock_app):
        with pytest.raises(ValueError):
            register_all_routers(mock_app, mode="unknown")


# ==================== 三级失败策略 ====================


class TestFailureStrategy:
    """L0 致命 / L1 降级 / L2 熔断。"""

    def test_l1_failure_is_isolated_and_others_continue(
        self, mock_app, isolated_logs, monkeypatch, caplog
    ):
        """L1 降级：单模块失败只记录，不影响其余条目。"""

        def _fake(spec: RouterSpec, attr: str) -> str:
            if spec.module_path == "routes.ai_routes":
                raise ImportError("boom")
            return f"{spec.module_path}.{attr}"

        monkeypatch.setattr(router_registry, "_import_router", _fake)
        monkeypatch.setattr(router_registry, "_condition_enabled", lambda key: True)

        with caplog.at_level(logging.ERROR, logger="core.router_registry"):
            report = register_all_routers(mock_app)

        assert len(report.failed) == 1
        assert report.failed[0]["module"] == "routes.ai_routes"
        assert "ImportError" in report.failed[0]["error"]
        # 其余条目照常注册
        assert len(report.succeeded) == 58
        assert "路由注册失败" in caplog.text

    def test_l1_failure_counter_is_persisted(
        self, mock_app, isolated_logs, monkeypatch
    ):
        """失败计数落盘，供 L2 熔断跨进程判定。"""

        def _fake(spec: RouterSpec, attr: str) -> str:
            if spec.module_path == "routes.ai_routes":
                raise ImportError("boom")
            return f"{spec.module_path}.{attr}"

        monkeypatch.setattr(router_registry, "_import_router", _fake)
        monkeypatch.setattr(router_registry, "_condition_enabled", lambda key: True)

        register_all_routers(mock_app)

        counters_path = isolated_logs / router_registry.FAILURE_COUNTER_FILENAME
        counters = json.loads(counters_path.read_text(encoding="utf-8"))
        assert counters["routes.ai_routes:router"] == 1

    def test_l0_strict_raises_with_full_failure_list(
        self, mock_app, isolated_logs, monkeypatch
    ):
        """L0 致命：strict=True 时收集完全部失败再抛。"""

        def _fake(spec: RouterSpec, attr: str) -> str:
            if spec.module_path in ("routes.ai_routes", "routes.exam_routes"):
                raise ImportError("boom")
            return f"{spec.module_path}.{attr}"

        monkeypatch.setattr(router_registry, "_import_router", _fake)
        monkeypatch.setattr(router_registry, "_condition_enabled", lambda key: True)

        with pytest.raises(RouterRegistrationError) as excinfo:
            register_all_routers(mock_app, strict=True)

        failed_modules = {item["module"] for item in excinfo.value.failures}
        assert failed_modules == {"routes.ai_routes", "routes.exam_routes"}
        assert "路由注册失败" in str(excinfo.value)

    def test_error_carries_failure_list_and_mode(self):
        """异常实例携带失败清单与 mode（from_failures 工厂）。"""
        error = RouterRegistrationError.from_failures(
            [{"module": "routes.ai_routes", "error": "ImportError: boom"}],
            mode=MODE_LAZY,
        )
        assert error.mode == MODE_LAZY
        assert error.failures[0]["module"] == "routes.ai_routes"
        assert "routes.ai_routes" in str(error)

    def test_l2_circuit_breaker_disables_failing_module(
        self, mock_app, isolated_logs, monkeypatch
    ):
        """L2 熔断：连续失败达阈值后直接跳过该模块。"""
        counters_path = isolated_logs / router_registry.FAILURE_COUNTER_FILENAME
        counters_path.write_text(
            json.dumps(
                {"routes.ai_routes:router": (router_registry.CIRCUIT_BREAKER_THRESHOLD)}
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            router_registry,
            "_import_router",
            lambda spec, attr: f"{spec.module_path}.{attr}",
        )
        monkeypatch.setattr(router_registry, "_condition_enabled", lambda key: True)

        report = register_all_routers(mock_app)

        assert len(report.disabled) == 1
        assert report.disabled[0]["module"] == "routes.ai_routes"
        assert "routes.ai_routes" not in mock_app.modules()
        assert "routes.ai_routes:router" not in report.succeeded

    def test_report_is_written_to_disk(
        self, mock_app, stub_import, isolated_logs, conditions_on
    ):
        register_all_routers(mock_app)

        report_path = isolated_logs / router_registry.REPORT_FILENAME
        assert report_path.is_file()
        data = json.loads(report_path.read_text(encoding="utf-8"))
        assert data["mode"] == MODE_LEGACY
        assert data["total"] == 61
        assert data["succeeded"] == 59
        assert data["failed"] == []
        assert len(data["skipped"]) == 2
        assert "generated_at" in data
        assert "duration_ms" in data


# ==================== 真实导入校验（integration） ====================


def _source_file(module_path: str) -> Optional[Path]:
    """返回模块在 backend/ 下的源文件路径；不存在返回 None。"""
    parts = module_path.split(".")
    base = Path(__file__).resolve().parent.parent
    module_file = base.joinpath(*parts[:-1], f"{parts[-1]}.py")
    package_file = base.joinpath(*parts, "__init__.py")
    if module_file.is_file():
        return module_file
    if package_file.is_file():
        return package_file
    return None


@pytest.mark.integration
def test_active_specs_with_source_file_import_successfully():
    """源文件已入库的 active 条目必须能真实导入并取到 router 对象。

    判定规则不含硬编码名单：仅当模块源文件确实存在于 backend/ 下时才要求
    导入成功。尚未入库的模块（share_routes、gamification_websocket_routes）
    会被跳过 —— 它们随 WIP 提交入库后自动纳入本用例的校验范围。
    """
    checked = 0
    for spec in active_specs():
        if _source_file(spec.module_path) is None:
            continue
        checked += 1
        module = importlib.import_module(spec.module_path)
        for attr in spec.router_attr:
            assert hasattr(module, attr), f"{spec.module_path} 缺少 {attr}"
    assert checked >= 40
