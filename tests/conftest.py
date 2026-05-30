"""
pytest全局配置和fixture

提供测试所需的通用配置、fixture和工具函数
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 设置测试环境变量
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["DEBUG"] = "false"

# 全局配置fixture
@pytest.fixture(scope="session")
def test_config():
    """测试全局配置"""
    return {
        "database_url": "sqlite+aiosqlite:///./test.db",
        "api_base_url": "http://localhost:8000",
        "test_data_dir": os.path.join(os.path.dirname(__file__), "data"),
        "max_concurrent_tests": 4,
        "test_timeout": 30
    }

# 数据库相关fixture
@pytest.fixture(scope="session")
def async_engine():
    """异步数据库引擎"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///./test.db",
        echo=False,
        pool_pre_ping=True
    )
    yield engine
    engine.sync_engine.dispose()

@pytest.fixture
async def async_session(async_engine):
    """异步数据库会话"""
    async_session_factory = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_factory() as session:
        yield session
        await session.rollback()

# 文件操作fixture
@pytest.fixture
def temp_file():
    """临时文件fixture"""
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    yield temp_file.name
    temp_file.close()
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)

@pytest.fixture
def temp_directory():
    """临时目录fixture"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

# Mock服务fixture
@pytest.fixture
def mock_http_client():
    """模拟HTTP客户端"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = Mock()
        mock_instance.get = AsyncMock()
        mock_instance.post = AsyncMock()
        mock_instance.put = AsyncMock()
        mock_instance.delete = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_redis_client():
    """模拟Redis客户端"""
    with patch('redis.asyncio.Redis') as mock_redis:
        mock_instance = Mock()
        mock_instance.get = AsyncMock()
        mock_instance.set = AsyncMock()
        mock_instance.delete = AsyncMock()
        mock_instance.exists = AsyncMock()
        mock_redis.return_value = mock_instance
        yield mock_instance

# 测试数据生成工具
class TestDataGenerator:
    """测试数据生成器"""
    
    @staticmethod
    def create_user_data(**kwargs):
        """生成用户测试数据"""
        base_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password': 'testpassword123',
            'role': 'student'
        }
        base_data.update(kwargs)
        return base_data
    
    @staticmethod
    def create_course_data(**kwargs):
        """生成课程测试数据"""
        base_data = {
            'title': 'Test Course',
            'description': 'Test course description',
            'category': 'programming',
            'difficulty': 'beginner',
            'duration': 60
        }
        base_data.update(kwargs)
        return base_data
    
    @staticmethod
    def create_csv_content(rows, headers=None):
        """生成CSV内容"""
        import csv
        import io
        
        if headers is None:
            headers = ['username', 'email', 'full_name', 'role']
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        
        return output.getvalue()

# 性能测试工具
class PerformanceTimer:
    """性能计时器"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """开始计时"""
        import time
        self.start_time = time.time()
        return self
    
    def stop(self):
        """停止计时"""
        import time
        self.end_time = time.time()
        return self
    
    @property
    def elapsed(self):
        """获取耗时（秒）"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
    
    @property
    def elapsed_ms(self):
        """获取耗时（毫秒）"""
        return self.elapsed * 1000

# 自定义标记
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "database: marks tests that require database access"
    )

# 测试报告钩子
def pytest_runtest_makereport(item, call):
    """测试执行报告钩子"""
    if call.when == "call":
        # 记录测试执行时间
        setattr(item, "duration", call.stop - call.start)

# 并行测试配置
def pytest_xdist_setupnodes(config, specs):
    """分布式测试节点设置"""
    # 可以在这里配置不同节点的环境
    pass

# 测试清理钩子
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_teardown(item):
    """测试清理钩子"""
    # 清理可能的副作用
    pass