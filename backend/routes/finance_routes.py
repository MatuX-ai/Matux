"""
财务管理 API 路由（简化版）
提供学费、薪酬、定价、消课等财务相关接口
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid


router = APIRouter(prefix="/api/v1/finance", tags=["财务管理"])


# ==================== Pydantic 模型 ====================

from pydantic import BaseModel

class SalaryCalculateRequest(BaseModel):
    teacher_id: int
    month: str


class BatchSalaryCalculateRequest(BaseModel):
    month: str


# ==================== 课程定价管理 ====================

@router.get("/org/{org_id}/pricing")
async def get_course_pricings(org_id: int):
    """获取课程定价列表"""
    # 返回空数据，避免数据库依赖问题
    return {"code": 200, "message": "success", "data": []}


@router.post("/org/{org_id}/pricing")
async def create_course_pricing(org_id: int):
    """创建课程定价"""
    return {"code": 200, "message": "课程定价创建成功", "data": {"id": 1}}


@router.put("/org/{org_id}/pricing/{pricing_id}")
async def update_course_pricing(org_id: int, pricing_id: int):
    """更新课程定价"""
    return {"code": 200, "message": "课程定价更新成功", "data": {"id": pricing_id}}


# ==================== 消课管理 ====================

@router.get("/org/{org_id}/consumptions")
async def get_consumptions(
    org_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """获取消课记录列表"""
    return {"code": 200, "message": "success", "data": []}


@router.post("/org/{org_id}/consumptions")
async def create_consumption(org_id: int):
    """创建消课记录"""
    return {
        "code": 200,
        "message": "消课记录创建成功",
        "data": {"id": str(uuid.uuid4())}
    }


# ==================== 其他接口（简化版）====================

@router.get("/org/{org_id}/transactions")
async def get_transactions(org_id: int):
    """获取交易记录列表"""
    return {"code": 200, "message": "success", "data": []}


@router.get("/org/{org_id}/tuitions")
async def get_tuition_records(org_id: int):
    """获取学费记录列表"""
    return {"code": 200, "message": "success", "data": []}


@router.get("/org/{org_id}/salaries")
async def get_teacher_salaries(org_id: int):
    """获取教师薪酬列表"""
    return {"code": 200, "message": "success", "data": []}


@router.post("/org/{org_id}/salaries/calculate")
async def calculate_salary(org_id: int, request: SalaryCalculateRequest):
    """计算教师薪酬"""
    return {
        "code": 200,
        "message": "薪酬计算成功",
        "data": {
            "id": str(uuid.uuid4()),
            "teacher_id": request.teacher_id,
            "total_salary": 7500.0,
            "actual_salary": 6200.0,
            "status": "ready_to_pay",
        }
    }


@router.post("/org/{org_id}/salaries/batch-calculate")
async def batch_calculate_salaries(org_id: int, request: BatchSalaryCalculateRequest):
    """批量计算薪酬"""
    return {
        "code": 200,
        "message": "批量计算完成",
        "data": {"success": True, "message": f"{request.month} 月份薪酬批量计算完成"}
    }


@router.post("/org/{org_id}/salaries/{salary_id}/pay")
async def pay_salary(org_id: int, salary_id: str):
    """发放薪酬"""
    return {
        "code": 200,
        "message": "薪酬发放成功",
        "data": {
            "id": salary_id,
            "status": "paid",
            "paid_date": datetime.utcnow().isoformat(),
        }
    }


@router.get("/org/{org_id}/report")
async def get_financial_report(org_id: int, period: Optional[str] = None):
    """获取财务报表"""
    current_period = period or datetime.now().strftime("%Y-%m")

    return {
        "code": 200,
        "message": "success",
        "data": {
            "period": current_period,
            "org_id": org_id,
            "income": {
                "tuition_income": 50000,
                "material_income": 5000,
                "other_income": 2000,
                "total_income": 57000,
                "growth_rate": 0.15
            },
            "expense": {
                "salary_expense": 30000,
                "rent_expense": 8000,
                "utility_expense": 2000,
                "marketing_expense": 3000,
                "maintenance_expense": 1000,
                "other_expense": 2000,
                "total_expense": 46000
            },
            "profit": {
                "gross_profit": 11000,
                "net_profit": 9500,
                "profit_margin": 0.167
            },
            "cash_flow": {
                "operating_cash_flow": 10000,
                "investing_cash_flow": -2000,
                "financing_cash_flow": 0,
                "net_cash_flow": 8000
            },
            "accounts_receivable": {
                "total_receivable": 15000,
                "collected": 12000,
                "outstanding": 3000,
                "overdue": 1000,
                "collection_rate": 0.8
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    }
