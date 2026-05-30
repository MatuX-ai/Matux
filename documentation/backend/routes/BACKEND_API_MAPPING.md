# iMatu 后端API端点映射文档

## 1. API整体架构

### 1.1 API版本管理

```
API版本策略:
/v1/ - 当前稳定版本
/v2/ - 开发中版本（如有）
/alpha/ - 内测版本
/beta/ - 公测版本

基础URL结构:
开发环境: http://localhost:8000/api/v1/
测试环境: https://test-api.imatu.com/api/v1/
生产环境: https://api.imatu.com/api/v1/
```

### 1.2 API设计原则

```python
# RESTful设计规范
- 使用名词而非动词
- 正确使用HTTP方法
- 合理的状态码返回
- 一致的命名约定
- 完整的错误处理

# 示例路由设计
GET    /users           # 获取用户列表
POST   /users           # 创建新用户
GET    /users/{id}      # 获取特定用户
PUT    /users/{id}      # 更新用户信息
DELETE /users/{id}      # 删除用户
```

## 2. 认证授权API

### 2.1 认证端点 (/api/v1/auth)

```python
# 路由文件: backend/routes/auth_routes.py

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录获取访问令牌"""
    pass

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """用户注册"""
    pass

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    pass

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_update: ProfileUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """更新用户个人资料"""
    pass

@router.post("/password-reset/request")
async def request_password_reset(email: str):
    """请求密码重置"""
    pass

@router.post("/password-reset/confirm")
async def confirm_password_reset(reset_data: PasswordResetConfirm):
    """确认密码重置"""
    pass

@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token: str):
    """刷新访问令牌"""
    pass
```

### 2.2 权限管理端点

```python
@router.get("/permissions")
async def get_user_permissions(current_user: User = Depends(get_current_user)):
    """获取用户权限列表"""
    pass

@router.get("/roles")
async def get_user_roles(current_user: User = Depends(get_current_user)):
    """获取用户角色信息"""
    pass
```

## 3. AI服务API

### 3.1 代码生成端点 (/api/v1/ai)

```python
# 路由文件: backend/routes/ai_routes.py

@router.post("/generate-code", response_model=CodeGenerationResponse)
async def generate_code(
    request: CodeGenerationRequest,
    current_user: User = Depends(get_current_user)
):
    """AI代码生成"""
    # 支持多种编程语言
    # 提供代码解释和优化建议
    pass

@router.post("/explain-code", response_model=CodeExplanationResponse)
async def explain_code(
    request: CodeExplanationRequest,
    current_user: User = Depends(get_current_user)
):
    """代码解释和分析"""
    pass

@router.post("/refactor-code", response_model=CodeRefactorResponse)
async def refactor_code(
    request: CodeRefactorRequest,
    current_user: User = Depends(get_current_user)
):
    """代码重构优化"""
    pass

@router.get("/models")
async def get_available_models(current_user: User = Depends(get_current_user)):
    """获取可用AI模型列表"""
    pass

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """AI对话接口"""
    pass

@router.get("/history")
async def get_generation_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """获取代码生成历史"""
    pass
```

## 4. 推荐系统API

### 4.1 推荐服务端点 (/api/v1/recommendations)

```python
# 路由文件: backend/routes/recommendation_routes.py

@router.get("/courses", response_model=List[CourseRecommendation])
async def get_course_recommendations(
    user_id: Optional[int] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """获取课程推荐"""
    pass

@router.get("/content", response_model=List[ContentRecommendation])
async def get_content_recommendations(
    content_type: Optional[str] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    pass

@router.get("/users", response_model=List[UserRecommendation])
async def get_user_recommendations(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """获取用户推荐（社交功能）"""
    pass

@router.post("/feedback")
async def submit_recommendation_feedback(
    feedback: RecommendationFeedback,
    current_user: User = Depends(get_current_user)
):
    """提交推荐反馈"""
    pass

@router.get("/personalized", response_model=PersonalizedRecommendations)
async def get_personalized_recommendations(
    current_user: User = Depends(get_current_user)
):
    """获取个性化综合推荐"""
    pass
```

## 5. 支付系统API

### 5.1 支付服务端点 (/api/v1/payments)

```python
# 路由文件: backend/routes/payment_routes.py

@router.post("/create", response_model=PaymentResponse)
async def create_payment(
    payment_request: PaymentCreate,
    current_user: User = Depends(get_current_user)
):
    """创建支付订单"""
    pass

@router.get("/{payment_id}", response_model=PaymentDetail)
async def get_payment_status(
    payment_id: str,
    current_user: User = Depends(get_current_user)
):
    """查询支付状态"""
    pass

@router.post("/{payment_id}/refund", response_model=RefundResponse)
async def request_refund(
    payment_id: str,
    refund_request: RefundRequest,
    current_user: User = Depends(get_current_user)
):
    """申请退款"""
    pass

@router.get("/history", response_model=List[PaymentHistory])
async def get_payment_history(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """获取支付历史记录"""
    pass

@router.post("/{payment_id}/webhook")
async def payment_webhook(
    payment_id: str,
    webhook_data: PaymentWebhook
):
    """支付回调处理"""
    pass

@router.get("/statistics")
async def get_payment_statistics(
    period: str = "month",
    current_user: User = Depends(get_current_user)
):
    """获取支付统计数据"""
    pass
```

