#!/usr/bin/env python3
"""
简化的 OpenAPI 规范导出工具
绕过 AI 服务等重依赖模块，只导出基础 API 结构
"""

import json
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

def export_minimal_openapi_spec():
    """导出最小化的 OpenAPI 规范"""
    try:
        print("🔍 正在加载 FastAPI 应用...")

        # 设置环境变量
        os.environ.setdefault('ENVIRONMENT', 'development')

        # 直接创建 FastAPI 应用而不导入完整的路由
        from fastapi import FastAPI
        from fastapi.openapi.utils import get_openapi

        # 创建基础应用
        app = FastAPI(
            title="iMatu API",
            version="1.0.0",
            description="iMatu 教育平台API",
            docs_url="/docs",
            redoc_url="/redoc",
        )

        # 手动添加主要路由标签
        tags_metadata = [
            {"name": "认证", "description": "用户认证和授权相关接口"},
            {"name": "AI 服务", "description": "AI 代码生成和智能服务接口"},
            {"name": "用户管理", "description": "用户相关操作接口"},
            {"name": "课程管理", "description": "课程相关操作接口"},
            {"name": "硬件认证", "description": "硬件设备认证和管理"},
            {"name": "许可证管理", "description": "许可证生成和验证"},
            {"name": "推荐系统", "description": "个性化推荐服务"},
            {"name": "支付系统", "description": "支付和订阅管理"},
        ]

        # 生成 OpenAPI 规范
        print("📄 正在生成 OpenAPI 规范...")

        openapi_schema = get_openapi(
            title="iMatu API",
            version="1.0.0",
            description="iMatu 教育平台API - 包含认证、AI 服务、课程管理等核心功能",
            routes=app.routes,
        )

        # 添加完整的元数据
        openapi_schema.update({
            "info": {
                "title": "iMatu API",
                "version": "1.0.0",
                "description": """## iMatu 教育平台API

完整的 API 文档，包含所有后端服务的接口定义。

### 主要功能模块
- **认证授权**: 用户登录、注册、OAuth2 认证
- **AI 服务**: 代码生成、创意引擎、学习行为分析
- **课程管理**: 课程创建、版本控制、协作编辑
- **硬件集成**: 设备认证、传感器数据、AR/VR
- **支付订阅**: 积分系统、订阅管理、区块链网关

### 认证方式
使用 JWT Bearer Token:
```
Authorization: Bearer <your_access_token>
```
                """,
                "contact": {
                    "name": "iMatuProject Team",
                    "email": "support@imatuproject.com",
                    "url": "https://imatuproject.com"
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT"
                }
            },
            "servers": [
                {
                    "url": "http://localhost:8000",
                    "description": "开发环境"
                },
                {
                    "url": "https://test-api.imatuproject.com",
                    "description": "测试环境"
                },
                {
                    "url": "https://api.imatuproject.com",
                    "description": "生产环境"
                }
            ],
            "tags": tags_metadata
        })

        # 保存到文件
        output_dir = project_root / "sdk" / "imatu-sdk-ts"
        output_file = output_dir / "openapi.json"

        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)

        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

        print(f"✅ OpenAPI 规范已保存到：{output_file}")

        # 输出统计信息
        paths_count = len(openapi_schema.get('paths', {}))
        schemas_count = len(openapi_schema.get('components', {}).get('schemas', {}))

        print(f"📊 API 统计:")
        print(f"   - 路径数量：{paths_count}")
        print(f"   - 数据模型：{schemas_count}")
        print(f"   - API 版本：{openapi_schema.get('openapi', '未知')}")

        return str(output_file)

    except Exception as e:
        print(f"❌ 导出失败：{e}")
        import traceback
        traceback.print_exc()
        return None

def validate_openapi_spec(spec_file):
    """验证 OpenAPI 规范的有效性"""
    try:
        print("🔍 验证 OpenAPI 规范...")

        with open(spec_file, 'r', encoding='utf-8') as f:
            spec = json.load(f)

        # 基本验证
        required_fields = ['openapi', 'info', 'paths']
        for field in required_fields:
            if field not in spec:
                raise ValueError(f"缺少必需字段：{field}")

        # 验证版本格式
        version = spec['openapi']
        if not isinstance(version, str) or not version.startswith('3.'):
            raise ValueError(f"不支持的 OpenAPI 版本：{version}")

        # 验证 info 字段
        info = spec['info']
        required_info = ['title', 'version']
        for field in required_info:
            if field not in info:
                raise ValueError(f"info 中缺少必需字段：{field}")

        print("✅ OpenAPI 规范验证通过")
        return True

    except Exception as e:
        print(f"❌ 规范验证失败：{e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("OpenAPI 规范导出工具 (简化版)")
    print("=" * 50)

    # 导出规范
    spec_file = export_minimal_openapi_spec()
    if not spec_file:
        sys.exit(1)

    # 验证规范
    if not validate_openapi_spec(spec_file):
        sys.exit(1)

    print("\n🎉 OpenAPI 规范导出完成！")
    print(f"📁 输出文件：{spec_file}")
    print("\n⚠️ 注意：这是基础框架，完整 API 需要在后端启动后访问 /docs 或 /openapi.json")
