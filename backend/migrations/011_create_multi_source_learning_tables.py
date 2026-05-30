"""
学生多来源学习关联管理系统数据库迁移脚本
创建学习来源、用户-组织关联、统一学习记录等相关数据表

迁移时间: 2026-03-18
版本: 011

使用方法:
    cd backend
    set PYTHONPATH=.
    python -c "from migrations.v011_create_multi_source_learning_tables import run_migration; run_migration()"
"""

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


def get_database_url():
    """从配置获取数据库URL"""
    try:
        from config.settings import settings
        # 返回同步数据库URL
        db_url = settings.DATABASE_URL
        # 如果是 aiosqlite，转换为普通 sqlite
        if db_url.startswith('sqlite+aiosqlite'):
            db_url = db_url.replace('sqlite+aiosqlite', 'sqlite')
        return db_url
    except Exception as e:
        logger.warning(f"无法从配置获取数据库URL: {e}")
        # 使用默认的SQLite
        return "sqlite:///./imato.db"


def run_migration():
    """执行迁移"""
    db_url = get_database_url()
    logger.info(f"使用数据库: {db_url}")
    
    engine = create_engine(db_url, echo=True)
    
    with engine.connect() as conn:
        # 1. 创建 learning_sources 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS learning_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                org_id INTEGER,
                source_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                name VARCHAR(255) NOT NULL,
                source_detail TEXT DEFAULT '{}',
                start_date DATE,
                end_date DATE,
                role VARCHAR(50) DEFAULT 'student',
                is_primary BOOLEAN DEFAULT 0,
                notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 2. 创建 user_organizations 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                org_id INTEGER,
                learning_source_type VARCHAR(50),
                role VARCHAR(50) DEFAULT 'student',
                is_primary BOOLEAN DEFAULT 0,
                status VARCHAR(20) DEFAULT 'active',
                member_id VARCHAR(100),
                class_name VARCHAR(100),
                department VARCHAR(100),
                start_date DATE,
                end_date DATE,
                extra_data TEXT DEFAULT '{}',
                notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 3. 创建 unified_learning_records 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS unified_learning_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id INTEGER,
                learning_source_id INTEGER NOT NULL,
                enrollment_id INTEGER,
                status VARCHAR(20) DEFAULT 'not_started',
                progress_percentage REAL DEFAULT 0.0,
                total_time_minutes INTEGER DEFAULT 0,
                score REAL,
                max_score REAL DEFAULT 100.0,
                grade_letter VARCHAR(5),
                completion_date TIMESTAMP,
                certificate_url VARCHAR(500),
                activity_detail TEXT DEFAULT '{}',
                notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 4. 为 course_enrollments 添加 learning_source_id 字段
        try:
            conn.execute(text("""
                ALTER TABLE course_enrollments 
                ADD COLUMN learning_source_id INTEGER
            """))
        except Exception as e:
            logger.info(f"字段可能已存在: {e}")
        
        # 5. 创建索引
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ls_user_type ON learning_sources(user_id, source_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ls_user_org ON learning_sources(user_id, org_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_uo_user_org ON user_organizations(user_id, org_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_uo_user_type ON user_organizations(user_id, learning_source_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ulr_user_source ON unified_learning_records(user_id, learning_source_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ulr_user_course ON unified_learning_records(user_id, course_id)"))
        
        conn.commit()
    
    logger.info("数据库迁移完成!")
    return True


def drop_tables():
    """删除表（用于测试）"""
    db_url = get_database_url()
    engine = create_engine(db_url, echo=True)
    
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS unified_learning_records"))
        conn.execute(text("DROP TABLE IF EXISTS user_organizations"))
        conn.execute(text("DROP TABLE IF EXISTS learning_sources"))
        conn.commit()
    
    logger.info("表已删除!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        drop_tables()
    else:
        run_migration()
