"""检查用户"""
import sqlite3

conn = sqlite3.connect('ai_service.db')
cursor = conn.cursor()

# 检查用户
cursor.execute("SELECT id, username, email, role FROM users LIMIT 5")
users = cursor.fetchall()
print("=== 用户列表 ===")
for u in users:
    print(f"ID={u[0]}, username={u[1]}, email={u[2]}, role={u[3]}")

conn.close()
