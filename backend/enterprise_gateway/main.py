"""
企业API网关主应用
提供OAuth2.0企业认证、设备白名单管理和API访问控制服务
"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from config.enterprise_settings import enterprise_settings
from middleware.enterprise_auth_middleware import EnterpriseAuthMiddleware
from routes import device_management_routes, enterprise_auth_routes, monitoring_routes
from utils.logger import setup_enterprise_logger


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=enterprise_settings.APP_NAME,
        version=enterprise_settings.APP_VERSION,
        description="""
        ## iMato企业API网关服务

        为企业客户提供安全、可靠、可监控的API访问服务。

        ### 主要特性
        - OAuth2.0企业级认证
        - 设备白名单访问控制
        - API调用配额管理
        - 详细的访问日志记录
        - 实时监控和告警

        ### 认证方式
        使用OAuth2.0 Client Credentials流程：
        1. 获取访问令牌: `POST /api/enterprise/oauth/token`
        2. 在请求头中包含: `Authorization: Bearer {access_token}`
        3. 可选设备标识: `X-Device-ID: {device_identifier}`

        ### 安全措施
        - 客户端凭据验证
        - 设备白名单控制
        - API调用配额限制
        - 详细的访问审计
        """,
        routes=app.routes,
    )

    # 添加企业API特有的安全方案
    openapi_schema["components"]["securitySchemes"] = {
        "EnterpriseOAuth2": {
            "type": "oauth2",
            "flows": {
                "clientCredentials": {
                    "tokenUrl": "/api/enterprise/oauth/token",
                    "scopes": {
                        "api:read": "读取API数据",
                        "api:write": "写入API数据",
                        "api:admin": "管理API配置",
                    },
                }
            },
        }
    }

    # 为所有需要认证的端点添加安全要求
    for path, path_item in openapi_schema["paths"].items():
        for method, operation in path_item.items():
            # 排除公开端点
            if (
                path not in ["/", "/health", "/docs", "/redoc", "/openapi.json"]
                and "/oauth/token" not in path
            ):
                operation["security"] = [{"EnterpriseOAuth2": ["api:read"]}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# 创建FastAPI应用实例
app = FastAPI(
    title=enterprise_settings.APP_NAME,
    version=enterprise_settings.APP_VERSION,
    description="为企业客户提供安全、可靠的API访问服务",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "企业认证", "description": "OAuth2.0企业认证相关接口"},
        {"name": "设备管理", "description": "设备白名单管理接口"},
        {"name": "API监控", "description": "企业API使用情况监控"},
    ],
)

# 配置自定义OpenAPI
app.openapi = custom_openapi

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=enterprise_settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置企业认证中间件
app.add_middleware(EnterpriseAuthMiddleware)

# 配置日志
logger = setup_enterprise_logger(
    enterprise_settings.LOG_LEVEL, enterprise_settings.LOG_FILE
)

# 包含路由
app.include_router(
    enterprise_auth_routes.router, prefix="/api/enterprise", tags=["企业认证"]
)
app.include_router(
    device_management_routes.router, prefix="/api/enterprise", tags=["设备管理"]
)
app.include_router(monitoring_routes.router, prefix="/api/enterprise", tags=["API监控"])


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(
        f"Starting {enterprise_settings.APP_NAME} v{enterprise_settings.APP_VERSION}"
    )
    logger.info("Enterprise API Gateway initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info(f"Shutting down {enterprise_settings.APP_NAME}")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理器"""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """请求验证异常处理器"""
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "message": f"Welcome to {enterprise_settings.APP_NAME}",
        "version": enterprise_settings.APP_VERSION,
        "status": "healthy",
        "features": ["OAuth2.0企业认证", "设备白名单管理", "API访问控制", "使用监控"],
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": enterprise_settings.APP_NAME,
        "version": enterprise_settings.APP_VERSION,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=enterprise_settings.HOST,
        port=enterprise_settings.PORT,
        reload=enterprise_settings.DEBUG,
        log_level=enterprise_settings.LOG_LEVEL.lower(),
    )
