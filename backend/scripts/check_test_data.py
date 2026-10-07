#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看关键测试账号和组织是否存在"""
import sqlite3

DB = "ai_service.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

print("=== Users ===")
cur.execute("SELECT id, username, email, role FROM users")
for row in cur.fetchall():
    print(f"  {row}")

print()
print("=== Organizations ===")
cur.execute("SELECT id, name, contact_email FROM organizations")
for row in cur.fetchall():
    print(f"  {row}")

print()
print("=== UserOrganizations ===")
cur.execute("SELECT id, user_id, org_id, role, is_primary FROM user_organizations")
for row in cur.fetchall():
    print(f"  {row}")

conn.close()