"""
租户感知的数据库会话
自动为查询添加租户过滤条件
"""

import logging
from typing import Any, Optional, Type

from sqlalchemy.orm import Query, Session
from sqlalchemy.sql.elements import BinaryExpression

from utils.tenant_context import TenantContext

logger = logging.getLogger(__name__)


class TenantAwareQuery(Query):
    """租户感知的查询类"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tenant_filtered = False

    def _apply_tenant_filter(self):
        """
        应用租户过滤条件（直接修改 self 的 where 条件）
        """
        if self._tenant_filtered:
            return

        self._tenant_filtered = True

        tenant_id = TenantContext.get_current_tenant()

        # 如果没有设置租户上下文，则不限制
        if tenant_id is None:
            logger.debug("未设置租户上下文，不应用过滤")
            return

        # 获取查询的实体（使用 getattr 绕过 Pylance 对私有属性的访问检查）
        primary_entity = getattr(self, '_primary_entity', None)
        if not primary_entity:
            return

        entity = primary_entity.entity_zero.class_

        # 检查实体是否有org_id字段
        if hasattr(entity, "org_id"):
            # 直接在 self 上添加过滤条件
            self._where_criteria += (entity.org_id == tenant_id,)
            logger.debug(f"为实体 {entity.__name__} 应用租户过滤: org_id = {tenant_id}")

    def all(self):
        """重写all方法，自动应用租户过滤"""
        self._apply_tenant_filter()
        return super().all()

    def first(self):
        """重写first方法，自动应用租户过滤"""
        self._apply_tenant_filter()
        return super().first()

    def one(self):
        """重写one方法，自动应用租户过滤"""
        self._apply_tenant_filter()
        return super().one()

    def one_or_none(self):
        """重写one_or_none方法，自动应用租户过滤"""
        self._apply_tenant_filter()
        return super().one_or_none()

    def count(self):
        """重写count方法，自动应用租户过滤"""
        self._apply_tenant_filter()
        return super().count()

    def get(self, ident):
        """重写get方法，自动应用租户过滤"""
        result = super().get(ident)
        if result and hasattr(result, "org_id"):
            tenant_id = TenantContext.get_current_tenant()
            if tenant_id and result.org_id != tenant_id:
                logger.warning(f"尝试访问不属于当前租户的数据: {ident}")
                return None
        return result


class TenantAwareSession(Session):
    """租户感知的数据库会话类"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 替换默认的query类
        self._query_cls = TenantAwareQuery

    def query(self, *entities: Any, **kwargs: Any) -> TenantAwareQuery:  # type: ignore[override]
        """
        重写query方法，返回租户感知的查询对象

        Args:
            *entities: 查询的实体
            **kwargs: 其他参数

        Returns:
            TenantAwareQuery: 租户感知的查询对象
        """
        return super().query(*entities, **kwargs)  # type: ignore[return-value]

    def add(self, instance, *args, **kwargs):
        """
        重写add方法，自动设置租户ID

        Args:
            instance: 要添加的实例
            *args: 其他参数
            **kwargs: 其他关键字参数
        """
        # 自动设置租户ID
        self._set_tenant_id(instance)
        return super().add(instance, *args, **kwargs)

    def bulk_save_objects(self, objects, *args, **kwargs):
        """
        重写bulk_save_objects方法，批量设置租户ID

        Args:
            objects: 对象列表
            *args: 其他参数
            **kwargs: 其他关键字参数
        """
        for obj in objects:
            self._set_tenant_id(obj)
        return super().bulk_save_objects(objects, *args, **kwargs)

    def _set_tenant_id(self, instance):
        """
        为实例设置租户ID

        Args:
            instance: 数据库实例
        """
        tenant_id = TenantContext.get_current_tenant()

        if tenant_id and hasattr(instance, "org_id"):
            # 如果实例已经有org_id且与当前租户不匹配，记录警告
            if (
                getattr(instance, "org_id", None) is not None
                and instance.org_id != tenant_id
            ):
                logger.warning(
                    f"实例 {type(instance).__name__} 的org_id ({instance.org_id}) "
                    f"与当前租户 ({tenant_id}) 不匹配"
                )

            # 设置租户ID
            instance.org_id = tenant_id
            logger.debug(f"为实例 {type(instance).__name__} 设置租户ID: {tenant_id}")


