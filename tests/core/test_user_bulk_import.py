"""
用户批量导入功能综合测试

整合了原有的多个用户导入测试实现，提供完整的功能测试覆盖：
- CSV文件解析和验证
- 数据格式校验
- 重复数据处理
- 冲突解决策略
- 性能基准测试
- 异常情况处理

测试范围:
- 文件上传和解析
- 数据验证和清洗
- 用户创建和更新
- 批量操作事务管理
- 错误处理和回滚
"""

import pytest
import pandas as pd
import io
from unittest.mock import AsyncMock, Mock, patch
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

# 导入相关服务和模型
from services.user_bulk_import_service import (
    UserBulkImportService,
    UserImportValidator,
    ConflictResolution,
    ImportResult,
)
from models.user import User, UserRole

class TestUserBulkImportService:
    """用户批量导入服务测试类"""
    
    def setup_method(self):
        """测试前置条件"""
        self.service = UserBulkImportService()
        self.validator = UserImportValidator()
        
    def teardown_method(self):
        """测试后置清理"""
        pass
    
    def test_parse_csv_file_valid(self):
        """测试有效的CSV文件解析"""
        csv_content = """username,email,full_name,role
testuser1,test1@example.com,Test User 1,student
testuser2,test2@example.com,Test User 2,teacher
testuser3,test3@example.com,Test User 3,admin"""
        
        df = pd.read_csv(io.StringIO(csv_content))
        assert len(df) == 3
        assert list(df.columns) == ['username', 'email', 'full_name', 'role']
        assert df.iloc[0]['username'] == 'testuser1'
        assert df.iloc[0]['email'] == 'test1@example.com'
    
    def test_parse_csv_file_missing_columns(self):
        """测试缺少必要列的CSV文件"""
        csv_content = """username,email
testuser1,test1@example.com
testuser2,test2@example.com"""
        
        df = pd.read_csv(io.StringIO(csv_content))
        
        # 验证缺少必要列的情况
        required_columns = ['username', 'email', 'full_name', 'role']
        missing_columns = set(required_columns) - set(df.columns)
        assert len(missing_columns) > 0
    
    def test_validate_user_data_valid(self):
        """测试有效的用户数据验证"""
        user_data = {
            'username': 'testuser123',
            'email': 'test@example.com',
            'full_name': 'Test User',
            'role': 'student'
        }
        
        is_valid, errors = self.validator.validate_user_data(user_data)
        assert is_valid == True
        assert len(errors) == 0
    
    def test_validate_user_data_invalid_email(self):
        """测试无效邮箱的数据验证"""
        user_data = {
            'username': 'testuser',
            'email': 'invalid-email',  # 无效邮箱格式
            'full_name': 'Test User',
            'role': 'student'
        }
        
        is_valid, errors = self.validator.validate_user_data(user_data)
        assert is_valid == False
        assert len(errors) > 0
        assert any('email' in error.lower() for error in errors)
    
    def test_validate_user_data_invalid_role(self):
        """测试无效角色的数据验证"""
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'full_name': 'Test User',
            'role': 'invalid_role'  # 无效角色
        }
        
        is_valid, errors = self.validator.validate_user_data(user_data)
        assert is_valid == False
        assert any('role' in error.lower() for error in errors)
    
    def test_validate_user_data_missing_required_fields(self):
        """测试缺少必要字段的数据验证"""
        user_data = {
            'username': 'testuser'
            # 缺少email, full_name, role
        }
        
        is_valid, errors = self.validator.validate_user_data(user_data)
        assert is_valid == False
        assert len(errors) > 0
        assert any('required' in error.lower() for error in errors)
    
    @pytest.mark.asyncio
    async def test_process_import_valid_data(self):
        """测试处理有效的导入数据"""
        # Mock数据库会话
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add_all = AsyncMock()
        mock_session.commit = AsyncMock()
        
        # 准备测试数据
        import_data = [
            {
                'username': 'testuser1',
                'email': 'test1@example.com',
                'full_name': 'Test User 1',
                'role': 'student'
            },
            {
                'username': 'testuser2',
                'email': 'test2@example.com',
                'full_name': 'Test User 2',
                'role': 'teacher'
            }
        ]
        
        # Mock用户查询结果（假设用户不存在）
        mock_session.execute.return_value.scalars.return_value.first.return_value = None
        
        result = await self.service.process_import(
            import_data=import_data,
            session=mock_session,
            conflict_resolution=ConflictResolution.SKIP
        )
        
        assert isinstance(result, ImportResult)
        assert result.total_processed == 2
        assert result.successfully_imported == 2
        assert result.failed_imports == 0
        assert result.skipped_duplicates == 0
    
    @pytest.mark.asyncio
    async def test_process_import_duplicate_handling_skip(self):
        """测试重复数据跳过处理"""
        mock_session = AsyncMock(spec=AsyncSession)
        
        # 模拟已存在的用户
        existing_user = User(
            username='existinguser',
            email='existing@example.com',
            full_name='Existing User',
            role=UserRole.STUDENT
        )
        
        # Mock查询结果返回已存在的用户
        mock_session.execute.return_value.scalars.return_value.first.return_value = existing_user
        
        import_data = [{
            'username': 'existinguser',
            'email': 'existing@example.com',
            'full_name': 'Existing User',
            'role': 'student'
        }]
        
        result = await self.service.process_import(
            import_data=import_data,
            session=mock_session,
            conflict_resolution=ConflictResolution.SKIP
        )
        
        assert result.skipped_duplicates == 1
        assert result.successfully_imported == 0
    
    @pytest.mark.asyncio
    async def test_process_import_duplicate_handling_update(self):
        """测试重复数据更新处理"""
        mock_session = AsyncMock(spec=AsyncSession)
        
        # 模拟已存在的用户
        existing_user = User(
            username='existinguser',
            email='old@example.com',
            full_name='Old Name',
            role=UserRole.STUDENT
        )
        
        mock_session.execute.return_value.scalars.return_value.first.return_value = existing_user
        mock_session.merge = AsyncMock(return_value=existing_user)
        
        import_data = [{
            'username': 'existinguser',
            'email': 'new@example.com',  # 新邮箱
            'full_name': 'New Name',     # 新姓名
            'role': 'teacher'            # 新角色
        }]
        
        result = await self.service.process_import(
            import_data=import_data,
            session=mock_session,
            conflict_resolution=ConflictResolution.UPDATE
        )
        
        # 验证用户信息被更新
        assert existing_user.email == 'new@example.com'
        assert existing_user.full_name == 'New Name'
        assert existing_user.role == UserRole.TEACHER
        assert result.successfully_imported == 1