## 6. 订阅系统API

### 6.1 订阅管理端点 (/api/v1/subscriptions)

```python
# 路由文件: backend/routes/subscription_routes.py

@router.get("/plans", response_model=List[SubscriptionPlan])
async def get_subscription_plans():
    """获取订阅计划列表"""
    pass

@router.post("/", response_model=SubscriptionResponse)
async def create_subscription(
    subscription_request: SubscriptionCreate,
    current_user: User = Depends(get_current_user)
):
    """创建订阅"""
    pass

@router.get("/me", response_model=SubscriptionDetail)
async def get_my_subscription(
    current_user: User = Depends(get_current_user)
):
    """获取我的订阅信息"""
    pass

@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    update_request: SubscriptionUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新订阅"""
    pass

@router.delete("/{subscription_id}")
async def cancel_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user)
):
    """取消订阅"""
    pass

@router.post("/{subscription_id}/upgrade", response_model=SubscriptionResponse)
async def upgrade_subscription(
    subscription_id: int,
    upgrade_request: SubscriptionUpgrade,
    current_user: User = Depends(get_current_user)
):
    """升级订阅"""
    pass
```

## 7. 硬件认证API

### 7.1 硬件服务端点 (/api/v1/hardware)

```python
# 路由文件: backend/routes/hardware_certification_routes.py

@router.post("/register", response_model=DeviceRegistrationResponse)
async def register_device(
    registration_data: DeviceRegistration,
    current_user: User = Depends(get_current_user)
):
    """设备注册"""
    pass

@router.post("/authenticate", response_model=DeviceAuthResponse)
async def authenticate_device(
    auth_data: DeviceAuthentication,
    current_user: User = Depends(get_current_user)
):
    """设备认证"""
    pass

@router.get("/{device_id}/status", response_model=DeviceStatus)
async def get_device_status(
    device_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取设备状态"""
    pass

@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device_info(
    device_id: str,
    update_data: DeviceUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新设备信息"""
    pass

@router.delete("/{device_id}")
async def delete_device(
    device_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除设备"""
    pass

@router.get("/my-devices", response_model=List[DeviceResponse])
async def get_my_devices(
    current_user: User = Depends(get_current_user)
):
    """获取我的设备列表"""
    pass
```

## 8. 许可证管理API

### 8.1 许可证服务端点 (/api/v1/licenses)

```python
# 路由文件: backend/routes/license_routes.py

@router.get("/", response_model=List[LicenseResponse])
async def get_licenses(
    skip: int = 0,
    limit: int = 50,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """获取许可证列表"""
    pass

@router.post("/", response_model=LicenseResponse)
async def create_license(
    license_data: LicenseCreate,
    current_user: User = Depends(get_current_user)
):
    """创建许可证"""
    pass

@router.get("/{license_id}", response_model=LicenseDetail)
async def get_license_detail(
    license_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取许可证详情"""
    pass

@router.put("/{license_id}", response_model=LicenseResponse)
async def update_license(
    license_id: int,
    update_data: LicenseUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新许可证"""
    pass

@router.delete("/{license_id}")
async def delete_license(
    license_id: int,
    current_user: User = Depends(get_current_user)
):
    """删除许可证"""
    pass

@router.post("/{license_id}/activate")
async def activate_license(
    license_id: int,
    activation_data: LicenseActivation,
    current_user: User = Depends(get_current_user)
):
    """激活许可证"""
    pass
```

### 8.2 用户许可证端点 (/api/v1/user-licenses)

```python
# 路由文件: backend/routes/user_license_routes.py

@router.get("/", response_model=List[UserLicenseResponse])
async def get_user_licenses(
    user_id: Optional[int] = None,
    license_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """获取用户许可证列表"""
    pass

@router.post("/", response_model=UserLicenseResponse)
async def assign_user_license(
    assignment_data: UserLicenseAssign,
    current_user: User = Depends(get_current_user)
):
    """分配用户许可证"""
    pass

@router.get("/{user_license_id}", response_model=UserLicenseDetail)
async def get_user_license_detail(
    user_license_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取用户许可证详情"""
    pass

@router.put("/{user_license_id}", response_model=UserLicenseResponse)
async def update_user_license(
    user_license_id: int,
    update_data: UserLicenseUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新用户许可证"""
    pass

@router.delete("/{user_license_id}")
async def revoke_user_license(
    user_license_id: int,
    current_user: User = Depends(get_current_user)
):
    """撤销用户许可证"""
    pass
```

## 9. 课程管理API

### 9.1 课程服务端点 (/courses)

