"""
熔断器集成使用示例
展示如何在实际项目中应用 Sentinel 熔断器保护第三方服务调用
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from backend.middleware.circuit_breaker import (
    circuit_breaker,
    CircuitBreakerManager,
    CircuitBreakerConfig,
    default_fallback_response,
    cached_response_fallback
)
from backend.database import get_db
from backend.core.security import get_current_user
from backend.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# 示例 1: OpenAI API 调用保护
# ============================================

async def openai_fallback(prompt: str, **kwargs):
    """OpenAI API 降级函数"""
    logger.warning(f"OpenAI API 不可用，返回降级响应")
    return {
        "fallback": True,
        "message": "AI 服务暂时不可用，已保存您的请求，稍后将处理",
        "queued": True,
        "prompt": prompt
    }


@circuit_breaker(
    name="OpenAI_API",
    failure_threshold=3,      # 失败 3 次后打开熔断器
    timeout=60.0,            # 60 秒后尝试恢复
    fallback=openai_fallback
)
async def call_openai_api(prompt: str, model: str = "gpt-4"):
    """
    调用 OpenAI API（受熔断器保护）

    如果连续失败 3 次，熔断器会打开，后续请求直接返回降级响应
    60 秒后，熔断器进入半开状态，允许少量请求测试
    """
    # 模拟 API 调用（实际项目中替换为真实调用）
    # import openai
    # response = await openai.ChatCompletion.create(
    #     model=model,
    #     messages=[{"role": "user", "content": prompt}]
    # )

    # 模拟可能的失败
    import random
    if random.random() < 0.3:  # 30% 概率失败
        raise Exception("OpenAI API connection timeout")

    return {
        "response": f"AI response to: {prompt}",
        "model": model
    }


@router.post("/ai/chat")
async def ai_chat(
    prompt: str,
    model: str = "gpt-4",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI 聊天接口（使用熔断器保护）

    当 OpenAI API 不可用时，自动降级返回友好提示
    """
    try:
        result = await call_openai_api(prompt, model)

        if result.get("fallback"):
            # 降级响应
            return {
                "success": False,
                "warning": result["message"],
                "data": result
            }
        else:
            # 正常响应
            return {
                "success": True,
                "data": result
            }

    except Exception as e:
        logger.error(f"AI 聊天失败：{str(e)}")
        raise HTTPException(status_code=503, detail=str(e))


# ============================================
# 示例 2: 支付接口保护
# ============================================

async def payment_fallback(order_id: str, amount: float, **kwargs):
    """支付接口降级函数"""
    logger.warning(f"支付接口不可用，订单 {order_id} 延迟处理")
    return {
        "fallback": True,
        "status": "pending",
        "message": "支付系统繁忙，订单已排队，将在 30 分钟内处理",
        "order_id": order_id,
        "retry_eta_minutes": 30
    }


@circuit_breaker(
    name="Payment_Gateway",
    failure_threshold=5,
    timeout=120.0,           # 支付系统恢复时间较长
    fallback=payment_fallback
)
async def process_payment(order_id: str, amount: float, user_id: str):
    """
    处理支付（受熔断器保护）

    连续失败 5 次后打开熔断器，避免雪崩效应
    """
    # 模拟支付网关调用
    # payment_result = await stripe.PaymentIntent.create(...)

    import random
    if random.random() < 0.2:  # 20% 概率失败
        raise Exception("Payment gateway timeout")

    return {
        "success": True,
        "transaction_id": f"txn_{order_id}",
        "amount": amount
    }


