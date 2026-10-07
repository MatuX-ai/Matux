#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看 organizations 表的列名"""
import sqlite3

DB = "ai_service.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("PRAGMA table_info(organizations)")
cols = cur.fetchall()
print("Columns:", cols)
print()
cur.execute("SELECT * FROM organizations LIMIT 3")
rows = cur.fetchall()
for row in rows:
    print("Row:", row)
conn.close()