"""
智能温室监控系统 - 第三阶段：成果展示与竞赛
作品提交、评审和排行榜系统
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List


class CompetitionJudgingSystem:
    """竞赛评审系统"""

    def __init__(self):
        self.submissions = []
        self.leaderboard = []

    def submit_work(
        self,
        user_id: int,
        username: str,
        task_id: str,
        ai_model_path: str,
        hardware_control_code: str,
        project_report: Dict[str, Any],
        demo_video_url: str = None,
    ) -> Dict[str, Any]:
        """
        提交作品

        Args:
            user_id: 用户 ID
            username: 用户名
            task_id: 任务 ID
            ai_model_path: AI 模型文件路径
            hardware_control_code: 硬件控制代码
            project_report: 项目报告
            demo_video_url: 演示视频 URL

        Returns:
            提交结果
        """
        print(f"\n📥 收到用户 {username} 的作品提交")

        # 1. 验证提交材料
        validation_result = self._validate_submission(
            ai_model_path, hardware_control_code, project_report
        )

        if not validation_result["valid"]:
            return {"success": False, "error": validation_result["error"]}

        # 2. 自动评审
        judging_result = self._auto_judge(
            ai_model_path, hardware_control_code, project_report
        )

        # 3. 计算总分
        total_score = judging_result["total_score"]

        # 4. 记录提交
        submission = {
            "submission_id": f'sub_{datetime.now().strftime("%Y%m%d%H%M%S")}_{user_id}',
            "user_id": user_id,
            "username": username,
            "task_id": task_id,
            "ai_model_path": ai_model_path,
            "hardware_control_code": hardware_control_code,
            "project_report": project_report,
            "demo_video_url": demo_video_url,
            "judging_result": judging_result,
            "total_score": total_score,
            "submitted_at": datetime.now().isoformat(),
            "status": "submitted",
        }

        self.submissions.append(submission)

        # 5. 更新排行榜
        self._update_leaderboard(submission)

        print(f"✅ 作品提交成功！总分：{total_score:.1f}")

        return {
            "success": True,
            "submission_id": submission["submission_id"],
            "total_score": total_score,
            "message": f"作品提交成功！当前排名：{self._get_user_rank(user_id)}",
        }

    def _validate_submission(
        self, ai_model_path: str, hardware_control_code: str, project_report: Dict
    ) -> Dict[str, Any]:
        """验证提交材料"""

        # 检查 AI 模型文件
        model_file = Path(ai_model_path)
        if not model_file.exists():
            return {"valid": False, "error": "AI 模型文件不存在"}

        if model_file.stat().st_size == 0:
            return {"valid": False, "error": "AI 模型文件为空"}

        # 检查硬件控制代码
        if not hardware_control_code or len(hardware_control_code.strip()) == 0:
            return {"valid": False, "error": "硬件控制代码不能为空"}

        # 检查项目报告
        required_fields = ["accuracy", "system_architecture", "performance_metrics"]
        for field in required_fields:
            if field not in project_report:
                return {"valid": False, "error": f"项目报告缺少必要字段：{field}"}

        return {"valid": True}

    def _auto_judge(
        self, ai_model_path: str, hardware_control_code: str, project_report: Dict
    ) -> Dict[str, Any]:
        """
        自动评审

        评分维度:
        - 模型准确率 (40%)
        - 系统稳定性 (30%)
        - 创新性 (20%)
        - 文档质量 (10%)
        """

        # 1. 模型准确率评分（40 分）
        accuracy = project_report.get("accuracy", 0.0)
        accuracy_score = min(100, accuracy * 100) * 0.4

        # 2. 系统稳定性评分（30 分）
        stability_metrics = project_report.get("performance_metrics", {})
        stability_score = stability_metrics.get("stability_score", 0) * 0.3

        # 3. 资源利用率评分（10 分）
        resource_efficiency = stability_metrics.get("resource_efficiency", 0)
        resource_score = resource_efficiency * 0.1

        # 4. 创新性评分（20 分）
        innovation_score = self._evaluate_innovation(project_report) * 0.2

        # 5. 文档质量评分（10 分）
        documentation_score = self._evaluate_documentation(project_report) * 0.1

        total_score = (
            accuracy_score
            + stability_score
            + resource_score
            + innovation_score
            + documentation_score
        )

        return {
            "accuracy_score": accuracy_score,
            "stability_score": stability_score,
            "resource_score": resource_score,
            "innovation_score": innovation_score,
            "documentation_score": documentation_score,
            "total_score": total_score,
            "judged_at": datetime.now().isoformat(),
        }

    def _evaluate_innovation(self, project_report: Dict) -> float:
        """评估创新性（0-100 分）"""
        score = 50  # 基础分

        # 检查特殊功能
        features = project_report.get("special_features", [])
        score += min(30, len(features) * 10)  # 每个特色功能 +10 分，最多 30 分

        # 检查优化算法
        if "optimization_algorithm" in project_report:
            score += 10

        # 检查自定义功能
        if "custom_features" in project_report:
            score += 10

        return min(100, score)

    def _evaluate_documentation(self, project_report: Dict) -> float:
        """评估文档质量（0-100 分）"""
        score = 0

        # 系统架构图
        if "system_architecture" in project_report:
            score += 30

        # 准确率曲线
        if "accuracy_curve" in project_report:
            score += 20

        # 性能分析
        if "performance_analysis" in project_report:
            score += 20

        # 代码注释
        if "code_comments" in project_report:
            score += 15

        # 使用说明
        if "usage_instructions" in project_report:
            score += 15

        return min(100, score)

    def _update_leaderboard(self, submission: Dict):
        """更新排行榜"""
        # 查找是否已有该用户的提交
        existing_idx = None
        for i, entry in enumerate(self.leaderboard):
            if entry["user_id"] == submission["user_id"]:
                existing_idx = i
                break

        leaderboard_entry = {
            "rank": 0,  # 待计算
            "user_id": submission["user_id"],
            "username": submission["username"],
            "total_score": submission["total_score"],
            "submission_id": submission["submission_id"],
            "submitted_at": submission["submitted_at"],
        }

        if existing_idx is not None:
            # 更新现有记录（取最高分）
            if (
                submission["total_score"]
                > self.leaderboard[existing_idx]["total_score"]
            ):
                self.leaderboard[existing_idx] = leaderboard_entry
        else:
            # 添加新记录
            self.leaderboard.append(leaderboard_entry)

        # 重新排序
        self.leaderboard.sort(key=lambda x: x["total_score"], reverse=True)

        # 更新排名
        for i, entry in enumerate(self.leaderboard):
            entry["rank"] = i + 1

    def _get_user_rank(self, user_id: int) -> int:
        """获取用户排名"""
        for entry in self.leaderboard:
            if entry["user_id"] == user_id:
                return entry["rank"]
        return 0  # 未找到

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """获取排行榜前 N 名"""
        return self.leaderboard[:limit]

    def get_awards(self) -> Dict[str, List[Dict]]:
        """获取获奖名单"""
        awards = {
            "gold": [],  # 金牌（第 1 名）
            "silver": [],  # 银牌（第 2-3 名）
            "bronze": [],  # 铜牌（第 4-10 名）
            "participation": [],  # 参与奖
        }

        sorted_leaderboard = sorted(
            self.leaderboard, key=lambda x: x["total_score"], reverse=True
        )

        for i, entry in enumerate(sorted_leaderboard):
            rank = i + 1

            if rank == 1:
                awards["gold"].append(
                    {**entry, "award": "金牌", "xp_reward": 2000, "badge": "🥇"}
                )
            elif rank <= 3:
                awards["silver"].append(
                    {**entry, "award": "银牌", "xp_reward": 1500, "badge": "🥈"}
                )
            elif rank <= 10:
                awards["bronze"].append(
                    {**entry, "award": "铜牌", "xp_reward": 1000, "badge": "🥉"}
                )
            else:
                awards["participation"].append(
                    {**entry, "award": "参与奖", "xp_reward": 500, "badge": "🎖️"}
                )

        return awards


def demonstrate_competition():
    """演示竞赛流程"""
    print("\n" + "=" * 80)
    print("🏆 智能温室监控系统 - 竞赛评审演示")
    print("=" * 80)

    # 初始化评审系统
    judging_system = CompetitionJudgingSystem()

    # 模拟 3 个作品提交
    mock_submissions = [
        {
            "user_id": 1001,
            "username": "AI 小能手",
            "ai_model_path": "models/model_1001.pth",
            "hardware_control_code": "code_1001.py",
            "project_report": {
                "accuracy": 0.95,
                "system_architecture": "完整架构图",
                "performance_metrics": {
                    "stability_score": 95,
                    "resource_efficiency": 90,
                },
                "special_features": ["自适应控制", "数据可视化"],
                "optimization_algorithm": "PID 控制优化",
            },
        },
        {
            "user_id": 1002,
            "username": "温室专家",
            "ai_model_path": "models/model_1002.pth",
            "hardware_control_code": "code_1002.py",
            "project_report": {
                "accuracy": 0.92,
                "system_architecture": "系统框图",
                "performance_metrics": {
                    "stability_score": 90,
                    "resource_efficiency": 85,
                },
                "special_features": ["远程监控"],
            },
        },
        {
            "user_id": 1003,
            "username": "创新达人",
            "ai_model_path": "models/model_1003.pth",
            "hardware_control_code": "code_1003.py",
            "project_report": {
                "accuracy": 0.88,
                "system_architecture": "详细设计文档",
                "performance_metrics": {
                    "stability_score": 88,
                    "resource_efficiency": 92,
                },
                "special_features": ["语音控制", "手机 APP", "数据分析"],
                "custom_features": ["微信小程序集成"],
            },
        },
    ]

    # 提交作品
    print("\n📥 接收作品提交...")
    for sub in mock_submissions:
        result = judging_system.submit_work(
            user_id=sub["user_id"],
            username=sub["username"],
            task_id="greenhouse_001",
            ai_model_path=sub["ai_model_path"],
            hardware_control_code=sub["hardware_control_code"],
            project_report=sub["project_report"],
        )
        print(f"  ✅ {sub['username']}: 总分 {result['total_score']:.1f}")

    # 显示排行榜
    print("\n" + "=" * 80)
    print("📊 最终排行榜")
    print("=" * 80)

    leaderboard = judging_system.get_leaderboard(limit=10)
    for entry in leaderboard:
        rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(entry["rank"], "")
        print(
            f"{rank_emoji} 第{entry['rank']}名：{entry['username']} - {entry['total_score']:.1f}分"
        )

    # 显示获奖名单
    print("\n" + "=" * 80)
    print("🏆 获奖名单")
    print("=" * 80)

    awards = judging_system.get_awards()

    print("\n🥇 金牌奖（第 1 名）:")
    for winner in awards["gold"]:
        print(
            f"   {winner['badge']} {winner['username']} - 获得 {winner['xp_reward']} XP"
        )

    print("\n🥈 银牌奖（第 2-3 名）:")
    for winner in awards["silver"]:
        print(
            f"   {winner['badge']} {winner['username']} - 获得 {winner['xp_reward']} XP"
        )

    print("\n🥉 铜牌奖（第 4-10 名）:")
    for winner in awards["bronze"]:
        print(
            f"   {winner['badge']} {winner['username']} - 获得 {winner['xp_reward']} XP"
        )

    print("\n🎖️ 参与奖:")
    for winner in awards["participation"]:
        print(
            f"   {winner['badge']} {winner['username']} - 获得 {winner['xp_reward']} XP"
        )

    print("\n" + "=" * 80)
    print("🎉 竞赛圆满结束！")
    print("=" * 80)

    return judging_system


if __name__ == "__main__":
    demonstrate_competition()
