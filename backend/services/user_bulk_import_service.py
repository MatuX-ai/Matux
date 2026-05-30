"""
用户批量导入服务
支持CSV/XLSX格式导入，提供字段映射、冲突检测与处理功能
"""

import io
from typing import Dict, List, Tuple

from fastapi import UploadFile
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserRole
from utils.logger import get_logger

logger = get_logger(__name__)


class ImportResult:
    """导入结果类"""

    def __init__(self):
        self.success_count = 0
        self.failed_count = 0
        self.conflicts_count = 0
        self.errors = []
        self.conflicts = []
        self.imported_users = []


class ConflictResolution:
    """冲突解决策略"""

    SKIP = "skip"  # 跳过重复项
    UPDATE = "update"  # 更新现有用户
    OVERWRITE = "overwrite"  # 完全覆盖
    ERROR = "error"  # 报错停止


class UserImportValidator:
    """用户导入数据验证器"""

    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """验证用户名"""
        if not username or not username.strip():
            return False, "用户名不能为空"

        username = username.strip()
        if len(username) < 3:
            return False, "用户名长度不能少于3个字符"

        if len(username) > 50:
            return False, "用户名长度不能超过50个字符"

        return True, ""

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """验证邮箱"""
        if not email or not email.strip():
            return False, "邮箱不能为空"

        email = email.strip().lower()
        if "@" not in email or "." not in email.split("@")[1]:
            return False, "邮箱格式不正确"

        if len(email) > 100:
            return False, "邮箱长度不能超过100个字符"

        return True, ""

    @staticmethod
    def validate_role(role: str) -> Tuple[bool, str]:
        """验证角色"""
        if not role:
            return True, ""  # 角色可选

        role = role.lower().strip()
        valid_roles = [r.value for r in UserRole]

        if role not in valid_roles:
            return False, f"无效的角色，有效角色包括: {', '.join(valid_roles)}"

        return True, ""