class TestUserImportValidator:
    """用户导入验证器测试类"""
    
    def setup_method(self):
        """测试前置条件"""
        self.validator = UserImportValidator()
    
    def test_username_validation_valid(self):
        """测试有效的用户名验证"""
        valid_usernames = [
            'testuser123',
            'user_name',
            'User123',
            'test-user-admin'
        ]
        
        for username in valid_usernames:
            is_valid, errors = self.validator.validate_username(username)
            assert is_valid == True, f"Username '{username}' should be valid"
            assert len(errors) == 0
    
    def test_username_validation_invalid(self):
        """测试无效的用户名验证"""
        invalid_usernames = [
            '',           # 空字符串
            'ab',         # 太短
            'a' * 51,     # 太长
            'test user',  # 包含空格
            'test@user',  # 包含特殊字符
            '123user'     # 以数字开头
        ]
        
        for username in invalid_usernames:
            is_valid, errors = self.validator.validate_username(username)
            assert is_valid == False, f"Username '{username}' should be invalid"
            assert len(errors) > 0
    
    def test_email_validation_valid(self):
        """测试有效的邮箱验证"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'test123@test-domain.org',
            'user+tag@example.com'
        ]
        
        for email in valid_emails:
            is_valid, errors = self.validator.validate_email(email)
            assert is_valid == True, f"Email '{email}' should be valid"
    
    def test_email_validation_invalid(self):
        """测试无效的邮箱验证"""
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'test@',
            'test.example.com',
            ''
        ]
        
        for email in invalid_emails:
            is_valid, errors = self.validator.validate_email(email)
            assert is_valid == False, f"Email '{email}' should be invalid"

# 性能测试
class TestUserBulkImportPerformance:
    """用户批量导入性能测试类"""
    
    def setup_method(self):
        """性能测试前置条件"""
        self.service = UserBulkImportService()
    
    @pytest.mark.asyncio
    async def test_large_batch_import_performance(self):
        """测试大批量导入性能"""
        import time
        
        # 生成大量测试数据
        large_import_data = []
        for i in range(1000):
            large_import_data.append({
                'username': f'user{i:04d}',
                'email': f'user{i:04d}@example.com',
                'full_name': f'Test User {i}',
                'role': 'student' if i % 3 == 0 else 'teacher'
            })
        
        # Mock数据库操作
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute.return_value.scalars.return_value.first.return_value = None
        mock_session.add_all = AsyncMock()
        mock_session.commit = AsyncMock()
        
        start_time = time.time()
        result = await self.service.process_import(
            import_data=large_import_data,
            session=mock_session,
            conflict_resolution=ConflictResolution.SKIP
        )
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # 验证结果正确性
        assert result.total_processed == 1000
        assert result.successfully_imported == 1000
        # 性能要求：处理1000个用户应在5秒内完成
        assert execution_time < 5.0, f"性能测试失败：执行时间 {execution_time:.3f}s 超过阈值"

# 异常处理测试
class TestUserBulkImportExceptionHandling:
    """用户批量导入异常处理测试"""
    
    def setup_method(self):
        """异常测试前置条件"""
        self.service = UserBulkImportService()
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """测试数据库错误处理"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit.side_effect = Exception("Database connection failed")
        
        import_data = [{
            'username': 'testuser',
            'email': 'test@example.com',
            'full_name': 'Test User',
            'role': 'student'
        }]
        
        # 应该捕获异常并返回适当的错误结果
        result = await self.service.process_import(
            import_data=import_data,
            session=mock_session,
            conflict_resolution=ConflictResolution.SKIP
        )
        
        # 验证错误被正确处理
        assert result.total_processed == 1
        assert result.failed_imports == 1
        assert len(result.error_messages) > 0
    
    def test_invalid_csv_format_handling(self):
        """测试无效CSV格式处理"""
        # 测试完全无效的CSV内容
        invalid_csv = "completely invalid content that is not CSV"
        
        try:
            df = pd.read_csv(io.StringIO(invalid_csv))
            # 如果pandas没有抛出异常，则验证数据为空
            assert df.empty == True
        except Exception:
            # 如果抛出异常，说明CSV格式确实无效
            pass

