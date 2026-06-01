#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试路径匹配逻辑
"""

def should_exclude(path: str, exclude_paths: list) -> bool:
    """检查路径是否应该排除验证"""
    return any(
        path == exclude_path or path.startswith(exclude_path)
        for exclude_path in exclude_paths
    )

# 测试路径
test_path = "/api/v1/local-knowledge-graph/health"
exclude_paths = [
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
    "/api/v1/health",
    "/api/v1/auth/token",
    "/api/v1/auth/register",
    "/api/v1/finance",
    "/api/v1/local-knowledge-graph",
]

result = should_exclude(test_path, exclude_paths)
print(f"测试路径: {test_path}")
print(f"排除路径: {exclude_paths}")
print(f"是否排除: {result}")

# 逐个测试
for exclude in exclude_paths:
    match = test_path == exclude or test_path.startswith(exclude)
    print(f"  {exclude}: {match}")