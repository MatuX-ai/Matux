"""
数据库初始化脚本
创建所有必要的表结构
"""

import os

from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    text,
)
from sqlalchemy.sql import func

# 加载环境变量
load_dotenv()


def create_basic_tables():
    """创建基础表结构"""

    database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    engine = create_engine(database_url)
    metadata = MetaData()

    # 创建users表
    users = Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("username", String(50), unique=True, index=True, nullable=False),
        Column("email", String(100), unique=True, index=True, nullable=False),
        Column("hashed_password", String(100), nullable=False),
        Column("role", String(20), default="user"),  # 新增role字段
        Column("is_active", Boolean, default=True),
        Column("is_superuser", Boolean, default=False),
        Column("created_at", DateTime, default=func.now()),
        Column("updated_at", DateTime, default=func.now(), onupdate=func.now()),
    )

    # 创建licenses表
    licenses = Table(
        "licenses",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("license_key", String(255), unique=True, index=True, nullable=False),
        Column("organization_id", Integer),  # 简化外键关系
        Column("license_type", String(20), default="commercial"),
        Column("status", String(20), default="pending"),
        Column("issued_at", DateTime, default=func.now()),
        Column("expires_at", DateTime, nullable=False),
        Column("activated_at", DateTime),
        Column("max_users", Integer, default=1),
        Column("max_devices", Integer, default=1),
        Column("features", Text),  # 存储JSON格式的功能列表
        Column("is_active", Boolean, default=True),
        Column("created_at", DateTime, default=func.now()),
        Column("updated_at", DateTime, default=func.now(), onupdate=func.now()),
    )

    # 创建organizations表
    organizations = Table(
        "organizations",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(255), nullable=False, index=True),
        Column("contact_email", String(255), unique=True, nullable=False, index=True),
        Column("phone", String(50)),
        Column("address", Text),
        Column("website", String(255)),
        Column("license_count", Integer, default=0),
        Column("max_users", Integer, default=100),
        Column("current_users", Integer, default=0),
        Column("is_active", Boolean, default=True),
        Column("created_at", DateTime, default=func.now()),
        Column("updated_at", DateTime, default=func.now(), onupdate=func.now()),
    )

    # 创建user_licenses表
    user_licenses = Table(
        "user_licenses",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("user_id", Integer, nullable=False, index=True),
        Column("license_id", Integer, nullable=False, index=True),
        Column("role", String(20), default="user", nullable=False),
        Column("status", String(20), default="inactive"),
        Column("can_manage", Boolean, default=False),
        Column("can_view", Boolean, default=True),
        Column("can_use", Boolean, default=True),
        Column("assigned_by", Integer),
        Column("assigned_at", DateTime, default=func.now()),
        Column("expires_at", DateTime),
        Column("created_at", DateTime, default=func.now()),
        Column("updated_at", DateTime, default=func.now(), onupdate=func.now()),
    )

    # 创建创意想法表
    creative_ideas = Table(
        "creative_ideas",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("user_id", Integer, nullable=False),
        Column("title", String(255), nullable=False),
        Column("description", Text),
        Column("category", String(100)),
        Column("prompt_template_id", Integer),
        Column("ai_generated_content", Text),  # 存储JSON字符串
        Column("images", Text),  # 存储JSON字符串
        Column("scores", Text),  # 存储JSON字符串
        Column("tags", Text),  # 存储JSON字符串
        Column("is_public", Boolean, default=False),
        Column("view_count", Integer, default=0),
        Column("like_count", Integer, default=0),
        Column("created_at", DateTime, default=func.now()),
        Column("updated_at", DateTime, default=func.now(), onupdate=func.now()),
    )

    # 创建Prompt模板表
    prompt_templates = Table(
        "prompt_templates",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(255), nullable=False),
        Column("category", String(100)),
        Column("template", Text, nullable=False),
        Column("variables", Text),  # 存储JSON字符串
        Column("description", Text),
        Column("usage_count", Integer, default=0),
        Column("is_public", Boolean, default=True),
        Column("created_by", Integer),
        Column("created_at", DateTime, default=func.now()),
        Column("updated_at", DateTime, default=func.now(), onupdate=func.now()),
    )

    # 创建创意评分记录表
    idea_scores = Table(
        "idea_scores",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("idea_id", Integer, nullable=False),
        Column("scorer_type", String(50)),  # 'ai', 'human', 'hybrid'
        Column("creativity_score", String(10)),  # 存储数值字符串
        Column("feasibility_score", String(10)),
        Column("commercial_score", String(10)),
        Column("total_score", String(10)),
        Column("analysis_details", Text),  # 存储JSON字符串
        Column("reviewer_id", Integer),
        Column("created_at", DateTime, default=func.now()),
    )

    # 创建所有表
    metadata.create_all(engine)
    print("✅ 基础表创建成功")

    # 验证表创建
    from sqlalchemy import inspect

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print(f"\n📋 已创建的表 ({len(tables)} 个):")
    for table in sorted(tables):
        columns = inspector.get_columns(table)
        print(f"  - {table} ({len(columns)} 列)")

    return engine


