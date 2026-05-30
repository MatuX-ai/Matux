#!/usr/bin/env python3
"""
API 契约优化验证脚本
检查所有关键组件是否正确配置
"""

import json
import sys
from pathlib import Path

def check_openapi_spec():
    """检查 OpenAPI 规范文件"""
    print("📄 检查 OpenAPI 规范...")

    openapi_path = Path("sdk/imatu-sdk-ts/openapi.json")

    if not openapi_path.exists():
        print(f"❌ OpenAPI 规范文件不存在：{openapi_path}")
        return False

    try:
        with open(openapi_path, 'r', encoding='utf-8') as f:
            spec = json.load(f)

        # 基本验证
        required_fields = ['openapi', 'info', 'paths', 'servers', 'tags']
        missing_fields = [f for f in required_fields if f not in spec]

        if missing_fields:
            print(f"⚠️  缺少字段：{missing_fields}")
            return False

        # 检查版本
        version = spec['openapi']
        if not version.startswith('3.'):
            print(f"❌ 不支持的 OpenAPI 版本：{version}")
            return False

        # 检查服务器配置
        servers = spec['servers']
        if not servers or len(servers) < 1:
            print("❌ 未配置服务器")
            return False

        # 检查标签
        tags = spec['tags']
        if not tags or len(tags) < 1:
            print("⚠️  未配置标签")
            return False

        print(f"✅ OpenAPI {version}")
        print(f"   - 服务器数量：{len(servers)}")
        print(f"   - API 标签：{len(tags)}")
        print(f"   - API 路径：{len(spec.get('paths', {}))}")

        return True

    except Exception as e:
        print(f"❌ 读取失败：{e}")
        return False

def check_sdk_files():
    """检查 SDK 文件"""
    print("\n📦 检查 TypeScript SDK...")

    sdk_dir = Path("sdk/imatu-sdk-ts/src")

    required_files = [
        "client.ts",
        "types.ts",
        "config.ts",
        "generated/auth.ts",
        "generated/ai.ts",
        "generated/users.ts",
        "generated/courses.ts"
    ]

    all_exist = True
    for file in required_files:
        file_path = sdk_dir / file
        if not file_path.exists():
            print(f"❌ 缺失文件：{file}")
            all_exist = False
        else:
            print(f"✅ {file}")

    return all_exist

def check_frontend_services():
    """检查前端服务是否使用统一客户端"""
    print("\n🔧 检查前端服务...")

    services_to_check = [
        "src/app/admin/sponsorship-dashboard/sponsorship-dashboard.service.ts",
        "src/shared/services/creativity.service.ts",
        "src/app/admin/dashboard/services/dashboard.service.ts"
    ]

    all_good = True
    for service_file in services_to_check:
        service_path = Path(service_file)

        if not service_path.exists():
            print(f"⚠️  文件不存在：{service_file}")
            continue

        content = service_path.read_text(encoding='utf-8')

        # 检查是否包含硬编码 URL
        if "'http://localhost:8000'" in content or '"http://localhost:8000"' in content:
            print(f"❌ 仍包含硬编码 URL: {service_file}")
            all_good = False
        else:
            print(f"✅ {service_file}")

    return all_good

def check_environment_files():
    """检查环境配置文件"""
    print("\n⚙️  检查环境配置...")

    env_files = [
        "src/environments/environment.ts",
        "src/environments/environment.prod.ts"
    ]

    all_exist = True
    for env_file in env_files:
        env_path = Path(env_file)
        if not env_path.exists():
            print(f"⚠️  环境文件不存在：{env_file}")
            continue

        content = env_path.read_text(encoding='utf-8')
        if 'apiUrl' in content:
            print(f"✅ {env_file} (已配置 apiUrl)")
        else:
            print(f"⚠️  {env_file} (未找到 apiUrl 配置)")

    return all_exist

def check_documentation():
    """检查文档"""
    print("\n📚 检查文档...")

    docs = [
        "docs/API_CONTRACT_OPTIMIZATION_REPORT.md",
        "docs/API_CONTRACT_USAGE_GUIDE.md",
        "docs/BACKEND_API_MAPPING.md",
        "docs/API_DESIGN_SPECIFICATION.md"
    ]

    all_exist = True
    for doc in docs:
        doc_path = Path(doc)
        if doc_path.exists():
            print(f"✅ {doc}")
        else:
            print(f"❌ 文档不存在：{doc}")
            all_exist = False

    return all_exist

def main():
    """主函数"""
    print("=" * 60)
    print("API 契约优化验证工具")
    print("=" * 60)

    results = []

    # 执行各项检查
    results.append(("OpenAPI 规范", check_openapi_spec()))
    results.append(("TypeScript SDK", check_sdk_files()))
    results.append(("前端服务", check_frontend_services()))
    results.append(("环境配置", check_environment_files()))
    results.append(("技术文档", check_documentation()))

    # 汇总结果
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计：{passed}/{total} 项检查通过")

    if passed == total:
        print("\n🎉 所有检查通过！API 契约优化完成！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 项检查未通过，请检查上述输出。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
