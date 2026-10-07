#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时验证脚本：列出 ai_service.db 所有表和行数"""
import sqlite3
import sys

DB = sys.argv[1] if len(sys.argv) > 1 else "ai_service.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print(f"Total tables: {len(tables)}")
print("=" * 60)
for t in tables:
    try:
        cur2 = conn.cursor()
        cur2.execute(f"SELECT COUNT(*) FROM {t}")
        n = cur2.fetchone()[0]
        print(f"  {t}: {n} rows")
    except Exception as e:
        print(f"  {t}: ERROR ({e})")
conn.close()