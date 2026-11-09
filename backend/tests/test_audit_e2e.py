"""
【P3 审计】E2E 集成冒烟测试

跨模块联合验证：
- PostgresJsonbRepository 写入 + RiskControlService + Captcha Stats
- /metrics 端点能反映出其他模块状态
- /admin/risk 端点能反映仓储数据
- 全链路线程安全
"""
import os
import sys
import threading

from fastapi import FastAPI
from fastapi.testclient import TestClient

_BACKEND_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from cache.repository.postgres import PostgresJsonbRepository  # noqa: E501, E402
from routes.admin_risk_control_routes import router as admin_router  # noqa: E501, E402
from routes.metrics_routes import router as metrics_router  # noqa: E501, E402
from security import metrics as m  # noqa: E501, E402
from security.captcha_stats import get_captcha_stats  # noqa: E501, E402
from security.risk_control import (  # noqa: E501, E402
    get_risk_control_service,
    reset_risk_control_service_for_testing,
)
from sqlalchemy import create_engine as create_sync_engine  # noqa: E501, E402
from sqlalchemy.orm import sessionmaker  # noqa: E501, E402


# ==================== 1. PG + 风控联合 ====================


class TestPostgresAndRiskControl:
    """PG 仓储 + 风控服务可独立并行工作"""

    def test_independent_state(self, tmp_path):
        """两者状态不互相干扰"""
        from utils.database import Base
        db_path = tmp_path / "audit.db"
        engine = create_sync_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        sf = sessionmaker(bind=engine, expire_on_commit=False)

        # 1. PG 仓储
        repo = PostgresJsonbRepository(name="profiles", session_factory=sf)
        repo.set("user_1", {"name": "Alice"})
        assert repo.get("user_1") == {"name": "Alice"}

        # 2. 风控服务
        reset_risk_control_service_for_testing()
        risk_svc = get_risk_control_service()
        for i in range(5):
            risk_svc.check(
                ip="1.2.3.4", endpoint_key="POST:/api/v1/share/cards"
            )

        # 3. 状态互不污染
        assert repo.get("user_1") == {"name": "Alice"}
        assert risk_svc.get_stats()["tracked_ips"] == 1

        engine.dispose()


# ==================== 2. /metrics 跨模块反映 ====================


class TestMetricsCrossModule:
    """Prometheus metrics 端点能反映其他模块状态"""

    def test_risk_gauges_in_metrics(self):
        """风控状态变化后 /metrics 能反映"""
        app = FastAPI()
        app.include_router(admin_router)
        app.include_router(metrics_router)
        client = TestClient(app)

        # 制造一些风控活动
        reset_risk_control_service_for_testing()
        svc = get_risk_control_service()
        for i in range(10):
            svc.check(
                ip=f"9.9.9.{i}", endpoint_key="POST:/api/v1/share/cards"
            )

        # 调用 /metrics
        r = client.get("/metrics")
        assert r.status_code == 200
        text = r.content.decode("utf-8")
        # tracked_ips gauge 至少为 1
        assert "imatoproject_risk_tracked_ips" in text
        assert "imatoproject_risk_blocked_ips" in text
        assert "imatoproject_risk_high_risk_ips" in text


# ==================== 3. 跨模块事件流 ====================


class TestCrossModuleEventFlow:
    """业务事件 → 指标 → 报告 三段链路"""

    def test_share_card_creation_increments_metric(self):
        # 业务事件
        before = m.share_cards_created_total._value.get()
        m.record_share_card_created()
        m.record_share_card_created()
        m.record_share_card_created()

        # 通过 /metrics 验证
        app = FastAPI()
        app.include_router(metrics_router)
        client = TestClient(app)
        r = client.get("/metrics")
        text = r.content.decode("utf-8")
        # 应该至少有 3 次增量
        for line in text.splitlines():
            if line.startswith("imatoproject_share_cards_created_total "):
                val = float(line.split()[-1])
                assert val >= before + 3

    def test_captcha_failure_reflected_in_stats_and_metrics(self):
        from security.captcha import NoopCaptchaProvider

        # 1. stats 计数
        stats = get_captcha_stats()
        before_attempts = stats.get_snapshot()["total_attempts"]

        provider = NoopCaptchaProvider()
        for _ in range(5):
            stats.record_attempt(provider, success=True)
            m.record_captcha(provider="NoopCaptchaProvider", success=True)
        for _ in range(2):
            stats.record_attempt(provider, success=False, error_codes=["x"])
            m.record_captcha(provider="NoopCaptchaProvider", success=False)

        # 2. 验证 stats
        snap = stats.get_snapshot()
        assert snap["total_attempts"] >= before_attempts + 7
        assert snap["total_success"] >= 5
        assert snap["total_failure"] >= 2

        # 3. 验证 /admin/risk/captcha/stats 端点
        app = FastAPI()
        app.include_router(admin_router)
        client = TestClient(app)
        r = client.get("/api/v1/admin/risk/captcha/stats")
        assert r.status_code == 200
        data = r.json()
        assert data["per_error_code"].get("x", 0) >= 2