# 集成测试
class TestUserBulkImportIntegration:
    """用户批量导入集成测试"""
    
    def setup_method(self):
        """集成测试前置条件"""
        self.service = UserBulkImportService()
        self.validator = UserImportValidator()
    
    def create_test_csv_content(self):
        """创建测试CSV内容"""
        return """username,email,full_name,role
student001,student001@example.com,Student One,student
teacher001,teacher001@example.com,Teacher One,teacher
admin001,admin001@example.com,Admin One,admin
student002,student002@example.com,Student Two,student"""
    
    def test_full_import_workflow(self):
        """测试完整的导入工作流程"""
        csv_content = self.create_test_csv_content()
        df = pd.read_csv(io.StringIO(csv_content))
        
        # 验证数据解析
        assert len(df) == 4
        assert set(df.columns) == {'username', 'email', 'full_name', 'role'}
        
        # 验证数据验证
        validation_errors = []
        for _, row in df.iterrows():
            is_valid, errors = self.validator.validate_user_data(row.to_dict())
            if not is_valid:
                validation_errors.extend(errors)
        
        # 在这个测试数据中应该没有验证错误
        assert len(validation_errors) == 0
        
        # 验证角色分布
        role_counts = df['role'].value_counts()
        assert role_counts['student'] == 2
        assert role_counts['teacher'] == 1
        assert role_counts['admin'] == 1

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short", "-x"])