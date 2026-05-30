"""
Hardware certification data models
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class CertificationStatus(str, Enum):
    """Certification status enumeration"""

    PENDING = "pending"
    CERTIFIED = "certified"
    FAILED = "failed"
    EXPIRED = "expired"


class TestCategory(str, Enum):
    """Test category enumeration"""

    FUNCTIONALITY = "functionality"
    PERFORMANCE = "performance"
    COMPATIBILITY = "compatibility"
    SECURITY = "security"
    RELIABILITY = "reliability"


class TestResult(BaseModel):
    """Single test result"""

    test_id: str
    category: TestCategory
    name: str
    description: str
    status: str
    duration_ms: Optional[int]
    error_message: Optional[str]
    timestamp: datetime


class CertificationRequest(BaseModel):
    """Certification request model"""

    hw_id: str
    device_info: Dict[str, str]
    test_results: List[TestResult]
    firmware_version: str
    hardware_version: str
    submitted_by: Optional[str]


class CertificationResponse(BaseModel):
    """Certification response model"""

    hw_id: str
    status: CertificationStatus
    badge_url: Optional[str]
    certified_at: Optional[datetime]
    expires_at: Optional[datetime]
    test_summary: Dict[str, int]
    failed_tests: List[TestResult]
    certificate_id: Optional[str]


class BadgeStyle(str, Enum):
    """Badge style enumeration"""

    STANDARD = "standard"
    COMPACT = "compact"
    DETAILED = "detailed"


class BadgeConfig(BaseModel):
    """Badge configuration model"""

    style: BadgeStyle = BadgeStyle.STANDARD
    show_timestamp: bool = True
    show_version: bool = True
    show_test_count: bool = True
    width: Optional[int] = None
    height: Optional[int] = None
    primary_color: str = "#2196f3"
    secondary_color: str = "#4caf50"


class HardwareCertificationDB:
    """Hardware certification database model (simplified)"""

    def __init__(self):
        self.hw_id: str = ""
        self.status: CertificationStatus = CertificationStatus.PENDING
        self.device_info: Dict[str, str] = {}
        self.test_results: List[TestResult] = []
        self.firmware_version: str = ""
        self.hardware_version: str = ""
        self.submitted_by: Optional[str] = None
        self.certified_at: Optional[datetime] = None
        self.expires_at: Optional[datetime] = None
        self.certificate_id: Optional[str] = None
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary format"""
        return {
            "hw_id": self.hw_id,
            "status": self.status.value,
            "device_info": self.device_info,
            "test_results": [result.dict() for result in self.test_results],
            "firmware_version": self.firmware_version,
            "hardware_version": self.hardware_version,
            "submitted_by": self.submitted_by,
            "certified_at": (
                self.certified_at.isoformat() if self.certified_at is not None else None
            ),
            "expires_at": self.expires_at.isoformat() if self.expires_at is not None else None,
            "certificate_id": self.certificate_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HardwareCertificationDB":
        """Create instance from dictionary"""
        instance = cls()
        instance.hw_id = data.get("hw_id", "")
        instance.status = CertificationStatus(
            data.get("status", CertificationStatus.PENDING)
        )
        instance.device_info = data.get("device_info", {})
        instance.test_results = [
            TestResult(**result) for result in data.get("test_results", [])
        ]
        instance.firmware_version = data.get("firmware_version", "")
        instance.hardware_version = data.get("hardware_version", "")
        instance.submitted_by = data.get("submitted_by")
        instance.certified_at = (
            datetime.fromisoformat(data["certified_at"])
            if data.get("certified_at")
            else None
        )
        instance.expires_at = (
            datetime.fromisoformat(data["expires_at"])
            if data.get("expires_at")
            else None
        )
        instance.certificate_id = data.get("certificate_id")
        instance.created_at = (
            datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.utcnow()
        )
        instance.updated_at = (
            datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else datetime.utcnow()
        )
        return instance
