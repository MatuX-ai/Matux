"""
AI-Edu 成就系统 API 测试脚本
测试成就系统的完整功能流程
"""

import requests
import json
from datetime import datetime


class AchievementTester:
    """成就系统测试器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.org_id = 1
        self.test_user_token = None
        self.test_results = []
        self.passed = 0
        self.failed = 0

    def login_test_user(self):
        """登录测试用户获取 token"""
        print("\n" + "="*60)
        print("步骤 1: 登录测试用户")
        print("="*60)

        try:
            # 使用测试账号登录（需要根据实际认证方式调整）
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json={
                    "username": "test_student",
                    "password": "test123"
                }
            )

            if response.status_code == 200:
                data = response.json()
                self.test_user_token = data.get('access_token')
                print(f"✅ 登录成功，Token: {self.test_user_token[:20]}...")
                return True
            else:
                print(f"❌ 登录失败：{response.text}")
                # 如果没有测试账号，使用模拟 token
                print("⚠️  使用模拟 Token 进行测试")
                self.test_user_token = "mock_token_12345"
                return True

        except Exception as e:
            print(f"❌ 登录异常：{e}")
            self.test_user_token = "mock_token_12345"
            return True

    def test_initialize_achievements(self):
        """测试 1: 初始化预定义成就"""
        test_name = "初始化预定义成就"
        print(f"\n{'='*60}")
        print(f"测试：{test_name}")
        print(f"{'='*60}")

        try:
            headers = {"Authorization": f"Bearer {self.test_user_token}"}

            response = requests.post(
                f"{self.base_url}/api/v1/org/{self.org_id}/achievements/admin/initialize",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                count = data.get('data', {}).get('initialized_count', 0)
                print(f"✅ 初始化成功：{count} 个成就")
                self.record_result(test_name, True, f"初始化了 {count} 个成就")
                return True
            else:
                print(f"❌ 初始化失败：{response.status_code}")
                self.record_result(test_name, False, response.text)
                return False

        except Exception as e:
            print(f"❌ 测试失败：{e}")
            self.record_result(test_name, False, str(e))
            return False

    def test_get_my_achievements(self):
        """测试 2: 获取我的成就列表"""
        test_name = "获取我的成就列表"
        print(f"\n{'='*60}")
        print(f"测试：{test_name}")
        print(f"{'='*60}")

        try:
            headers = {"Authorization": f"Bearer {self.test_user_token}"}

            response = requests.get(
                f"{self.base_url}/api/v1/org/{self.org_id}/achievements/my/list",
                headers=headers,
                params={"include_locked": False}
            )

            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)
                print(f"✅ 获取成功：{count} 个已解锁成就")

                if count > 0:
                    achievements = data.get('data', [])
                    for ach in achievements[:3]:  # 只显示前 3 个
                        ach_name = ach.get('achievement', {}).get('name', 'Unknown')
                        unlocked_at = ach.get('unlocked_at', 'N/A')
                        print(f"   - {ach_name} (解锁时间：{unlocked_at})")

                self.record_result(test_name, True, f"获取到 {count} 个成就")
                return True
            else:
                print(f"❌ 获取失败：{response.status_code}")
                self.record_result(test_name, False, response.text)
                return False

        except Exception as e:
            print(f"❌ 测试失败：{e}")
            self.record_result(test_name, False, str(e))
            return False

    def test_update_progress(self):
        """测试 3: 更新成就进度"""
        test_name = "更新成就进度并解锁成就"
        print(f"\n{'='*60}")
        print(f"测试：{test_name}")
        print(f"{'='*60}")

        try:
            headers = {"Authorization": f"Bearer {self.test_user_token}"}

            # 模拟学习时长达到 600 分钟（10 小时），应该解锁"勤奋学习者"成就
            response = requests.post(
                f"{self.base_url}/api/v1/org/{self.org_id}/achievements/progress/update",
                headers=headers,
                json={
                    "metric_name": "study_time_minutes",
                    "metric_value": 600,
                    "period_type": "all_time"
                }
            )

            if response.status_code == 200:
                data = response.json()
                newly_unlocked = data.get('data', {}).get('newly_unlocked', [])

                print(f"✅ 进度更新成功")

                if newly_unlocked:
                    print(f"🎉 新解锁成就：{len(newly_unlocked)} 个")
                    for unlocked in newly_unlocked:
                        print(f"   - {unlocked.get('achievement_name')} (+{unlocked.get('points_reward')} 积分)")
                else:
                    print(f"ℹ️  没有新解锁的成就（可能已经解锁过了）")

                self.record_result(test_name, True, f"更新进度，新解锁 {len(newly_unlocked)} 个成就")
                return True
            else:
                print(f"❌ 更新失败：{response.status_code}")
                self.record_result(test_name, False, response.text)
                return False

        except Exception as e:
            print(f"❌ 测试失败：{e}")
            self.record_result(test_name, False, str(e))
            return False

    def test_get_statistics(self):
        """测试 4: 获取成就统计信息"""
        test_name = "获取成就统计信息"
        print(f"\n{'='*60}")
        print(f"测试：{test_name}")
        print(f"{'='*60}")

        try:
            headers = {"Authorization": f"Bearer {self.test_user_token}"}

            response = requests.get(
                f"{self.base_url}/api/v1/org/{self.org_id}/achievements/my/statistics",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                stats = data.get('data', {})

                print(f"✅ 统计信息获取成功")
                print(f"   - 总成就数：{stats.get('total_achievements', 0)}")
                print(f"   - 已解锁：{stats.get('unlocked_count', 0)}")
                print(f"   - 完成率：{stats.get('completion_rate', 0)}%")

                # 分类统计
                category_breakdown = stats.get('category_breakdown', {})
                if category_breakdown:
                    print(f"\n   分类详情:")
                    for cat, cat_stats in category_breakdown.items():
                        print(f"     - {cat}: {cat_stats.get('unlocked')}/{cat_stats.get('total')} ({cat_stats.get('rate')}%)")

                self.record_result(test_name, True, f"完成率 {stats.get('completion_rate', 0)}%")
                return True
            else:
                print(f"❌ 获取失败：{response.status_code}")
                self.record_result(test_name, False, response.text)
                return False

        except Exception as e:
            print(f"❌ 测试失败：{e}")
            self.record_result(test_name, False, str(e))
            return False

    def test_claim_reward(self):
        """测试 5: 领取成就奖励"""
        test_name = "领取成就奖励"
        print(f"\n{'='*60}")
        print(f"测试：{test_name}")
        print(f"{'='*60}")

        try:
            headers = {"Authorization": f"Bearer {self.test_user_token}"}

            # 先获取已解锁但未领取的成就
            list_response = requests.get(
                f"{self.base_url}/api/v1/org/{self.org_id}/achievements/my/list",
                headers=headers,
                params={"include_locked": False}
            )

            if list_response.status_code != 200:
                print(f"❌ 获取成就列表失败")
                self.record_result(test_name, False, "无法获取成就列表")
                return False

            achievements_data = list_response.json()
            achievements = achievements_data.get('data', [])

            # 查找第一个未领取的成就
            claimable = None
            for ach in achievements:
                if not ach.get('is_claimed', True):
                    claimable = ach
                    break

            if claimable:
                achievement_id = ach.get('achievement_id')

                response = requests.post(
                    f"{self.base_url}/api/v1/org/{self.org_id}/achievements/my/{achievement_id}/claim",
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    reward = data.get('data', {})
                    print(f"✅ 领取成功：+{reward.get('points', 0)} 积分")
                    print(f"   徽章：{reward.get('badge', 'N/A')}")
                    print(f"   消息：{reward.get('message', '')}")

                    self.record_result(test_name, True, f"获得 {reward.get('points', 0)} 积分")
                    return True
                else:
                    print(f"❌ 领取失败：{response.status_code}")
                    self.record_result(test_name, False, response.text)
                    return False
            else:
                print(f"ℹ️  所有成就奖励都已领取")
                self.record_result(test_name, True, "没有待领取的奖励")
                return True

        except Exception as e:
            print(f"❌ 测试失败：{e}")
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
        print(f"❌ 失败：{self.failed}")
        print(f"📈 成功率：{success_rate:.1f}%\n")

        for result in self.test_results:
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {result['test_name']}: {result['message']}")

        print(f"\n{'='*60}")

        if self.failed == 0:
            print("🎉 所有测试通过！成就系统运行正常！")
        else:
            print("⚠️  部分测试失败，请检查日志和配置。")

        print(f"{'='*60}\n")

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*80)
        print("🚀 AI-Edu 成就系统 API 测试套件")
        print("="*80)

        # 登录
        if not self.login_test_user():
            print("❌ 无法登录，终止测试")
            return

        try:
            # 运行各项测试
            self.test_initialize_achievements()
            self.test_get_my_achievements()
            self.test_update_progress()
            self.test_get_statistics()
            self.test_claim_reward()

        finally:
            # 生成报告
            self.generate_report()


def main():
    """主函数"""
    tester = AchievementTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
