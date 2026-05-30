"""
导入新增的课程模块 (module_02, module_03)
"""

from sqlalchemy import create_engine, text
from pathlib import Path
import json

db_path = Path(__file__).parent.parent / 'data' / 'ai_edu_standalone.db'
database_url = f"sqlite:///{db_path}"

engine = create_engine(database_url)

print("=" * 80)
print("AI-Edu 新增课程模块导入")
print("=" * 80)

# 读取所有新模块
modules_dir = Path(__file__).parent.parent / 'data' / 'ai-edu-resources' / 'modules'
module_folders = [f for f in modules_dir.iterdir() if f.is_dir() and f.name.startswith('module_')]

print(f"\n找到 {len(module_folders)} 个模块目录")

with engine.begin() as conn:
    for module_folder in module_folders:
        print(f"\n{'='*60}")
        print(f"处理模块：{module_folder.name}")
        
        # 读取 module.json
        module_json = module_folder / 'module.json'
        if not module_json.exists():
            print(f"  ⚠️  跳过：未找到 module.json")
            continue
        
        with open(module_json, 'r', encoding='utf-8') as f:
            module_data = json.load(f)
        
        print(f"  📄 模块名称：{module_data.get('name', 'Unknown')}")
        
        # 插入或更新模块
        try:
            # 检查是否已存在
            result = conn.execute(text(
                "SELECT id FROM ai_edu_modules WHERE module_code = :code"
            ), {'code': module_data.get('module_code', '')})
            
            existing = result.fetchone()
            
            if existing:
                print(f"  ℹ️  模块已存在，ID: {existing[0]}")
                module_id = existing[0]
            else:
                # 插入新模块
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
                
                # 获取刚插入的 ID
                result = conn.execute(text(
                    "SELECT last_insert_rowid()"
                ))
                module_id = result.scalar()
                print(f"  ✅ 模块插入成功，ID: {module_id}")
            
            # 读取并插入课时
            lesson_files = list(module_folder.glob('lesson_*.json'))
            print(f"  📚 找到 {len(lesson_files)} 个课时文件")
            
            for lesson_file in lesson_files:
                with open(lesson_file, 'r', encoding='utf-8') as f:
                    lesson_data = json.load(f)
                
                # 检查课时是否已存在
                result = conn.execute(text(
                    "SELECT id FROM ai_edu_lessons WHERE lesson_code = :code"
                ), {'code': lesson_data.get('lesson_code', '')})
                
                if result.fetchone():
                    print(f"    ⏭️  跳过课时：{lesson_data.get('title', 'Unknown')} (已存在)")
                    continue
                
                # 插入课时
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
                print(f"    ✅ 课时插入成功：{lesson_data.get('title', 'Unknown')}")
        
        except Exception as e:
            print(f"  ❌ 处理失败：{e}")
            import traceback
            traceback.print_exc()

print("\n" + "=" * 80)
print("✅ 所有模块导入完成!")
print("=" * 80)
