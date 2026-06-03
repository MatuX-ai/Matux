"""
Anti-Cheat Service - 防作弊检测引擎

提供多维度作弊检测：
1. 屏幕切换检测（blur/focus 事件）
2. 答题时间异常分析
3. 设备指纹聚类
4. 剪贴板操作检测
5. IP 异常检测
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.exam import (
    AttemptStatus,
    CheatEvent,
    CheatType,
    ExamAttempt,
)


class AntiCheatService:
    """防作弊检测服务"""

    async def report_cheat_event(
        self,
        db: AsyncSession,
        attempt_id: int,
        cheat_type: str,
        details: Optional[dict] = None,
        severity: int = 1,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> CheatEvent:
        """上报作弊事件"""
        event = CheatEvent(
            attempt_id=attempt_id,
            cheat_type=CheatType(cheat_type),
            severity=severity,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(event)

        # 检查是否触发阈值
        await self._check_threshold(db, attempt_id)

        await db.commit()
        await db.refresh(event)
        return event

    async def _check_threshold(self, db: AsyncSession, attempt_id: int):
        """检查是否达到作弊阈值"""
        # 获取该答题记录的所有作弊事件
        stmt = (
            select(CheatEvent)
            .filter(CheatEvent.attempt_id == attempt_id)
            .order_by(CheatEvent.timestamp.desc())
        )
        result = await db.execute(stmt)
        events = result.scalars().all()

        if not events:
            return

        # 计算总严重程度
        total_severity = sum(e.severity for e in events)

        # 获取答题记录信息
        attempt_stmt = select(ExamAttempt).filter(ExamAttempt.id == attempt_id)
        attempt_result = await db.execute(attempt_stmt)
        attempt = attempt_result.scalar_one_or_none()

        if not attempt:
            return

        # 检查考试配置的防作弊阈值
        from models.exam import Exam

        exam_stmt = select(Exam).filter(Exam.id == attempt.exam_id)
        exam_result = await db.execute(exam_stmt)
        exam = exam_result.scalar_one_or_none()

        if not exam or not exam.anti_cheat_enabled:
            return

        # 严重程度达到阈值时作废答题记录
        if total_severity >= 10:
            attempt.status = AttemptStatus.VOIDED

    async def analyze_time_anomaly(
        self,
        db: AsyncSession,
        attempt_id: int,
        question_id: int,
        time_spent_seconds: int,
        min_expected_seconds: int = 3,
    ) -> Optional[CheatEvent]:
        """分析答题时间异常"""
        if time_spent_seconds < min_expected_seconds:
            event = await self.report_cheat_event(
                db=db,
                attempt_id=attempt_id,
                cheat_type=CheatType.TIME_ANOMALY.value,
                details={
                    "question_id": question_id,
                    "time_spent_seconds": time_spent_seconds,
                    "min_expected_seconds": min_expected_seconds,
                },
                severity=3,
            )
            return event
        return None

    async def analyze_screen_switches(
        self,
        db: AsyncSession,
        attempt_id: int,
        current_switches: int,
        max_allowed: int = 3,
    ) -> Optional[CheatEvent]:
        """分析屏幕切换次数"""
        if current_switches > max_allowed:
            event = await self.report_cheat_event(
                db=db,
                attempt_id=attempt_id,
                cheat_type=CheatType.SCREEN_SWITCH.value,
                details={
                    "current_switches": current_switches,
                    "max_allowed": max_allowed,
                },
                severity=min(current_switches - max_allowed, 5),
            )
            return event
        return None

    async def analyze_paste_event(
        self,
        db: AsyncSession,
        attempt_id: int,
        content_length: int,
    ) -> CheatEvent:
        """分析粘贴事件"""
        severity = 1
        if content_length > 100:
            severity = 4
        elif content_length > 50:
            severity = 2

        return await self.report_cheat_event(
            db=db,
            attempt_id=attempt_id,
            cheat_type=CheatType.COPY_PASTE.value,
            details={"content_length": content_length},
            severity=severity,
        )

    async def analyze_multi_device(
        self,
        db: AsyncSession,
        attempt_id: int,
        device_fingerprint: str,
    ) -> Optional[CheatEvent]:
        """分析多设备登录"""
        # 获取当前答题记录
        attempt_stmt = select(ExamAttempt).filter(ExamAttempt.id == attempt_id)
        attempt_result = await db.execute(attempt_stmt)
        attempt = attempt_result.scalar_one_or_none()

        if not attempt:
            return None

        # 检查该用户的其他活跃答题记录是否有不同设备
        stmt = (
            select(ExamAttempt)
            .filter(
                ExamAttempt.user_id == attempt.user_id,
                ExamAttempt.id != attempt_id,
                ExamAttempt.status == AttemptStatus.IN_PROGRESS,
                ExamAttempt.device_fingerprint.isnot(None),
                ExamAttempt.device_fingerprint != device_fingerprint,
            )
        )
        result = await db.execute(stmt)
        other_attempts = result.scalars().all()

        if other_attempts:
            return await self.report_cheat_event(
                db=db,
                attempt_id=attempt_id,
                cheat_type=CheatType.MULTI_DEVICE.value,
                details={
                    "current_device": device_fingerprint,
                    "other_devices": [a.device_fingerprint for a in other_attempts],
                },
                severity=4,
            )

        return None

    async def get_cheat_events(
        self, db: AsyncSession, attempt_id: int
    ) -> list[CheatEvent]:
        """获取答题记录的作弊事件"""
        stmt = (
            select(CheatEvent)
            .filter(CheatEvent.attempt_id == attempt_id)
            .order_by(CheatEvent.timestamp.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_exam_cheat_summary(self, db: AsyncSession, exam_id: int) -> dict:
        """获取测验防作弊统计摘要"""
        # 获取所有被标记作弊的答题记录
        stmt = (
            select(CheatEvent)
            .join(ExamAttempt)
            .filter(ExamAttempt.exam_id == exam_id)
        )
        result = await db.execute(stmt)
        events = result.scalars().all()

        if not events:
            return {
                "total_events": 0,
                "voided_attempts": 0,
                "cheat_type_breakdown": {},
                "high_severity_count": 0,
            }

        # 按类型统计
        breakdown = {}
        for event in events:
            ctype = event.cheat_type.value if event.cheat_type else "unknown"
            breakdown[ctype] = breakdown.get(ctype, 0) + 1

        # 严重事件统计
        high_severity = sum(1 for e in events if e.severity >= 4)

        # 作废统计
        attempt_ids = set(e.attempt_id for e in events)
        voided_stmt = select(func.count()).select_from(ExamAttempt).filter(
            ExamAttempt.id.in_(attempt_ids),
            ExamAttempt.status == AttemptStatus.VOIDED,
        )
        voided_result = await db.execute(voided_stmt)

        return {
            "total_events": len(events),
            "voided_attempts": voided_result.scalar() or 0,
            "cheat_type_breakdown": breakdown,
            "high_severity_count": high_severity,
        }


# 全局服务实例
anti_cheat_service = AntiCheatService()
