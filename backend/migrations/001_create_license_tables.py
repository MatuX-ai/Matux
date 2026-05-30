"""
许可证管理系统数据库迁移脚本
创建组织和许可证相关数据表
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config.settings import settings
from models.license import Base, License, Organization


def create_license_tables():
    """创建许可证管理相关数据表"""

    # 创建数据库引擎
    engine = create_engine(settings.DATABASE_URL)

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    print("许可证管理数据表创建成功!")

    # 创建索引以提高查询性能
    with engine.connect() as conn:
        # 为许可证表创建复合索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_licenses_org_status 
            ON licenses (organization_id, status)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_licenses_expires 
            ON licenses (expires_at)
        """))

        # 为组织表创建索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_organizations_active 
            ON organizations (is_active)
        """))

        # 为日志表创建索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_activity_logs_license 
            ON license_activity_logs (license_key)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_validation_attempts_license 
            ON license_validation_attempts (license_key)
        """))

        conn.commit()

    print("索引创建完成!")


def drop_license_tables():
    """删除许可证管理相关数据表"""
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.drop_all(bind=engine)
    print("许可证管理数据表删除成功!")


def insert_sample_data():
    """插入示例数据用于测试"""
    from datetime import datetime, timedelta

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 创建示例组织
        sample_org = Organization(
            name="示例教育机构",
            contact_email="contact@sample-edu.com",
            phone="+86-138-0000-0000",
            address="北京市朝阳区示例路123号",
            website="https://www.sample-edu.com",
            max_users=500,
        )
        db.add(sample_org)
        db.flush()  # 获取ID但不提交

        # 创建示例许可证
        sample_license = License(
            license_key="LICENSE-SAMPLE-001-ABCDEF123456",
            organization_id=sample_org.id,
            license_type="education",
            status="active",
            expires_at=datetime.utcnow() + timedelta(days=365),
            max_users=100,
            max_devices=50,
            features=["basic_access", "advanced_features", "api_access"],
            metadata={
                "school_type": "primary",
                "grade_levels": ["1", "2", "3", "4", "5", "6"],
                "student_capacity": 300,
            },
            notes="示例教育许可证 - 用于测试目的",
        )
        db.add(sample_license)

        # 创建另一个示例组织
        test_org = Organization(
            name="测试科技公司", contact_email="admin@test-tech.com", max_users=200
        )
        db.add(test_org)
        db.flush()

        # 创建测试许可证
        test_license = License(
            license_key="LICENSE-TEST-002-XYZ789",
            organization_id=test_org.id,
            license_type="commercial",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(days=180),
            max_users=50,
            features=["basic_access"],
            notes="测试商业许可证",
        )
        db.add(test_license)

        db.commit()
        print("示例数据插入成功!")

    except Exception as e:
        db.rollback()
        print(f"插入示例数据失败: {e}")
    finally:
        db.close()


def main():
    """主函数"""
    print("开始执行许可证管理系统数据库迁移...")

    # 创建表结构
    create_license_tables()

    # 询问是否插入示例数据
    response = input("是否插入示例数据用于测试? (y/n): ")
    if response.lower() == "y":
        insert_sample_data()

    print("数据库迁移完成!")


if __name__ == "__main__":
    main()
