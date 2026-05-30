"""
许可证管理系统完整功能演示
展示系统核心功能，无需外部依赖
"""

from datetime import datetime, timedelta
import hashlib
import secrets
import string
import sys


# 模拟数据库存储
class MockDatabase:
    def __init__(self):
        self.organizations = {}
        self.licenses = {}
        self.next_org_id = 1
        self.next_license_id = 1

    def create_organization(self, data):
        org_id = self.next_org_id
        self.next_org_id += 1

        org = {
            "id": org_id,
            "name": data["name"],
            "contact_email": data["contact_email"],
            "phone": data.get("phone", ""),
            "address": data.get("address", ""),
            "website": data.get("website", ""),
            "license_count": 0,
            "max_users": data.get("max_users", 100),
            "current_users": 0,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        self.organizations[org_id] = org
        return org

    def get_organization(self, org_id):
        return self.organizations.get(org_id)

    def create_license(self, data):
        license_id = self.next_license_id
        self.next_license_id += 1

        # 生成许可证密钥
        prefix = "LICENSE"
        key_length = 32
        characters = string.ascii_uppercase + string.digits
        random_part = "".join(secrets.choice(characters) for _ in range(key_length))
        checksum = hashlib.md5(random_part.encode()).hexdigest()[:4].upper()
        license_key = f"{prefix}-{random_part}-{checksum}"

        # 计算过期时间
        expires_at = datetime.utcnow() + timedelta(days=data.get("duration_days", 365))

        license = {
            "id": license_id,
            "license_key": license_key,
            "organization_id": data["organization_id"],
            "product_id": data.get("product_id"),
            "license_type": data.get("license_type", "commercial"),
            "status": "active",
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "activated_at": None,
            "max_users": data.get("max_users", 1),
            "max_devices": data.get("max_devices", 1),
            "current_users": 0,
            "current_devices": 0,
            "features": data.get("features", []),
            "restrictions": {},
            "metadata": {},
            "notes": data.get("notes", ""),
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        self.licenses[license_id] = license

        # 更新组织许可证计数
        org = self.organizations.get(data["organization_id"])
        if org:
            org["license_count"] += 1

        return license

    def get_license(self, license_key):
        for license_data in self.licenses.values():
            if license_data["license_key"] == license_key:
                return license_data
        return None

    def get_organization_licenses(self, org_id):
        return [
            license_data
            for license_data in self.licenses.values()
            if license_data["organization_id"] == org_id
        ]


# 许可证服务类
class LicenseDemoService:
    def __init__(self):
        self.db = MockDatabase()

    def create_organization(self, org_data):
        """创建组织"""
        return self.db.create_organization(org_data)

    def create_license(self, license_data):
        """创建许可证"""
        return self.db.create_license(license_data)

    def validate_license(self, license_key):
        """验证许可证"""
        license_data = self.db.get_license(license_key)

        if not license_data:
            return {"valid": False, "error": "许可证不存在"}

        # 检查状态
        if license_data["status"] != "active":
            return {
                "valid": False,
                "error": f"许可证状态无效: {license_data['status']}",
            }

        # 检查是否过期
        expires_at = datetime.fromisoformat(license_data["expires_at"])
        if datetime.utcnow() > expires_at:
            license_data["status"] = "expired"
            return {"valid": False, "error": "许可证已过期"}

        # 检查是否被禁用
        if not license_data["is_active"]:
            return {"valid": False, "error": "许可证已被禁用"}

        return {"valid": True, "license_info": license_data}

    def get_organization_licenses(self, org_id):
        """获取组织许可证"""
        return self.db.get_organization_licenses(org_id)


def demonstrate_system():
    """演示系统功能"""
    print("=" * 60)
    print("🚀 许可证管理系统功能演示")
    print("=" * 60)

    service = LicenseDemoService()

    # 1. 创建组织
    print("\n📋 1. 创建教育机构组织")
    org_data = {
        "name": "北京示范小学",
        "contact_email": "admin@beijing-school.edu.cn",
        "phone": "010-12345678",
        "address": "北京市海淀区中关村大街1号",
        "website": "https://www.beijing-school.edu.cn",
        "max_users": 500,
    }

    organization = service.create_organization(org_data)
    print(f"✅ 组织创建成功:")
    print(f"   ID: {organization['id']}")
    print(f"   名称: {organization['name']}")
    print(f"   邮箱: {organization['contact_email']}")

    # 2. 生成许可证
    print("\n🔑 2. 为组织生成教育版许可证")
    license_data = {
        "organization_id": organization["id"],
        "license_type": "education",
        "duration_days": 365,
        "max_users": 300,
        "max_devices": 150,
        "features": ["basic_access", "advanced_features", "api_access", "reporting"],
        "notes": "2026学年教育许可证",
    }

    license_obj = service.create_license(license_data)
    print(f"✅ 许可证生成成功:")
    print(f"   许可证密钥: {license_obj['license_key']}")
    print(f"   类型: {license_obj['license_type']}")
    print(f"   有效期至: {license_obj['expires_at'][:10]}")
    print(f"   最大用户数: {license_obj['max_users']}")
    print(f"   功能特性: {', '.join(license_obj['features'])}")

    # 3. 验证许可证
    print("\n✅ 3. 验证许可证有效性")
    validation_result = service.validate_license(license_obj["license_key"])
    if validation_result["valid"]:
        info = validation_result["license_info"]
        print(f"✅ 许可证验证通过:")
        print(f"   状态: {info['status']}")
        print(
            f"   剩余天数: {(datetime.fromisoformat(info['expires_at']) - datetime.utcnow()).days} 天"
        )
        print(f"   当前用户数: {info['current_users']}/{info['max_users']}")
    else:
        print(f"❌ 许可证验证失败: {validation_result['error']}")

    # 4. 创建第二个组织和许可证
    print("\n📋 4. 创建商业公司组织")
    company_org = service.create_organization(
        {
            "name": "科技创新有限公司",
            "contact_email": "contact@tech-company.com",
            "max_users": 100,
        }
    )

    company_license = service.create_license(
        {
            "organization_id": company_org["id"],
            "license_type": "commercial",
            "duration_days": 180,
            "max_users": 50,
            "features": ["basic_access", "api_access"],
        }
    )

    print(f"✅ 商业许可证生成: {company_license['license_key']}")

    # 5. 展示组织的所有许可证
    print("\n📚 5. 组织许可证列表")
    org_licenses = service.get_organization_licenses(organization["id"])
    print(f"   {organization['name']} 拥有 {len(org_licenses)} 个许可证:")
    for lic in org_licenses:
        status_icon = "✅" if lic["status"] == "active" else "⚠️"
        print(f"   {status_icon} {lic['license_key'][:20]}... ({lic['license_type']})")

    # 6. 测试无效许可证
    print("\n🧪 6. 测试无效许可证")
    invalid_result = service.validate_license("LICENSE-INVALID-KEY-1234")
    print(
        f"   无效许可证验证: {'✅ 通过' if invalid_result['valid'] else '❌ 失败 - ' + invalid_result['error']}"
    )

    # 7. 系统统计
    print("\n📈 7. 系统统计信息")
    total_orgs = len(service.db.organizations)
    total_licenses = len(service.db.licenses)
    active_licenses = len(
        [l for l in service.db.licenses.values() if l["status"] == "active"]
    )

    print(f"   总组织数: {total_orgs}")
    print(f"   总许可证数: {total_licenses}")
    print(f"   活跃许可证: {active_licenses}")

    print("\n" + "=" * 60)
    print("🎉 演示完成！系统核心功能正常工作。")
    print("=" * 60)

    return True


def show_api_examples():
    """显示API使用示例"""
    print("\n📖 API使用示例:")
    print("\n1. 创建组织:")
    print("""   POST /api/v1/organizations
   {
     "name": "我的学校",
     "contact_email": "admin@school.com",
     "max_users": 200
   }""")

    print("\n2. 生成许可证:")
    print("""   POST /api/v1/licenses
   {
     "organization_id": 1,
     "license_type": "education",
     "duration_days": 365,
     "max_users": 100,
     "features": ["basic_access", "api_access"]
   }""")

    print("\n3. 验证许可证:")
    print("""   POST /api/v1/licenses/LICENSE-KEY-HERE/validate
   Headers: X-License-Key: YOUR_LICENSE_KEY""")

    print("\n4. 获取统计信息:")
    print("   GET /api/v1/statistics")


if __name__ == "__main__":
    try:
        success = demonstrate_system()
        show_api_examples()

        if success:
            print("\n💡 系统已准备好进行实际部署和使用！")
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
