"""
AI-Edu-for-Kids 课程资源导入服务
支持批量导入课程资源、数据集和代码项目
"""

from datetime import datetime
import json
import logging
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.ai_edu_rewards import AIEduLesson, AIEduModule, AIEduRewardRule

logger = logging.getLogger(__name__)


class AIEduResourceImporter:
    """AI 课程资源导入器"""

    RESOURCE_TYPES = {
        "python": "Python 代码项目",
        "scratch": "Scratch 项目",
        "html": "HTML 互动课件",
        "dataset": "数据集",
        "lesson_plan": "教案文档",
        "ppt": "PPT 课件",
    }

    def __init__(self, base_path: str, db_session: Session):
        """
        初始化导入器

        Args:
            base_path: 资源根路径
            db_session: 数据库会话
        """
        self.base_path = Path(base_path)
        self.db = db_session
        self.imported_count = 0
        self.failed_count = 0
        self.skipped_count = 0

    def import_all(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        导入所有资源

        Args:
            dry_run: 是否仅预演（不实际写入数据库）

        Returns:
            导入统计信息
        """
        logger.info(f"开始导入 AI-Edu 资源 from {self.base_path}")
        if dry_run:
            logger.info("【预演模式】不会实际写入数据库")

        stats = {
            "start_time": datetime.now(),
            "modules": 0,
            "lessons": 0,
            "resources": 0,
            "errors": [],
        }

        try:
            # 1. 导入课程模块
            stats["modules"] = self._import_modules(dry_run)

            # 2. 导入课程课时
            stats["lessons"] = self._import_lessons(dry_run)

            # 3. 导入奖励规则
            stats["rules"] = self._import_reward_rules(dry_run)

            # 4. 导入物理资源文件
            stats["resources"] = self._import_physical_resources(dry_run)

            self.imported_count = (
                stats["modules"] + stats["lessons"] + stats["resources"]
            )

        except Exception as e:
            logger.error(f"导入过程中出错：{e}")
            stats["errors"].append(str(e))

        finally:
            stats["end_time"] = datetime.now()
            stats["total_imported"] = self.imported_count
            stats["total_failed"] = self.failed_count
            stats["total_skipped"] = self.skipped_count

            logger.info(
                f"导入完成！成功：{self.imported_count}, 失败：{self.failed_count}, 跳过：{self.skipped_count}"
            )

        return stats

    def _import_modules(self, dry_run: bool = False) -> int:
        """导入课程模块"""
        logger.info("正在导入课程模块...")

        modules_dir = self.base_path / "modules"
        if not modules_dir.exists():
            logger.warning(f"模块目录不存在：{modules_dir}")
            return 0

        imported = 0
        module_config_files = list(modules_dir.glob("**/module.json"))

        for config_file in module_config_files:
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    module_data = json.load(f)

                # 检查是否已存在
                existing = (
                    self.db.query(AIEduModule)
                    .filter(AIEduModule.module_code == module_data.get("code"))
                    .first()
                )

                if existing:
                    logger.info(f"跳过已存在的模块：{module_data.get('name')}")
                    self.skipped_count += 1
                    continue

                # 创建新模块
                module = AIEduModule(
                    module_code=module_data.get("code"),
                    name=module_data.get("name"),
                    description=module_data.get("description", ""),
                    category=module_data.get("category"),
                    grade_ranges=module_data.get("grade_ranges", []),
                    expected_lessons=module_data.get("expected_lessons", 0),
                    expected_duration_minutes=module_data.get("duration_minutes", 0),
                    prerequisites=module_data.get("prerequisites", []),
                    is_active=True,
                    display_order=module_data.get("order", 0),
                )

                if not dry_run:
                    self.db.add(module)
                    self.db.commit()
                    logger.info(f"✅ 导入模块：{module.name} (ID: {module.id})")
                else:
                    logger.info(f"【预演】将导入模块：{module.name}")

                imported += 1

            except Exception as e:
                logger.error(f"❌ 导入模块失败 {config_file}: {e}")
                self.failed_count += 1
                if not dry_run:
                    self.db.rollback()

        return imported

    def _import_lessons(self, dry_run: bool = False) -> int:
        """导入课程课时"""
        logger.info("正在导入课程课时...")

        lessons_dir = self.base_path / "lessons"
        if not lessons_dir.exists():
            logger.warning(f"课时目录不存在：{lessons_dir}")
            return 0

        imported = 0
        lesson_config_files = list(lessons_dir.glob("**/lesson.json"))

        for config_file in lesson_config_files:
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    lesson_data = json.load(f)

                # 检查是否已存在
                existing = (
                    self.db.query(AIEduLesson)
                    .filter(AIEduLesson.lesson_code == lesson_data.get("code"))
                    .first()
                )

                if existing:
                    logger.info(f"跳过已存在的课时：{lesson_data.get('title')}")
                    self.skipped_count += 1
                    continue

                # 获取所属模块
                module = (
                    self.db.query(AIEduModule)
                    .filter(AIEduModule.module_code == lesson_data.get("module_code"))
                    .first()
                )

                if not module:
                    logger.error(f"找不到所属模块：{lesson_data.get('module_code')}")
                    self.failed_count += 1
                    continue

                # 创建课时
                lesson = AIEduLesson(
                    module_id=module.id,
                    lesson_code=lesson_data.get("code"),
                    title=lesson_data.get("title"),
                    subtitle=lesson_data.get("subtitle", ""),
                    content_type=lesson_data.get("content_type", "hybrid"),
                    content_url=lesson_data.get("content_url", ""),
                    resources=lesson_data.get("resources", []),
                    learning_objectives=lesson_data.get("learning_objectives", []),
                    knowledge_points=lesson_data.get("knowledge_points", []),
                    estimated_duration_minutes=lesson_data.get("duration_minutes", 45),
                    has_quiz=lesson_data.get("has_quiz", False),
                    quiz_passing_score=lesson_data.get("passing_score", 80.0),
                    has_practice=lesson_data.get("has_practice", False),
                    practice_type=lesson_data.get("practice_type"),
                    base_points=lesson_data.get("base_points", 20),
                    bonus_conditions=lesson_data.get("bonus_conditions", {}),
                    is_active=True,
                    display_order=lesson_data.get("order", 0),
                )

                if not dry_run:
                    self.db.add(lesson)
                    self.db.commit()
                    logger.info(f"✅ 导入课时：{lesson.title} (ID: {lesson.id})")
                else:
                    logger.info(f"【预演】将导入课时：{lesson.title}")

                imported += 1

            except Exception as e:
                logger.error(f"❌ 导入课时失败 {config_file}: {e}")
                self.failed_count += 1
                if not dry_run:
                    self.db.rollback()

        return imported

    def _import_reward_rules(self, dry_run: bool = False) -> int:
        """导入奖励规则"""
        logger.info("正在导入奖励规则...")

        rules_dir = self.base_path / "rules"
        if not rules_dir.exists():
            logger.warning(f"规则目录不存在：{rules_dir}")
            return 0

        imported = 0
        rule_config_files = list(rules_dir.glob("*.json"))

        for config_file in rule_config_files:
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    rule_data = json.load(f)

                # 检查是否已存在
                existing = (
                    self.db.query(AIEduRewardRule)
                    .filter(AIEduRewardRule.rule_code == rule_data.get("code"))
                    .first()
                )

                if existing:
                    logger.info(f"跳过已存在的规则：{rule_data.get('name')}")
                    self.skipped_count += 1
                    continue

                # 查找关联的成就
                achievement_id = None
                if rule_data.get("achievement_code"):
                    from models.ai_edu_rewards import AIEduAchievement

                    achievement = (
                        self.db.query(AIEduAchievement)
                        .filter(
                            AIEduAchievement.achievement_code
                            == rule_data.get("achievement_code")
                        )
                        .first()
                    )
                    if achievement:
                        achievement_id = achievement.id

                # 创建规则
                rule = AIEduRewardRule(
                    rule_code=rule_data.get("code"),
                    rule_name=rule_data.get("name"),
                    description=rule_data.get("description", ""),
                    rule_type=rule_data.get("type"),
                    base_points=rule_data.get("base_points", 20),
                    grade_multipliers=rule_data.get("grade_multipliers", {}),
                    quality_coefficients=rule_data.get("quality_coefficients", {}),
                    time_bonus_enabled=rule_data.get("time_bonus_enabled", False),
                    standard_time_minutes=rule_data.get("standard_time_minutes"),
                    time_bonus_rate=rule_data.get("time_bonus_rate", 0.5),
                    streak_bonus_enabled=rule_data.get("streak_bonus_enabled", True),
                    streak_multipliers=rule_data.get("streak_multipliers", {}),
                    achievement_id=achievement_id,
                    trigger_conditions=rule_data.get("trigger_conditions", []),
                    priority=rule_data.get("priority", 100),
                    cooldown_seconds=rule_data.get("cooldown_seconds", 0),
                    is_active=True,
                )

                if not dry_run:
                    self.db.add(rule)
                    self.db.commit()
                    logger.info(f"✅ 导入规则：{rule.rule_name}")
                else:
                    logger.info(f"【预演】将导入规则：{rule.rule_name}")

                imported += 1

            except Exception as e:
                logger.error(f"❌ 导入规则失败 {config_file}: {e}")
                self.failed_count += 1
                if not dry_run:
                    self.db.rollback()

        return imported

    def _import_physical_resources(self, dry_run: bool = False) -> int:
        """导入物理资源文件（代码、数据集等）"""
        logger.info("正在导入物理资源...")

        resources_dir = self.base_path / "resources"
        if not resources_dir.exists():
            logger.warning(f"资源目录不存在：{resources_dir}")
            return 0

        imported = 0
        target_base = Path("/data/ai-edu-resources")  # 目标存储路径
        target_base.mkdir(parents=True, exist_ok=True)

        # 复制资源文件
        for resource_file in resources_dir.rglob("*"):
            if resource_file.is_file():
                try:
                    relative_path = resource_file.relative_to(resources_dir)
                    target_path = target_base / relative_path

                    # 确保目标目录存在
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    if not dry_run:
                        shutil.copy2(resource_file, target_path)
                        logger.info(f"✅ 复制资源：{relative_path}")
                    else:
                        logger.info(f"【预演】将复制：{relative_path}")

                    imported += 1

                except Exception as e:
                    logger.error(f"❌ 复制资源失败 {resource_file}: {e}")
                    self.failed_count += 1

        return imported


def create_sample_module_data() -> Dict[str, Any]:
    """创建示例模块数据"""
    return {
        "code": "ai-basics",
        "name": "人工智能基础",
        "description": "面向中小学生的 AI 通识教育入门课程",
        "category": "basic_concepts",
        "grade_ranges": [
            {"min": 1, "max": 2, "label": "小学低段"},
            {"min": 3, "max": 4, "label": "小学中段"},
            {"min": 5, "max": 6, "label": "小学高段"},
            {"min": 7, "max": 9, "label": "初中段"},
        ],
        "expected_lessons": 8,
        "duration_minutes": 360,
        "prerequisites": [],
        "order": 1,
    }


if __name__ == "__main__":
    # 使用示例
    from utils.database import get_sync_db

    # 创建数据库会话
    db = next(get_sync_db())

    # 创建导入器
    importer = AIEduResourceImporter(
        base_path="/path/to/ai-edu-resources", db_session=db
    )

    # 执行导入（先预演）
    stats = importer.import_all(dry_run=True)

    print("\n=== 导入统计 ===")
    print(f"模块：{stats['modules']}")
    print(f"课时：{stats['lessons']}")
    print(f"资源：{stats['resources']}")
    print(f"错误：{len(stats['errors'])}")
