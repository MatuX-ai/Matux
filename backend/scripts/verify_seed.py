#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 test_student 的冷启动数据完整性"""
import sqlite3

DB = "ai_service.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

print("=" * 70)
print("test_student 冷启动数据完整性验证")
print("=" * 70)

# test_student user_id
cur.execute("SELECT id, username FROM users WHERE username='test_student'")
row = cur.fetchone()
student_id = row[0]
print(f"\n[Test Student] ID={student_id}, username={row[1]}")

# Organization
cur.execute("SELECT id, name, code FROM organizations")
print(f"\n[Organizations] {cur.fetchall()}")

# User-Org associations
cur.execute("SELECT user_id, org_id, role, is_primary FROM user_organizations")
print(f"\n[UserOrgs] {cur.fetchall()}")

# Learning sources
cur.execute(f"""
    SELECT id, name, source_type, is_primary FROM learning_sources
    WHERE user_id = {student_id}
""")
print(f"\n[Learning Sources for student]")
for r in cur.fetchall():
    print(f"  - {r}")

# Courses
cur.execute("SELECT id, title, category, difficulty, status FROM courses")
print(f"\n[Courses] ({cur.rowcount})")
for r in cur.fetchall():
    print(f"  - [{r[0]}] {r[1]} ({r[2]}/{r[3]}) - {r[4]}")

# Lessons
cur.execute("SELECT course_id, COUNT(*) FROM course_lessons GROUP BY course_id")
print(f"\n[Lessons per course]")
for r in cur.fetchall():
    print(f"  - course {r[0]}: {r[1]} lessons")

# Enrollments
cur.execute(f"""
    SELECT c.title, e.progress, e.status, e.enrollment_date
    FROM course_enrollments e
    JOIN courses c ON c.id = e.course_id
    WHERE e.user_id = {student_id}
""")
print(f"\n[Enrollments for test_student]")
for r in cur.fetchall():
    print(f"  - {r[0]}: progress={r[1]}%, status={r[2]}, date={r[3]}")

# Assignments
cur.execute("SELECT course_id, COUNT(*) FROM course_assignments GROUP BY course_id")
print(f"\n[Assignments per course]")
for r in cur.fetchall():
    print(f"  - course {r[0]}: {r[1]} assignments")

# Learning records (最近 30 天)
cur.execute(f"""
    SELECT DATE(start_time), COUNT(*), SUM(duration_minutes)
    FROM unified_learning_records
    WHERE user_id = {student_id}
    GROUP BY DATE(start_time)
    ORDER BY DATE(start_time) DESC
""")
print(f"\n[Learning Records by day (test_student)]")
total_records = 0
total_minutes = 0
for r in cur.fetchall():
    print(f"  - {r[0]}: {r[1]} records, {r[2]} min")
    total_records += r[1]
    total_minutes += r[2] or 0
print(f"  TOTAL: {total_records} records, {total_minutes} minutes")

# 汇总
print()
print("=" * 70)
print("汇总")
print("=" * 70)
cur.execute(f"SELECT COUNT(*) FROM courses")
print(f"  courses 总数: {cur.fetchone()[0]}")
cur.execute(f"SELECT COUNT(*) FROM course_enrollments WHERE user_id = {student_id}")
print(f"  test_student 报名数: {cur.fetchone()[0]}")
cur.execute(f"SELECT COUNT(*) FROM course_lessons")
print(f"  course_lessons 总数: {cur.fetchone()[0]}")
cur.execute(f"SELECT COUNT(*) FROM course_assignments")
print(f"  course_assignments 总数: {cur.fetchone()[0]}")
cur.execute(f"SELECT COUNT(*) FROM learning_sources WHERE user_id = {student_id}")
print(f"  test_student 学习来源数: {cur.fetchone()[0]}")
cur.execute(f"SELECT COUNT(*) FROM unified_learning_records WHERE user_id = {student_id}")
print(f"  test_student 学习记录数: {cur.fetchone()[0]}")
cur.execute(f"SELECT COUNT(*) FROM organizations")
print(f"  组织总数: {cur.fetchone()[0]}")
cur.execute(f"SELECT COUNT(*) FROM user_organizations WHERE user_id = {student_id}")
print(f"  test_student 用户-组织关联数: {cur.fetchone()[0]}")

conn.close()