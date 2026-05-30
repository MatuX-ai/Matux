"""
License（许可证）模型
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class LicenseStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


class LicenseType(str, Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    TRIAL = "trial"


class Organization(BaseModel):
    id: int = 0
    name: str = ""
    code: str = ""
    license_type: LicenseType = LicenseType.BASIC
    is_active: bool = True
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class OrganizationCreate(BaseModel):
    name: str
    code: str
    license_type: LicenseType = LicenseType.BASIC


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    license_type: Optional[LicenseType] = None
    is_active: Optional[bool] = None


class OrganizationResponse(BaseModel):
    id: int
    name: str
    code: str
    license_type: LicenseType
    is_active: bool
    created_at: datetime
    updated_at: datetime


class License(BaseModel):
    id: int = 0
    organization_id: int = 0
    license_type: LicenseType = LicenseType.BASIC
    status: LicenseStatus = LicenseStatus.ACTIVE
    max_users: int = 10
    valid_from: datetime = datetime.now()
    valid_until: datetime = datetime.now()
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class LicenseCreate(BaseModel):
    organization_id: int
    license_type: LicenseType = LicenseType.BASIC
    max_users: int = 10


class LicenseResponse(BaseModel):
    id: int
    organization_id: int
    license_type: LicenseType
    status: LicenseStatus
    max_users: int
    valid_from: datetime
    valid_until: datetime


class LicenseActivityLog(BaseModel):
    id: int = 0
    license_id: int = 0
    action: str = ""
    details: str = ""
    created_at: datetime = datetime.now()


class LicenseValidationAttempt(BaseModel):
    id: int = 0
    license_id: int = 0
    success: bool = False
    ip_address: str = ""
    user_agent: str = ""
    created_at: datetime = datetime.now()
