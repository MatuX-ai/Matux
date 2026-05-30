# 基于许可证的权限控制 - 使用示例

## 📚 概述

本文档提供基于许可证的权限控制系统的完整使用示例，帮助开发者快速集成到实际项目中。

---

## 🚀 快速开始

### 1. 导入依赖

```python
from fastapi import APIRouter, Depends
from backend.middleware.license_permission import (
    require_license_type,
    require_feature,
    LicensePermissionService,
    check_license_permission
)
from backend.models.license import LicenseType
```

---

## 💡 使用方式

### 方式一：装饰器（推荐）

#### 简单用法
```python
router = APIRouter()

@router.post("/ai/generate-course")
@require_license_type(LicenseType.WINDOWS_LOCAL, LicenseType.CLOUD_HOSTED)
async def generate_ai_course(
    request: CourseGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI 课程生成（仅付费版可用）
    """
    # 业务逻辑...
    return {"course_id": "123"}
```

#### 多个许可证类型
```python
@router.post("/advanced-analytics")
@require_license_type(
    LicenseType.CLOUD_HOSTED,
    LicenseType.ENTERPRISE
)
async def get_advanced_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    高级数据分析（云托管版和企业版专用）
    """
    pass
```

### 方式二：功能权限装饰器

```python
@router.get("/chat/assistant")
@require_feature("ai_chat_assistant")
async def ai_chat_assistant(
    message: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI 聊天助手（根据权限矩阵自动判断）
    """
    # 如果用户许可证不支持，会自动抛出 403
    response = await call_llm_api(message)
    return {"response": response}
```

### 方式三：服务层手动检查

```python
@router.get("/check-permission")
async def check_my_permissions(
    feature: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    手动检查特定功能权限
    """
    license_service = LicensePermissionService(db)
    
    result = await license_service.verify_feature_access(
        user_id=current_user.id,
        feature=feature
    )
    
    return result

# 返回示例：
# {
#     "allowed": true,
#     "reason": "权限验证通过",
#     "upgrade_suggestion": "",
#     "license_type": "cloud_hosted"
# }
```

### 方式四：依赖注入

```python
@router.get("/premium-feature")
async def access_premium_feature(
    permission_result: dict = Depends(
        check_license_permission("ai_course_generation")
    ),
    current_user: User = Depends(get_current_user)
):
    """
    使用依赖注入检查权限
    """
    if not permission_result["allowed"]:
        raise HTTPException(
            status_code=403,
            detail=permission_result
        )
    
    # 继续业务逻辑...
    return {"data": "premium content"}
```

---

## 📋 完整路由示例

### 课程管理路由

```python
from fastapi import APIRouter, Depends, HTTPException
from backend.middleware.license_permission import require_license_type, require_feature
from backend.models.license import LicenseType

router = APIRouter(prefix="/courses", tags=["Courses"])

# ============================================
# 基础功能（所有版本可用）
# ============================================

@router.get("/list")
async def list_courses(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """列出所有课程（基础功能）"""
    courses = db.query(Course).filter(
        Course.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return {"courses": courses, "total": len(courses)}

@router.post("/create")
async def create_course(
    request: CourseCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建课程（基础功能）"""
    course = Course(**request.dict(), user_id=current_user.id)
    db.add(course)
    db.commit()
    return {"course_id": course.id}

# ============================================
# AI 功能（仅付费版可用）
# ============================================

@router.post("/generate")
@require_license_type(
    LicenseType.WINDOWS_LOCAL,
    LicenseType.CLOUD_HOSTED,
    LicenseType.ENTERPRISE
)
async def generate_course_with_ai(
    request: AICourseGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """使用 AI 生成课程（付费版专用）"""
    # AI 生成逻辑...
    course_data = await ai_generate_course(request.topic)
    
    course = Course(
        **course_data,
        user_id=current_user.id,
        generated_by_ai=True
    )
    db.add(course)
    db.commit()
    
    return {"course_id": course.id, "ai_generated": True}

@router.post("/{course_id}/enhance")
@require_feature("ai_course_generation")
async def enhance_course(
    course_id: str,
    enhancements: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """增强课程内容（AI 功能）"""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # AI 增强逻辑...
    enhanced_content = await ai_enhance_content(course.content, enhancements)
    course.content = enhanced_content
    db.commit()
    
    return {"status": "enhanced", "content": enhanced_content}

# ============================================
# 云端同步功能（仅云托管版和企业版）
# ============================================

@router.post("/sync-to-cloud")
@require_feature("cloud_sync")
async def sync_course_to_cloud(
    course_ids: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """同步课程到云端（云托管版专用）"""
    for course_id in course_ids:
        await upload_to_cloud_storage(course_id, current_user.id)
    
    return {"status": "synced", "count": len(course_ids)}

@router.get("/cloud/list")
@require_feature("cloud_sync")
async def list_cloud_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """列出云端课程（云托管版专用）"""
    cloud_courses = await fetch_from_cloud_storage(current_user.id)
    return {"courses": cloud_courses}

# ============================================
# 离线模式功能（仅 Windows 本地版和企业版）
# ============================================

@router.post("/download-for-offline")
@require_feature("offline_mode")
async def download_for_offline(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下载课程供离线使用（Windows 本地版专用）"""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # 下载到本地存储...
    local_path = await save_to_local_storage(course)
    
    return {
        "status": "downloaded",
        "local_path": local_path,
        "available_offline": True
    }

@router.get("/offline/list")
@require_feature("offline_mode")
async def list_offline_courses(
    current_user: User = Depends(get_current_user)
):
    """列出可离线使用的课程（Windows 本地版专用）"""
    offline_courses = await get_locally_stored_courses(current_user.id)
    return {"courses": offline_courses}
```

