#!/usr/bin/env python3
"""
AI-Edu-for-Kids 简化版资源导入工具

这个版本独立于其他模块，避免 Role 模型冲突问题
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text

def main():
    print("=" * 80)
    print("AI-Edu-for-Kids 简化版资源导入工具")
    print("=" * 80)
    
    # 参数解析
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python scripts/simple_import_ai_edu.py <资源路径> [--execute]")
        print("\n示例:")
        print('  python scripts/simple_import_ai_edu.py "g:\\iMato\\data\\ai-edu-resources"')
        print('  python scripts/simple_import_ai_edu.py "g:\\iMato\\data\\ai-edu-resources" --execute')
        return 1
    
    resource_path = Path(sys.argv[1])
    execute_mode = '--execute' in sys.argv
    
    mode_str = "实际执行" if execute_mode else "预演"
    print(f"\n资源路径：{resource_path}")
    print(f"模式：{mode_str}")
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    # 连接数据库
    db_path = Path(__file__).parent.parent / 'data' / 'ai_edu_standalone.db'
    database_url = f"sqlite:///{db_path}"
    
    print("\n正在连接数据库...")
    engine = create_engine(database_url)
    print("✅ 数据库连接成功")
    
    # 统计信息
    stats = {
        'modules': 0,
        'lessons': 0,
        'errors': []
    }
    
    try:
        # 导入模块
        print(f"\n【{mode_str}】开始导入模块...")
        modules_dir = resource_path / 'modules'
        
        if not modules_dir.exists():
            print(f"⚠️  模块目录不存在：{modules_dir}")
        else:
            module_json = modules_dir / 'module.json'
            if module_json.exists():
                with open(module_json, 'r', encoding='utf-8') as f:
                    module_data = json.load(f)
                
                print(f"  📄 读取模块：{module_data.get('name', 'Unknown')}")
                
                if execute_mode:
                    # 插入模块数据
                    with engine.begin() as conn:  # 使用 begin() 自动管理事务
                        from sqlalchemy import insert
                        
                        stmt = text("""
                            INSERT INTO ai_edu_modules 
                            (module_code, name, description, category, grade_ranges, 
                             expected_lessons, expected_duration_minutes, is_active, display_order)
                            VALUES 
                            (:module_code, :name, :description, :category, :grade_ranges,
                             :expected_lessons, :expected_duration_minutes, :is_active, :display_order)
                        """)
                        
                        params = {
                            'module_code': module_data.get('module_code', ''),
                            'name': module_data.get('name', ''),
                            'description': module_data.get('description', ''),
                            'category': module_data.get('category', ''),
                            'grade_ranges': json.dumps(module_data.get('grade_ranges', [])),
                            'expected_lessons': module_data.get('expected_lessons', 0),
                            'expected_duration_minutes': module_data.get('expected_duration_minutes', 0),
                            'is_active': module_data.get('is_active', True),
                            'display_order': module_data.get('display_order', 0)
                        }
                        
                        conn.execute(stmt, params)
                        conn.commit()
                        print(f"  ✅ 模块插入成功")
                    
                    stats['modules'] = 1
                
                # 导入课时
                print(f"\n【{mode_str}】开始导入课时...")
                lesson_files = list(modules_dir.glob('lesson_*.json'))
                
                for lesson_file in lesson_files:
                    with open(lesson_file, 'r', encoding='utf-8') as f:
                        lesson_data = json.load(f)
                    
                    print(f"  📄 读取课时：{lesson_data.get('title', 'Unknown')}")
                    
                    if execute_mode:
                        with engine.begin() as conn:  # 使用 begin() 自动管理事务
                            # 先获取刚插入的模块 ID
                            result = conn.execute(text(
                                f"SELECT id FROM ai_edu_modules WHERE module_code = '{module_data.get('module_code', '')}'"
                            ))
                            module_row = result.fetchone()
                            
                            if module_row:
                                module_id = module_row[0]
                                
                                stmt = text("""
                                    INSERT INTO ai_edu_lessons
                                    (module_id, lesson_code, title, subtitle, content_type,
                                     resources, learning_objectives, knowledge_points,
                                     estimated_duration_minutes, has_quiz, quiz_passing_score,
                                     has_practice, practice_type, base_points, is_active, display_order)
                                    VALUES
                                    (:module_id, :lesson_code, :title, :subtitle, :content_type,
                                     :resources, :learning_objectives, :knowledge_points,
                                     :estimated_duration_minutes, :has_quiz, :quiz_passing_score,
                                     :has_practice, :practice_type, :base_points, :is_active, :display_order)
                                """)
                                
                                params = {
                                    'module_id': module_id,
                                    'lesson_code': lesson_data.get('lesson_code', ''),
                                    'title': lesson_data.get('title', ''),
                                    'subtitle': lesson_data.get('subtitle', ''),
                                    'content_type': lesson_data.get('content_type', ''),
                                    'resources': json.dumps(lesson_data.get('resources', [])),
                                    'learning_objectives': json.dumps(lesson_data.get('learning_objectives', [])),
                                    'knowledge_points': json.dumps(lesson_data.get('knowledge_points', [])),
                                    'estimated_duration_minutes': lesson_data.get('estimated_duration_minutes', 0),
                                    'has_quiz': lesson_data.get('has_quiz', False),
                                    'quiz_passing_score': lesson_data.get('quiz_passing_score', 60.0),
                                    'has_practice': lesson_data.get('has_practice', False),
                                    'practice_type': lesson_data.get('practice_type'),
                                    'base_points': lesson_data.get('base_points', 20),
                                    'is_active': lesson_data.get('is_active', True),
                                    'display_order': lesson_data.get('display_order', 0)
                                }
                                
                                conn.execute(stmt, params)
                                conn.commit()
                                print(f"  ✅ 课时插入成功")
                                
                                stats['lessons'] += 1
                            else:
                                print(f"  ❌ 找不到对应的模块，跳过此课时")
            
            else:
                print(f"⚠️  未找到 module.json 文件")
        
        # 打印统计
        print("\n" + "=" * 80)
        print("导入统计")
        print("=" * 80)
        print(f"模块数量：{stats['modules']}")
        print(f"课时数量：{stats['lessons']}")
        print(f"失败总数：{len(stats['errors'])}")
        
        if stats['errors']:
            print("\n错误详情:")
            for error in stats['errors']:
                print(f"  - {error}")
        
        elapsed = (datetime.now() - datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')).total_seconds()
        print(f"\n耗时：{elapsed:.2f}秒")
        print(f"完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not execute_mode:
            print("\n💡 提示：当前为预演模式，数据未实际写入数据库")
            print("   添加 --execute 参数执行实际导入")
        
        print("\n" + "=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 导入过程出错：{e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
