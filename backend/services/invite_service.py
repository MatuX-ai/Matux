"""
【P3-C】邀请码服务

负责：
- 生成邀请码（唯一性 + 限制 + 奖励）
- 使用邀请码（注册时调用）
- 追踪邀请记录
- 奖励发放（mock 实现，未来接积分系统）
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.share import (
    InviteCode,
    InviteCodeStatus,
    InviteRecord,
    InviteRecordStatus,
    RewardType,
)
from utils.short_code import generate_unique_short_code

logger = logging.getLogger(__name__)


class InviteCodeAlreadyExhausted(Exception):
    """邀请码已达使用上限"""
    pass


class InviteCodeExpired(Exception):
    """邀请码已过期"""
    pass


class InviteCodeNotFound(Exception):
    """邀请码不存在"""
    pass


class InviteService:
    """邀请码服务"""

    def __init__(self, db: Session):
        self.db = db

    # ========== 生成邀请码 ==========

    def create_code(
        self,
        creator_id: int,
        usage_limit: Optional[int] = None,
        reward_type: str = RewardType.POINTS,
        reward_value: int = 100,
        channel: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> InviteCode:
        """
        创建邀请码

        Args:
            creator_id: 创建者用户 ID
            usage_limit: 使用上限（None = 无限）
            reward_type: 奖励类型
            reward_value: 奖励值
            channel: 推广渠道
            expires_at: 过期时间

        Returns:
            InviteCode 实例
        """
        # 生成唯一邀请码
        code = generate_unique_short_code(
            check_exists=self._check_code_exists,
            length=8,
        )

        invite = InviteCode(
            code=code,
            creator_id=creator_id,
            usage_limit=usage_limit,
            reward_type=reward_type,
            reward_value=reward_value,
            channel=channel,
            status=InviteCodeStatus.ACTIVE,
            expires_at=expires_at,
        )
        self.db.add(invite)
        self.db.commit()
        self.db.refresh(invite)

        logger.info(
            f"邀请码已创建：code={invite.code} creator={creator_id} "
            f"reward={reward_type}:{reward_value}"
        )
        return invite

    # ========== 查询 ==========

    def get_by_code(self, code: str) -> Optional[InviteCode]:
        """通过 code 查询"""
        return self.db.query(InviteCode).filter_by(code=code).first()

    def get_by_id(self, code_id: int) -> Optional[InviteCode]:
        """通过 ID 查询"""
        return self.db.query(InviteCode).filter_by(id=code_id).first()

    def list_by_creator(
        self, creator_id: int, limit: int = 50, offset: int = 0
    ) -> List[InviteCode]:
        """列出我创建的所有邀请码"""
        return (
            self.db.query(InviteCode)
            .filter_by(creator_id=creator_id)
            .order_by(InviteCode.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def list_records_by_inviter(
        self, inviter_id: int, limit: int = 50, offset: int = 0
    ) -> List[InviteRecord]:
        """列出我发起的所有邀请记录"""
        return (
            self.db.query(InviteRecord)
            .filter_by(inviter_id=inviter_id)
            .order_by(InviteRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    # ========== 使用邀请码 ==========

    def use_code(
        self,
        code: str,
        invitee_id: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> InviteRecord:
        """
        使用邀请码（被邀请人注册后调用）

        Args:
            code: 邀请码
            invitee_id: 被邀请人用户 ID
            metadata: 扩展元数据（IP、设备等）

        Returns:
            InviteRecord 实例

        Raises:
            InviteCodeNotFound: 邀请码不存在
            InviteCodeAlreadyExhausted: 已达使用上限
            InviteCodeExpired: 已过期
        """
        invite = self.get_by_code(code)
        if not invite:
            raise InviteCodeNotFound(f"邀请码不存在：{code}")
        if not invite.is_available():
            # 优先按业务语义检查：使用上限 → 过期 → 状态
            if invite.usage_limit and invite.used_count >= invite.usage_limit:
                raise InviteCodeAlreadyExhausted(
                    f"邀请码已达使用上限（{invite.usage_limit} 次）"
                )
            if invite.expires_at:
                # 兼容 SQLite 测试场景：naive vs aware datetime 比较
                now = datetime.now(timezone.utc)
                expires = invite.expires_at
                if expires.tzinfo is None:
                    now = now.replace(tzinfo=None)
                if expires < now:
                    # 标记为过期
                    invite.status = InviteCodeStatus.EXPIRED
                    self.db.commit()
                    raise InviteCodeExpired(f"邀请码已过期")
            if invite.status != InviteCodeStatus.ACTIVE:
                raise InviteCodeNotFound(f"邀请码已 {invite.status}")

        # 创建邀请记录
        record = InviteRecord(
            code_id=invite.id,
            inviter_id=invite.creator_id,
            invitee_id=invitee_id,
            status=InviteRecordStatus.REGISTERED,
            registered_at=datetime.now(timezone.utc),
            extra_metadata=metadata or {},
        )
        self.db.add(record)

        # 更新使用次数
        invite.used_count = (invite.used_count or 0) + 1
        if invite.usage_limit and invite.used_count >= invite.usage_limit:
            invite.status = InviteCodeStatus.EXHAUSTED

        self.db.commit()
        self.db.refresh(record)

        # 触发奖励发放（mock：仅记录日志，未来接积分系统）
        self._schedule_reward(record, invite)

        logger.info(
            f"邀请码已使用：code={code} invitee={invitee_id} "
            f"reward={invite.reward_type}:{invite.reward_value}"
        )
        return record

    # ========== 奖励发放 ==========

    def _schedule_reward(self, record: InviteRecord, invite: InviteCode) -> None:
        """
        触发奖励发放（mock 实现）

        当前实现：
        - 仅记录日志
        - 标记记录为 "rewarded" 状态
        - 未来接积分系统时实现真正的奖励发放
        """
        try:
            logger.info(
                f"[mock 奖励发放] inviter={record.inviter_id} "
                f"reward={invite.reward_type}:{invite.reward_value}"
            )
            record.rewarded_at = datetime.now(timezone.utc)
            record.status = InviteRecordStatus.REWARDED
            self.db.commit()
        except Exception as e:
            logger.warning(f"奖励发放失败（mock）：{e}")

    # ========== 内部方法 ==========

    def _check_code_exists(self, code: str) -> bool:
        """检查邀请码是否已存在"""
        return self.db.query(InviteCode).filter_by(code=code).first() is not None


# ==================== 工厂方法 ====================


def get_invite_service(db: Session) -> InviteService:
    """获取邀请服务实例（工厂方法）"""
    return InviteService(db)


__all__ = [
    "InviteService",
    "InviteCodeNotFound",
    "InviteCodeAlreadyExhausted",
    "InviteCodeExpired",
    "get_invite_service",
]