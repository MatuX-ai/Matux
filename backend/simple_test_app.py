#!/usr/bin/env python3
"""
简化测试应用
用于验证熔断器功能而不依赖完整应用
"""

import random
import time

from fastapi import FastAPI
import uvicorn

from middleware.circuit_breaker import CircuitBreakerConfig, CircuitBreakerMiddleware

app = FastAPI(title="熔断器测试应用", version="1.0.0")

# 配置熔断器
circuit_config = CircuitBreakerConfig(
    failure_threshold=3, timeout=10, half_open_attempts=2
)

app.add_middleware(CircuitBreakerMiddleware, config=circuit_config)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "circuit-breaker-test"}


@app.get("/test/success")
async def success_endpoint():
    """总是成功的端点"""
    return {"message": "success", "timestamp": time.time()}


@app.get("/test/faulty")
async def faulty_endpoint():
    """故障端点 - 70%概率失败"""
    if random.random() < 0.7:
        raise ConnectionError("Simulated connection failure")
    return {"message": "success", "timestamp": time.time()}


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus指标端点"""
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    from starlette.responses import Response

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    print("🚀 启动熔断器测试应用...")
    print("📝 访问 http://localhost:8000/docs 查看API文档")
    print("📊 访问 http://localhost:8000/metrics 查看指标")
    print("🔧 测试端点:")
    print("   - 成功端点: http://localhost:8000/test/success")
    print("   - 故障端点: http://localhost:8000/test/faulty")
    print("   - 健康检查: http://localhost:8000/health")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
