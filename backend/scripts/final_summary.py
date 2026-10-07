#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终数据汇总报告 - 用于生成 UI_UPGRADE_AND_SEED_REPORT"""
import sqlite3
import json
import sys

DB = "ai_service.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

# test_student user_id
cur.execute("SELECT id, username FROM users WHERE username='test_student'")
row = cur.fetchone()
student_id = row[0]

# 收集数据
data = {}

# Core tables
for table in ["organizations", "users", "user_organizations", "learning_sources",
              "courses", "course_lessons", "course_enrollments", "course_assignments",
              "unified_learning_records"]:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    data[table] = cur.fetchone()[0]

# test_student specific
for table in ["learning_sources", "course_enrollments", "unified_learning_records"]:
    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id = {student_id}")
    data[f"{table}_for_student"] = cur.fetchone()[0]

# Optional tables (achievement/leaderboard/recommendation) - check existence
optional_tables = ["achievements", "user_achievements", "user_points",
                    "point_transactions", "leaderboards", "leaderboard_entries",
                    "daily_tasks", "ai_recommendations"]
for table in optional_tables:
    cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    if cur.fetchone():
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        data[f"{table}_count"] = cur.fetchone()[0]
    else:
        data[f"{table}_count"] = "table_missing"

# Enrollment status for student
cur.execute(f"""
    SELECT c.title, e.progress_percentage, e.score, e.status
    FROM course_enrollments e
    JOIN courses c ON c.id = e.course_id
    WHERE e.user_id = {student_id}
    ORDER BY e.enrolled_at DESC
""")
data["enrollments_detail"] = [
    {"course": r[0], "progress": r[1], "score": r[2], "status": r[3]}
    for r in cur.fetchall()
]

# Course stats
cur.execute("""
    SELECT category, COUNT(*) FROM courses GROUP BY category
""")
data["course_by_category"] = {r[0]: r[1] for r in cur.fetchall()}

cur.execute("""
    SELECT difficulty, COUNT(*) FROM courses GROUP BY difficulty
""")
data["course_by_difficulty"] = {r[0]: r[1] for r in cur.fetchall()}

# Learning records by day (last 30)
cur.execute(f"""
    SELECT DATE(completion_date), COUNT(*), SUM(total_time_minutes)
    FROM unified_learning_records
    WHERE user_id = {student_id} AND completion_date IS NOT NULL
    GROUP BY DATE(completion_date)
    ORDER BY DATE(completion_date)
""")
data["learning_by_day"] = [
    {"date": r[0], "records": r[1], "minutes": r[2] or 0}
    for r in cur.fetchall()
]

# Course lesson distribution
cur.execute("""
    SELECT c.title, COUNT(cl.id)
    FROM courses c LEFT JOIN course_lessons cl ON cl.course_id = c.id
    GROUP BY c.id ORDER BY c.id
""")
data["lessons_per_course"] = [
    {"course": r[0], "lessons": r[1]} for r in cur.fetchall()
]

print(json.dumps(data, ensure_ascii=False, indent=2, default=str))

conn.close()