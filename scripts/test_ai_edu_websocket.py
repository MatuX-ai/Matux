"""
AI-Edu 学习进度 WebSocket 同步功能测试脚本
测试 WebSocket 实时同步功能的完整工作流程
"""

import asyncio
import json
import websockets
from datetime import datetime


class AIEduWebSocketTester:
    """AI-Edu WebSocket 测试器"""

    def __init__(self, base_url: str = "ws://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.passed = 0
        self.failed = 0

    async def test_connection(self):
        """测试 1: WebSocket 连接"""
        test_name = "WebSocket 连接测试"
        print(f"\n{'='*60}")
        print(f"测试：{test_name}")
        print(f"{'='*60}")

        try:
            ws_url = f"{self.base_url}/ws/ai-edu/progress/1?org_id=1"

            async with websockets.connect(ws_url) as websocket:
                print(f"✅ WebSocket 连接成功")

                # 等待欢迎消息
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                welcome_data = json.loads(welcome_msg)

                if welcome_data.get("type") == "connected":
                    print(f"✅ 收到欢迎消息：{welcome_data.get('message')}")
                    self.record_result(test_name, True, "连接成功并收到欢迎消息")
                    return True, websocket
                else:
                    print(f"❌ 未收到预期的欢迎消息")
                    self.record_result(test_name, False, "未收到预期的欢迎消息")
                    return False, None

        except Exception as e:
            print(f"❌ 连接失败：{e}")
            self.record_result(test_name, False, str(e))
            return False, None

    async def test_ping_pong(self, websocket):
        """测试 2: 心跳检测"""
        test_name = "心跳检测 (Ping/Pong)"
        print(f"\n{'='*60}")
        print(f"测试：{test_name}")
        print(f"{'='*60}")

        try:
            # 发送 ping
            await websocket.send(json.dumps({"type": "ping"}))
            print(f"📤 发送 Ping")

            # 接收 pong
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)

            if response_data.get("type") == "pong":
                print(f"✅ 收到 Pong 响应：{response_data.get('timestamp')}")
                self.record_result(test_name, True, "心跳检测成功")
                return True
            else:
                print(f"❌ 未收到 Pong 响应")
                self.record_result(test_name, False, "未收到 Pong 响应")
                return False

        except Exception as e:
            print(f"❌ 心跳检测失败：{e}")
            self.record_result(test_name, False, str(e))
            return False

    async def test_progress_update(self, websocket):
        """测试 3: 更新学习进度"""
        test_name = "更新学习进度"
        print(f"\n{'='*60}")
        print(f"测试：{test_name}")
        print(f"{'='*60}")

        try:
            progress_data = {
                "type": "update_progress",
                "data": {
                    "lesson_id": 1,
                    "progress": {
                        "progress_percentage": 75,
                        "time_spent_seconds": 450,
                        "quiz_score": 88.5,
                        "status": "in_progress"
                    }
                }
            }

            # 发送进度更新
            await websocket.send(json.dumps(progress_data))
            print(f"📤 发送进度更新：{progress_data['data']}")

            # 接收确认
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)

            if response_data.get("type") == "progress_confirmed":
                confirmed = response_data.get("data", {})
                print(f"✅ 进度更新已确认:")
                print(f"   - 进度 ID: {confirmed.get('progress_id')}")
                print(f"   - 课程 ID: {confirmed.get('lesson_id')}")
                print(f"   - 进度：{confirmed.get('progress_percentage')}%")
                print(f"   - 状态：{confirmed.get('status')}")

                self.record_result(test_name, True, "进度更新成功并得到确认")
                return True
            else:
                print(f"❌ 未收到进度确认")
                print(f"   响应：{response_data}")
                self.record_result(test_name, False, "未收到进度确认")
                return False

        except Exception as e:
            print(f"❌ 进度更新失败：{e}")
            self.record_result(test_name, False, str(e))
            return False

    async def test_get_state(self, websocket):
        """测试 4: 获取当前学习状态"""
        test_name = "获取当前学习状态"
        print(f"\n{'='*60}")
        print(f"测试：{test_name}")
        print(f"{'='*60}")

        try:
            # 发送获取状态请求
            await websocket.send(json.dumps({"type": "get_state"}))
            print(f"📤 请求当前学习状态")

            # 接收响应
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)

            if response_data.get("type") == "current_state":
                state = response_data.get("data", {})
                print(f"✅ 收到当前学习状态:")
                if state and "lesson_id" in state:
                    print(f"   - 课程 ID: {state.get('lesson_id')}")
                    print(f"   - 进度：{state.get('progress')}%")
                    print(f"   - 状态：{state.get('status')}")
                else:
                    print(f"   ℹ️  暂无活跃学习状态")

                self.record_result(test_name, True, "成功获取学习状态")
                return True
            else:
                print(f"❌ 未收到状态响应")
                self.record_result(test_name, False, "未收到状态响应")
                return False

        except Exception as e:
            print(f"❌ 获取状态失败：{e}")
            self.record_result(test_name, False, str(e))
            return False

    async def test_subscribe_lesson(self, websocket):
        """测试 5: 订阅课程进度"""
        test_name = "订阅/取消订阅课程"
        print(f"\n{'='*60}")
        print(f"测试：{test_name}")
        print(f"{'='*60}")

        try:
            # 订阅
            subscribe_msg = {
                "type": "subscribe_lesson",
                "data": {"lesson_id": 1}
            }
            await websocket.send(json.dumps(subscribe_msg))
            print(f"📤 订阅课程 1")

            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)

            if response_data.get("type") == "subscribed":
                print(f"✅ 订阅成功：{response_data.get('message')}")
            else:
                print(f"❌ 订阅失败")
                self.record_result(test_name, False, "订阅失败")
                return False

            # 取消订阅
            unsubscribe_msg = {
                "type": "unsubscribe_lesson",
                "data": {"lesson_id": 1}
            }
            await websocket.send(json.dumps(unsubscribe_msg))
            print(f"📤 取消订阅课程 1")

            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)

            if response_data.get("type") == "unsubscribed":
                print(f"✅ 取消订阅成功：{response_data.get('message')}")
                self.record_result(test_name, True, "订阅/取消订阅成功")
                return True
            else:
                print(f"❌ 取消订阅失败")
                self.record_result(test_name, False, "取消订阅失败")
                return False

        except Exception as e:
            print(f"❌ 订阅测试失败：{e}")
            self.record_result(test_name, False, str(e))
            return False

    def record_result(self, test_name: str, passed: bool, message: str):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)

        if passed:
            self.passed += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.failed += 1
            print(f"❌ {test_name}: {message}")

    def generate_report(self):
        """生成测试报告"""
        print(f"\n{'='*60}")
        print(f"📊 测试报告")
        print(f"{'='*60}")

        total = len(self.test_results)
        success_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"\n总测试数：{total}")
        print(f"✅ 通过：{self.passed}")
        print(f"❌ 失败：{{self.failed}}")
        print(f"📈 成功率：{success_rate:.1f}%\n")

        for result in self.test_results:
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {result['test_name']}: {result['message']}")

        print(f"\n{'='*60}")

        if self.failed == 0:
            print("🎉 所有测试通过！WebSocket 功能运行正常！")
        else:
            print("⚠️  部分测试失败，请检查日志和配置。")

        print(f"{'='*60}\n")

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*80)
        print("🚀 AI-Edu 学习进度 WebSocket 同步功能测试")
        print("="*80)

        # 测试 1: 连接
        connected, websocket = await self.test_connection()
        if not connected or not websocket:
            print("❌ 无法建立连接，终止测试")
            self.generate_report()
            return

        try:
            # 测试 2: 心跳
            await self.test_ping_pong(websocket)

            # 测试 3: 进度更新
            await self.test_progress_update(websocket)

            # 测试 4: 获取状态
            await self.test_get_state(websocket)

            # 测试 5: 订阅
            await self.test_subscribe_lesson(websocket)

        finally:
            # 关闭连接
            await websocket.close()
            print("\n🔌 WebSocket 连接已关闭")

        # 生成报告
        self.generate_report()


async def main():
    """主函数"""
    tester = AIEduWebSocketTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
