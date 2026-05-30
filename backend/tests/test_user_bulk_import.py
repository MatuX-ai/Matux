"""
用户批量导入功能测试
"""

import io
from unittest.mock import AsyncMock, patch

from fastapi import UploadFile
import pandas as pd
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserRole
from services.user_bulk_import_service import (
    ConflictResolution,
    ImportResult,
    UserBulkImportService,
    UserImportValidator,
)


class TestUserImportValidator:
    """用户导入数据验证器测试"""

    def test_validate_username_valid(self):
        """测试有效的用户名验证"""
        validator = UserImportValidator()
        is_valid, error = validator.validate_username("testuser")
        assert is_valid is True
        assert error == ""

    def test_validate_username_empty(self):
        """测试空用户名验证"""
        validator = UserImportValidator()
        is_valid, error = validator.validate_username("")
        assert is_valid is False
        assert "不能为空" in error

    def test_validate_username_too_short(self):
        """测试过短用户名验证"""
        validator = UserImportValidator()
        is_valid, error = validator.validate_username("ab")
        assert is_valid is False
        assert "不能少于3个字符" in error

    def test_validate_username_too_long(self):
        """测试过长用户名验证"""
        validator = UserImportValidator()
        long_username = "a" * 51
        is_valid, error = validator.validate_username(long_username)
        assert is_valid is False
        assert "不能超过50个字符" in error

    def test_validate_email_valid(self):
        """测试有效的邮箱验证"""
        validator = UserImportValidator()
        is_valid, error = validator.validate_email("test@example.com")
        assert is_valid is True
        assert error == ""

    def test_validate_email_invalid_format(self):
        """测试无效邮箱格式验证"""
        validator = UserImportValidator()
        is_valid, error = validator.validate_email("invalid-email")
        assert is_valid is False
        assert "格式不正确" in error

    def test_validate_role_valid(self):
        """测试有效角色验证"""
        validator = UserImportValidator()
        is_valid, error = validator.validate_role("admin")
        assert is_valid is True
        assert error == ""

    def test_validate_role_invalid(self):
        """测试无效角色验证"""
        validator = UserImportValidator()
        is_valid, error = validator.validate_role("invalid_role")
        assert is_valid is False
        assert "无效的角色" in error


