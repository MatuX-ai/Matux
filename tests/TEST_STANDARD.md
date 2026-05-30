# 测试文件标准化规范

## 测试文件命名规范

### Python测试文件
```
test_[模块名].py                    # 单元测试
test_[模块名]_[功能].py             # 特定功能测试
integration_test_[模块名].py        # 集成测试
performance_test_[模块名].py        # 性能测试
```

### JavaScript/TypeScript测试文件
```
[组件名].test.ts                    # 单元测试
[组件名].spec.ts                    # 规范测试
integration.test.ts                 # 集成测试
```

### 测试脚本文件
```
[功能名]_test_script.py             # 测试脚本
[功能名]_validation.py              # 验证脚本
```

## 目录结构规范

```
/tests/
├── __init__.py                     # 包初始化文件
├── conftest.py                     # pytest配置文件
├── core/                          # 核心服务测试
│   ├── __init__.py
│   ├── test_user_management.py
│   ├── test_authentication.py
│   ├── test_authorization.py
│   └── test_tenant_isolation.py
├── ai/                            # AI服务测试
│   ├── __init__.py
│   ├── test_ai_service.py
│   ├── test_code_completion.py
│   ├── test_creativity_engine.py
│   └── test_dynamic_course.py
├── hardware/                      # 硬件集成测试
│   ├── __init__.py
│   ├── test_hardware_certification.py
│   ├── test_hardware_api.py
│   └── test_hardware_acceleration.py
├── blockchain/                    # 区块链测试
│   ├── __init__.py
│   ├── test_blockchain_api.py
│   ├── test_smart_contracts.py
│   └── test_gateway_integration.py
├── multimedia/                    # 多媒体测试
│   ├── __init__.py
│   ├── test_multimedia_support.py
│   └── test_content_storage.py
├── performance/                   # 性能测试
│   ├── __init__.py
│   ├── test_concurrent_access.py
│   ├── test_load_performance.py
│   └── test_stress_testing.py
└── security/                      # 安全测试
    ├── __init__.py
    ├── test_security_scanning.py
    ├── test_permission_validation.py
    └── test_data_protection.py
```

## 测试文件内容模板

### Python单元测试模板
```python
"""
[模块名]模块单元测试

测试覆盖:
- [功能点1]
- [功能点2]
- [边界条件]
"""

import pytest
from unittest.mock import Mock, patch
from [模块路径] import [被测试类/函数]

class Test[模块名]:
    """[模块名]测试类"""
    
    def setup_method(self):
        """测试前置条件"""
        self.[测试对象] = [被测试类]()
        
    def teardown_method(self):
        """测试后置清理"""
        pass
    
    def test_[功能描述](self):
        """测试[具体功能]"""
        # 准备测试数据
        test_input = [输入数据]
        
        # 执行测试
        result = self.[测试对象].[方法名](test_input)
        
        # 验证结果
        assert [期望结果] == result
        
    def test_[边界条件](self):
        """测试边界条件"""
        # 测试边界情况
        with pytest.raises([期望异常]):
            self.[测试对象].[方法名]([边界输入])
```

### 集成测试模板
```python
"""
[模块名]集成测试

测试服务间交互和完整业务流程
"""

import pytest
from [服务模块] import [服务类]

class Test[IntegrationName]Integration:
    """集成测试类"""
    
    @pytest.fixture
    def setup_services(self):
        """设置测试服务"""
        # 初始化相关服务
        service1 = [Service1]()
        service2 = [Service2]()
        return service1, service2
    
    def test_[业务流程](self, setup_services):
        """测试完整业务流程"""
        service1, service2 = setup_services
        
        # 执行业务流程
        result1 = service1.[方法]()
        result2 = service2.[方法](result1)
        
        # 验证最终结果
        assert [期望结果] == result2
```

### 性能测试模板
```python
"""
[模块名]性能测试

基准性能指标:
- 响应时间: < [时间]ms
- 吞吐量: > [请求数]/s
- 并发支持: [并发数] users
"""

import time
import pytest
from [模块] import [被测试对象]

class Test[PerformanceName]Performance:
    """性能测试类"""
    
    def test_response_time(self):
        """测试响应时间"""
        start_time = time.time()
        
        # 执行操作
        result = [被测试对象].[方法]()
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # 转换为毫秒
        
        assert response_time < [阈值], f"响应时间 {response_time}ms 超过阈值"
        
    def test_throughput(self):
        """测试吞吐量"""
        start_time = time.time()
        request_count = 0
        
        # 批量执行请求
        for i in range([测试次数]):
            [被测试对象].[方法]()
            request_count += 1
            
        end_time = time.time()
        duration = end_time - start_time
        throughput = request_count / duration
        
        assert throughput > [阈值], f"吞吐量 {throughput} req/s 低于阈值"
```

## 测试配置文件

### pytest配置 (conftest.py)
```python
"""
pytest全局配置和fixture
"""

import pytest
import os
from unittest.mock import Mock

# 全局fixture
@pytest.fixture(scope="session")
def test_config():
    """测试配置"""
    return {
        "database_url": "sqlite:///test.db",
        "api_base_url": "http://localhost:8000",
        "test_data_dir": "tests/data"
    }

@pytest.fixture
def mock_database():
    """模拟数据库连接"""
    mock_db = Mock()
    mock_db.execute.return_value = []
    return mock_db

# 测试环境变量
os.environ["TESTING"] = "true"
os.environ["DEBUG"] = "false"
```

## 测试执行规范

### 命令行执行
```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/core/

# 运行特定测试文件
pytest tests/core/test_user_management.py

# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 并行执行测试
pytest -n auto
```

### CI/CD集成
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=backend --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 质量保证检查清单

### 测试编写检查
- [ ] 测试用例覆盖核心功能
- [ ] 包含边界条件测试
- [ ] 使用适当的mock和stub
- [ ] 测试数据准备充分
- [ ] 断言条件明确具体

### 测试执行检查
- [ ] 所有测试通过
- [ ] 无警告信息
- [ ] 执行时间合理
- [ ] 资源清理完整
- [ ] 并发安全性验证

### 维护性检查
- [ ] 命名规范统一
- [ ] 代码结构清晰
- [ ] 注释说明完整
- [ ] 依赖关系明确
- [ ] 易于扩展修改

---
*iMatu测试标准化规范 | 版本 v1.0 | 最后更新 2026年3月*