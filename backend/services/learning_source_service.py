"""
学习来源管理服务
处理学习来源的创建、查询、更新等业务逻辑
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload

from models.learning_source import (
    LearningSource,
    LearningSourceCreate,
    LearningSourceResponse,
    LearningSourceStatus,
    LearningSourceType,
    LearningSourceUpdate,
)
from models.user import User

logger = logging.getLogger(__name__)


class LearningSourceService:
    """学习来源管理服务类"""

    def __init__(self, db: Session):
        self.db = db

    def create_learning_source(
        self, source_data: LearningSourceCreate, current_user: Optional[User] = None
    ) -> LearningSource:
        """
        创建学习来源记录

        Args:
            source_data: 学习来源创建数据
            current_user: 当前用户（可选）

        Returns:
            LearningSource: 创建的学习来源对象

        Raises:
            ValueError: 数据验证失败
        """
        try:
            # 检查用户是否存在
            user = self.db.query(User).filter(User.id == source_data.user_id).first()
            if not user:
                raise ValueError(f"用户ID {source_data.user_id} 不存在")

            # 检查组织是否存在（如果提供了org_id）
            if source_data.org_id:
                from models.license import Organization
                org = (
                    self.db.query(Organization)
                    .filter(Organization.id == source_data.org_id)
                    .first()
                )
                if not org:
                    raise ValueError(f"组织ID {source_data.org_id} 不存在")

            # 检查是否已存在相同的学习来源
            existing = (
                self.db.query(LearningSource)
                .filter(
                    LearningSource.user_id == source_data.user_id,
                    LearningSource.source_type == source_data.source_type,
                    LearningSource.org_id == source_data.org_id,
                    LearningSource.name == source_data.name,
                )
                .first()
            )
            if existing:
                raise ValueError("该学习来源已存在")

            # 如果设置为主来源，需要取消其他主来源
            if source_data.is_primary:
                self._clear_primary_sources(source_data.user_id)

            # 创建学习来源
            source = LearningSource(**source_data.dict())
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)

            logger.info(
                f"用户 {source_data.user_id} 创建学习来源: {source_data.name}"
            )
            return source

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建学习来源失败: {str(e)}")
            raise

    def get_learning_source(self, source_id: int) -> Optional[LearningSource]:
        """获取学习来源详情"""
        return (
            self.db.query(LearningSource)
            .options(joinedload(LearningSource.organization))
            .filter(LearningSource.id == source_id)
            .first()
        )

    def get_user_learning_sources(
        self,
        user_id: int,
        source_type: Optional[LearningSourceType] = None,
        status: Optional[LearningSourceStatus] = None,
        include_inactive: bool = False,
    ) -> List[LearningSource]:
        """
        获取用户的所有学习来源

        Args:
            user_id: 用户ID
            source_type: 学习来源类型过滤
            status: 状态过滤
            include_inactive: 是否包含已停用的来源

        Returns:
            List[LearningSource]: 学习来源列表
        """
        query = (
            self.db.query(LearningSource)
            .options(joinedload(LearningSource.organization))
            .filter(LearningSource.user_id == user_id)
        )

        if source_type:
            query = query.filter(LearningSource.source_type == source_type)

        if status:
            query = query.filter(LearningSource.status == status)
        elif not include_inactive:
            query = query.filter(LearningSource.status == LearningSourceStatus.ACTIVE)

        return query.order_by(LearningSource.is_primary.desc(), LearningSource.created_at.desc()).all()

    def update_learning_source(
        self, source_id: int, source_data: LearningSourceUpdate
    ) -> LearningSource:
        """
        更新学习来源

        Args:
            source_id: 学习来源ID
            source_data: 更新数据

        Returns:
            LearningSource: 更新后的学习来源

        Raises:
            ValueError: 数据验证失败或不存在
        """
        source = self.get_learning_source(source_id)
        if not source:
            raise ValueError(f"学习来源ID {source_id} 不存在")

        # 如果设置为主来源，需要取消其他主来源
        if source_data.is_primary and not source.is_primary:
            self._clear_primary_sources(source.user_id)

        # 更新字段
        update_data = source_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(source, key, value)

        self.db.commit()
        self.db.refresh(source)

        logger.info(f"更新学习来源: {source_id}")
        return source

    def delete_learning_source(self, source_id: int, soft: bool = True) -> bool:
        """
        删除学习来源

        Args:
            source_id: 学习来源ID
            soft: 是否软删除（默认True）

        Returns:
            bool: 是否删除成功
        """
        source = self.get_learning_source(source_id)
        if not source:
            raise ValueError(f"学习来源ID {source_id} 不存在")

        if soft:
            # 软删除
            source.is_active = False
            source.status = LearningSourceStatus.INACTIVE
            self.db.commit()
        else:
            # 硬删除
            self.db.delete(source)
            self.db.commit()

        logger.info(f"删除学习来源: {source_id}, 软删除: {soft}")
        return True

    def _clear_primary_sources(self, user_id: int) -> None:
        """清除用户的所有主学习来源标记"""
        self.db.query(LearningSource).filter(
            LearningSource.user_id == user_id,
            LearningSource.is_primary == True,
        ).update({"is_primary": False})
        self.db.commit()

    def get_source_stats(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户学习来源统计

        Args:
            user_id: 用户ID

        Returns:
            Dict: 统计信息
        """
        sources = self.get_user_learning_sources(user_id, include_inactive=True)

        stats = {
            "total": len(sources),
            "active": len([s for s in sources if s.status == LearningSourceStatus.ACTIVE]),
            "by_type": {},
            "primary": None,
        }

        # 按类型统计
        for source_type in LearningSourceType:
            count = len([s for s in sources if s.source_type == source_type])
            if count > 0:
                stats["by_type"][source_type.value] = count

        # 获取主来源
        primary = next((s for s in sources if s.is_primary), None)
        if primary:
            stats["primary"] = LearningSourceResponse.model_validate(primary).model_dump()

        return stats