### Token 计费路由

```python
from backend.middleware.license_permission import require_license_type

router = APIRouter(prefix="/token", tags=["Token Billing"])

@router.get("/balance")
@require_license_type(
    LicenseType.WINDOWS_LOCAL,
    LicenseType.CLOUD_HOSTED,
    LicenseType.ENTERPRISE
)
async def get_token_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查询 Token 余额（付费版专用）"""
    balance = await get_user_token_balance(current_user.id, db)
    return {
        "total": balance.total,
        "used": balance.used,
        "remaining": balance.remaining
    }

@router.post("/purchase")
@require_license_type(
    LicenseType.WINDOWS_LOCAL,
    LicenseType.CLOUD_HOSTED,
    LicenseType.ENTERPRISE
)
async def purchase_token_package(
    package_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """购买 Token 套餐（付费版专用）"""
    result = await process_token_purchase(
        user_id=current_user.id,
        package_id=package_id,
        db=db
    )
    return result

@router.get("/monthly-bonus")
@require_feature("monthly_bonus_tokens")
async def claim_monthly_bonus(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """领取月度赠送 Token（云托管版和企业版专用）"""
    bonus_amount = await calculate_monthly_bonus(current_user.id, db)
    
    if bonus_amount > 0:
        await add_bonus_tokens(current_user.id, bonus_amount, db)
        return {
            "claimed": True,
            "amount": bonus_amount
        }
    else:
        return {
            "claimed": False,
            "reason": "本月已领取过赠送 Token"
        }
```

---

## 🔍 错误处理

### 标准错误响应

```python
# 无许可证
{
    "error": "no_license",
    "message": "未找到有效许可证，请先激活许可证",
    "upgrade_suggestion": "请购买或激活许可证以使用该功能"
}

# 许可证不足
{
    "error": "insufficient_license",
    "message": "当前许可证类型 (open_source) 不支持此功能",
    "required_types": ["windows_local", "cloud_hosted"],
    "current_type": "open_source",
    "upgrade_suggestion": "升级到 Windows 本地版或云托管版以解锁 AI 功能和高级特性"
}

# 许可证过期
{
    "error": "expired_license",
    "message": "许可证已过期",
    "upgrade_suggestion": "请续费或重新购买许可证"
}

# 功能不允许
{
    "error": "feature_not_allowed",
    "message": "当前许可证类型 (open_source) 不支持 'cloud_sync' 功能",
    "upgrade_suggestion": "升级到 Windows 本地版或云托管版以解锁 AI 功能和高级特性"
}
```

### 自定义错误处理

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

