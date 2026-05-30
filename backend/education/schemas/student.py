"""
iMato 教育培训管理系统 - 学员管理数据验证模式
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class StudentStatusEnum(str, Enum):
    """学员状态枚举"""
    在读 = "在读"
    休学 = "休学"
    毕业 = "毕业"
    退学 = "退学"
    转校 = "转校"


class GenderEnum(str, Enum):
    """性别枚举"""
    male = "male"
    female = "female"


class RelationshipTypeEnum(str, Enum):
    """关系类型枚举"""
    父亲 = "父亲"
    母亲 = "母亲"
    其他监护人 = "其他监护人"


# ==================== 家长信息 Schema ====================

class ParentInfoBase(BaseModel):
    """家长信息基础模型"""
    name: str = Field(..., description="姓名", min_length=1, max_length=50)
    relationship_type: RelationshipTypeEnum = Field(..., description="与学员关系")
    phone: str = Field(..., description="手机号")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    wechat: Optional[str] = Field(None, description="微信", max_length=50)
    qq: Optional[str] = Field(None, description="QQ", max_length=20)
    address: Optional[str] = Field(None, description="地址", max_length=200)
    is_primary: bool = Field(False, description="是否为主要联系人")
    notes: Optional[str] = Field(None, description="备注", max_length=500)


class ParentInfoCreate(ParentInfoBase):
    """创建家长信息"""
    pass


class ParentInfoUpdate(ParentInfoBase):
    """更新家长信息"""
    pass


class ParentInfoResponse(ParentInfoBase):
    """家长信息响应"""
    id: str
    student_id: str

    class Config:
        from_attributes = True


# ==================== 学员档案 Schema ====================

class StudentProfileBase(BaseModel):
    """学员档案基础模型"""
    name: str = Field(..., description="姓名", min_length=1, max_length=50)
    gender: GenderEnum = Field(..., description="性别")
    birth_date: Optional[str] = Field(None, description="出生日期 (YYYY-MM-DD)")
    grade: Optional[str] = Field(None, description="年级", max_length=50)
    school: Optional[str] = Field(None, description="学校", max_length=100)

    # 联系方式
    phone: Optional[str] = Field(None, description="手机号", pattern=r"^\d{10,15}$")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    address: Optional[str] = Field(None, description="地址", max_length=200)

    # 身份证信息
    id_card_number: Optional[str] = Field(None, description="身份证号", pattern=r"^\d{17}[\dXx]$")
    id_card_address: Optional[str] = Field(None, description="身份证地址", max_length=200)

    # 学籍状态
    status: StudentStatusEnum = Field(StudentStatusEnum.在读, description="学籍状态")
    enrollment_date: str = Field(..., description="入学日期 (YYYY-MM-DD)")
    graduation_date: Optional[str] = Field(None, description="预计毕业日期 (YYYY-MM-DD)")
    actual_graduation_date: Optional[str] = Field(None, description="实际毕业日期 (YYYY-MM-DD)")

    # 分班信息
    current_class_id: Optional[str] = Field(None, description="班级 ID", max_length=50)
    current_class_name: Optional[str] = Field(None, description="班级名称", max_length=100)

    # 课时信息
    total_purchased_hours: int = Field(0, description="购买课时数", ge=0)
    total_consumed_hours: int = Field(0, description="已消耗课时数", ge=0)
    remaining_hours: int = Field(0, description="剩余课时数", ge=0)

    # 紧急联系人
    emergency_contact: Optional[str] = Field(None, description="紧急联系人", max_length=50)
    emergency_phone: Optional[str] = Field(None, description="紧急联系电话", pattern=r"^\d{10,15}$")

    # 备注
    notes: Optional[str] = Field(None, description="备注", max_length=1000)

    @validator('remaining_hours')
    def validate_remaining_hours(cls, v, values):
        """验证剩余课时数"""
        purchased = values.get('total_purchased_hours', 0)
        consumed = values.get('total_consumed_hours', 0)
        expected = purchased - consumed

        if v != expected:
            raise ValueError(f'剩余课时数应等于购买课时数减去已消耗课时数 (应为{expected})')

        return v


class StudentProfileCreate(StudentProfileBase):
    """创建学员档案"""
    parents: Optional[List[ParentInfoCreate]] = Field(None, description="家长信息列表")


class StudentProfileUpdate(BaseModel):
    """更新学员档案"""
    name: Optional[str] = Field(None, description="姓名", min_length=1, max_length=50)
    gender: Optional[GenderEnum] = Field(None, description="性别")
    birth_date: Optional[str] = Field(None, description="出生日期 (YYYY-MM-DD)")
    grade: Optional[str] = Field(None, description="年级", max_length=50)
    school: Optional[str] = Field(None, description="学校", max_length=100)
    phone: Optional[str] = Field(None, description="手机号", pattern=r"^\d{10,15}$")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    address: Optional[str] = Field(None, description="地址", max_length=200)
    id_card_number: Optional[str] = Field(None, description="身份证号", pattern=r"^\d{17}[\dXx]$")
    id_card_address: Optional[str] = Field(None, description="身份证地址", max_length=200)
    status: Optional[StudentStatusEnum] = Field(None, description="学籍状态")
    enrollment_date: Optional[str] = Field(None, description="入学日期 (YYYY-MM-DD)")
    graduation_date: Optional[str] = Field(None, description="预计毕业日期 (YYYY-MM-DD)")
    actual_graduation_date: Optional[str] = Field(None, description="实际毕业日期 (YYYY-MM-DD)")
    current_class_id: Optional[str] = Field(None, description="班级 ID", max_length=50)
    current_class_name: Optional[str] = Field(None, description="班级名称", max_length=100)
    total_purchased_hours: Optional[int] = Field(None, description="购买课时数", ge=0)
    total_consumed_hours: Optional[int] = Field(None, description="已消耗课时数", ge=0)
    remaining_hours: Optional[int] = Field(None, description="剩余课时数", ge=0)
    emergency_contact: Optional[str] = Field(None, description="紧急联系人", max_length=50)
    emergency_phone: Optional[str] = Field(None, description="紧急联系电话", pattern=r"^\d{10,15}$")
    notes: Optional[str] = Field(None, description="备注", max_length=1000)
    parents: Optional[List[ParentInfoUpdate]] = Field(None, description="家长信息列表")


class StudentProfileResponse(StudentProfileBase):
    """学员档案响应"""
    id: str
    avatar_url: Optional[str] = Field(None, description="头像 URL", max_length=500)
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = Field(None, description="创建人", max_length=50)
    parents: Optional[List[ParentInfoResponse]] = Field(None, description="家长信息列表")

    class Config:
        from_attributes = True


# ==================== 查询和响应 Schema ====================

class StudentQuery(BaseModel):
    """学员查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(None, description="搜索关键词")
    grade: Optional[str] = Field(None, description="年级")
    school: Optional[str] = Field(None, description="学校")
    status: Optional[StudentStatusEnum] = Field(None, description="状态")
    class_id: Optional[str] = Field(None, description="班级 ID")


class StudentListResponse(BaseModel):
    """学员列表响应"""
    total: int = Field(..., description="总数")
    list: List[StudentProfileResponse] = Field(..., description="学员列表")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