class TenantQueryHelper:
    """租户查询助手类"""

    @staticmethod
    def filter_by_tenant(query: Query, model_class: Type[Any]) -> Query:
        """
        为查询添加租户过滤条件

        Args:
            query: SQLAlchemy查询对象
            model_class: 模型类

        Returns:
            Query: 添加了租户过滤的查询对象
        """
        tenant_id = TenantContext.get_current_tenant()

        if tenant_id and hasattr(model_class, "org_id"):
            return query.filter(model_class.org_id == tenant_id)

        return query

    @staticmethod
    def validate_tenant_ownership(
        instance: Any, expected_org_id: Optional[int] = None
    ) -> bool:
        """
        验证实例是否属于指定租户

        Args:
            instance: 数据库实例
            expected_org_id: 期望的租户ID，如果为None则使用当前上下文

        Returns:
            bool: 如果属于指定租户返回True，否则返回False
        """
        if not hasattr(instance, "org_id"):
            # 如果实例没有org_id字段，则认为验证通过
            return True

        if expected_org_id is None:
            expected_org_id = TenantContext.get_current_tenant()

        if expected_org_id is None:
            # 没有指定租户ID且上下文也没有，认为验证通过
            return True

        actual_org_id = getattr(instance, "org_id", None)
        is_valid = actual_org_id == expected_org_id

        if not is_valid:
            logger.warning(
                f"租户所有权验证失败: 实例(org_id={actual_org_id}) "
                f"不属于租户({expected_org_id})"
            )

        return is_valid

    @staticmethod
    def get_tenant_filter_conditions(
        model_class: Type[Any],
    ) -> Optional[BinaryExpression]:
        """
        获取模型的租户过滤条件

        Args:
            model_class: 模型类

        Returns:
            Optional[BinaryExpression]: 过滤条件，如果没有租户上下文则返回None
        """
        tenant_id = TenantContext.get_current_tenant()

        if tenant_id and hasattr(model_class, "org_id"):
            return model_class.org_id == tenant_id

        return None

    @staticmethod
    def apply_tenant_filters_to_query(query: Query) -> Query:
        """
        为查询应用所有相关的租户过滤条件

        Args:
            query: SQLAlchemy查询对象

        Returns:
            Query: 应用了租户过滤的查询对象
        """
        # 获取查询涉及的所有实体
        entities = getattr(query, "_entities", [])

        for entity in entities:
            if hasattr(entity, "entity_zero") and entity.entity_zero:
                model_class = entity.entity_zero.class_
                query = TenantQueryHelper.filter_by_tenant(query, model_class)

        return query


# 便捷函数
def get_tenant_aware_session(session: Session) -> TenantAwareSession:
    """
    将普通会话转换为租户感知会话

    Args:
        session: 普通数据库会话

    Returns:
        TenantAwareSession: 租户感知会话
    """
    if isinstance(session, TenantAwareSession):
        return session

    # 创建新的租户感知会话
    tenant_session = TenantAwareSession(
        bind=session.bind,
        autoflush=session.autoflush,
        autocommit=getattr(session, 'autocommit', False),
        expire_on_commit=session.expire_on_commit,
    )

    return tenant_session


def with_tenant_filter(query: Query, model_class: Optional[Type[Any]] = None) -> Query:
    """
    为查询添加租户过滤的便捷函数

    Args:
        query: SQLAlchemy查询对象
        model_class: 模型类（可选）

    Returns:
        Query: 应用了租户过滤的查询对象
    """
    if model_class:
        return TenantQueryHelper.filter_by_tenant(query, model_class)
    else:
        return TenantQueryHelper.apply_tenant_filters_to_query(query)