class UserBulkImportService:
    """用户批量导入服务"""

    def __init__(self):
        self.validator = UserImportValidator()

    async def parse_csv_file(self, file_content: bytes) -> List[Dict]:
        """解析CSV文件"""
        try:
            # 使用pandas读取CSV，自动处理编码问题
            df = pd.read_csv(io.BytesIO(file_content))
            return df.to_dict("records")
        except Exception as e:
            logger.error(f"CSV解析失败: {str(e)}")
            raise ValueError(f"CSV文件解析失败: {str(e)}")

    async def parse_xlsx_file(self, file_content: bytes) -> List[Dict]:
        """解析XLSX文件"""
        try:
            # 使用pandas读取Excel文件
            df = pd.read_excel(io.BytesIO(file_content))
            return df.to_dict("records")
        except Exception as e:
            logger.error(f"Excel解析失败: {str(e)}")
            raise ValueError(f"Excel文件解析失败: {str(e)}")

    async def parse_upload_file(self, file: UploadFile) -> List[Dict]:
        """根据文件类型解析上传文件"""
        content = await file.read()

        if file.content_type == "text/csv":
            return await self.parse_csv_file(content)
        elif file.content_type in [
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ]:
            return await self.parse_xlsx_file(content)
        else:
            raise ValueError("不支持的文件格式，请上传CSV或Excel文件")

    def map_fields(
        self, raw_data: List[Dict], field_mapping: Dict[str, str] = None
    ) -> List[Dict]:
        """字段映射处理"""
        if not field_mapping:
            # 默认字段映射
            field_mapping = {"username": "username", "email": "email", "role": "role"}

        mapped_data = []
        for row in raw_data:
            mapped_row = {}
            for target_field, source_field in field_mapping.items():
                # 查找源字段（支持多种可能的列名）
                value = None
                possible_names = [
                    source_field,
                    source_field.upper(),
                    source_field.title(),
                ]

                for name in possible_names:
                    if name in row and row[name] is not None and str(row[name]).strip():
                        value = str(row[name]).strip()
                        break

                mapped_row[target_field] = value

            # 只保留有关键字段的数据
            if mapped_row.get("username") or mapped_row.get("email"):
                mapped_data.append(mapped_row)

        return mapped_data

    async def check_conflicts(self, db: AsyncSession, users_data: List[Dict]) -> Dict:
        """检查数据冲突"""
        conflicts = {
            "email_conflicts": [],  # 邮箱冲突
            "username_conflicts": [],  # 用户名冲突
            "invalid_data": [],  # 数据验证失败
        }

        # 收集所有邮箱和用户名用于批量查询
        emails = [
            user.get("email", "").lower().strip()
            for user in users_data
            if user.get("email")
        ]
        usernames = [
            user.get("username", "").strip()
            for user in users_data
            if user.get("username")
        ]

        # 查询已存在的用户
        existing_emails = set()
        existing_usernames = set()

        if emails:
            email_query = select(User.email).where(User.email.in_(emails))
            email_result = await db.execute(email_query)
            existing_emails = {email[0].lower() for email in email_result.fetchall()}

        if usernames:
            username_query = select(User.username).where(User.username.in_(usernames))
            username_result = await db.execute(username_query)
            existing_usernames = {
                username[0] for username in username_result.fetchall()
            }

        # 检查每条记录
        for i, user_data in enumerate(users_data):
            row_num = i + 2  # Excel行号（从第2行开始，第1行为标题）

            # 验证用户名
            username = user_data.get("username", "")
            if username:
                is_valid, error_msg = self.validator.validate_username(username)
                if not is_valid:
                    conflicts["invalid_data"].append(
                        {
                            "row": row_num,
                            "field": "username",
                            "value": username,
                            "error": error_msg,
                        }
                    )
                elif username in existing_usernames:
                    conflicts["username_conflicts"].append(
                        {"row": row_num, "username": username, "existing": True}
                    )

            # 验证邮箱
            email = user_data.get("email", "")
            if email:
                is_valid, error_msg = self.validator.validate_email(email)
                if not is_valid:
                    conflicts["invalid_data"].append(
                        {
                            "row": row_num,
                            "field": "email",
                            "value": email,
                            "error": error_msg,
                        }
                    )
                elif email.lower().strip() in existing_emails:
                    conflicts["email_conflicts"].append(
                        {"row": row_num, "email": email, "existing": True}
                    )

            # 验证角色
            role = user_data.get("role", "")
            if role:
                is_valid, error_msg = self.validator.validate_role(role)
                if not is_valid:
                    conflicts["invalid_data"].append(
                        {
                            "row": row_num,
                            "field": "role",
                            "value": role,
                            "error": error_msg,
                        }
                    )

        return conflicts

    async def import_users(
        self,
        db: AsyncSession,
        file: UploadFile,
        conflict_resolution: str = ConflictResolution.SKIP,
        field_mapping: Dict[str, str] = None,
        generate_password: bool = True,
    ) -> ImportResult:
        """
        批量导入用户

        Args:
            db: 数据库会话
            file: 上传的文件
            conflict_resolution: 冲突解决策略
            field_mapping: 字段映射配置
            generate_password: 是否自动生成密码

        Returns:
            ImportResult: 导入结果
        """
        result = ImportResult()

        try:
            # 解析文件
            logger.info(f"开始解析文件: {file.filename}")
            raw_data = await self.parse_upload_file(file)

            if not raw_data:
                raise ValueError("文件为空或无法解析")

            logger.info(f"解析到 {len(raw_data)} 条记录")

            # 字段映射
            mapped_data = self.map_fields(raw_data, field_mapping)
            logger.info(f"字段映射后剩余 {len(mapped_data)} 条有效记录")

            # 检查冲突
            conflicts = await self.check_conflicts(db, mapped_data)

            # 处理冲突
            if conflicts["email_conflicts"] or conflicts["username_conflicts"]:
                if conflict_resolution == ConflictResolution.ERROR:
                    result.conflicts = conflicts
                    result.errors.append("发现数据冲突，导入已停止")
                    return result
                elif conflict_resolution == ConflictResolution.SKIP:
                    # 移除有冲突的记录
                    conflict_usernames = {
                        conflict["username"]
                        for conflict in conflicts["username_conflicts"]
                    }
                    conflict_emails = {
                        conflict["email"].lower()
                        for conflict in conflicts["email_conflicts"]
                    }

                    filtered_data = []
                    for user_data in mapped_data:
                        username = user_data.get("username", "")
                        email = user_data.get("email", "").lower()

                        if username in conflict_usernames or email in conflict_emails:
                            result.conflicts_count += 1
                            continue

                        filtered_data.append(user_data)

                    mapped_data = filtered_data
                    result.conflicts = conflicts

            # 验证最终数据
            valid_users = []
            for i, user_data in enumerate(mapped_data):
                row_num = i + 2

                # 基本验证
                if not user_data.get("username") and not user_data.get("email"):
                    result.failed_count += 1
                    result.errors.append(f"第{row_num}行: 用户名和邮箱都为空")
                    continue

                # 构建用户对象
                user = User()
                user.username = (
                    user_data.get("username", "").strip()
                    if user_data.get("username")
                    else ""
                )
                user.email = (
                    user_data.get("email", "").lower().strip()
                    if user_data.get("email")
                    else ""
                )

                # 设置默认密码或随机密码
                if generate_password:
                    import secrets
                    import string

                    alphabet = string.ascii_letters + string.digits
                    password = "".join(secrets.choice(alphabet) for _ in range(12))
                    user.set_password(password)
                else:
                    user.set_password("123456")  # 默认密码

                # 设置角色
                role_str = user_data.get("role", "user").lower().strip()
                try:
                    user.role = (
                        UserRole(role_str)
                        if role_str in [r.value for r in UserRole]
                        else UserRole.USER
                    )
                except ValueError:
                    user.role = UserRole.USER

                user.is_active = True
                user.is_superuser = False

                valid_users.append(user)

            # 批量保存用户
            if valid_users:
                db.add_all(valid_users)
                await db.commit()

                # 刷新获取ID
                for user in valid_users:
                    await db.refresh(user)
                    result.imported_users.append(user.to_dict())

                result.success_count = len(valid_users)
                logger.info(f"成功导入 {result.success_count} 个用户")

        except Exception as e:
            logger.error(f"批量导入失败: {str(e)}")
            result.errors.append(f"导入过程发生错误: {str(e)}")
            await db.rollback()

        return result


# 创建服务实例
user_bulk_import_service = UserBulkImportService()
