#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vircadia Web SDK 和 API 测试脚本

用于测试 Vircadia 元宇宙平台的各项功能，包括：
- 用户认证流程
- 场景加载和切换
- 对象交互
- Avatar 系统
- 性能基准测试

使用方法:
    python scripts/test_vircadia_api.py

依赖:
    requests
    websockets
    asyncio
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests


class VircadiaAPITester:
    """Vircadia API 测试器"""

    def __init__(self, base_url: str = "http://localhost:9000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.test_results: Dict[str, Any] = {
            "test_date": datetime.now().isoformat(),
            "server_url": base_url,
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }
        }

    def log(self, message: str, level: str = "INFO"):
        """日志输出"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def record_test_result(
        self,
        test_name: str,
        passed: bool,
        duration_ms: float,
        error_message: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        """记录测试结果"""
        result = {
            "name": test_name,
            "passed": passed,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
            "error": error_message,
            "details": details or {}
        }

        self.test_results["tests"].append(result)
        self.test_results["summary"]["total"] += 1

        if passed:
            self.test_results["summary"]["passed"] += 1
            self.log(f"✓ {test_name} - PASSED ({duration_ms:.2f}ms)", "SUCCESS")
        else:
            self.test_results["summary"]["failed"] += 1
            self.log(f"✗ {test_name} - FAILED: {error_message}", "ERROR")

    # ==================== 认证测试 ====================

    async def test_login(self):
        """测试用户登录"""
        test_name = "用户登录测试"
        start_time = time.time()

        try:
            login_data = {
                "username": "testuser",
                "password": "testpassword123"
            }

            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json=login_data,
                timeout=10
            )

            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")

                self.record_test_result(
                    test_name,
                    True,
                    duration_ms,
                    details={
                        "status_code": response.status_code,
                        "token_type": data.get("token_type"),
                        "expires_in": data.get("expires_in"),
                        "user_id": data.get("user", {}).get("id")
                    }
                )
                return True
            else:
                self.record_test_result(
                    test_name,
                    False,
                    duration_ms,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_test_result(test_name, False, duration_ms, str(e))
            return False

    async def test_logout(self):
        """测试用户登出"""
        test_name = "用户登出测试"
        start_time = time.time()

        try:
            if not self.access_token:
                self.record_test_result(
                    test_name,
                    False,
                    0,
                    "未登录，无法测试登出"
                )
                return False

            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.post(
                f"{self.base_url}/api/auth/logout",
                headers=headers,
                timeout=10
            )

            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                self.record_test_result(test_name, True, duration_ms)
                return True
            else:
                self.record_test_result(
                    test_name,
                    False,
                    duration_ms,
                    f"HTTP {response.status_code}"
                )
                return False

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_test_result(test_name, False, duration_ms, str(e))
            return False

    async def test_token_refresh(self):
        """测试 Token 刷新"""
        test_name = "Token 刷新测试"
        start_time = time.time()

        try:
            refresh_data = {"refresh_token": "test-refresh-token"}

            response = self.session.post(
                f"{self.base_url}/api/auth/refresh",
                json=refresh_data,
                timeout=10
            )

            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                self.record_test_result(
                    test_name,
                    True,
                    duration_ms,
                    details={
                        "new_token_type": data.get("token_type"),
                        "new_expires_in": data.get("expires_in")
                    }
                )
                return True
            else:
                self.record_test_result(
                    test_name,
                    False,
                    duration_ms,
                    f"HTTP {response.status_code}"
                )
                return False

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_test_result(test_name, False, duration_ms, str(e))
            return False

    # ==================== 场景管理测试 ====================

    async def test_query_scenes(self):
        """测试查询场景列表"""
        test_name = "查询场景列表"
        start_time = time.time()

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

            params = {
                "page": 1,
                "limit": 10,
                "public_only": True
            }

            response = self.session.get(
                f"{self.base_url}/api/scenes",
                headers=headers,
                params=params,
                timeout=10
            )

            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                scenes = data.get("data", [])

                self.record_test_result(
                    test_name,
                    True,
                    duration_ms,
                    details={
                        "total_scenes": len(scenes),
                        "total_count": data.get("total", 0)
                    }
                )
                return True
            else:
                self.record_test_result(
                    test_name,
                    False,
                    duration_ms,
                    f"HTTP {response.status_code}"
                )
                return False

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_test_result(test_name, False, duration_ms, str(e))
            return False

    async def test_get_scene_details(self):
        """测试获取场景详情"""
        test_name = "获取场景详情"
        start_time = time.time()

        try:
            scene_id = "default-classroom"
            headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

            response = self.session.get(
                f"{self.base_url}/api/scenes/{scene_id}",
                headers=headers,
                timeout=10
            )

            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                scene = response.json()
                self.record_test_result(
                    test_name,
                    True,
                    duration_ms,
                    details={
                        "scene_name": scene.get("name"),
                        "scene_url": scene.get("sceneUrl")
                    }
                )
                return True
            elif response.status_code == 404:
                self.record_test_result(
                    test_name,
                    False,
                    duration_ms,
                    "场景不存在"
                )
                return False
            else:
                self.record_test_result(
                    test_name,
                    False,
                    duration_ms,
                    f"HTTP {response.status_code}"
                )
                return False

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_test_result(test_name, False, duration_ms, str(e))
            return False

    # ==================== 对象交互测试 ====================

    async def test_get_objects(self):
        """测试获取场景对象列表"""
        test_name = "获取场景对象列表"
        start_time = time.time()

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

            response = self.session.get(
                f"{self.base_url}/api/objects",
                headers=headers,
                timeout=10
            )

            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                objects = response.json()
                self.record_test_result(
                    test_name,
                    True,
                    duration_ms,
                    details={
                        "object_count": len(objects)
                    }
                )
                return True
            else:
                self.record_test_result(
                    test_name,
                    False,
                    duration_ms,
                    f"HTTP {response.status_code}"
                )
                return False

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_test_result(test_name, False, duration_ms, str(e))
            return False

    async def test_object_interaction(self):
        """测试对象交互"""
        test_name = "对象交互测试"
        start_time = time.time()

        try:
            object_id = "test-object-1"
            interaction_data = {
                "interaction_type": "click",
                "data": {"timestamp": time.time()}
            }

            headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

            response = self.session.post(
                f"{self.base_url}/api/objects/{object_id}/interact",
                headers=headers,
                json=interaction_data,
                timeout=10
            )

            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result = response.json()
                self.record_test_result(
                    test_name,
                    result.get("success", False),
                    duration_ms,
                    details=result
                )
                return result.get("success", False)
            elif response.status_code == 404:
                self.record_test_result(
                    test_name,
                    False,
                    duration_ms,
                    "对象不存在"
                )
                return False
            else:
                self.record_test_result(
                    test_name,
                    False,
                    duration_ms,
                    f"HTTP {response.status_code}"
                )
                return False

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_test_result(test_name, False, duration_ms, str(e))
            return False

    # ==================== Avatar 系统测试 ====================

    async def test_get_available_avatars(self):
        """测试获取可用 Avatar 列表"""
        test_name = "获取可用 Avatar 列表"
        start_time = time.time()

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

            params = {"page": 1, "limit": 10}

            response = self.session.get(
                f"{self.base_url}/api/avatars",
                headers=headers,
                params=params,
                timeout=10
            )

            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                avatars = data.get("data", [])

                self.record_test_result(
                    test_name,
                    True,
                    duration_ms,
                    details={
                        "avatar_count": len(avatars),
                        "total": data.get("total", 0)
                    }
                )
                return True
            else:
                self.record_test_result(
                    test_name,
                    False,
                    duration_ms,
                    f"HTTP {response.status_code}"
                )
                return False

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_test_result(test_name, False, duration_ms, str(e))
            return False

    # ==================== 性能测试 ====================

    async def test_api_response_time(self):
        """测试 API 响应时间"""
        test_name = "API 响应时间测试"
        start_time = time.time()

        try:
            times = []
            iterations = 10

            for i in range(iterations):
                req_start = time.time()

                headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
                response = self.session.get(
                    f"{self.base_url}/api/scenes",
                    headers=headers,
                    timeout=10
                )

                req_end = time.time()
                times.append((req_end - req_start) * 1000)

                if response.status_code != 200:
                    self.record_test_result(
                        test_name,
                        False,
                        (time.time() - start_time) * 1000,
                        f"第 {i+1} 次请求失败：HTTP {response.status_code}"
                    )
                    return False

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            passed = avg_time < 200  # 平均响应时间小于 200ms

            self.record_test_result(
                test_name,
                passed,
                (time.time() - start_time) * 1000,
                details={
                    "avg_ms": round(avg_time, 2),
                    "min_ms": round(min_time, 2),
                    "max_ms": round(max_time, 2),
                    "iterations": iterations
                }
            )
            return passed

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_test_result(test_name, False, duration_ms, str(e))
            return False

    async def test_concurrent_requests(self):
        """测试并发请求"""
        test_name = "并发请求测试"
        start_time = time.time()

        try:
            import concurrent.futures

            def make_request():
                req_start = time.time()
                headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
                response = self.session.get(
                    f"{self.base_url}/api/scenes",
                    headers=headers,
                    timeout=10
                )
                req_end = time.time()
                return (response.status_code, (req_end - req_start) * 1000)

            concurrent_count = 5
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_count) as executor:
                futures = [executor.submit(make_request) for _ in range(concurrent_count)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            success_count = sum(1 for status, _ in results if status == 200)
            avg_time = sum(time for _, time in results) / len(results)

            passed = success_count == concurrent_count and avg_time < 500

            self.record_test_result(
                test_name,
                passed,
                (time.time() - start_time) * 1000,
                details={
                    "concurrent_count": concurrent_count,
                    "success_count": success_count,
                    "avg_time_ms": round(avg_time, 2)
                }
            )
            return passed

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_test_result(test_name, False, duration_ms, str(e))
            return False

    # ==================== WebSocket 测试 ====================

    async def test_websocket_connection(self):
        """测试 WebSocket 连接"""
        test_name = "WebSocket 连接测试"

        try:
            import websockets

            ws_url = self.base_url.replace("http", "ws") + "/ws"
            if self.access_token:
                ws_url += f"?token={self.access_token}"

            start_time = time.time()

            async with websockets.connect(ws_url) as websocket:
                connect_time = (time.time() - start_time) * 1000

                # 发送心跳消息
                await websocket.send(json.dumps({"type": "ping"}))

                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)

                if response_data.get("type") == "pong":
                    self.record_test_result(
                        test_name,
                        True,
                        connect_time,
                        details={"connect_time_ms": round(connect_time, 2)}
                    )
                    return True
                else:
                    self.record_test_result(
                        test_name,
                        False,
                        connect_time,
                        "未收到 pong 响应"
                    )
                    return False

        except Exception as e:
            self.record_test_result(test_name, False, 0, str(e))
            return False

    # ==================== 运行测试 ====================

    async def run_all_tests(self):
        """运行所有测试"""
        self.log("=" * 60)
        self.log("开始运行 Vircadia API 测试套件")
        self.log("=" * 60)

        # 1. 认证测试
        self.log("\n【认证测试】")
        await self.test_login()
        await self.test_token_refresh()
        await self.test_logout()

        # 重新登录以进行后续测试
        await self.test_login()

        # 2. 场景管理测试
        self.log("\n【场景管理测试】")
        await self.test_query_scenes()
        await self.test_get_scene_details()

        # 3. 对象交互测试
        self.log("\n【对象交互测试】")
        await self.test_get_objects()
        await self.test_object_interaction()

        # 4. Avatar 系统测试
        self.log("\n【Avatar 系统测试】")
        await self.test_get_available_avatars()

        # 5. 性能测试
        self.log("\n【性能测试】")
        await self.test_api_response_time()
        await self.test_concurrent_requests()

        # 6. WebSocket 测试
        self.log("\n【WebSocket 测试】")
        await self.test_websocket_connection()

        # 清理
        await self.test_logout()

        # 生成报告
        self.generate_report()

    def generate_report(self):
        """生成测试报告"""
        import os

        report_dir = "backtest_reports"
        os.makedirs(report_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(report_dir, f"vircadia_p1_dev_001_{timestamp}.json")

        # 计算通过率
        summary = self.test_results["summary"]
        pass_rate = (summary["passed"] / summary["total"] * 100) if summary["total"] > 0 else 0

        self.test_results["pass_rate"] = round(pass_rate, 2)
        self.test_results["summary"]["success_rate"] = f"{pass_rate:.2f}%"

        # 保存报告
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)

        self.log("\n" + "=" * 60)
        self.log("测试完成!")
        self.log("=" * 60)
        self.log(f"总测试数：{summary['total']}")
        self.log(f"通过：{summary['passed']}")
        self.log(f"失败：{summary['failed']}")
        self.log(f"跳过：{summary['skipped']}")
        self.log(f"通过率：{pass_rate:.2f}%")
        self.log(f"详细报告：{report_file}")


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Vircadia API 测试工具")
    parser.add_argument(
        "--url",
        default="http://localhost:9000",
        help="Vircadia 服务器 URL (默认：http://localhost:9000)"
    )

    args = parser.parse_args()

    tester = VircadiaAPITester(args.url)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
