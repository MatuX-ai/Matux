"""
添加课时数据到数据库
"""

from sqlalchemy import create_engine, text
from pathlib import Path
import json

db_path = Path(__file__).parent.parent / 'data' / 'ai_edu_standalone.db'
database_url = f"sqlite:///{db_path}"

engine = create_engine(database_url)

print("=" * 80)
print("AI-Edu 课时数据导入")
print("=" * 80)

# 读取课时文件
resource_path = Path(__file__).parent.parent / 'data' / 'ai-edu-resources' / 'modules'
lesson_files = list(resource_path.glob('lesson_*.json'))

print(f"\n找到 {len(lesson_files)} 个课时文件")

with engine.begin() as conn:
    for lesson_file in lesson_files:
        print(f"\n正在处理：{lesson_file.name}")
        
        with open(lesson_file, 'r', encoding='utf-8') as f:
            lesson_data = json.load(f)
        
        # 获取对应的模块 ID
        module_code = 'basic_concepts_01'  # 根据实际模块代码调整
        result = conn.execute(text(
            f"SELECT id FROM ai_edu_modules WHERE module_code = '{module_code}'"
        ))
        module_row = result.fetchone()
        
        if not module_row:
            print(f"  ⚠️  未找到对应的模块，跳过")
            continue
        
        module_id = module_row[0]
        print(f"  找到模块 ID: {module_id}")
        
        # 插入课时数据
        try:
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
            print(f"  ✅ 课时'{lesson_data.get('title', '')}'插入成功")
            
        except Exception as e:
            print(f"  ❌ 插入失败：{e}")

print("\n" + "=" * 80)
print("✅ 课时数据导入完成!")
print("=" * 80)
