"""
Migration 008: 创建创意激发引擎相关数据表

此迁移脚本创建以下表：
- creative_ideas: 创意想法存储表
- prompt_templates: Prompt模板表
- idea_scores: 创意评分记录表
"""

from datetime import datetime
import os
import sys

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    create_engine,
)

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings


def upgrade():
    """升级数据库 - 创建创意相关表"""
    # 对于SQLite数据库，创建同步引擎
    sync_database_url = settings.DATABASE_URL.replace(
        "sqlite+aiosqlite://", "sqlite://"
    )
    engine = create_engine(sync_database_url)
    metadata = MetaData()

    # 导入现有模型以确保外键引用正确

    # 创意想法表
    creative_ideas = Table(
        "creative_ideas",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
        Column("title", String(255), nullable=False),
        Column("description", Text),
        Column("category", String(100)),
        Column("prompt_template_id", Integer, ForeignKey("prompt_templates.id")),
        Column("ai_generated_content", JSON),
        Column("images", JSON),
        Column("scores", JSON),
        Column("tags", JSON),
        Column("is_public", Boolean, default=False),
        Column("view_count", Integer, default=0),
        Column("like_count", Integer, default=0),
        Column("created_at", DateTime, default=datetime.utcnow),
        Column(
            "updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
        ),
    )

    # Prompt模板表
    prompt_templates = Table(
        "prompt_templates",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(255), nullable=False),
        Column("category", String(100)),
        Column("template", Text, nullable=False),
        Column("variables", JSON),
        Column("description", Text),
        Column("usage_count", Integer, default=0),
        Column("is_public", Boolean, default=True),
        Column("created_by", Integer, ForeignKey("users.id")),
        Column("created_at", DateTime, default=datetime.utcnow),
        Column(
            "updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
        ),
    )

    # 创意评分记录表
    idea_scores = Table(
        "idea_scores",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("idea_id", Integer, ForeignKey("creative_ideas.id"), nullable=False),
        Column("scorer_type", String(50)),  # 'ai', 'human', 'hybrid'
        Column("creativity_score", Numeric(precision=3, scale=2)),
        Column("feasibility_score", Numeric(precision=3, scale=2)),
        Column("commercial_score", Numeric(precision=3, scale=2)),
        Column("total_score", Numeric(precision=3, scale=2)),
        Column("analysis_details", JSON),
        Column("reviewer_id", Integer, ForeignKey("users.id")),
        Column("created_at", DateTime, default=datetime.utcnow),
    )

    # 创建表
    metadata.create_all(engine)

    # 插入默认的Prompt模板
    insert_default_templates(engine)

    print("✅ 创意引擎数据表创建成功")
    print("✅ 默认Prompt模板已插入")


def downgrade():
    """降级数据库 - 删除创意相关表"""
    # 对于SQLite数据库，创建同步引擎
    sync_database_url = settings.DATABASE_URL.replace(
        "sqlite+aiosqlite://", "sqlite://"
    )
    engine = create_engine(sync_database_url)
    metadata = MetaData()

    # 导入模型

    # 按依赖顺序删除表
    tables_to_drop = ["idea_scores", "creative_ideas", "prompt_templates"]

    for table_name in tables_to_drop:
        try:
            table = Table(table_name, metadata, autoload_with=engine)
            table.drop(engine)
            print(f"✅ 表 {table_name} 已删除")
        except Exception as e:
            print(f"⚠️  表 {table_name} 删除失败: {str(e)}")


def insert_default_templates(engine):
    """插入默认的Prompt模板"""
    from datetime import datetime

    default_templates = [
        {
            "name": "低成本IoT解决方案",
            "category": "technology",
            "template": "为{场景}设计一个低成本的IoT解决方案，要求使用常见的传感器和微控制器，在预算{预算}元以内实现{功能}功能，并考虑{约束条件}。",
            "variables": {
                "场景": {"type": "string", "description": "应用场景描述"},
                "预算": {"type": "number", "description": "预算金额"},
                "功能": {"type": "string", "description": "所需功能"},
                "约束条件": {"type": "string", "description": "技术或环境约束"},
            },
            "description": "适用于设计低成本物联网解决方案的Prompt模板",
        },
        {
            "name": "商业创新想法",
            "category": "business",
            "template": "基于{行业}行业的现状，提出一个创新的商业模式，解决{问题}问题，目标用户是{目标用户}，核心竞争优势是{优势}。",
            "variables": {
                "行业": {"type": "string", "description": "目标行业"},
                "问题": {"type": "string", "description": "要解决的问题"},
                "目标用户": {"type": "string", "description": "目标用户群体"},
                "优势": {"type": "string", "description": "核心竞争优势"},
            },
            "description": "用于生成商业创新想法的Prompt模板",
        },
        {
            "name": "教育科技应用",
            "category": "education",
            "template": "设计一个{年龄段}学生的{学科}学习应用，利用{技术}技术，帮助学生更好地理解{概念}概念，提高{能力}能力。",
            "variables": {
                "年龄段": {"type": "string", "description": "学生年龄段"},
                "学科": {"type": "string", "description": "学科名称"},
                "技术": {"type": "string", "description": "使用的技术"},
                "概念": {"type": "string", "description": "核心概念"},
                "能力": {"type": "string", "description": "培养的能力"},
            },
            "description": "专门用于教育科技应用设计的Prompt模板",
        },
        {
            "name": "可持续发展项目",
            "category": "environment",
            "template": "针对{地区}地区的{环境问题}问题，设计一个可持续发展的解决方案，结合{技术}技术，实现{目标}目标，同时考虑{社会因素}因素。",
            "variables": {
                "地区": {"type": "string", "description": "地理区域"},
                "环境问题": {"type": "string", "description": "具体的环境问题"},
                "技术": {"type": "string", "description": "使用的技术手段"},
                "目标": {"type": "string", "description": "期望达成的目标"},
                "社会因素": {"type": "string", "description": "相关的社会经济因素"},
            },
            "description": "用于可持续发展项目设计的Prompt模板",
        },
        {
            "name": "创意产品设计",
            "category": "design",
            "template": "为{用户群体}设计一款{产品类型}产品，解决{痛点}痛点，采用{设计理念}设计理念，融入{元素}元素，使产品具有{特色}特色。",
            "variables": {
                "用户群体": {"type": "string", "description": "目标用户群体"},
                "产品类型": {"type": "string", "description": "产品类别"},
                "痛点": {"type": "string", "description": "用户痛点"},
                "设计理念": {"type": "string", "description": "设计哲学"},
                "元素": {"type": "string", "description": "设计元素"},
                "特色": {"type": "string", "description": "产品特色"},
            },
            "description": "通用的产品创意设计Prompt模板",
        },
    ]

    # 插入模板数据
    with engine.connect() as conn:
        for template in default_templates:
            sql = """
            INSERT INTO prompt_templates (name, category, template, variables, description, is_public, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            conn.execute(
                sql,
                (
                    template["name"],
                    template["category"],
                    template["template"],
                    template["variables"],
                    template["description"],
                    True,
                    datetime.utcnow(),
                    datetime.utcnow(),
                ),
            )
        conn.commit()


if __name__ == "__main__":
    # 运行迁移
    upgrade()