@router.post("/payment/charge")
async def charge_payment(
    order_id: str,
    amount: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    支付扣款接口（使用熔断器保护）
    """
    result = await process_payment(order_id, amount, current_user.id)

    if result.get("fallback"):
        return {"warning": result["message"], "order": result}
    else:
        return {"success": "支付成功", "transaction": result}


# ============================================
# 示例 3: 数据库连接保护
# ============================================

async def database_fallback(query_type: str, **kwargs):
    """数据库操作降级函数"""
    logger.warning(f"数据库连接不可用，{query_type} 操作降级处理")
    return {
        "fallback": True,
        "status": "queued",
        "message": "数据库繁忙，操作已加入队列",
        "query_type": query_type
    }


@circuit_breaker(
    name="Database_Primary",
    failure_threshold=10,     # 数据库容忍度更高
    timeout=30.0,
    fallback=database_fallback
)
async def execute_database_query(query: str, params: dict):
    """
    执行数据库查询（受熔断器保护）
    """
    # 实际项目中使用真实的数据库连接池
    # from backend.database import get_connection
    # conn = await get_connection()
    # result = await conn.execute(query, params)

    return {"result": "query executed", "query": query}


# ============================================
# 示例 4: 外部 API 调用（通用）
# ============================================

async def external_api_fallback(url: str, **kwargs):
    """外部 API 降级函数 - 使用缓存"""
    # 尝试从 Redis 获取缓存数据
    cache_key = f"cache:{url}"
    cached_data = await cached_response_fallback(cache_key)

    if cached_data:
        logger.info(f"从缓存获取数据：{cache_key}")
        return cached_data

    logger.warning(f"外部 API 不可用且无缓存：{url}")
    return default_fallback_response()


@circuit_breaker(
    name="External_Weather_API",
    failure_threshold=3,
    timeout=60.0,
    fallback=external_api_fallback
)
async def fetch_weather_data(city: str):
    """
    获取天气数据（受熔断器保护）
    """
    # 调用外部天气 API
    # async with aiohttp.ClientSession() as session:
    #     async with session.get(f"https://api.weather.com/{city}") as resp:
    #         return await resp.json()

    return {"city": city, "temperature": 25, "condition": "sunny"}


@router.get("/weather/{city}")
async def get_weather(
    city: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取城市天气（使用熔断器保护）
    """
    weather_data = await fetch_weather_data(city)

    if weather_data.get("fallback"):
        return {"warning": "天气服务暂时不可用", "data": weather_data}
    else:
        return weather_data


# ============================================
# 示例 5: 短信发送服务保护
# ============================================

async def sms_fallback(phone_number: str, message: str, **kwargs):
    """短信发送降级函数"""
    logger.warning(f"短信服务不可用，消息已记录：{phone_number}")
    return {
        "fallback": True,
        "status": "queued",
        "message": "短信系统繁忙，消息已加入发送队列",
        "phone_number": phone_number,
        "estimated_delay_seconds": 60
    }


@circuit_breaker(
    name="SMS_Service",
    failure_threshold=5,
    timeout=60.0,
    fallback=sms_fallback
)
async def send_sms(phone_number: str, message: str):
    """
    发送短信（受熔断器保护）
    """
    # 调用短信服务商 API
    # result = await twilio_client.messages.create(...)

    return {
        "success": True,
        "message_id": f"sms_{int(time.time())}",
        "phone_number": phone_number
    }


@router.post("/sms/send")
async def send_sms_endpoint(
    phone_number: str,
    message: str,
    current_user: User = Depends(get_current_user)
):
    """
    发送短信接口（使用熔断器保护）
    """
    result = await send_sms(phone_number, message)

    if result.get("fallback"):
        return {"warning": result["message"], "data": result}
    else:
        return {"success": "短信发送成功", "data": result}


# ============================================
# 示例 6: 文件上传到云存储
# ============================================

async def cloud_storage_fallback(file_name: str, file_size: int, **kwargs):
    """云存储上传降级函数"""
    logger.warning(f"云存储不可用，文件 {file_name} 暂存本地")
    return {
        "fallback": True,
        "status": "local_storage",
        "message": "云存储繁忙，文件暂存本地服务器，稍后将同步",
        "file_name": file_name,
        "sync_later": True
    }


@circuit_breaker(
    name="Cloud_Storage_S3",
    failure_threshold=5,
    timeout=90.0,
    fallback=cloud_storage_fallback
)
async def upload_to_s3(file_name: str, file_content: bytes, bucket: str):
    """
    上传文件到 S3（受熔断器保护）
    """
    # import boto3
    # s3 = boto3.client('s3')
    # s3.put_object(Bucket=bucket, Key=file_name, Body=file_content)

    return {
        "success": True,
        "url": f"https://s3.amazonaws.com/{bucket}/{file_name}",
        "file_name": file_name
    }


@router.post("/upload/s3")
async def upload_to_s3_endpoint(
    file_name: str,
    file_size: int,
    bucket: str = "default",
    current_user: User = Depends(get_current_user)
):
    """
    上传文件到 S3（使用熔断器保护）
    """
    result = await upload_to_s3(file_name, b"file_content", bucket)

    if result.get("fallback"):
        return {"warning": result["message"], "data": result}
    else:
        return {"success": "上传成功", "data": result}


# ============================================
# 监控和管理端点
# ============================================

@router.get("/circuit-breaker/status")
async def get_circuit_breaker_status():
    """
    获取所有熔断器的状态

    用于监控和调试
    """
    manager = CircuitBreakerManager.get_instance()
    stats = manager.get_all_stats()

    return {
        "total_breakers": len(stats),
        "breakers": stats
    }


@router.post("/circuit-breaker/reset")
async def reset_circuit_breakers(breaker_name: Optional[str] = None):
    """
    重置熔断器

    Args:
        breaker_name: 指定熔断器名称，如果不提供则重置所有
    """
    manager = CircuitBreakerManager.get_instance()

    if breaker_name:
        if breaker_name in manager.get_all_breakers():
            breaker = manager.get_breaker(breaker_name)
            breaker._reset_state()
            return {"message": f"熔断器 {breaker_name} 已重置"}
        else:
            raise HTTPException(
                status_code=404, detail=f"熔断器 {breaker_name} 不存在")
    else:
        manager.reset_all()
        return {"message": "所有熔断器已重置"}


# ============================================
# 自定义配置示例
# ============================================

# 创建自定义配置的熔断器
custom_config = CircuitBreakerConfig(
    failure_threshold=10,       # 允许失败 10 次
    success_threshold=5,        # 需要成功 5 次才能恢复
    timeout=180.0,             # 3 分钟后尝试恢复
    half_open_max_calls=5,     # 半开状态允许 5 个测试请求
)

custom_breaker_manager = CircuitBreakerManager.get_instance()
custom_breaker = custom_breaker_manager.get_breaker(
    "Custom_Service",
    config=custom_config
)


@router.post("/custom-service/call")
async def call_custom_service(data: dict):
    """
    使用自定义配置的熔断器调用服务
    """
    async def custom_service_call():
        # 业务逻辑
        return {"result": "success"}

    result = await custom_breaker.call(custom_service_call)
    return result


# ============================================
# 批量调用示例
# ============================================

@router.post("/batch/process")
async def batch_process(items: List[dict]):
    """
    批量处理（每个子调用都受熔断器保护）
    """
    results = []

    for item in items:
        try:
            # 每个调用都有独立的熔断器保护
            result = await call_openai_api(item.get("prompt", ""))
            results.append(result)
        except Exception as e:
            results.append({"error": str(e), "item": item})

    return {
        "total": len(items),
        "success": sum(1 for r in results if not r.get("error")),
        "failed": sum(1 for r in results if r.get("error")),
        "results": results
    }
