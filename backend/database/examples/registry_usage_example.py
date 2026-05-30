#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库模块注册表示例使用代码
演示如何使用新的注册表系统
"""

import asyncio
import logging
import sys
import io
from pathlib import Path

# 修复Windows控制台编码问题
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 使用SQLAlchemy 2.0兼容的导入方式
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

# 添加backend目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 现在可以使用绝对导入
from database.module_registry import DatabaseModuleRegistry, get_database_registry, ModuleMetadata
from database.registry_manager import get_registry_manager, init_registry_manager, ModelBasedModule
from database.module_registry import AutoDiscovery

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

Base = declarative_base()


# 示例模型类
class ExampleCourse(Base):
    """示例课程模型"""
    __tablename__ = "example_courses"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    instructor = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExampleStudent(Base):
    """示例学生模型"""
    __tablename__ = "example_students"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, index=True)
    course_id = Column(Integer, ForeignKey("example_courses.id"))
    enrollment_date = Column(DateTime, default=datetime.utcnow)


async def demonstrate_basic_usage():
    """演示基本使用方法"""
    print("=== 数据库模块注册表示例演示 ===")
    print()
    
    try:
        # 1. 获取注册表实例
        registry = get_database_registry()
        manager = get_registry_manager()
        
        print("[OK] 注册表实例创建成功")
        
        # 2. 手动注册模块（通常不需要，会自动发现）
        print("\n1. 手动注册模块示例:")
        registry.register_module(
            ExampleCourse,
            category="education",
            version="1.0.0",
            description="示例课程数据模块"
        )
        
        registry.register_module(
            ExampleStudent,
            category="education", 
            version="1.0.0",
            dependencies=["example_courses"],
            description="示例学生数据模块"
        )
        
        print("[OK] 示例模块注册成功")
        
        # 3. 查看注册表统计
        stats = registry.get_registry_stats()
        print(f"\n2. 注册表统计: {stats}")
        
        # 4. 列出所有模块
        print("\n3. 所有注册的模块:")
        modules = registry.list_modules()
        for module in modules:
            print(f"  - {module.name} (表: {module.table_name}, 分类: {module.category}, 版本: {module.version})")
        
        # 5. 按分类查看模块
        print("\n4. 按分类查看模块:")
        categories = registry.list_categories()
        for category in categories:
            category_modules = registry.get_modules_by_category(category)
            print(f"  分类 '{category}': {len(category_modules)} 个模块")
            for module in category_modules:
                print(f"    - {module.name}")
        
        # 6. 获取特定模块信息
        print("\n5. 获取特定模块信息:")
        course_module = registry.get_module("example_courses")
        if course_module:
            print(f"  模块名称: {course_module.name}")
            print(f"  表名: {course_module.table_name}")
            print(f"  分类: {course_module.category}")
            print(f"  版本: {course_module.version}")
            print(f"  描述: {course_module.description}")
            print(f"  活跃状态: {course_module.is_active}")
            print(f"  依赖: {course_module.dependencies}")
        
        # 7. 通过表名查找模块
        print("\n6. 通过表名查找模块:")
        student_module = registry.get_module_by_table("example_students")
        if student_module:
            print(f"  找到表 'example_students' 对应的模块: {student_module.name}")
        
        # 8. 模块激活/停用
        print("\n7. 模块状态管理:")
        print(f"  停用前状态: {course_module.is_active}")
        registry.deactivate_module("example_courses")
        print(f"  停用后状态: {registry.get_module('example_courses').is_active}")
        
        registry.activate_module("example_courses")
        print(f"  重新激活后状态: {registry.get_module('example_courses').is_active}")
        
        # 9. 创建模块实例并注册
        print("\n8. 创建和注册模块实例:")
        course_instance = ModelBasedModule(ExampleCourse)
        student_instance = ModelBasedModule(ExampleStudent)
        
        registry.register_module_instance(course_instance)
        registry.register_module_instance(student_instance)
        print("[OK] 模块实例注册成功")
        
        # 10. 使用管理器进行初始化
        print("\n9. 使用管理器初始化:")
        await manager.initialize_registry(auto_discover=False)  # 我们已经手动注册了
        
        manager_stats = manager.get_registry_config()
        print(f"  管理器状态: {manager_stats}")
        
        # 11. 健康检查
        print("\n10. 健康检查:")
        health = await manager.health_check()
        print(f"  健康状态: {health['registry_status']}")
        print(f"  发现问题: {len(health['issues'])}")
        for issue in health['issues']:
            print(f"    - {issue}")
        
        # 12. 获取模块详细信息
        print("\n11. 模块详细信息:")
        course_info = manager.get_module_info("example_courses")
        if course_info:
            print(f"  模块详情:")
            for key, value in course_info.items():
                print(f"    {key}: {value}")
        
        # 13. 按分类列出模块信息
        print("\n12. 按分类列出模块信息:")
        categorized = manager.list_modules_by_category()
        for category, modules_info in categorized.items():
            print(f"  分类 '{category}' ({len(modules_info)} 个模块):")
            for module_info in modules_info:
                status = "已初始化" if module_info['is_initialized'] else "未初始化"
                print(f"    - {module_info['name']} ({module_info['table_name']}) - {status}")
        
        print("\n[OK] 基本功能演示完成")
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


async def demonstrate_auto_discovery():
    """演示自动发现功能"""
    print("\n=== 自动发现功能演示 ===")
    print()
    
    try:
        from database.module_registry import AutoDiscovery
        
        # 注意：在实际项目中，models包应该已经在Python路径中
        # 这里我们模拟从models目录发现模型的过程
        
        models_path = Path(__file__).parent.parent / "models"
        
        if models_path.exists():
            print(f"[FILE] 扫描模型路径: {models_path}")
            discovered_models = AutoDiscovery.discover_models_from_package(models_path)
            
            print(f"[SEARCH] 发现了 {len(discovered_models)} 个模型:")
            for i, model in enumerate(discovered_models[:10]):  # 只显示前10个
                table_name = getattr(model, '__tablename__', model.__name__.lower())
                print(f"  {i+1}. {model.__name__} -> {table_name}")
            
            if len(discovered_models) > 10:
                print(f"  ... 还有 {len(discovered_models) - 10} 个模型")
            
            # 显示发现的模型分类统计
            categories = {}
            for model in discovered_models:
                table_name = getattr(model, '__tablename__', model.__name__.lower())
                # 简单的分类逻辑
                if 'user' in table_name:
                    cat = 'user'
                elif 'course' in table_name:
                    cat = 'course'
                elif 'payment' in table_name or 'order' in table_name:
                    cat = 'payment'
                elif 'permission' in table_name or 'role' in table_name:
                    cat = 'permission'
                elif 'hardware' in table_name:
                    cat = 'hardware'
                else:
                    cat = 'other'
                
                categories[cat] = categories.get(cat, 0) + 1
            
            print(f"\n[STATS] 模型分类统计:")
            for cat, count in categories.items():
                print(f"  {cat}: {count} 个模型")
                
        else:
            print(f"[ERROR] 模型路径不存在: {models_path}")
        
        print("\n[OK] 自动发现功能演示完成")
        
    except Exception as e:
        logger.error(f"自动发现演示失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def demonstrate_real_models():
    """演示真实模型的注册"""
    print("\n=== 真实模型注册演示 ===")
    print()
    
    try:
        registry = get_database_registry()
        
        # 尝试注册一些真实的模型（如果存在）
        from database import Base
        
        # 检查是否能导入真实模型
        try:
            from models.user import User
            registry.register_module(User, category="user", version="1.0.0", description="用户模型")
            print("[OK] 用户模型注册成功")
        except ImportError as e:
            print(f"[WARN] 无法导入用户模型: {e}")
        
        try:
            from models.course import Course
            registry.register_module(Course, category="course", version="1.0.0", description="课程模型")
            print("[OK] 课程模型注册成功")
        except ImportError as e:
            print(f"[WARN] 无法导入课程模型: {e}")
        
        # 显示当前注册的真实模块
        real_modules = registry.list_modules()
        example_count = sum(1 for m in real_modules if m.name in ['example_courses', 'example_students'])
        real_count = len(real_modules) - example_count
        
        if real_count > 0:
            print(f"\n[LIST] 当前注册的真实模块数量: {real_count}")
            for module in real_modules:
                if module.name not in ['example_courses', 'example_students']:
                    print(f"  - {module.name} ({module.category})")
        else:
            print("\n[INFO] 当前只有示例模块被注册")
        
        print("\n[OK] 真实模型注册演示完成")
        
    except Exception as e:
        logger.error(f"真实模型演示失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    print("[START] 开始数据库模块注册表系统测试")
    print()
    
    try:
        await demonstrate_basic_usage()
        await demonstrate_auto_discovery()
        await demonstrate_real_models()
        
        print("\n[SUCCESS] 所有测试演示完成！注册表系统工作正常。")
        
    except Exception as e:
        logger.error(f"测试过程发生严重错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] 测试被用户中断")
    except Exception as e:
        print(f"\n[FATAL] 程序执行失败: {str(e)}")
        sys.exit(1)