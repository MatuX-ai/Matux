"""
硬件模块租赁系统数据库迁移脚本
创建硬件模块和租赁记录相关表
"""

import enum
import os

from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.sql import func

# 加载环境变量
load_dotenv()


class HardwareModuleStatus(str, enum.Enum):
    """硬件模块状态枚举"""

    AVAILABLE = "available"  # 可租赁
    RENTED = "rented"  # 已租赁
    MAINTENANCE = "maintenance"  # 维护中
    DAMAGED = "damaged"  # 损坏
    RETIRED = "retired"  # 已退役


class ModuleRentalStatus(str, enum.Enum):
    """模块租赁记录状态枚举"""

    ACTIVE = "active"  # 租赁中
    COMPLETED = "completed"  # 已完成
    OVERDUE = "overdue"  # 已逾期
    CANCELLED = "cancelled"  # 已取消
    RETURNED = "returned"  # 已归还


class DamageLevel(str, enum.Enum):
    """损坏等级枚举"""

    NONE = "none"  # 无损坏
    MINOR = "minor"  # 轻微损坏
    MODERATE = "moderate"  # 中等损坏
    SEVERE = "severe"  # 严重损坏
    DESTROYED = "destroyed"  # 完全损毁


def create_hardware_modules_table():
    """创建硬件模块表"""

    # 获取数据库URL
    database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    # 创建引擎
    engine = create_engine(database_url)
    metadata = MetaData()

    # 定义hardware_modules表
    hardware_modules = Table(
        "hardware_modules",
        metadata,
        Column("id", Integer, primary_key=True, index=True),
        Column("module_type", String(100), nullable=False, index=True),  # 模块类型
        Column(
            "serial_number", String(100), unique=True, nullable=False, index=True
        ),  # 序列号
        Column("name", String(200), nullable=False),  # 模块名称
        # 状态和价格信息
        Column(
            "status", Enum(HardwareModuleStatus), default=HardwareModuleStatus.AVAILABLE
        ),
        Column("price_per_day", Float, default=1.0),  # 日租金1元
        Column("deposit_amount", Float, default=50.0),  # 押金
        # 库存和位置信息
        Column("quantity_available", Integer, default=1),  # 可用数量
        Column("total_quantity", Integer, default=1),  # 总数量
        Column("location", String(200)),  # 存放位置
        Column("description", Text),  # 描述信息
        # 技术规格
        Column("specifications", Text),  # 技术参数
        Column("compatible_models", Text),  # 兼容型号
        # 状态和时间戳
        Column("is_active", Boolean, default=True),
        Column("created_at", DateTime, default=func.now()),
        Column("updated_at", DateTime, default=func.now(), onupdate=func.now()),
    )

    # 创建表
    metadata.create_all(engine)
    print("✅ hardware_modules 表创建成功")

    # 验证表创建
    from sqlalchemy import inspect

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "hardware_modules" in tables:
        print("✅ 表验证通过")
        # 显示表结构
        columns = inspector.get_columns("hardware_modules")
        print(f"📊 表结构 ({len(columns)} 列):")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
    else:
        print("❌ 表创建失败")


def create_module_rental_records_table():
    """创建模块租赁记录表"""

    # 获取数据库URL
    database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    # 创建引擎
    engine = create_engine(database_url)
    # 使用新的metadata对象，避免外键解析问题
    metadata = MetaData()

    # 定义module_rental_records表
    module_rental_records = Table(
        "module_rental_records",
        metadata,
        Column("id", Integer, primary_key=True, index=True),
        Column("module_id", Integer, nullable=False),
        Column("user_license_id", Integer, nullable=False),
        # 租赁时间信息
        Column("rental_start_date", DateTime, nullable=False),  # 租赁开始时间
        Column("rental_end_date", DateTime, nullable=False),  # 预计归还时间
        Column("actual_return_date", DateTime),  # 实际归还时间
        # 财务信息
        Column("daily_rate", Float, nullable=False),  # 日租金
        Column("total_amount", Float, nullable=False),  # 总金额
        Column("deposit_paid", Float, default=0.0),  # 已付押金
        Column("deposit_refunded", Float, default=0.0),  # 已退押金
        # 损坏和赔偿信息
        Column("is_damaged", Boolean, default=False),  # 是否损坏
        Column("damage_level", Enum(DamageLevel), default=DamageLevel.NONE),  # 损坏等级
        Column("damage_description", Text),  # 损坏描述
        Column("compensation_amount", Float, default=0.0),  # 赔偿金额
        # 状态信息
        Column("status", Enum(ModuleRentalStatus), default=ModuleRentalStatus.ACTIVE),
        Column("cancellation_reason", Text),  # 取消原因
        # 时间戳
        Column("created_at", DateTime, default=func.now()),
        Column("updated_at", DateTime, default=func.now(), onupdate=func.now()),
    )

    # 创建表
    metadata.create_all(engine)
    print("✅ module_rental_records 表创建成功")

    # 验证表创建
    from sqlalchemy import inspect

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "module_rental_records" in tables:
        print("✅ 表验证通过")
        # 显示表结构
        columns = inspector.get_columns("module_rental_records")
        print(f"📊 表结构 ({len(columns)} 列):")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
    else:
        print("❌ 表创建失败")


