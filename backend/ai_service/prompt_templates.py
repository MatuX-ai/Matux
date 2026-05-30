"""
Prompt模板管理系统
负责Prompt模板的创建、管理、检索和使用统计
"""

from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional

from models.creativity_models import (
    PromptTemplate,
    PromptTemplateCreate,
    PromptTemplateResponse,
)
from utils.database import get_sync_db

logger = logging.getLogger(__name__)


class PromptTemplateManager:
    """Prompt模板管理器"""

    def __init__(self):
        self.default_categories = [
            "technology",
            "business",
            "design",
            "education",
            "healthcare",
            "environment",
            "entertainment",
            "other",
        ]

    async def create_template(
        self, template_data: PromptTemplateCreate, user_id: Optional[int] = None
    ) -> PromptTemplateResponse:
        """
        创建新的Prompt模板

        Args:
            template_data: 模板创建数据
            user_id: 创建者用户ID（可选）

        Returns:
            PromptTemplateResponse: 创建的模板响应
        """
        logger.info(f"创建新的Prompt模板: {template_data.name}")

        try:
            with get_sync_db() as db:
                # 验证模板变量格式
                if template_data.variables:
                    self._validate_template_variables(template_data.variables)

                # 创建模板记录
                template_record = PromptTemplate(
                    name=template_data.name,
                    category=template_data.category,
                    template=template_data.template,
                    variables=(
                        json.dumps(template_data.variables)
                        if template_data.variables
                        else None
                    ),
                    description=template_data.description,
                    is_public=template_data.is_public,
                    created_by=user_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                # 添加到数据库
                db.add(template_record)
                db.commit()
                db.refresh(template_record)

                logger.info(f"模板创建成功，ID: {template_record.id}")

                return PromptTemplateResponse(
                    id=template_record.id,
                    name=template_record.name,
                    category=template_record.category,
                    template=template_record.template,
                    variables=(
                        json.loads(template_record.variables)
                        if template_record.variables
                        else None
                    ),
                    description=template_record.description,
                    usage_count=template_record.usage_count,
                    is_public=template_record.is_public,
                    created_by=template_record.created_by,
                    created_at=template_record.created_at,
                    updated_at=template_record.updated_at,
                )

        except Exception as e:
            logger.error(f"创建模板失败: {str(e)}")
            raise

    async def get_template(self, template_id: int) -> Optional[PromptTemplateResponse]:
        """
        获取指定ID的模板

        Args:
            template_id: 模板ID

        Returns:
            PromptTemplateResponse: 模板响应或None
        """
        logger.debug(f"获取模板: {template_id}")

        try:
            with get_sync_db() as db:
                template_record = (
                    db.query(PromptTemplate)
                    .filter(PromptTemplate.id == template_id)
                    .first()
                )

                if not template_record:
                    return None

                return PromptTemplateResponse(
                    id=template_record.id,
                    name=template_record.name,
                    category=template_record.category,
                    template=template_record.template,
                    variables=(
                        json.loads(template_record.variables)
                        if template_record.variables
                        else None
                    ),
                    description=template_record.description,
                    usage_count=template_record.usage_count,
                    is_public=template_record.is_public,
                    created_by=template_record.created_by,
                    created_at=template_record.created_at,
                    updated_at=template_record.updated_at,
                )

        except Exception as e:
            logger.error(f"获取模板失败: {str(e)}")
            raise

    async def list_templates(
        self,
        category: Optional[str] = None,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[PromptTemplateResponse]:
        """
        列出模板

        Args:
            category: 分类筛选
            is_public: 是否公开筛选
            limit: 限制数量
            offset: 偏移量

        Returns:
            List[PromptTemplateResponse]: 模板列表
        """
        logger.debug(f"列出模板 - 分类: {category}, 公开: {is_public}")

        try:
            with get_sync_db() as db:
                query = db.query(PromptTemplate)

                # 应用筛选条件
                if category:
                    query = query.filter(PromptTemplate.category == category)

                if is_public is not None:
                    query = query.filter(PromptTemplate.is_public == is_public)

                # 应用分页
                templates = query.offset(offset).limit(limit).all()

                return [
                    PromptTemplateResponse(
                        id=template.id,
                        name=template.name,
                        category=template.category,
                        template=template.template,
                        variables=(
                            json.loads(template.variables)
                            if template.variables
                            else None
                        ),
                        description=template.description,
                        usage_count=template.usage_count,
                        is_public=template.is_public,
                        created_by=template.created_by,
                        created_at=template.created_at,
                        updated_at=template.updated_at,
                    )
                    for template in templates
                ]

        except Exception as e:
            logger.error(f"列出模板失败: {str(e)}")
            raise

    async def update_template(
        self, template_id: int, update_data: Dict[str, Any]
    ) -> Optional[PromptTemplateResponse]:
        """
        更新模板

        Args:
            template_id: 模板ID
            update_data: 更新数据

        Returns:
            PromptTemplateResponse: 更新后的模板或None
        """
        logger.info(f"更新模板: {template_id}")

        try:
            with get_sync_db() as db:
                template_record = (
                    db.query(PromptTemplate)
                    .filter(PromptTemplate.id == template_id)
                    .first()
                )

                if not template_record:
                    return None

                # 更新字段
                if "name" in update_data:
                    template_record.name = update_data["name"]
                if "category" in update_data:
                    template_record.category = update_data["category"]
                if "template" in update_data:
                    template_record.template = update_data["template"]
                if "variables" in update_data:
                    self._validate_template_variables(update_data["variables"])
                    template_record.variables = json.dumps(update_data["variables"])
                if "description" in update_data:
                    template_record.description = update_data["description"]
                if "is_public" in update_data:
                    template_record.is_public = update_data["is_public"]

                template_record.updated_at = datetime.utcnow()

                db.commit()
                db.refresh(template_record)

                logger.info(f"模板更新成功: {template_id}")

                return self._record_to_response(template_record)

        except Exception as e:
            logger.error(f"更新模板失败: {str(e)}")
            raise

    async def delete_template(self, template_id: int) -> bool:
        """
        删除模板

        Args:
            template_id: 模板ID

        Returns:
            bool: 是否删除成功
        """
        logger.info(f"删除模板: {template_id}")

        try:
            with get_sync_db() as db:
                template_record = (
                    db.query(PromptTemplate)
                    .filter(PromptTemplate.id == template_id)
                    .first()
                )

                if not template_record:
                    return False

                db.delete(template_record)
                db.commit()

                logger.info(f"模板删除成功: {template_id}")
                return True

        except Exception as e:
            logger.error(f"删除模板失败: {str(e)}")
            raise

    async def increment_usage_count(self, template_id: int) -> bool:
        """
        增加模板使用次数

        Args:
            template_id: 模板ID

        Returns:
            bool: 是否更新成功
        """
        try:
            with get_sync_db() as db:
                template_record = (
                    db.query(PromptTemplate)
                    .filter(PromptTemplate.id == template_id)
                    .first()
                )

                if template_record:
                    template_record.usage_count += 1
                    template_record.updated_at = datetime.utcnow()
                    db.commit()
                    return True

            return False

        except Exception as e:
            logger.warning(f"增加使用次数失败: {str(e)}")
            return False

    async def search_templates(
        self, query: str, limit: int = 20
    ) -> List[PromptTemplateResponse]:
        """
        搜索模板

        Args:
            query: 搜索关键词
            limit: 限制数量

        Returns:
            List[PromptTemplateResponse]: 搜索结果
        """
        logger.debug(f"搜索模板: {query}")

        try:
            with get_sync_db() as db:
                # 搜索名称、描述和分类
                search_results = (
                    db.query(PromptTemplate)
                    .filter(
                        (PromptTemplate.name.ilike(f"%{query}%"))
                        | (PromptTemplate.description.ilike(f"%{query}%"))
                        | (PromptTemplate.category.ilike(f"%{query}%"))
                    )
                    .filter(PromptTemplate.is_public == True)
                    .limit(limit)
                    .all()
                )

                return [
                    self._record_to_response(template) for template in search_results
                ]

        except Exception as e:
            logger.error(f"搜索模板失败: {str(e)}")
            raise

    async def get_popular_templates(
        self, limit: int = 10
    ) -> List[PromptTemplateResponse]:
        """
        获取热门模板（按使用次数排序）

        Args:
            limit: 限制数量

        Returns:
            List[PromptTemplateResponse]: 热门模板列表
        """
        logger.debug(f"获取热门模板，限制: {limit}")

        try:
            with get_sync_db() as db:
                popular_templates = (
                    db.query(PromptTemplate)
                    .filter(PromptTemplate.is_public == True)
                    .order_by(PromptTemplate.usage_count.desc())
                    .limit(limit)
                    .all()
                )

                return [
                    self._record_to_response(template) for template in popular_templates
                ]

        except Exception as e:
            logger.error(f"获取热门模板失败: {str(e)}")
            raise

    async def get_template_statistics(self) -> Dict[str, Any]:
        """
        获取模板统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            with get_sync_db() as db:
                total_count = db.query(PromptTemplate).count()
                public_count = (
                    db.query(PromptTemplate)
                    .filter(PromptTemplate.is_public == True)
                    .count()
                )

                # 按分类统计
                category_stats = {}
                for category in self.default_categories:
                    count = (
                        db.query(PromptTemplate)
                        .filter(PromptTemplate.category == category)
                        .count()
                    )
                    category_stats[category] = count

                # 使用次数统计
                total_usages = db.query(PromptTemplate.usage_count).sum() or 0

                return {
                    "total_templates": total_count,
                    "public_templates": public_count,
                    "private_templates": total_count - public_count,
                    "category_distribution": category_stats,
                    "total_usages": int(total_usages),
                    "average_usage_per_template": (
                        round(total_usages / total_count, 2) if total_count > 0 else 0
                    ),
                }

        except Exception as e:
            logger.error(f"获取模板统计失败: {str(e)}")
            raise

    async def render_template(self, template_id: int, variables: Dict[str, Any]) -> str:
        """
        渲染模板（填充变量）

        Args:
            template_id: 模板ID
            variables: 变量值字典

        Returns:
            str: 渲染后的模板内容
        """
        template = await self.get_template(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")

        rendered_template = template.template

        # 替换变量
        if variables and template.variables:
            for var_name, var_value in variables.items():
                placeholder = f"{{{var_name}}}"
                rendered_template = rendered_template.replace(
                    placeholder, str(var_value)
                )

        # 增加使用次数
        await self.increment_usage_count(template_id)

        return rendered_template

    def _validate_template_variables(self, variables: Dict[str, Any]):
        """验证模板变量格式"""
        if not isinstance(variables, dict):
            raise ValueError("变量必须是字典格式")

        for var_name, var_config in variables.items():
            if not isinstance(var_config, dict):
                raise ValueError(f"变量 {var_name} 的配置必须是字典格式")

            if "type" not in var_config:
                raise ValueError(f"变量 {var_name} 必须包含 type 字段")

            valid_types = ["string", "number", "boolean", "array", "object"]
            if var_config["type"] not in valid_types:
                raise ValueError(f"变量 {var_name} 的类型必须是 {valid_types} 之一")

    def _record_to_response(self, record: PromptTemplate) -> PromptTemplateResponse:
        """将数据库记录转换为响应对象"""
        return PromptTemplateResponse(
            id=record.id,
            name=record.name,
            category=record.category,
            template=record.template,
            variables=json.loads(record.variables) if record.variables else None,
            description=record.description,
            usage_count=record.usage_count,
            is_public=record.is_public,
            created_by=record.created_by,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


# 创建全局实例
prompt_template_manager = PromptTemplateManager()
