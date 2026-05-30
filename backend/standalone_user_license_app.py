"""
独立的用户许可证路由文件
不依赖其他模块，专注用户许可证功能
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import hashlib
from typing import Optional

from fastapi import Body, Depends, FastAPI, HTTPException, Path, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt


# 简化的模型定义
class User:
    def __init__(
        self, id, username, email, role="user", is_active=True, is_superuser=False
    ):
        self.id = id
        self.username = username
        self.email = email
        self.role = role
        self.is_active = is_active
        self.is_superuser = is_superuser

    def has_role(self, role):
        return self.role == role

    def has_any_role(self, roles):
        return self.role in roles

    def can_manage_licenses(self):
        return self.role in ["admin", "org_admin"]

    def is_admin(self):
        return self.role in ["admin", "org_admin"] or self.is_superuser


class License:
    def __init__(self, id, license_key, organization_id, license_type="commercial"):
        self.id = id
        self.license_key = license_key
        self.organization_id = organization_id
        self.license_type = license_type
        self.is_valid = True
        self.expires_at = datetime.now() + timedelta(days=365)


class UserLicense:
    def __init__(self, user_id, license_id, role="user", status="active"):
        self.user_id = user_id
        self.license_id = license_id
        self.role = role
        self.status = status
        self.can_manage = role in ["admin", "org_admin"]
        self.can_use = True
        self.can_view = True
        self.assigned_at = datetime.now()


# 简化的认证系统
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# 内存数据库（开发用）
users_db = {}
licenses_db = {}
user_licenses_db = {}


# 初始化示例数据
def init_sample_data():
    # 创建示例用户
    admin_pwd = hashlib.md5("password123".encode()).hexdigest()
    users_db[1] = User(1, "admin", "admin@example.com", "admin")
    users_db[2] = User(2, "orgadmin", "orgadmin@example.com", "org_admin")
    users_db[3] = User(3, "user1", "user1@example.com", "user")
    users_db[4] = User(4, "user2", "user2@example.com", "premium")

    # 存储密码
    users_db[1].hashed_password = admin_pwd
    users_db[2].hashed_password = admin_pwd
    users_db[3].hashed_password = admin_pwd
    users_db[4].hashed_password = admin_pwd

    # 创建示例许可证
    licenses_db[1] = License(1, "TEST-LICENSE-001", 1, "enterprise")
    licenses_db[2] = License(2, "TEST-LICENSE-002", 2, "commercial")

    # 创建用户许可证关联
    user_licenses_db[(1, 1)] = UserLicense(1, 1, "admin", "active")
    user_licenses_db[(2, 1)] = UserLicense(2, 1, "org_admin", "active")
    user_licenses_db[(3, 2)] = UserLicense(3, 2, "user", "active")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 查找用户
    user = None
    for u in users_db.values():
        if u.username == username:
            user = u
            break

    if user is None:
        raise credentials_exception
    return user


# 创建FastAPI应用
app = FastAPI(title="用户许可证对接服务", version="1.0.0")


# 认证路由
@app.post("/api/v1/auth/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录获取令牌"""
    # 验证用户
    user = None
    for u in users_db.values():
        if u.username == form_data.username:
            # 简单密码验证
            if hasattr(u, "hashed_password"):
                input_hash = hashlib.md5(form_data.password.encode()).hexdigest()
                if input_hash == u.hashed_password:
                    user = u
                    break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/v1/auth/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
    }


# 用户许可证路由
@app.get("/api/v1/users/{user_id}/licenses")
async def get_user_licenses(
    user_id: int = Path(..., description="用户ID"),
    include_inactive: bool = Query(False, description="是否包含非活跃的许可证"),
    current_user: User = Depends(get_current_user),
):
    """获取用户的所有许可证关联"""
    # 权限检查
    if current_user.id != user_id and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权查看其他用户的许可证信息"
        )

    # 获取用户许可证
    user_licenses = []
    for (uid, lid), ul in user_licenses_db.items():
        if uid == user_id:
            if include_inactive or ul.status == "active":
                license_info = licenses_db.get(lid)
                user_licenses.append(
                    {
                        "user_id": ul.user_id,
                        "license_id": ul.license_id,
                        "role": ul.role,
                        "status": ul.status,
                        "can_manage": ul.can_manage,
                        "can_use": ul.can_use,
                        "can_view": ul.can_view,
                        "assigned_at": ul.assigned_at.isoformat(),
                        "license_key": (
                            license_info.license_key if license_info else None
                        ),
                        "license_type": (
                            license_info.license_type if license_info else None
                        ),
                    }
                )

    return user_licenses


@app.post("/api/v1/users/{user_id}/licenses")
async def assign_license_to_user(
    user_id: int = Path(..., description="用户ID"),
    license_id: int = Body(..., embed=True),
    role: str = Body("user", embed=True),
    current_user: User = Depends(get_current_user),
):
    """为用户分配许可证"""
    # 权限检查
    if not current_user.can_manage_licenses():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权分配许可证"
        )

    # 检查用户和许可证是否存在
    if user_id not in [u.id for u in users_db.values()]:
        raise HTTPException(status_code=404, detail="用户不存在")

    if license_id not in licenses_db:
        raise HTTPException(status_code=404, detail="许可证不存在")

    # 检查是否已存在关联
    if (user_id, license_id) in user_licenses_db:
        raise HTTPException(status_code=409, detail="用户已关联此许可证")

    # 创建关联
    user_license = UserLicense(user_id, license_id, role, "active")
    user_licenses_db[(user_id, license_id)] = user_license

    # 返回结果
    license_info = licenses_db[license_id]
    return {
        "user_id": user_license.user_id,
        "license_id": user_license.license_id,
        "role": user_license.role,
        "status": user_license.status,
        "can_manage": user_license.can_manage,
        "can_use": user_license.can_use,
        "can_view": user_license.can_view,
        "assigned_at": user_license.assigned_at.isoformat(),
        "license_key": license_info.license_key,
        "license_type": license_info.license_type,
    }


@app.get("/api/v1/users/me/licenses")
async def get_my_licenses(
    include_inactive: bool = Query(False, description="是否包含非活跃的许可证"),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的所有许可证（便捷接口）"""
    return await get_user_licenses(current_user.id, include_inactive, current_user)


# 健康检查和其他端点
@app.get("/")
async def root():
    return {
        "message": "User License Integration Service",
        "version": "1.0.0",
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/info")
async def api_info():
    return {
        "service": "用户许可证对接服务",
        "version": "1.0.0",
        "endpoints": {
            "认证": "/api/v1/auth/*",
            "用户许可证": "/api/v1/users/*",
            "文档": "/docs",
        },
        "authentication": "JWT Token",
        "test_accounts": {
            "admin": "password123",
            "orgadmin": "password123",
            "user1": "password123",
            "user2": "password123",
        },
    }


# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """初始化示例数据"""
    init_sample_data()
    print("✅ 用户许可证服务启动成功")
    print("📝 API文档: http://localhost:8000/docs")
    print("🏥 健康检查: http://localhost:8000/health")
    print("🔐 测试账户已初始化")


if __name__ == "__main__":
    import uvicorn

    print("🚀 启动用户许可证对接服务...")
    print("📝 API文档: http://localhost:8000/docs")
    print("🏥 健康检查: http://localhost:8000/health")
    print("🔐 测试账户:")
    print("   - admin / password123 (管理员)")
    print("   - orgadmin / password123 (企业管理员)")
    print("   - user1 / password123 (普通用户)")
    print("   - user2 / password123 (高级用户)")

    uvicorn.run("standalone_user_license_app:app", host="0.0.0.0", port=8000)
