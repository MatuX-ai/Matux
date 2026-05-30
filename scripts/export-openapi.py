#!/usr/bin/env python3
"""
OpenAPI规范导出工具
从FastAPI应用中提取完整的OpenAPI JSON规范
"""

import json
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def export_openapi_spec():
    """导出OpenAPI规范"""
    try:
        print("🔍 正在加载FastAPI应用...")
        
        # 设置环境变量
        os.environ.setdefault('ENVIRONMENT', 'development')
        
        # 动态导入FastAPI应用
        import importlib.util
        
        # 尝试不同的导入路径
        backend_main_path = project_root / "backend" / "main.py"
        
        if not backend_main_path.exists():
            raise FileNotFoundError(f"找不到后端主文件: {backend_main_path}")
        
        # 添加backend目录到Python路径
        backend_path = str(project_root / "backend")
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
            
        # 使用importlib加载模块
        spec = importlib.util.spec_from_file_location("backend_main", backend_main_path)
        backend_main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(backend_main)
        
        # 获取FastAPI应用实例
        app = getattr(backend_main, 'app', None)
        if app is None:
            raise AttributeError("在main.py中找不到'app'实例")
            
        print("✅ 成功加载FastAPI应用")
        
        # 生成OpenAPI规范
        print("📄 正在生成OpenAPI规范...")
        
        from fastapi.openapi.utils import get_openapi
        
        openapi_schema = get_openapi(
            title=app.title or "iMatu API",
            version=app.version or "1.0.0",
            description=app.description or "iMatu教育平台API",
            routes=app.routes,
        )
        
        # 添加额外的元数据
        openapi_schema.update({
            "info": {
                "title": app.title or "iMatu API",
                "version": app.version or "1.0.0",
                "description": app.description or "iMatu教育平台API",
                "contact": {
                    "name": "iMatuProject Team",
                    "email": "support@imatuproject.com"
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
                    "url": "https://api.imatuproject.com",
                    "description": "生产环境"
                }
            ],
            "tags": [
                {
                    "name": "认证",
                    "description": "用户认证和授权相关接口"
                },
                {
                    "name": "AI服务",
                    "description": "AI代码生成和智能服务接口"
                },
                {
                    "name": "课程管理",
                    "description": "课程相关操作接口"
                },
                {
                    "name": "用户管理",
                    "description": "用户相关操作接口"
                }
            ]
        })
        
        # 保存到文件
        output_dir = project_root / "sdk" / "imatu-sdk-ts"
        output_file = output_dir / "openapi.json"
        
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
            
        print(f"✅ OpenAPI规范已保存到: {output_file}")
        
        # 输出统计信息
        paths_count = len(openapi_schema.get('paths', {}))
        schemas_count = len(openapi_schema.get('components', {}).get('schemas', {}))
        
        print(f"📊 API统计:")
        print(f"   - 路径数量: {paths_count}")
        print(f"   - 数据模型: {schemas_count}")
        print(f"   - API版本: {openapi_schema.get('openapi', '未知')}")
        
        return str(output_file)
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装所有必要的依赖包")
        return None
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def validate_openapi_spec(spec_file):
    """验证OpenAPI规范的有效性"""
    try:
        print("🔍 验证OpenAPI规范...")
        
        with open(spec_file, 'r', encoding='utf-8') as f:
            spec = json.load(f)
            
        # 基本验证
        required_fields = ['openapi', 'info', 'paths']
        for field in required_fields:
            if field not in spec:
                raise ValueError(f"缺少必需字段: {field}")
                
        # 验证版本格式
        version = spec['openapi']
        if not isinstance(version, str) or not version.startswith('3.'):
            raise ValueError(f"不支持的OpenAPI版本: {version}")
            
        # 验证info字段
        info = spec['info']
        required_info = ['title', 'version']
        for field in required_info:
            if field not in info:
                raise ValueError(f"info中缺少必需字段: {field}")
                
        print("✅ OpenAPI规范验证通过")
        return True
        
    except Exception as e:
        print(f"❌ 规范验证失败: {e}")
        return False

def optimize_openapi_spec(spec_file):
    """优化OpenAPI规范"""
    try:
        print("🔧 优化OpenAPI规范...")
        
        with open(spec_file, 'r', encoding='utf-8') as f:
            spec = json.load(f)
            
        # 移除不必要的字段
        if 'components' in spec and 'schemas' in spec['components']:
            schemas = spec['components']['schemas']
            # 移除空的schemas
            spec['components']['schemas'] = {
                name: schema for name, schema in schemas.items() 
                if schema and isinstance(schema, dict)
            }
            
        # 优化paths描述
        if 'paths' in spec:
            for path, methods in spec['paths'].items():
                for method, operation in methods.items():
                    # 确保有操作摘要
                    if 'summary' not in operation and 'description' in operation:
                        operation['summary'] = operation['description'][:50] + '...' if len(operation['description']) > 50 else operation['description']
                        
        # 重新保存优化后的规范
        with open(spec_file, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
            
        print("✅ OpenAPI规范优化完成")
        return True
        
    except Exception as e:
        print(f"❌ 规范优化失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("OpenAPI规范导出工具")
    print("=" * 50)
    
    # 导出规范
    spec_file = export_openapi_spec()
    if not spec_file:
        sys.exit(1)
        
    # 验证规范
    if not validate_openapi_spec(spec_file):
        sys.exit(1)
        
    # 优化规范
    optimize_openapi_spec(spec_file)
    
    print("\n🎉 OpenAPI规范导出和优化完成！")
    print(f"📁 输出文件: {spec_file}")

if __name__ == "__main__":
    main()