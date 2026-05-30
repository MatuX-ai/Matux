"""
企业赞助管理系统数据库迁移脚本
创建赞助活动、品牌曝光、积分转换等相关数据表
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config.settings import settings
from models.license import Organization
from models.sponsorship import (
    Base,
    BrandExposure,
    ExposureType,
    ImpactCategory,
    PointConversionRule,
    PointTransaction,
    PointTransactionType,
    SocialImpact,
    Sponsorship,
    SponsorshipStatus,
)


def create_sponsorship_tables():
    """创建赞助管理相关数据表"""

    # 创建数据库引擎
    engine = create_engine(settings.DATABASE_URL)

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    print("赞助管理数据表创建成功!")

    # 创建索引以提高查询性能
    with engine.connect() as conn:
        # 为赞助活动表创建复合索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sponsorships_org_status 
            ON sponsorships (org_id, status)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sponsorships_date_range 
            ON sponsorships (start_date, end_date)
        """))

        # 为品牌曝光表创建索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_brand_exposures_sponsorship_type 
            ON brand_exposures (sponsorship_id, exposure_type)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_brand_exposures_timestamp 
            ON brand_exposures (exposed_at)
        """))

        # 为积分交易表创建索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_point_transactions_sponsorship_type 
            ON point_transactions (sponsorship_id, transaction_type)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_point_transactions_timestamp 
            ON point_transactions (created_at)
        """))

        # 为社会影响力表创建索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_social_impacts_sponsorship_category 
            ON social_impacts (sponsorship_id, category)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_social_impacts_completion 
            ON social_impacts (is_completed)
        """))

        # 为组织表添加赞助相关字段（如果不存在）
        try:
            conn.execute(text("""
                ALTER TABLE organizations 
                ADD COLUMN IF NOT EXISTS total_sponsorship_amount FLOAT DEFAULT 0.0
            """))

            conn.execute(text("""
                ALTER TABLE organizations 
                ADD COLUMN IF NOT EXISTS active_sponsorships INTEGER DEFAULT 0
            """))

            conn.execute(text("""
                ALTER TABLE organizations 
                ADD COLUMN IF NOT EXISTS total_brand_exposures INTEGER DEFAULT 0
            """))

            conn.execute(text("""
                ALTER TABLE organizations 
                ADD COLUMN IF NOT EXISTS accumulated_points FLOAT DEFAULT 0.0
            """))

            print("组织表赞助字段添加成功!")
        except Exception as e:
            print(f"添加组织表字段时出现警告（可能已存在）: {e}")

        conn.commit()

    print("索引创建完成!")


def drop_sponsorship_tables():
    """删除赞助管理相关数据表"""
    engine = create_engine(settings.DATABASE_URL)

    # 删除外键约束
    with engine.connect() as conn:
        conn.execute(text("DROP INDEX IF EXISTS idx_sponsorships_org_status"))
        conn.execute(text("DROP INDEX IF EXISTS idx_sponsorships_date_range"))
        conn.execute(text("DROP INDEX IF EXISTS idx_brand_exposures_sponsorship_type"))
        conn.execute(text("DROP INDEX IF EXISTS idx_brand_exposures_timestamp"))
        conn.execute(
            text("DROP INDEX IF EXISTS idx_point_transactions_sponsorship_type")
        )
        conn.execute(text("DROP INDEX IF EXISTS idx_point_transactions_timestamp"))
        conn.execute(
            text("DROP INDEX IF EXISTS idx_social_impacts_sponsorship_category")
        )
        conn.execute(text("DROP INDEX IF EXISTS idx_social_impacts_completion"))
        conn.commit()

    # 删除表
    tables_to_drop = [
        "point_conversion_rules",
        "social_impacts",
        "point_transactions",
        "brand_exposures",
        "sponsorships",
    ]

    for table_name in tables_to_drop:
        try:
            with engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                conn.commit()
            print(f"表 {table_name} 删除成功")
        except Exception as e:
            print(f"删除表 {table_name} 时出错: {e}")

    print("赞助管理数据表删除成功!")


def insert_sample_data():
    """插入示例数据用于测试"""
    from datetime import datetime, timedelta

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 查找或创建示例组织
        sample_org = (
            db.query(Organization).filter(Organization.name == "示例教育机构").first()
        )

        if not sample_org:
            print("未找到示例组织，请先运行许可证迁移脚本")
            return

        # 创建示例赞助活动
        sample_sponsorship = Sponsorship(
            org_id=sample_org.id,
            name="2026年度教育科技赞助计划",
            description="支持教育科技创新发展的年度赞助活动，重点关注编程教育和AI技术应用",
            sponsor_amount=50000.0,
            currency="CNY",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=365),
            exposure_types=[
                ExposureType.BANNER.value,
                ExposureType.SIDEBAR.value,
                ExposureType.CONTENT_INTEGRATION.value,
            ],
            target_audience={
                "age_range": "15-25",
                "interests": ["programming", "ai", "technology"],
                "geography": ["China"],
            },
            branding_guidelines={
                "logo_requirements": "最小尺寸100x100px",
                "color_scheme": "#007bff",
                "placement_restrictions": "不得与其他竞品同时展示",
            },
            status=SponsorshipStatus.ACTIVE.value,
        )
        db.add(sample_sponsorship)
        db.flush()

        # 创建品牌曝光记录
        exposures = [
            BrandExposure(
                sponsorship_id=sample_sponsorship.id,
                exposure_type=ExposureType.BANNER.value,
                platform="主网站",
                placement="首页顶部横幅",
                creative_asset="https://example.com/banner.jpg",
                view_count=15000,
                click_count=450,
                engagement_count=120,
                conversion_count=25,
                duration_seconds=30,
                geo_location={"country": "CN", "city": "Beijing"},
            ),
            BrandExposure(
                sponsorship_id=sample_sponsorship.id,
                exposure_type=ExposureType.SIDEBAR.value,
                platform="课程页面",
                placement="右侧边栏",
                view_count=8000,
                click_count=160,
                engagement_count=80,
                conversion_count=12,
                duration_seconds=15,
                geo_location={"country": "CN", "city": "Shanghai"},
            ),
        ]

        for exposure in exposures:
            db.add(exposure)

        # 创建积分交易记录
        point_transactions = [
            PointTransaction(
                sponsorship_id=sample_sponsorship.id,
                transaction_type=PointTransactionType.EARNED.value,
                points_amount=1500.0,
                balance_before=0.0,
                balance_after=1500.0,
                reference_id=f"EXP-{sample_sponsorship.id}-001",
                description="基于品牌曝光获得积分奖励",
            ),
            PointTransaction(
                sponsorship_id=sample_sponsorship.id,
                transaction_type=PointTransactionType.CONVERTED.value,
                points_amount=500.0,
                balance_before=1500.0,
                balance_after=1000.0,
                reference_id=f"CVR-{sample_sponsorship.id}-001",
                description="积分转换为教育资源捐赠",
            ),
        ]

        for transaction in point_transactions:
            db.add(transaction)

        # 创建社会影响力记录
        social_impact = SocialImpact(
            sponsorship_id=sample_sponsorship.id,
            category=ImpactCategory.EDUCATION.value,
            title="编程教育普及项目",
            description="通过赞助资金支持偏远地区学校开展编程教育，提升学生数字素养",
            target_beneficiaries=500,
            actual_beneficiaries=320,
            metrics={
                "schools_supported": 8,
                "teachers_trained": 24,
                "student_hours_taught": 2400,
            },
            evidence_documents=[
                "https://example.com/evidence/report1.pdf",
                "https://example.com/evidence/photos.zip",
            ],
            start_date=datetime.utcnow() - timedelta(days=90),
            end_date=datetime.utcnow() + timedelta(days=180),
            is_completed=False,
            completion_percentage=64.0,
        )
        db.add(social_impact)

        # 创建积分转换规则
        conversion_rules = [
            PointConversionRule(
                name="教育资源捐赠",
                points_required=1000.0,
                reward_type="educational_resources",
                reward_value={
                    "type": "online_courses",
                    "quantity": 50,
                    "value_per_unit": 200,
                },
                min_sponsorship_amount=10000.0,
                applicable_categories=["education", "technology"],
                validity_period_days=365,
                max_conversions_per_user=5,
            ),
            PointConversionRule(
                name="环保公益项目",
                points_required=2000.0,
                reward_type="environmental_project",
                reward_value={
                    "type": "tree_planting",
                    "trees_per_point": 0.1,
                    "location": "northern_china",
                },
                min_sponsorship_amount=20000.0,
                applicable_categories=["environment"],
                validity_period_days=730,
                max_conversions_per_user=3,
            ),
        ]

        for rule in conversion_rules:
            db.add(rule)

        # 更新组织的赞助统计数据
        sample_org.total_sponsorship_amount += sample_sponsorship.sponsor_amount
        sample_org.active_sponsorships += 1
        sample_org.total_brand_exposures = sum(e.view_count for e in exposures)
        sample_org.accumulated_points = 1000.0  # 示例积分余额

        db.commit()
        print("赞助系统示例数据插入成功!")

    except Exception as e:
        db.rollback()
        print(f"插入示例数据失败: {e}")
        raise
    finally:
        db.close()


def main():
    """主函数"""
    print("开始执行企业赞助管理系统数据库迁移...")

    # 创建表结构
    create_sponsorship_tables()

    # 询问是否插入示例数据
    response = input("是否插入示例数据用于测试? (y/n): ")
    if response.lower() == "y":
        insert_sample_data()

    print("数据库迁移完成!")


if __name__ == "__main__":
    main()
