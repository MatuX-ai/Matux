import sqlite3

conn = sqlite3.connect('ai_service.db')
cursor = conn.cursor()

# 列出所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('数据库表:')
tables = cursor.fetchall()
for row in tables:
    print(f'  - {row[0]}')

# 检查 exam_attempts 表
print('\n检查 exam 表:')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%exam%'")
for row in cursor.fetchall():
    print(f'  - {row[0]}')

# 列出所有表
all_tables = [t[0] for t in tables]
if 'exam_attempts' in all_tables:
    cursor.execute('SELECT id, exam_id, user_id, status, started_at FROM exam_attempts ORDER BY id DESC LIMIT 5')
    print('\nexam_attempts 表记录:')
    print('ID | Exam | User | Status | Started At')
    print('-' * 60)
    for row in cursor.fetchall():
        print(f'{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}')
elif 'exams' in all_tables:
    cursor.execute('SELECT id, title, status, created_at FROM exams LIMIT 5')
    print('\nexams 表记录:')
    for row in cursor.fetchall():
        print(f'  {row}')
else:
    print('\n未找到 exams 相关表')

conn.close()