class TestUserBulkImportService:
    """用户批量导入服务测试"""

    @pytest.fixture
    def service(self):
        return UserBulkImportService()

    @pytest.fixture
    def mock_db_session(self):
        return AsyncMock(spec=AsyncSession)

    def test_map_fields_default_mapping(self, service):
        """测试默认字段映射"""
        raw_data = [
            {"username": "user1", "email": "user1@example.com", "role": "user"},
            {"Username": "user2", "Email": "user2@example.com", "Role": "admin"},
        ]

        mapped_data = service.map_fields(raw_data)

        assert len(mapped_data) == 2
        assert mapped_data[0]["username"] == "user1"
        assert mapped_data[0]["email"] == "user1@example.com"
        assert mapped_data[0]["role"] == "user"
        assert mapped_data[1]["username"] == "user2"
        assert mapped_data[1]["email"] == "user2@example.com"
        assert mapped_data[1]["role"] == "admin"

    def test_map_fields_custom_mapping(self, service):
        """测试自定义字段映射"""
        raw_data = [{"用户名称": "user1", "电子邮箱": "user1@example.com"}]

        field_mapping = {
            "username": "用户名称",
            "email": "电子邮箱",
            "role": "用户角色",
        }

        mapped_data = service.map_fields(raw_data, field_mapping)

        assert len(mapped_data) == 1
        assert mapped_data[0]["username"] == "user1"
        assert mapped_data[0]["email"] == "user1@example.com"

    @pytest.mark.asyncio
    async def test_parse_csv_file(self, service):
        """测试CSV文件解析"""
        # 创建测试CSV数据
        csv_data = "username,email,role\nuser1,user1@example.com,user\nuser2,user2@example.com,admin"
        file_content = csv_data.encode("utf-8")

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = pd.DataFrame(
                {
                    "username": ["user1", "user2"],
                    "email": ["user1@example.com", "user2@example.com"],
                    "role": ["user", "admin"],
                }
            )
            mock_read_csv.return_value = mock_df

            result = await service.parse_csv_file(file_content)

            assert len(result) == 2
            assert result[0]["username"] == "user1"
            assert result[1]["email"] == "user2@example.com"

    @pytest.mark.asyncio
    async def test_parse_xlsx_file(self, service):
        """测试Excel文件解析"""
        # 创建测试Excel数据
        df = pd.DataFrame(
            {
                "username": ["user1", "user2"],
                "email": ["user1@example.com", "user2@example.com"],
                "role": ["user", "admin"],
            }
        )
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        file_content = buffer.getvalue()

        with patch("pandas.read_excel") as mock_read_excel:
            mock_read_excel.return_value = df

            result = await service.parse_xlsx_file(file_content)

            assert len(result) == 2
            assert result[0]["username"] == "user1"

    @pytest.mark.asyncio
    async def test_check_conflicts_no_conflicts(self, service, mock_db_session):
        """测试无冲突情况下的冲突检查"""
        users_data = [
            {"username": "newuser1", "email": "new1@example.com"},
            {"username": "newuser2", "email": "new2@example.com"},
        ]

        # 模拟数据库查询返回空结果
        mock_db_session.execute.return_value.fetchall.return_value = []

        conflicts = await service.check_conflicts(mock_db_session, users_data)

        assert conflicts["email_conflicts"] == []
        assert conflicts["username_conflicts"] == []
        assert conflicts["invalid_data"] == []

    @pytest.mark.asyncio
    async def test_check_conflicts_with_email_conflict(self, service, mock_db_session):
        """测试邮箱冲突检查"""
        users_data = [
            {"username": "user1", "email": "existing@example.com"},
            {"username": "user2", "email": "new@example.com"},
        ]

        # 模拟已有用户的邮箱
        mock_result = AsyncMock()
        mock_result.fetchall.return_value = [("existing@example.com",)]
        mock_db_session.execute.return_value = mock_result

        conflicts = await service.check_conflicts(mock_db_session, users_data)

        assert len(conflicts["email_conflicts"]) == 1
        assert conflicts["email_conflicts"][0]["email"] == "existing@example.com"

    @pytest.mark.asyncio
    async def test_import_users_success(self, service, mock_db_session):
        """测试成功的用户导入"""
        # 创建测试CSV文件
        csv_content = "username,email,role\nnewuser,new@example.com,user"
        upload_file = UploadFile(
            filename="test.csv", file=io.BytesIO(csv_content.encode())
        )

        # 模拟无冲突
        with patch.object(service, "check_conflicts", return_value={}):
            with patch.object(mock_db_session, "add_all") as mock_add_all:
                with patch.object(mock_db_session, "commit") as mock_commit:
                    with patch.object(mock_db_session, "refresh") as mock_refresh:
                        # 创建模拟用户对象
                        mock_user = User()
                        mock_user.id = 1
                        mock_user.username = "newuser"
                        mock_user.email = "new@example.com"
                        mock_user.role = UserRole.USER

                        result = await service.import_users(
                            db=mock_db_session,
                            file=upload_file,
                            conflict_resolution=ConflictResolution.SKIP,
                        )

                        assert result.success_count == 1
                        assert result.failed_count == 0
                        assert result.conflicts_count == 0
                        assert len(result.imported_users) == 1

    @pytest.mark.asyncio
    async def test_import_users_with_conflicts_skip(self, service, mock_db_session):
        """测试冲突时跳过的导入策略"""
        csv_content = "username,email,role\nexistinguser,existing@example.com,user"
        upload_file = UploadFile(
            filename="test.csv", file=io.BytesIO(csv_content.encode())
        )

        # 模拟存在冲突
        conflicts = {
            "username_conflicts": [{"username": "existinguser", "row": 2}],
            "email_conflicts": [],
            "invalid_data": [],
        }

        with patch.object(service, "check_conflicts", return_value=conflicts):
            result = await service.import_users(
                db=mock_db_session,
                file=upload_file,
                conflict_resolution=ConflictResolution.SKIP,
            )

            assert result.success_count == 0
            assert result.conflicts_count == 1
            assert len(result.conflicts["username_conflicts"]) == 1

    @pytest.mark.asyncio
    async def test_import_users_error_on_conflict(self, service, mock_db_session):
        """测试冲突时报错的导入策略"""
        csv_content = "username,email,role\nexistinguser,existing@example.com,user"
        upload_file = UploadFile(
            filename="test.csv", file=io.BytesIO(csv_content.encode())
        )

        # 模拟存在冲突
        conflicts = {
            "username_conflicts": [{"username": "existinguser", "row": 2}],
            "email_conflicts": [],
            "invalid_data": [],
        }

        with patch.object(service, "check_conflicts", return_value=conflicts):
            result = await service.import_users(
                db=mock_db_session,
                file=upload_file,
                conflict_resolution=ConflictResolution.ERROR,
            )

            assert result.success_count == 0
            assert len(result.errors) > 0
            assert "发现数据冲突" in result.errors[0]


# API端点测试
class TestUserBulkImportAPI:
    """用户批量导入API测试"""

    @pytest.mark.asyncio
    async def test_bulk_import_unauthorized(self, client):
        """测试未授权的批量导入请求"""
        response = await client.post("/api/v1/auth/bulk-import")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_bulk_import_forbidden_non_admin(self, client, auth_headers_user):
        """测试非管理员用户批量导入被拒绝"""
        response = await client.post(
            "/api/v1/auth/bulk-import", headers=auth_headers_user
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_bulk_import_invalid_file_type(self, client, auth_headers_admin):
        """测试无效文件类型"""
        files = {"file": ("test.txt", b"invalid content", "text/plain")}
        response = await client.post(
            "/api/v1/auth/bulk-import", files=files, headers=auth_headers_admin
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_bulk_import_success(self, client, auth_headers_admin):
        """测试成功的批量导入"""
        # 创建测试CSV内容
        csv_content = "username,email,role\nnewuser,new@example.com,user"

        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"conflict_resolution": "skip", "generate_password": "true"}

        with patch("routes.auth_routes.user_bulk_import_service") as mock_service:
            # 模拟导入结果
            mock_result = ImportResult()
            mock_result.success_count = 1
            mock_result.failed_count = 0
            mock_result.conflicts_count = 0
            mock_result.errors = []
            mock_result.conflicts = {}
            mock_result.imported_users = [
                {
                    "id": 1,
                    "username": "newuser",
                    "email": "new@example.com",
                    "role": "user",
                    "is_active": True,
                    "is_superuser": False,
                }
            ]

            mock_service.import_users.return_value = mock_result

            response = await client.post(
                "/api/v1/auth/bulk-import",
                files=files,
                data=data,
                headers=auth_headers_admin,
            )

            assert response.status_code == 200
            result_data = response.json()
            assert result_data["success_count"] == 1
            assert len(result_data["imported_users"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
