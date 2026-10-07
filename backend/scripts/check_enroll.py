#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 course_enrollments 表结构"""
import sqlite3
conn = sqlite3.connect("ai_service.db")
cur = conn.cursor()
cur.execute("PRAGMA table_info(course_enrollments)")
print("course_enrollments columns:")
for r in cur.fetchall():
    print(f"  {r}")
print()
cur.execute("PRAGMA table_info(unified_learning_records)")
print("unified_learning_records columns:")
for r in cur.fetchall():
    print(f"  {r}")
print()
cur.execute("SELECT * FROM course_enrollments")
print("course_enrollments rows:")
for r in cur.fetchall():
    print(f"  {r}")
conn.close()