def insert_sample_data(engine):
    """插入示例数据"""
    print("\n📥 插入示例数据...")

    with engine.connect() as conn:
        import hashlib

        # 使用简单MD5哈希作为示例（生产环境应使用更强的加密）
        def simple_hash(password):
            return hashlib.md5(password.encode()).hexdigest()

        # 插入示例用户
        hashed_password = simple_hash("password123")

        # 检查是否已有数据
        result = conn.execute(text("SELECT COUNT(*) FROM users")).fetchone()
        if result[0] == 0:
            conn.execute(
                text("""
                INSERT INTO users (username, email, hashed_password, role, is_active) VALUES
                ('admin', 'admin@example.com', :pwd, 'admin', 1),
                ('orgadmin', 'orgadmin@example.com', :pwd, 'org_admin', 1),
                ('user1', 'user1@example.com', :pwd, 'user', 1),
                ('user2', 'user2@example.com', :pwd, 'premium', 1)
            """),
                {"pwd": hashed_password},
            )
            print("✅ 示例用户数据插入成功")
        else:
            print("✅ 用户数据已存在")

        # 插入示例组织
        result = conn.execute(text("SELECT COUNT(*) FROM organizations")).fetchone()
        if result[0] == 0:
            conn.execute(text("""
                INSERT INTO organizations (name, contact_email, phone, max_users) VALUES
                ('测试科技有限公司', 'contact@test-tech.com', '010-12345678', 100),
                ('创新软件公司', 'info@innovate-software.com', '021-87654321', 50)
            """))
            print("✅ 示例组织数据插入成功")
        else:
            print("✅ 组织数据已存在")

        # 插入示例许可证
        result = conn.execute(text("SELECT COUNT(*) FROM licenses")).fetchone()
        if result[0] == 0:
            from datetime import datetime, timedelta

            expiry_date = datetime.now() + timedelta(days=365)

            conn.execute(
                text("""
                INSERT INTO licenses (license_key, organization_id, license_type, status, expires_at, max_users, features) VALUES
                ('TEST-LICENSE-001', 1, 'enterprise', 'active', :expiry, 100, '["feature1", "feature2", "feature3"]'),
                ('TEST-LICENSE-002', 2, 'commercial', 'active', :expiry, 50, '["feature1", "feature2"]')
            """),
                {"expiry": expiry_date},
            )
            print("✅ 示例许可证数据插入成功")
        else:
            print("✅ 许可证数据已存在")

        # 插入默认Prompt模板
        result = conn.execute(text("SELECT COUNT(*) FROM prompt_templates")).fetchone()
        if result[0] == 0:
            from datetime import datetime
            import json

            default_templates = [
                {
                    "name": "低成本IoT解决方案",
                    "category": "technology",
                    "template": "为{场景}设计一个低成本的IoT解决方案，要求使用常见的传感器和微控制器，在预算{预算}元以内实现{功能}功能，并考虑{约束条件}。",
                    "variables": json.dumps(
                        {
                            "场景": {"type": "string", "description": "应用场景描述"},
                            "预算": {"type": "number", "description": "预算金额"},
                            "功能": {"type": "string", "description": "所需功能"},
                            "约束条件": {
                                "type": "string",
                                "description": "技术或环境约束",
                            },
                        }
                    ),
                    "description": "适用于设计低成本物联网解决方案的Prompt模板",
                },
                {
                    "name": "商业创新想法",
                    "category": "business",
                    "template": "基于{行业}行业的现状，提出一个创新的商业模式，解决{问题}问题，目标用户是{目标用户}，核心竞争优势是{优势}。",
                    "variables": json.dumps(
                        {
                            "行业": {"type": "string", "description": "目标行业"},
                            "问题": {"type": "string", "description": "要解决的问题"},
                            "目标用户": {
                                "type": "string",
                                "description": "目标用户群体",
                            },
                            "优势": {"type": "string", "description": "核心竞争优势"},
                        }
                    ),
                    "description": "用于生成商业创新想法的Prompt模板",
                },
                {
                    "name": "教育科技应用",
                    "category": "education",
                    "template": "设计一个{年龄段}学生的{学科}学习应用，利用{技术}技术，帮助学生更好地理解{概念}概念，提高{能力}能力。",
                    "variables": json.dumps(
                        {
                            "年龄段": {"type": "string", "description": "学生年龄段"},
                            "学科": {"type": "string", "description": "学科名称"},
                            "技术": {"type": "string", "description": "使用的技术"},
                            "概念": {"type": "string", "description": "核心概念"},
                            "能力": {"type": "string", "description": "培养的能力"},
                        }
                    ),
                    "description": "专门用于教育科技应用设计的Prompt模板",
                },
                {
                    "name": "可持续发展项目",
                    "category": "environment",
                    "template": "针对{地区}地区的{环境问题}问题，设计一个可持续发展的解决方案，结合{技术}技术，实现{目标}目标，同时考虑{社会因素}因素。",
                    "variables": json.dumps(
                        {
                            "地区": {"type": "string", "description": "地理区域"},
                            "环境问题": {
                                "type": "string",
                                "description": "具体的环境问题",
                            },
                            "技术": {"type": "string", "description": "使用的技术手段"},
                            "目标": {"type": "string", "description": "期望达成的目标"},
                            "社会因素": {
                                "type": "string",
                                "description": "相关的社会经济因素",
                            },
                        }
                    ),
                    "description": "用于可持续发展项目设计的Prompt模板",
                },
                {
                    "name": "创意产品设计",
                    "category": "design",
                    "template": "为{用户群体}设计一款{产品类型}产品，解决{痛点}痛点，采用{设计理念}设计理念，融入{元素}元素，使产品具有{特色}特色。",
                    "variables": json.dumps(
                        {
                            "用户群体": {
                                "type": "string",
                                "description": "目标用户群体",
                            },
                            "产品类型": {"type": "string", "description": "产品类别"},
                            "痛点": {"type": "string", "description": "用户痛点"},
                            "设计理念": {"type": "string", "description": "设计哲学"},
                            "元素": {"type": "string", "description": "设计元素"},
                            "特色": {"type": "string", "description": "产品特色"},
                        }
                    ),
                    "description": "通用的产品创意设计Prompt模板",
                },
            ]

            for template in default_templates:
                conn.execute(
                    text("""
                    INSERT INTO prompt_templates (name, category, template, variables, description, is_public, created_at, updated_at)
                    VALUES (:name, :category, :template, :variables, :description, :is_public, :created_at, :updated_at)
                """),
                    {
                        "name": template["name"],
                        "category": template["category"],
                        "template": template["template"],
                        "variables": template["variables"],
                        "description": template["description"],
                        "is_public": True,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now(),
                    },
                )
            print("✅ 默认Prompt模板插入成功")
        else:
            print("✅ Prompt模板数据已存在")

        conn.commit()


if __name__ == "__main__":
    print("🚀 开始数据库初始化...")

    try:
        # 创建表结构
        engine = create_basic_tables()

        # 插入示例数据
        insert_sample_data(engine)

        print("\n🎉 数据库初始化完成!")
        print("\n📊 可用的测试账户:")
        print("  - 管理员: admin / password123 (角色: admin)")
        print("  - 企业管理员: orgadmin / password123 (角色: org_admin)")
        print("  - 普通用户: user1 / password123 (角色: user)")
        print("  - 高级用户: user2 / password123 (角色: premium)")

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback

        traceback.print_exc()
