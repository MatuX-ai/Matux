"""检查测验数据"""
import sqlite3

conn = sqlite3.connect('ai_service.db')
cursor = conn.cursor()

# 检查 exams 表
print("=== exams 表数据 ===")
cursor.execute("SELECT id, title, status, total_questions FROM exams")
exams = cursor.fetchall()
for e in exams:
    print(f"  ID={e[0]}, title={e[1]}, status={e[2]}, questions={e[3]}")

if not exams:
    print("  没有测验数据!")

# 检查 exam_questions 表
print("\n=== exam_questions 表数据 ===")
cursor.execute("SELECT id, exam_id, question_type, title FROM exam_questions LIMIT 10")
questions = cursor.fetchall()
for q in questions:
    print(f"  ID={q[0]}, exam_id={q[1]}, type={q[2]}, title={q[3][:50]}...")

if not questions:
    print("  没有题目数据!")

# 检查 exam_attempts 表
print("\n=== exam_attempts 表数据 ===")
cursor.execute("SELECT id, exam_id, user_id, status FROM exam_attempts")
attempts = cursor.fetchall()
for a in attempts:
    print(f"  ID={a[0]}, exam_id={a[1]}, user_id={a[2]}, status={a[3]}")

if not attempts:
    print("  没有答题记录!")

conn.close()
