"""
学习行为特征服务
提供学习行为数据的收集、处理、分析和查询功能
"""

from collections import defaultdict
from datetime import datetime, timedelta
import json
import logging
import statistics
from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from models.learning_behavior import (
    BehaviorAnalyticsRequest,
    BehaviorCategory,
    BehaviorEventType,
    LearningBehaviorCreate,
    LearningBehaviorFeature,
    LearningBehaviorSummary,
    LearningBehaviorUpdate,
)

logger = logging.getLogger(__name__)


class LearningBehaviorService:
    """学习行为特征服务类"""

    def __init__(self, db: Session = None):
        self.db = db
        self.model_class = LearningBehaviorFeature
        self.summary_model_class = LearningBehaviorSummary

    def create_behavior_record(
        self, behavior_data: LearningBehaviorCreate, org_id: int
    ) -> LearningBehaviorFeature:
        """创建学习行为记录"""
        try:
            # 创建行为记录
            behavior_record = LearningBehaviorFeature(
                org_id=org_id,
                student_id=behavior_data.student_id,
                category=behavior_data.category.value,
                event_type=behavior_data.event_type.value,
                context_id=behavior_data.context_id,
                session_id=behavior_data.session_id,
                event_timestamp=behavior_data.event_timestamp,
                duration_seconds=behavior_data.duration_seconds or 0,
                debug_duration_seconds=behavior_data.debug_duration_seconds or 0,
                debug_attempts=behavior_data.debug_attempts or 0,
                breakpoints_used=behavior_data.breakpoints_used or 0,
                debug_commands_executed=behavior_data.debug_commands_executed or 0,
                error_types_encountered=(
                    json.dumps(behavior_data.error_types_encountered)
                    if behavior_data.error_types_encountered
                    else None
                ),
                hardware_operation_success_rate=behavior_data.hardware_operation_success_rate
                or 0.0,
                hardware_operations_count=behavior_data.hardware_operations_count or 0,
                successful_operations=behavior_data.successful_operations or 0,
                failed_operations=behavior_data.failed_operations or 0,
                hardware_types_used=(
                    json.dumps(behavior_data.hardware_types_used)
                    if behavior_data.hardware_types_used
                    else None
                ),
                hardware_connection_duration=behavior_data.hardware_connection_duration
                or 0,
                success_indicator=behavior_data.success_indicator or False,
                performance_score=behavior_data.performance_score,
                difficulty_level=behavior_data.difficulty_level,
                help_requested=behavior_data.help_requested or False,
                hints_used=behavior_data.hints_used or 0,
                platform=behavior_data.platform,
                device_type=behavior_data.device_type,
                browser_info=behavior_data.browser_info,
            )

            self.db.add(behavior_record)
            self.db.commit()
            self.db.refresh(behavior_record)

            logger.info(
                f"创建学习行为记录成功: ID={behavior_record.id}, 学生ID={behavior_record.student_id}"
            )
            return behavior_record

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建学习行为记录失败: {str(e)}")
            raise

    def update_behavior_record(
        self, record_id: int, update_data: LearningBehaviorUpdate
    ) -> LearningBehaviorFeature:
        """更新学习行为记录"""
        try:
            record = (
                self.db.query(LearningBehaviorFeature)
                .filter(LearningBehaviorFeature.id == record_id)
                .first()
            )

            if not record:
                raise ValueError(f"未找到ID为 {record_id} 的行为记录")

            # 更新字段
            if update_data.duration_seconds is not None:
                record.duration_seconds = update_data.duration_seconds
            if update_data.debug_duration_seconds is not None:
                record.debug_duration_seconds = update_data.debug_duration_seconds
            if update_data.debug_attempts is not None:
                record.debug_attempts = update_data.debug_attempts
            if update_data.hardware_operation_success_rate is not None:
                record.hardware_operation_success_rate = (
                    update_data.hardware_operation_success_rate
                )
            if update_data.success_indicator is not None:
                record.success_indicator = update_data.success_indicator
            if update_data.performance_score is not None:
                record.performance_score = update_data.performance_score
            if update_data.is_processed is not None:
                record.is_processed = update_data.is_processed
            if update_data.processing_notes is not None:
                record.processing_notes = update_data.processing_notes

            record.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(record)

            logger.info(f"更新学习行为记录成功: ID={record.id}")
            return record

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新学习行为记录失败: {str(e)}")
            raise

    def get_behavior_records(
        self,
        student_id: Optional[int] = None,
        category: Optional[BehaviorCategory] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[LearningBehaviorFeature]:
        """获取学习行为记录"""
        try:
            query = self.db.query(LearningBehaviorFeature)

            if student_id:
                query = query.filter(LearningBehaviorFeature.student_id == student_id)

            if category:
                query = query.filter(LearningBehaviorFeature.category == category.value)

            if start_date:
                query = query.filter(
                    LearningBehaviorFeature.event_timestamp >= start_date
                )

            if end_date:
                query = query.filter(
                    LearningBehaviorFeature.event_timestamp <= end_date
                )

            records = (
                query.order_by(LearningBehaviorFeature.event_timestamp.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            logger.info(f"获取学习行为记录: 数量={len(records)}")
            return records

        except Exception as e:
            logger.error(f"获取学习行为记录失败: {str(e)}")
            raise

    def calculate_debug_metrics(
        self, student_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """计算代码调试相关指标"""
        try:
            # 查询调试相关记录
            debug_records = (
                self.db.query(LearningBehaviorFeature)
                .filter(
                    and_(
                        LearningBehaviorFeature.student_id == student_id,
                        LearningBehaviorFeature.category.in_(
                            [
                                BehaviorCategory.CODE_DEBUGGING.value,
                                BehaviorCategory.LEARNING_ACTIVITY.value,
                            ]
                        ),
                        LearningBehaviorFeature.event_timestamp.between(
                            start_date, end_date
                        ),
                        LearningBehaviorFeature.debug_duration_seconds > 0,
                    )
                )
                .all()
            )

            if not debug_records:
                return {
                    "total_debug_duration": 0,
                    "avg_debug_duration": 0,
                    "debug_sessions_count": 0,
                    "total_debug_attempts": 0,
                    "avg_debug_attempts_per_session": 0,
                    "debug_efficiency_score": 0,
                }

            # 计算各项指标
            total_duration = sum(
                record.debug_duration_seconds for record in debug_records
            )
            avg_duration = total_duration / len(debug_records)
            sessions_count = len(debug_records)
            total_attempts = sum(record.debug_attempts for record in debug_records)
            avg_attempts = total_attempts / sessions_count if sessions_count > 0 else 0

            # 计算调试效率分数 (基于平均时长和成功率)
            success_records = [r for r in debug_records if r.success_indicator]
            success_rate = (
                len(success_records) / len(debug_records) if debug_records else 0
            )

            # 效率评分：成功率权重60%，时长权重40%
            efficiency_score = (
                success_rate * 0.6 + (1 - avg_duration / 3600) * 0.4
            ) * 100

            metrics = {
                "total_debug_duration": total_duration,
                "avg_debug_duration": round(avg_duration, 2),
                "debug_sessions_count": sessions_count,
                "total_debug_attempts": total_attempts,
                "avg_debug_attempts_per_session": round(avg_attempts, 2),
                "debug_success_rate": round(success_rate * 100, 2),
                "debug_efficiency_score": round(efficiency_score, 2),
            }

            logger.info(
                f"计算调试指标完成: 学生ID={student_id}, 会话数={sessions_count}"
            )
            return metrics

        except Exception as e:
            logger.error(f"计算调试指标失败: {str(e)}")
            raise

    def calculate_hardware_metrics(
        self, student_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """计算硬件操作相关指标"""
        try:
            # 查询硬件操作记录
            hardware_records = (
                self.db.query(LearningBehaviorFeature)
                .filter(
                    and_(
                        LearningBehaviorFeature.student_id == student_id,
                        LearningBehaviorFeature.category
                        == BehaviorCategory.HARDWARE_OPERATION.value,
                        LearningBehaviorFeature.event_timestamp.between(
                            start_date, end_date
                        ),
                        LearningBehaviorFeature.hardware_operations_count > 0,
                    )
                )
                .all()
            )

            if not hardware_records:
                return {
                    "total_operations": 0,
                    "successful_operations": 0,
                    "success_rate": 0,
                    "unique_hardware_types": 0,
                    "avg_connection_duration": 0,
                    "hardware_proficiency_score": 0,
                }

            # 计算各项指标
            total_ops = sum(
                record.hardware_operations_count for record in hardware_records
            )
            successful_ops = sum(
                record.successful_operations for record in hardware_records
            )
            success_rate = successful_ops / total_ops if total_ops > 0 else 0

            # 统计不同硬件类型
            hardware_types = set()
            for record in hardware_records:
                if record.hardware_types_used:
                    try:
                        types = json.loads(record.hardware_types_used)
                        hardware_types.update(types)
                    except Exception:
                        pass

            # 计算平均连接时长
            connection_durations = [
                r.hardware_connection_duration
                for r in hardware_records
                if r.hardware_connection_duration > 0
            ]
            avg_connection_duration = (
                statistics.mean(connection_durations) if connection_durations else 0
            )

            # 计算硬件熟练度分数
            # 基于成功率、操作多样性、平均时长等因素
            diversity_score = min(len(hardware_types) / 5, 1.0)  # 最多5种设备得满分
            duration_efficiency = (
                min(avg_connection_duration / 300, 1.0)
                if avg_connection_duration > 0
                else 0
            )

            proficiency_score = (
                success_rate * 0.5 + diversity_score * 0.3 + duration_efficiency * 0.2
            ) * 100

            metrics = {
                "total_operations": total_ops,
                "successful_operations": successful_ops,
                "success_rate": round(success_rate * 100, 2),
                "unique_hardware_types": len(hardware_types),
                "avg_connection_duration": round(avg_connection_duration, 2),
                "hardware_proficiency_score": round(proficiency_score, 2),
                "hardware_types_list": list(hardware_types),
            }

            logger.info(f"计算硬件指标完成: 学生ID={student_id}, 操作总数={total_ops}")
            return metrics

        except Exception as e:
            logger.error(f"计算硬件指标失败: {str(e)}")
            raise

    def generate_behavior_summary(
        self,
        student_id: int,
        period_start: datetime,
        period_end: datetime,
        period_type: str = "daily",
    ) -> LearningBehaviorSummary:
        """生成学习行为汇总"""
        try:
            # 计算各类指标
            debug_metrics = self.calculate_debug_metrics(
                student_id, period_start, period_end
            )
            hardware_metrics = self.calculate_hardware_metrics(
                student_id, period_start, period_end
            )

            # 获取学习活动记录
            activity_records = (
                self.db.query(LearningBehaviorFeature)
                .filter(
                    and_(
                        LearningBehaviorFeature.student_id == student_id,
                        LearningBehaviorFeature.category
                        == BehaviorCategory.LEARNING_ACTIVITY.value,
                        LearningBehaviorFeature.event_type.in_(
                            [
                                BehaviorEventType.LESSON_COMPLETE.value,
                                BehaviorEventType.EXERCISE_SUBMIT.value,
                            ]
                        ),
                        LearningBehaviorFeature.event_timestamp.between(
                            period_start, period_end
                        ),
                    )
                )
                .all()
            )

            # 统计学习成效
            lessons_completed = len(
                [
                    r
                    for r in activity_records
                    if r.event_type == BehaviorEventType.LESSON_COMPLETE.value
                ]
            )
            exercises_completed = len(
                [
                    r
                    for r in activity_records
                    if r.event_type == BehaviorEventType.EXERCISE_SUBMIT.value
                    and r.success_indicator
                ]
            )

            performance_scores = [
                r.performance_score
                for r in activity_records
                if r.performance_score is not None
            ]
            avg_performance = (
                statistics.mean(performance_scores) if performance_scores else 0
            )

            # 统计辅助特征
            help_requests = len([r for r in activity_records if r.help_requested])
            hints_used = sum(r.hints_used for r in activity_records)

            # 检查是否已存在相同时间段的汇总记录
            existing_summary = (
                self.db.query(LearningBehaviorSummary)
                .filter(
                    and_(
                        LearningBehaviorSummary.student_id == student_id,
                        LearningBehaviorSummary.period_type == period_type,
                        LearningBehaviorSummary.period_start == period_start,
                        LearningBehaviorSummary.period_end == period_end,
                    )
                )
                .first()
            )

            if existing_summary:
                # 更新现有记录
                summary = existing_summary
            else:
                # 创建新记录
                summary = LearningBehaviorSummary(
                    org_id=activity_records[0].org_id if activity_records else 1,
                    student_id=student_id,
                    period_type=period_type,
                    period_start=period_start,
                    period_end=period_end,
                )

            # 更新汇总数据
            summary.total_debug_duration = debug_metrics["total_debug_duration"]
            summary.avg_debug_duration = debug_metrics["avg_debug_duration"]
            summary.debug_sessions_count = debug_metrics["debug_sessions_count"]
            summary.total_hardware_operations = hardware_metrics["total_operations"]
            summary.successful_hardware_operations = hardware_metrics[
                "successful_operations"
            ]
            summary.hardware_success_rate = hardware_metrics["success_rate"]
            summary.unique_hardware_types = hardware_metrics["unique_hardware_types"]
            summary.lessons_completed = lessons_completed
            summary.exercises_completed = exercises_completed
            summary.average_performance_score = round(avg_performance, 2)
            summary.help_requests_count = help_requests
            summary.hints_used_count = hints_used
            summary.last_updated = datetime.utcnow()

            if not existing_summary:
                self.db.add(summary)

            self.db.commit()
            self.db.refresh(summary)

            logger.info(f"生成行为汇总完成: 学生ID={student_id}, 期间={period_type}")
            return summary

        except Exception as e:
            self.db.rollback()
            logger.error(f"生成行为汇总失败: {str(e)}")
            raise

    def get_behavior_analytics(
        self, request: BehaviorAnalyticsRequest
    ) -> Dict[str, Any]:
        """获取行为分析数据"""
        try:
            # 获取基础统计数据
            records = self.get_behavior_records(
                student_id=request.student_id,
                category=request.category,
                start_date=request.start_date,
                end_date=request.end_date,
            )

            # 计算详细分析
            debug_stats = (
                self.calculate_debug_metrics(
                    request.student_id, request.start_date, request.end_date
                )
                if request.student_id
                else {}
            )

            hardware_stats = (
                self.calculate_hardware_metrics(
                    request.student_id, request.start_date, request.end_date
                )
                if request.student_id
                else {}
            )

            # 生成趋势数据
            trends = self._generate_trends_data(records, request.period_type)

            # 计算学习效果指标
            learning_effectiveness = self._calculate_learning_effectiveness(records)

            analytics_data = {
                "student_id": request.student_id,
                "category": request.category.value if request.category else None,
                "period_type": request.period_type,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "total_records": len(records),
                "debug_statistics": debug_stats,
                "hardware_statistics": hardware_stats,
                "learning_effectiveness": learning_effectiveness,
                "trends": trends,
            }

            logger.info(f"获取行为分析数据完成: 记录数={len(records)}")
            return analytics_data

        except Exception as e:
            logger.error(f"获取行为分析数据失败: {str(e)}")
            raise

    def _generate_trends_data(
        self, records: List[LearningBehaviorFeature], period_type: str
    ) -> List[Dict[str, Any]]:
        """生成趋势数据"""
        if not records:
            return []

        # 按时间段分组
        period_groups = defaultdict(list)

        for record in records:
            if period_type == "daily":
                period_key = record.event_timestamp.date()
            elif period_type == "weekly":
                period_key = record.event_timestamp.isocalendar()[:2]  # (year, week)
            else:  # monthly
                period_key = (record.event_timestamp.year, record.event_timestamp.month)

            period_groups[period_key].append(record)

        # 生成趋势数据
        trends = []
        for period_key, period_records in sorted(period_groups.items()):
            trend_data = {
                "period": str(period_key),
                "record_count": len(period_records),
                "debug_sessions": len(
                    [
                        r
                        for r in period_records
                        if r.category == BehaviorCategory.CODE_DEBUGGING.value
                    ]
                ),
                "hardware_operations": sum(
                    r.hardware_operations_count
                    for r in period_records
                    if r.hardware_operations_count
                ),
                "success_rate": len([r for r in period_records if r.success_indicator])
                / len(period_records)
                * 100,
            }
            trends.append(trend_data)

        return trends

    def _calculate_learning_effectiveness(
        self, records: List[LearningBehaviorFeature]
    ) -> Dict[str, Any]:
        """计算学习效果指标"""
        if not records:
            return {}

        # 成功率统计
        success_records = [r for r in records if r.success_indicator]
        overall_success_rate = len(success_records) / len(records) * 100

        # 按类别统计成功率
        category_success = defaultdict(list)
        for record in records:
            category_success[record.category].append(
                1 if record.success_indicator else 0
            )

        category_rates = {
            category: (sum(success_list) / len(success_list)) * 100
            for category, success_list in category_success.items()
        }

        # 性能得分统计
        performance_scores = [
            r.performance_score for r in records if r.performance_score is not None
        ]
        avg_performance = (
            statistics.mean(performance_scores) if performance_scores else 0
        )

        return {
            "overall_success_rate": round(overall_success_rate, 2),
            "category_success_rates": {
                k: round(v, 2) for k, v in category_rates.items()
            },
            "average_performance_score": round(avg_performance, 2),
            "total_activities": len(records),
            "successful_activities": len(success_records),
        }

    def batch_process_behavior_data(
        self, student_id: int, days_back: int = 30
    ) -> Dict[str, Any]:
        """批量处理学习行为数据"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)

            # 生成不同周期的汇总
            periods = [
                ("daily", start_date, end_date),
                ("weekly", start_date, end_date),
                ("monthly", start_date.replace(day=1), end_date),
            ]

            results = {}
            for period_type, period_start, period_end in periods:
                summary = self.generate_behavior_summary(
                    student_id, period_start, period_end, period_type
                )
                results[period_type] = {
                    "summary_id": summary.id,
                    "period_start": summary.period_start,
                    "period_end": summary.period_end,
                    "debug_sessions": summary.debug_sessions_count,
                    "hardware_success_rate": summary.hardware_success_rate,
                    "lessons_completed": summary.lessons_completed,
                }

            logger.info(f"批量处理完成: 学生ID={student_id}")
            return results

        except Exception as e:
            logger.error(f"批量处理失败: {str(e)}")
            raise


# 便捷函数
def get_learning_behavior_service(db: Session = None) -> LearningBehaviorService:
    """获取学习行为服务实例"""
    return LearningBehaviorService(db)