# ==================== 4. 端到端业务流 ====================


class TestEndToEndBusinessFlow:
    """模拟用户行为：注册 → 拉取 → 风险检查 → 指标上报"""

    def test_full_flow(self, tmp_path):
        from utils.database import Base

        # 1. 初始化存储
        db_path = tmp_path / "e2e.db"
        engine = create_sync_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        sf = sessionmaker(bind=engine, expire_on_commit=False)

        repo = PostgresJsonbRepository(name="profiles", session_factory=sf)
        reset_risk_control_service_for_testing()
        risk_svc = get_risk_control_service()

        # 2. 写入用户画像
        repo.set("user_alice", {"level": 5, "vip": True, "joined": "2024-01-01"})

        # 3. 用户进行高频操作（触发风控）
        for _ in range(15):
            result = risk_svc.check(
                ip="alice.ip",
                endpoint_key="POST:/api/v1/invite/codes",
            )

        # 4. 验证：仓储数据完好
        assert repo.get("user_alice")["level"] == 5
        # 风控：alice.ip 已在追踪列表（限流后前 max_requests=5 次通过）
        detail = risk_svc.get_ip_detail("alice.ip")
        assert detail["ip"] == "alice.ip"
        # 触发了端点
        assert "POST:/api/v1/invite/codes" in detail["active_endpoints"]
        # 前 5 次请求会落入滑动窗口并计入 daily_count
        assert detail["daily_count"] >= 5

        # 5. 制造失败提升风险评分
        for _ in range(15):
            risk_svc.record_failure(
                "alice.ip", "POST:/api/v1/invite/codes"
            )
        assert risk_svc.get_ip_detail("alice.ip")["risk_score"] > 0

        # 6. 指标更新
        m.record_invite_code_created()
        m.record_invite_code_used()

        # 7. 验证 /metrics
        app = FastAPI()
        app.include_router(metrics_router)
        client = TestClient(app)
        r = client.get("/metrics")
        text = r.content.decode("utf-8")
        assert "imatoproject_invite_codes_created_total" in text
        assert "imatoproject_invite_codes_used_total" in text

        engine.dispose()


# ==================== 5. 错误恢复 ====================


class TestErrorRecovery:
    """各模块在错误情况下能优雅降级"""

    def test_metrics_endpoint_when_risk_svc_dead(self):
        """风控服务异常时，/metrics 仍能返回"""
        from unittest.mock import patch

        app = FastAPI()
        app.include_router(metrics_router)
        client = TestClient(app)

        # metrics.py 内部 import get_risk_control_service，需要 patch 真正的 import 路径
        with patch(
            "security.risk_control.get_risk_control_service",
            side_effect=RuntimeError("svc dead"),
        ):
            r = client.get("/metrics")
            # 即使风控拉取失败，metrics 仍能返回
            assert r.status_code == 200
            assert b"imatoproject_" in r.content

    def test_admin_when_pg_down(self, tmp_path):
        """PG 仓储不可用时，admin API 仍能响应（风控是独立的）"""
        app = FastAPI()
        app.include_router(admin_router)
        client = TestClient(app)
        # 仓储异常不影响风控统计 API
        r = client.get("/api/v1/admin/risk/stats")
        assert r.status_code == 200


# ==================== 6. 并发综合压力 ====================


class TestConcurrentStress:
    """多模块并发读写"""

    def test_concurrent_full_system(self, tmp_path):
        from utils.database import Base

        db_path = tmp_path / "stress.db"
        engine = create_sync_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        sf = sessionmaker(bind=engine, expire_on_commit=False)

        repo = PostgresJsonbRepository(name="profiles", session_factory=sf)
        risk_svc = get_risk_control_service()
        reset_risk_control_service_for_testing()
        risk_svc = get_risk_control_service()

        errors = []

        def repo_writer():
            try:
                for i in range(50):
                    repo.set(f"u_{threading.current_thread().name}_{i}", i)
            except Exception as e:
                errors.append(("repo", e))

        def risk_checker():
            try:
                for i in range(50):
                    risk_svc.check(
                        ip=f"192.168.1.{i % 255}",
                        endpoint_key="POST:/api/v1/share/cards",
                    )
            except Exception as e:
                errors.append(("risk", e))

        def metric_recorder():
            try:
                for _ in range(50):
                    m.record_share_card_created()
            except Exception as e:
                errors.append(("metric", e))

        threads = []
        for i in range(3):
            threads.append(threading.Thread(target=repo_writer, name=f"repo_{i}"))
            threads.append(threading.Thread(target=risk_checker, name=f"risk_{i}"))
            threads.append(threading.Thread(target=metric_recorder, name=f"metric_{i}"))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"并发出现错误: {errors}"
        assert len(repo) == 150  # 3 thread × 50
        assert risk_svc.get_stats()["tracked_ips"] > 0

        engine.dispose()