@app.exception_handler(HTTPException)
async def license_exception_handler(request: Request, exc: HTTPException):
    """自定义许可证异常处理器"""
    
    if exc.status_code == 403:
        detail = exc.detail
        
        if isinstance(detail, dict):
            error_type = detail.get("error", "")
            
            # 根据错误类型返回不同的响应
            if error_type == "no_license":
                return JSONResponse(
                    status_code=403,
                    content={
                        "code": "LICENSE_REQUIRED",
                        "message": detail["message"],
                        "action_required": "PURCHASE_LICENSE",
                        "upgrade_link": "/pricing"
                    }
                )
            
            elif error_type == "insufficient_license":
                return JSONResponse(
                    status_code=403,
                    content={
                        "code": "LICENSE_UPGRADE_REQUIRED",
                        "message": detail["message"],
                        "current_license": detail["current_type"],
                        "required_licenses": detail["required_types"],
                        "upgrade_link": f"/pricing?target={detail['required_types'][0]}"
                    }
                )
    
    # 默认处理
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail)}
    )
```

---

## 🧪 测试示例

### 单元测试

```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_open_source_user_access_basic_feature():
    """测试开源版用户访问基础功能"""
    # 模拟登录（开源版用户）
    response = client.post("/login", json={
        "username": "opensource_user",
        "password": "password123"
    })
    token = response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 访问基础功能（应该成功）
    response = client.get("/courses/list", headers=headers)
    assert response.status_code == 200

def test_open_source_user_denied_ai_feature():
    """测试开源版用户访问 AI 功能被拒绝"""
    # 模拟登录（开源版用户）
    response = client.post("/login", json={
        "username": "opensource_user",
        "password": "password123"
    })
    token = response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 访问 AI 功能（应该被拒绝）
    response = client.post("/courses/generate", headers=headers)
    assert response.status_code == 403
    assert response.json()["error"] == "insufficient_license"

def test_cloud_hosted_user_can_sync():
    """测试云托管版用户可以云端同步"""
    # 模拟登录（云托管版用户）
    response = client.post("/login", json={
        "username": "cloud_user",
        "password": "password123"
    })
    token = response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 访问云端同步功能（应该成功）
    response = client.post("/courses/sync-to-cloud", headers=headers)
    assert response.status_code == 200
```

---

## 📊 最佳实践

### 1. 在路由层级使用装饰器

```python
# ✅ 推荐：在路由函数上使用装饰器
@router.post("/ai/generate")
@require_license_type(LicenseType.WINDOWS_LOCAL)
async def generate(...):
    pass

# ❌ 不推荐：在业务逻辑中手动检查
async def generate(...):
    license = get_user_license()
    if license.type != LicenseType.WINDOWS_LOCAL:
        raise HTTPException(403)
    pass
```

### 2. 使用功能名称而非硬编码许可证类型

```python
# ✅ 推荐：使用功能名称，更易维护
@require_feature("ai_chat_assistant")
async def chat(...):
    pass

# ❌ 不推荐：硬编码许可证类型
@require_license_type(LicenseType.WINDOWS_LOCAL, LicenseType.CLOUD_HOSTED)
async def chat(...):
    pass
```

### 3. 提供清晰的升级建议

```python
# ✅ 推荐：在错误响应中包含升级链接
{
    "error": "insufficient_license",
    "upgrade_link": "/pricing?target=cloud_hosted"
}

# ❌ 不推荐：只返回错误信息
{
    "error": "permission denied"
}
```

### 4. 缓存权限检查结果

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def check_permission_cached(user_id: str, feature: str, ttl: int = 300):
    """缓存权限检查结果（5 分钟有效期）"""
    return license_service.verify_feature_access(user_id, feature)
```

---

## 🔄 扩展示例

### 添加新的许可证类型

```python
# 1. 在 LicenseType 枚举中添加
class LicenseType(str, Enum):
    # ... existing types ...
    STARTUP = "startup"  # 创业公司版

# 2. 更新权限矩阵
PERMISSION_MATRIX["ai_course_generation"][LicenseType.STARTUP] = True

# 3. 添加升级建议
UPGRADE_SUGGESTIONS[LicenseType.STARTUP] = "升级到商业版以获得更多功能"
```

### 添加新的受控功能

```python
# 在权限矩阵中添加新功能
PERMISSION_MATRIX["video_conferencing"] = {
    LicenseType.OPEN_SOURCE: False,
    LicenseType.WINDOWS_LOCAL: False,
    LicenseType.CLOUD_HOSTED: True,
    LicenseType.ENTERPRISE: True,
}

# 在路由中使用
@router.post("/video/meeting")
@require_feature("video_conferencing")
async def create_video_meeting(...):
    pass
```

---

**最后更新**: 2026-03-14  
**维护者**: iMato Team
