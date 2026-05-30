"""
权限系统演示脚本
展示RBAC权限系统的完整功能和使用方法
"""

import asyncio
from datetime import datetime, timedelta
import logging

from models.user import User, UserRole
from models.permission import Permission, Role
from services.permission_service import permission_service
from utils.decorators import require_role, require_permission, admin_required
from utils.database import get_async_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demonstrate_permission_system():
    """演示权限系统功能"""
    
    print("=" * 60)
    print("🔐 RBAC权限系统演示")
    print("=" * 60)
    
    async for db in get_async_db():
        try:
            # 1. 初始化权限系统
            print("\n📋 1. 初始化权限系统")
            print("-" * 40)
            
            permission_map = await permission_service.initialize_system_permissions(db)
            print(f"✅ 创建了 {len(permission_map)} 个系统权限")
            
            role_map = await permission_service.initialize_system_roles(db)
            print(f"✅ 创建了 {len(role_map)} 个系统角色")
            
            # 2. 展示系统权限
            print("\n🎯 2. 系统权限概览")
            print("-" * 40)
            
            permissions = await permission_service.get_permission_logs(limit=10, db=db)
            print("系统预定义权限包括:")
            permission_categories = {}
            for perm_code in permission_map.keys():
                category = perm_code.split('.')[0]
                if category not in permission_categories:
                    permission_categories[category] = []
                permission_categories[category].append(perm_code)
            
            for category, perms in permission_categories.items():
                print(f"  📁 {category.upper()} 类权限:")
                for perm in perms[:3]:  # 只显示前3个
                    print(f"    • {perm}")
                if len(perms) > 3:
                    print(f"    ... 还有 {len(perms) - 3} 个权限")
            
            # 3. 展示系统角色
            print("\n👥 3. 系统角色概览")
            print("-" * 40)
            
            system_roles = [
                ("super_admin", "超级管理员", "拥有系统全部权限"),
                ("admin", "管理员", "管理系统主要功能"),
                ("org_admin", "企业管理员", "管理企业相关功能"),
                ("teacher", "教师", "课程教学相关权限"),
                ("student", "学生", "学习相关权限")
            ]
            
            for code, name, desc in system_roles:
                print(f"  👤 {name} ({code})")
                print(f"     {desc}")
            
            # 4. 演示权限检查装饰器
            print("\n🛡️ 4. 权限检查装饰器演示")
            print("-" * 40)
            
            # 创建测试用户
            admin_user = User()
            admin_user.id = 1
            admin_user.username = "admin_user"
            admin_user.role = UserRole.ADMIN
            admin_user.is_superuser = True
            
            normal_user = User()
            normal_user.id = 2
            normal_user.username = "normal_user"
            normal_user.role = UserRole.USER
            
            # 测试角色装饰器
            @require_role(UserRole.ADMIN)
            async def admin_only_function(current_user=None):
                return "✅ 管理员功能执行成功"
            
            @require_permission("user.read")
            async def permission_required_function(current_user=None, db=None):
                return "✅ 需要用户读取权限的功能执行成功"
            
            print("测试角色权限装饰器:")
            try:
                result = await admin_only_function(current_user=admin_user)
                print(f"  管理员调用: {result}")
            except Exception as e:
                print(f"  管理员调用失败: {e}")
            
            try:
                result = await admin_only_function(current_user=normal_user)
                print(f"  普通用户调用: {result}")
            except Exception as e:
                print(f"  ❌ 普通用户调用失败: {type(e).__name__}")
            
            print("\n测试权限装饰器:")
            try:
                result = await permission_required_function(current_user=admin_user, db=db)
                print(f"  管理员调用: {result}")
            except Exception as e:
                print(f"  管理员调用失败: {e}")
            
            # 5. 演示用户角色管理
            print("\n👤 5. 用户角色管理演示")
            print("-" * 40)
            
            # 为普通用户分配教师角色
            try:
                assignment = await permission_service.assign_role_to_user(
                    user_id=normal_user.id,
                    role_code="teacher",
                    assigned_by=admin_user.id,
                    db=db
                )
                print(f"✅ 成功为用户 {normal_user.username} 分配教师角色")
                print(f"   分配ID: {assignment.id}")
                print(f"   分配时间: {assignment.assigned_at}")
                
                # 检查用户权限
                user_permissions = await permission_service.get_user_permissions(normal_user.id, db)
                print(f"   用户现在拥有 {len(user_permissions)} 个权限:")
                for perm in user_permissions[:5]:  # 显示前5个
                    print(f"     • {perm.code}")
                if len(user_permissions) > 5:
                    print(f"     ... 还有 {len(user_permissions) - 5} 个权限")
                
                # 撤销角色
                revoke_result = await permission_service.revoke_role_from_user(
                    user_id=normal_user.id,
                    role_code="teacher",
                    revoked_by=admin_user.id,
                    db=db
                )
                print(f"✅ 成功撤销用户 {normal_user.username} 的教师角色")
                
            except Exception as e:
                print(f"❌ 角色管理操作失败: {e}")
            
            # 6. 权限检查演示
            print("\n🔍 6. 权限检查演示")
            print("-" * 40)
            
            test_cases = [
                (admin_user.id, "user.create", "管理员创建用户权限"),
                (normal_user.id, "user.read", "普通用户读取用户权限"),
                (normal_user.id, "user.delete", "普通用户删除用户权限"),
                (admin_user.id, "system.config", "管理员系统配置权限")
            ]
            
            for user_id, perm_code, description in test_cases:
                has_permission = await permission_service.check_user_permission(
                    user_id, perm_code, db
                )
                status = "✅ 有权限" if has_permission else "❌ 无权限"
                print(f"  {description}: {status}")
            
            # 7. 权限日志演示
            print("\n📝 7. 权限日志演示")
            print("-" * 40)
            
            # 记录一些测试日志
            await permission_service.log_permission_change(
                user_id=admin_user.id,
                target_user_id=normal_user.id,
                action_type="demo_test",
                resource_type="user",
                resource_id=normal_user.id,
                role_code="teacher",
                description="权限系统演示测试日志",
                db=db
            )
            
            # 查询日志
            logs = await permission_service.get_permission_logs(limit=5, db=db)
            print(f"最近 {len(logs)} 条权限日志:")
            for log in logs:
                print(f"  • [{log.created_at.strftime('%Y-%m-%d %H:%M:%S')}] "
                      f"{log.action_type} - {log.description}")
            
            print("\n🎉 权限系统演示完成!")
            print("=" * 60)
            
            break
            
        except Exception as e:
            logger.error(f"演示过程中发生错误: {e}")
            raise


