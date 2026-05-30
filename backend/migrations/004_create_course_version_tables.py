"""
课程版本控制表创建迁移脚本
"""

import os
import sys

from sqlalchemy import MetaData, create_engine
from sqlalchemy.schema import CreateTable

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from models.course_version import CourseVersion, MergeRequest, VersionBranch


def create_course_version_tables():
    """创建课程版本控制相关表"""
    settings = Settings()

    # 创建引擎
    engine = create_engine(settings.DATABASE_URL)
    MetaData()

    print("正在创建课程版本控制表...")

    try:
        # 创建表
        CourseVersion.__table__.create(engine, checkfirst=True)
        print("✓ CourseVersion 表创建成功")

        VersionBranch.__table__.create(engine, checkfirst=True)
        print("✓ VersionBranch 表创建成功")

        MergeRequest.__table__.create(engine, checkfirst=True)
        print("✓ MergeRequest 表创建成功")

        print("\n所有课程版本控制表创建完成!")

    except Exception as e:
        print(f"创建表时发生错误: {e}")
        raise


def drop_course_version_tables():
    """删除课程版本控制相关表"""
    settings = Settings()

    # 创建引擎
    engine = create_engine(settings.DATABASE_URL)

    print("正在删除课程版本控制表...")

    try:
        # 删除表（按依赖顺序）
        MergeRequest.__table__.drop(engine, checkfirst=True)
        print("✓ MergeRequest 表删除成功")

        VersionBranch.__table__.drop(engine, checkfirst=True)
        print("✓ VersionBranch 表删除成功")

        CourseVersion.__table__.drop(engine, checkfirst=True)
        print("✓ CourseVersion 表删除成功")

        print("\n所有课程版本控制表删除成功!")

    except Exception as e:
        print(f"删除表时发生错误: {e}")
        raise


def show_table_schema():
    """显示表结构"""
    print("\n=== CourseVersion 表结构 ===")
    print(CreateTable(CourseVersion.__table__))

    print("\n=== VersionBranch 表结构 ===")
    print(CreateTable(VersionBranch.__table__))

    print("\n=== MergeRequest 表结构 ===")
    print(CreateTable(MergeRequest.__table__))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="课程版本控制表管理")
    parser.add_argument(
        "action",
        choices=["create", "drop", "schema"],
        help="操作类型: create(创建表), drop(删除表), schema(显示表结构)",
    )

    args = parser.parse_args()

    if args.action == "create":
        create_course_version_tables()
    elif args.action == "drop":
        drop_course_version_tables()
    elif args.action == "schema":
        show_table_schema()
