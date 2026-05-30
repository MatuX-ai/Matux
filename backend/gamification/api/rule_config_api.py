"""
规则配置API接口
提供规则引擎的配置管理、规则创建、更新等功能
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..models.rule_engine import (
    GamificationRule,
    RuleAction,
    RuleActionType,
    RuleCondition,
    RuleConditionType,
    RuleEngineConfig,
    RuleOperator,
)
from ..services.rule_engine_service import RuleEngineService

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/rules", tags=["规则管理"])


# 请求/响应模型
class RuleConditionRequest(BaseModel):
    condition_type: str
    operator: str
    value: Any
    field_name: Optional[str] = None


class RuleActionRequest(BaseModel):
    action_type: str
    parameters: Dict[str, Any]


class GamificationRuleRequest(BaseModel):
    name: str
    description: str
    conditions: List[RuleConditionRequest]
    actions: List[RuleActionRequest]
    priority: int = 0
    cooldown_seconds: int = 0
    max_executions: int = -1


class RuleExecutionResult(BaseModel):
    rule_id: str
    rule_name: str
    success: bool
    execution_time: str
    details: Optional[str] = None


class RuleStatisticsResponse(BaseModel):
    total_rules: int
    active_rules: int
    rule_execution_counts: Dict[str, int]
    streak_counter_count: int


# 依赖注入
def get_rule_engine_service() -> RuleEngineService:
    """获取规则引擎服务实例"""
    return RuleEngineService()


@router.get("/list", response_model=List[Dict[str, Any]])
async def list_rules(
    active_only: bool = Query(False, description="只显示激活的规则"),
    service: RuleEngineService = Depends(get_rule_engine_service),
):
    """
    获取规则列表

    Args:
        active_only: 是否只显示激活的规则
        service: 规则引擎服务依赖

    Returns:
        规则列表
    """
    try:
        if active_only:
            rules = service.config.get_active_rules()
        else:
            rules = service.config.rules

        return [rule.to_dict() for rule in rules]
    except Exception as e:
        logger.error(f"获取规则列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取规则列表失败")


@router.get("/{rule_id}", response_model=Dict[str, Any])
async def get_rule(
    rule_id: str, service: RuleEngineService = Depends(get_rule_engine_service)
):
    """
    获取特定规则详情

    Args:
        rule_id: 规则ID
        service: 规则引擎服务依赖

    Returns:
        规则详情
    """
    try:
        for rule in service.config.rules:
            if rule.rule_id == rule_id:
                return rule.to_dict()

        raise HTTPException(status_code=404, detail="规则不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取规则详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取规则详情失败")


@router.post("/create", response_model=Dict[str, Any])
async def create_rule(
    rule_request: GamificationRuleRequest,
    service: RuleEngineService = Depends(get_rule_engine_service),
):
    """
    创建新规则

    Args:
        rule_request: 规则创建请求
        service: 规则引擎服务依赖

    Returns:
        创建的规则信息
    """
    try:
        # 转换条件
        conditions = []
        for cond_req in rule_request.conditions:
            try:
                condition = RuleCondition(
                    condition_type=RuleConditionType(cond_req.condition_type),
                    operator=RuleOperator(cond_req.operator),
                    value=cond_req.value,
                    field_name=cond_req.field_name,
                )
                conditions.append(condition)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"无效的条件参数: {e}")

        # 转换动作
        actions = []
        for act_req in rule_request.actions:
            try:
                action = RuleAction(
                    action_type=RuleActionType(act_req.action_type),
                    parameters=act_req.parameters,
                )
                actions.append(action)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"无效的动作参数: {e}")

        # 创建规则
        import uuid

        rule = GamificationRule(
            rule_id=str(uuid.uuid4()),
            name=rule_request.name,
            description=rule_request.description,
            conditions=conditions,
            actions=actions,
            priority=rule_request.priority,
            cooldown_seconds=rule_request.cooldown_seconds,
            max_executions=rule_request.max_executions,
        )

        # 添加到引擎
        success = service.add_custom_rule(rule)
        if not success:
            raise HTTPException(status_code=500, detail="规则添加失败")

        return {"status": "success", "message": "规则创建成功", "rule": rule.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建规则失败: {e}")
        raise HTTPException(status_code=500, detail="创建规则失败")


@router.put("/{rule_id}")
async def update_rule(
    rule_id: str,
    updates: Dict[str, Any],
    service: RuleEngineService = Depends(get_rule_engine_service),
):
    """
    更新规则配置

    Args:
        rule_id: 规则ID
        updates: 更新内容
        service: 规则引擎服务依赖

    Returns:
        更新结果
    """
    try:
        success = service.update_rule(rule_id, updates)
        if success:
            return {"status": "success", "message": "规则更新成功"}
        else:
            raise HTTPException(status_code=404, detail="规则不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新规则失败: {e}")
        raise HTTPException(status_code=500, detail="更新规则失败")


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: str, service: RuleEngineService = Depends(get_rule_engine_service)
):
    """
    删除规则

    Args:
        rule_id: 规则ID
        service: 规则引擎服务依赖

    Returns:
        删除结果
    """
    try:
        success = service.remove_rule(rule_id)
        if success:
            return {"status": "success", "message": "规则删除成功"}
        else:
            raise HTTPException(status_code=404, detail="规则不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除规则失败: {e}")
        raise HTTPException(status_code=500, detail="删除规则失败")


@router.post("/{rule_id}/toggle")
async def toggle_rule_status(
    rule_id: str, service: RuleEngineService = Depends(get_rule_engine_service)
):
    """
    切换规则激活状态

    Args:
        rule_id: 规则ID
        service: 规则引擎服务依赖

    Returns:
        切换结果
    """
    try:
        # 查找规则并切换状态
        for rule in service.config.rules:
            if rule.rule_id == rule_id:
                rule.is_active = not rule.is_active
                rule.updated_at = None  # 服务层会自动更新
                return {
                    "status": "success",
                    "message": f"规则状态已{'激活' if rule.is_active else '停用'}",
                    "is_active": rule.is_active,
                }

        raise HTTPException(status_code=404, detail="规则不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换规则状态失败: {e}")
        raise HTTPException(status_code=500, detail="切换规则状态失败")


@router.get("/statistics", response_model=RuleStatisticsResponse)
async def get_rule_statistics(
    service: RuleEngineService = Depends(get_rule_engine_service),
):
    """
    获取规则执行统计

    Args:
        service: 规则引擎服务依赖

    Returns:
        规则统计信息
    """
    try:
        stats = service.get_rule_statistics()
        return RuleStatisticsResponse(**stats)
    except Exception as e:
        logger.error(f"获取规则统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取规则统计失败")


@router.get("/templates/list")
async def list_rule_templates():
    """
    获取预定义规则模板列表

    Returns:
        规则模板列表
    """
    try:
        from ..models.rule_engine import PREDEFINED_RULE_TEMPLATES

        templates = []
        for template_name, template_rule in PREDEFINED_RULE_TEMPLATES.items():
            templates.append(
                {
                    "template_id": template_name,
                    "name": template_rule.name,
                    "description": template_rule.description,
                    "conditions_count": len(template_rule.conditions),
                    "actions_count": len(template_rule.actions),
                }
            )

        return {"templates": templates, "total_templates": len(templates)}
    except Exception as e:
        logger.error(f"获取规则模板失败: {e}")
        raise HTTPException(status_code=500, detail="获取规则模板失败")


@router.post("/templates/{template_id}/instantiate")
async def instantiate_template(
    template_id: str,
    customizations: Dict[str, Any] = None,
    service: RuleEngineService = Depends(get_rule_engine_service),
):
    """
    基于模板创建规则实例

    Args:
        template_id: 模板ID
        customizations: 自定义参数
        service: 规则引擎服务依赖

    Returns:
        创建的规则实例
    """
    try:
        import uuid

        from ..models.rule_engine import PREDEFINED_RULE_TEMPLATES

        if template_id not in PREDEFINED_RULE_TEMPLATES:
            raise HTTPException(status_code=404, detail="模板不存在")

        # 获取模板
        template_rule = PREDEFINED_RULE_TEMPLATES[template_id]

        # 创建规则实例
        rule_instance = GamificationRule(
            rule_id=str(uuid.uuid4()),
            name=customizations.get("name", template_rule.name),
            description=customizations.get("description", template_rule.description),
            conditions=template_rule.conditions.copy(),
            actions=template_rule.actions.copy(),
            priority=customizations.get("priority", template_rule.priority),
            cooldown_seconds=customizations.get(
                "cooldown_seconds", template_rule.cooldown_seconds
            ),
            max_executions=customizations.get(
                "max_executions", template_rule.max_executions
            ),
        )

        # 添加到引擎
        success = service.add_custom_rule(rule_instance)
        if not success:
            raise HTTPException(status_code=500, detail="规则实例化失败")

        return {
            "status": "success",
            "message": "规则实例化成功",
            "rule": rule_instance.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"实例化规则模板失败: {e}")
        raise HTTPException(status_code=500, detail="实例化规则模板失败")


@router.get("/export")
async def export_rules_config(
    service: RuleEngineService = Depends(get_rule_engine_service),
):
    """
    导出规则配置

    Args:
        service: 规则引擎服务依赖

    Returns:
        规则配置JSON
    """
    try:
        config_json = service.export_rules_config()
        return {"config": config_json}
    except Exception as e:
        logger.error(f"导出规则配置失败: {e}")
        raise HTTPException(status_code=500, detail="导出规则配置失败")


@router.post("/import")
async def import_rules_config(
    config_data: Dict[str, Any],
    service: RuleEngineService = Depends(get_rule_engine_service),
):
    """
    导入规则配置

    Args:
        config_data: 配置数据
        service: 规则引擎服务依赖

    Returns:
        导入结果
    """
    try:
        config_json = config_data.get("config", "")
        if not config_json:
            raise HTTPException(status_code=400, detail="配置数据不能为空")

        success = service.import_rules_config(config_json)
        if success:
            return {"status": "success", "message": "规则配置导入成功"}
        else:
            raise HTTPException(status_code=400, detail="配置导入失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入规则配置失败: {e}")
        raise HTTPException(status_code=500, detail="导入规则配置失败")
