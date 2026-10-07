"""检查数据库表结构"""
import sqlite3

conn = sqlite3.connect('ai_service.db')
cursor = conn.cursor()

# 获取所有表名
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("数据库中的表:")
for table in tables:
    print(f"  - {table[0]}")

# 检查 exam 相关表是否存在
exam_tables = ['exams', 'exam_questions', 'exam_attempts', 'cheat_events']
for table_name in exam_tables:
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    exists = cursor.fetchone()
    if exists:
        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"\n表 {table_name} 的列:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    else:
        print(f"\n表 {table_name} 不存在!")

conn.close()
