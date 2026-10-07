"""检查exam相关表"""
from sqlalchemy import text
from utils.database import get_sync_db
import sys
sys.path.insert(0, '.')


db_gen = get_sync_db()
db = next(db_gen)
try:
    # 检查表
    result = db.execute(
        text("SELECT name FROM sqlite_master WHERE type='table'"))
    tables = [row[0] for row in result.fetchall()]
    print('Tables:', tables)

    # 检查exam_attempts表结构
    if 'exam_attempts' in tables:
        result = db.execute(text("PRAGMA table_info(exam_attempts)"))
        columns = [row[1] for row in result.fetchall()]
        print('exam_attempts columns:', columns)
    else:
        print('exam_attempts table NOT FOUND')
finally:
    next(db_gen, None)