def show_permission_api_examples():
    """展示权限API使用示例"""
    
    print("\n📚 权限API使用示例")
    print("=" * 60)
    
    api_examples = [
        {
            "title": "获取当前用户权限",
            "endpoint": "GET /api/v1/auth/me/permissions",
            "description": "获取当前认证用户的权限列表",
            "curl": 'curl -H "Authorization: Bearer <token>" '
                   'http://localhost:8000/api/v1/auth/me/permissions'
        },
        {
            "title": "检查用户权限",
            "endpoint": "GET /api/v1/auth/permissions/check?permission_code=user.read",
            "description": "检查当前用户是否具有指定权限",
            "curl": 'curl -H "Authorization: Bearer <token>" '
                   '"http://localhost:8000/api/v1/auth/permissions/check?permission_code=user.read"'
        },
        {
            "title": "为用户分配角色",
            "endpoint": "POST /api/v1/auth/users/{user_id}/roles/{role_code}",
            "description": "为指定用户分配角色（需要管理员权限）",
            "curl": 'curl -X POST -H "Authorization: Bearer <admin_token>" '
                   'http://localhost:8000/api/v1/auth/users/123/roles/teacher'
        },
        {
            "title": "创建自定义权限",
            "endpoint": "POST /api/v1/permissions/permissions",
            "description": "创建新的权限定义（需要系统配置权限）",
            "curl": '''curl -X POST -H "Authorization: Bearer <admin_token>" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "文档管理",
    "code": "document.manage",
    "description": "管理文档相关权限",
    "category": "document",
    "action": "manage"
  }' \\
  http://localhost:8000/api/v1/permissions/permissions'''
        },
        {
            "title": "获取权限变更日志",
            "endpoint": "GET /api/v1/permissions/logs",
            "description": "获取权限变更历史记录（仅管理员）",
            "curl": 'curl -H "Authorization: Bearer <admin_token>" '
                   '"http://localhost:8000/api/v1/permissions/logs?action_type=assign_role"'
        }
    ]
    
    for example in api_examples:
        print(f"\n🎯 {example['title']}")
        print(f"   接口: {example['endpoint']}")
        print(f"   说明: {example['description']}")
        print(f"   示例: {example['curl']}")


def show_decorator_usage_examples():
    """展示装饰器使用示例"""
    
    print("\n🎨 权限装饰器使用示例")
    print("=" * 60)
    
    examples = [
        {
            "title": "基本角色检查",
            "code": '''
@app.get("/admin/dashboard")
@require_role(UserRole.ADMIN)
async def admin_dashboard(current_user: User = Depends(get_current_user)):
    return {"message": "欢迎来到管理面板"}
''',
            "description": "只有管理员才能访问此接口"
        },
        {
            "title": "权限检查",
            "code": '''
@app.post("/users")
@require_permission("user.create")
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 创建用户逻辑
    pass
''',
            "description": "需要用户创建权限才能执行"
        },
        {
            "title": "多个权限任一满足",
            "code": '''
@app.put("/documents/{doc_id}")
@require_permission(["document.edit", "document.manage"], require_all=False)
async def update_document(doc_id: int):
    # 更新文档逻辑
    pass
''',
            "description": "拥有任一权限即可访问"
        },
        {
            "title": "角色或权限检查",
            "code": '''
@app.delete("/sensitive-data")
@require_any_role_or_permission(
    roles=[UserRole.ADMIN],
    permissions=["data.delete_sensitive"]
)
async def delete_sensitive_data():
    # 删除敏感数据
    pass
''',
            "description": "管理员或有特定权限的用户可以访问"
        },
        {
            "title": "动态权限检查",
            "code": '''
@app.post("/resources")
@conditional_require_permission(
    condition_field="action",
    permission_mapping={
        "create": "resource.create",
        "update": "resource.update",
        "delete": "resource.delete"
    }
)
async def manage_resource(action: str):
    # 根据action参数动态检查权限
    pass
''',
            "description": "根据操作类型动态要求不同权限"
        }
    ]
    
    for example in examples:
        print(f"\n📝 {example['title']}")
        print(f"说明: {example['description']}")
        print("代码:")
        print(example['code'])


if __name__ == "__main__":
    print("🚀 启动权限系统演示...")
    
    # 运行演示
    asyncio.run(demonstrate_permission_system())
    
    # 显示API示例
    show_permission_api_examples()
    
    # 显示装饰器示例
    show_decorator_usage_examples()
    
    print("\n💡 提示:")
    print("• 使用 'python backend/migrations/003_create_permission_system.py upgrade' 创建表结构")
    print("• 使用 'python backend/migrations/003_create_permission_system.py seed' 填充初始数据")
    print("• 查看详细的API文档: http://localhost:8000/docs")