```python
# 路由文件: backend/routes/course_routes.py

@router.get("/", response_model=List[CourseResponse])
async def get_courses(
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """获取课程列表"""
    pass

@router.post("/", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_current_user)
):
    """创建课程"""
    pass

@router.get("/{course_id}", response_model=CourseDetail)
async def get_course_detail(
    course_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取课程详情"""
    pass

@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    update_data: CourseUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新课程"""
    pass

@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user)
):
    """删除课程"""
    pass

@router.post("/{course_id}/enroll")
async def enroll_in_course(
    course_id: int,
    enrollment_data: CourseEnrollment,
    current_user: User = Depends(get_current_user)
):
    """报名课程"""
    pass
```

## 10. 多租户配置API

### 10.1 租户配置端点 (/tenant-config)

```python
# 路由文件: backend/routes/tenant_config_routes.py

@router.get("/{org_id}", response_model=TenantConfigResponse)
async def get_tenant_config(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取组织配置信息"""
    pass

@router.put("/{org_id}", response_model=TenantConfigResponse)
async def update_tenant_config(
    org_id: int,
    config_data: TenantConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新组织配置"""
    pass

@router.get("/{org_id}/resources", response_model=ResourceUsage)
async def get_resource_usage(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取资源使用情况"""
    pass

@router.post("/{org_id}/resources/check")
async def check_resource_availability(
    org_id: int,
    resource_check: ResourceCheck,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """检查资源可用性"""
    pass
```

## 11. 教育机构管理API

### 11.1 机构服务端点 (/educational-institutions)

```python
# 路由文件: backend/routes/educational_institution_routes.py

@router.get("/", response_model=List[InstitutionResponse])
async def get_institutions(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """获取教育机构列表"""
    pass

@router.post("/", response_model=InstitutionResponse)
async def create_institution(
    institution_data: InstitutionCreate,
    current_user: User = Depends(get_current_user)
):
    """创建教育机构"""
    pass

@router.get("/{institution_id}", response_model=InstitutionDetail)
async def get_institution_detail(
    institution_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取机构详情"""
    pass

@router.put("/{institution_id}", response_model=InstitutionResponse)
async def update_institution(
    institution_id: int,
    update_data: InstitutionUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新机构信息"""
    pass

@router.delete("/{institution_id}")
async def delete_institution(
    institution_id: int,
    current_user: User = Depends(get_current_user)
):
    """删除机构"""
    pass
```

## 12. API响应格式规范

### 12.1 成功响应格式

```python
# 标准成功响应模型
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# 列表响应模型
class ListResponse(BaseModel):
    success: bool = True
    data: List[Any]
    pagination: PaginationInfo
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PaginationInfo(BaseModel):
    total: int
    page: int
    size: int
    pages: int
```

### 12.2 错误响应格式

```python
# 标准错误响应模型
class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorInfo
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorInfo(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

# 常见错误码定义
ERROR_CODES = {
    "AUTH_001": "无效的认证令牌",
    "AUTH_002": "权限不足",
    "VALID_001": "请求参数验证失败",
    "DATA_001": "数据不存在",
    "DATA_002": "数据冲突",
    "SYS_001": "系统内部错误"
}
```

## 13. API安全性配置

### 13.1 认证装饰器

```python
# 权限检查装饰器
def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user or not current_user.has_permission(permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"缺少必要权限: {permission}"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@router.get("/sensitive-data")
@require_permission("VIEW_SENSITIVE_DATA")
async def get_sensitive_data(current_user: User = Depends(get_current_user)):
    pass
```

### 13.2 请求限流

```python
# 限流中间件
class RateLimitMiddleware:
    def __init__(self, app: ASGIApp, calls: int = 100, period: int = 60):
        self.app = app
        self.calls = calls
        self.period = period
        self.requests = {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client_ip = scope["client"][0]
        now = time.time()
        
        # 清理过期记录
        self.requests = {
            ip: calls for ip, calls in self.requests.items()
            if now - calls[0] < self.period
        }
        
        # 检查限流
        if client_ip in self.requests:
            last_request_time, count = self.requests[client_ip]
            if now - last_request_time < self.period and count >= self.calls:
                response = Response(
                    content=json.dumps({"error": "请求过于频繁"}),
                    status_code=429,
                    media_type="application/json"
                )
                await response(scope, receive, send)
                return
        
        # 记录请求
        self.requests[client_ip] = (now, self.requests.get(client_ip, (0, 0))[1] + 1)
        await self.app(scope, receive, send)
```

## 14. API文档和测试

### 14.1 自动生成文档

```python
# Swagger UI配置
app = FastAPI(
    title="iMatu API",
    description="iMatu教育平台API文档",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "认证",
            "description": "用户认证和授权相关接口"
        },
        {
            "name": "AI服务",
            "description": "AI代码生成和智能服务接口"
        }
    ]
)

# 自定义OpenAPI配置
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="iMatu API",
        version="1.0.0",
        description="教育平台API接口文档",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://your-domain.com/logo.png",
        "altText": "iMatu Logo"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### 14.2 API测试用例

```python
# Pytest测试示例
class TestAuthAPI:
    def test_login_success(self, client, test_user):
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": test_user.username,
                "password": "testpassword"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_protected_endpoint_without_auth(self, client):
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_invalid_token(self, client):
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
```

---
*API文档版本：v1.0 | 最后更新：2026年2月*