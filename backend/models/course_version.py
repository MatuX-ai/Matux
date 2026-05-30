"""
课程版本管理模型（存根）
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CourseVersion(BaseModel):
    id: int
    course_id: int
    version_number: int
    snapshot: Dict[str, Any]
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class CourseVersionCreate(BaseModel):
    course_id: int
    snapshot: Dict[str, Any]
    created_by: int


class CourseVersionResponse(BaseModel):
    id: int
    version_number: int
    created_by: int
    created_at: datetime


class VersionBranch(BaseModel):
    id: int
    name: str
    course_id: int
    base_version_id: int
    created_by: int
    created_at: datetime


class BranchCreate(BaseModel):
    name: str
    course_id: int
    base_version_id: int
    created_by: int


class BranchResponse(BaseModel):
    id: int
    name: str
    base_version_number: int
    created_at: datetime


class CommitData(BaseModel):
    version_id: int
    changes: Dict[str, Any]
    message: str
    author_id: int


class CourseSnapshot(BaseModel):
    id: int
    course_id: int
    version_id: int
    data: Dict[str, Any]
    created_at: datetime


class MergeRequest(BaseModel):
    id: int
    source_branch_id: int
    target_branch_id: int
    status: str
    created_by: int
    created_at: datetime
    reviewed_by: Optional[int] = None


class MergeRequestCreate(BaseModel):
    source_branch_id: int
    target_branch_id: int
    created_by: int


class MergeRequestResponse(BaseModel):
    id: int
    status: str
    source_branch_name: str
    target_branch_name: str


class VersionChange(BaseModel):
    id: int
    version_id: int
    field_name: str
    old_value: Any
    new_value: Any
    changed_by: int
    changed_at: datetime