def create_indexes():
    """创建必要的索引以提高查询性能"""

    database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            # 为硬件模块表创建复合索引
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_hardware_modules_type_status 
                ON hardware_modules (module_type, status)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_hardware_modules_available 
                ON hardware_modules (status, quantity_available)
            """)

            # 为租赁记录表创建索引
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rental_records_user_license 
                ON module_rental_records (user_license_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rental_records_module 
                ON module_rental_records (module_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rental_records_status_dates 
                ON module_rental_records (status, rental_end_date)
            """)

            conn.commit()
            print("✅ 索引创建成功")

        except Exception as e:
            print(f"⚠️  索引创建失败: {e}")


def insert_sample_data():
    """插入示例数据用于测试"""

    database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            # 检查是否已有数据
            result = conn.execute("SELECT COUNT(*) FROM hardware_modules")
            count = result.fetchone()[0]

            if count == 0:
                # 插入示例硬件模块数据
                sample_modules = [
                    {
                        "module_type": "ESP32",
                        "serial_number": "ESP32-001",
                        "name": "ESP32开发板",
                        "status": "available",
                        "price_per_day": 1.0,
                        "deposit_amount": 50.0,
                        "quantity_available": 5,
                        "total_quantity": 5,
                        "location": "A区-01货架",
                        "description": "ESP32-WROOM-32开发板，适用于物联网项目",
                        "specifications": "CPU: Xtensa LX6双核, RAM: 520KB, Flash: 4MB",
                        "compatible_models": "Arduino IDE, MicroPython, ESP-IDF",
                    },
                    {
                        "module_type": "DHT22",
                        "serial_number": "DHT22-001",
                        "name": "DHT22温湿度传感器",
                        "status": "available",
                        "price_per_day": 1.0,
                        "deposit_amount": 30.0,
                        "quantity_available": 10,
                        "total_quantity": 10,
                        "location": "B区-03货架",
                        "description": "数字温湿度传感器，精度高",
                        "specifications": "温度范围: -40~80°C, 湿度范围: 0~100%RH",
                        "compatible_models": "Arduino, Raspberry Pi, ESP32",
                    },
                    {
                        "module_type": "OLED",
                        "serial_number": "OLED-001",
                        "name": "0.96寸OLED显示屏",
                        "status": "available",
                        "price_per_day": 1.0,
                        "deposit_amount": 40.0,
                        "quantity_available": 8,
                        "total_quantity": 8,
                        "location": "C区-02货架",
                        "description": "128x64像素OLED显示屏",
                        "specifications": "分辨率: 128x64, 接口: I2C/SPI",
                        "compatible_models": "Arduino, ESP32, Raspberry Pi",
                    },
                ]

                for module in sample_modules:
                    conn.execute(
                        """
                        INSERT INTO hardware_modules 
                        (module_type, serial_number, name, status, price_per_day, deposit_amount,
                         quantity_available, total_quantity, location, description, specifications, compatible_models)
                        VALUES (:module_type, :serial_number, :name, :status, :price_per_day, :deposit_amount,
                                :quantity_available, :total_quantity, :location, :description, :specifications, :compatible_models)
                    """,
                        **module,
                    )

                conn.commit()
                print("✅ 示例数据插入成功")
            else:
                print("ℹ️  数据表中已有数据，跳过示例数据插入")

        except Exception as e:
            print(f"⚠️  示例数据插入失败: {e}")


def main():
    print("🚀 开始硬件模块数据库迁移...")

    try:
        # 创建硬件模块表
        create_hardware_modules_table()

        # 创建租赁记录表
        create_module_rental_records_table()

        # 创建索引
        create_indexes()

        # 插入示例数据
        insert_sample_data()

        print("\n🎉 硬件模块数据库迁移完成!")
        print("\n📋 创建的表:")
        print("  - hardware_modules: 硬件模块信息表")
        print("  - module_rental_records: 模块租赁记录表")
        print("\n🔧 创建的索引:")
        print("  - idx_hardware_modules_type_status: 模块类型和状态复合索引")
        print("  - idx_hardware_modules_available: 可用性查询索引")
        print("  - idx_rental_records_user_license: 用户租赁记录索引")
        print("  - idx_rental_records_module: 模块租赁历史索引")
        print("  - idx_rental_records_status_dates: 状态和日期复合索引")
        print("\n📦 插入的示例数据:")
        print("  - ESP32开发板 x5")
        print("  - DHT22传感器 x10")
        print("  - OLED显示屏 x8")

    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
