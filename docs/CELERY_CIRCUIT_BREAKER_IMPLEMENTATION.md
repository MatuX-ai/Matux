# Celery任务熔断器实现文档

## 概述

本文档详细描述了iMato项目中Celery任务超时熔断机制的实现方案。该机制为异步任务提供了超时控制和熔断降级能力，默认超时时间为30秒。

## 架构设计

### 核心组件

#### 1. CeleryTaskCircuitBreaker (核心熔断器)
位于: `backend/middleware/celery_circuit_breaker.py`

**主要功能:**
- 任务执行状态监控
- 超时检测和记录
- 失败率计算
- 状态机管理 (CLOSED → OPEN → HALF_OPEN)

**状态转换逻辑:**
```
CLOSED (正常) → OPEN (熔断) → HALF_OPEN (半开) → CLOSED (恢复)
```

#### 2. TaskCircuitBreakerManager (管理器)
负责管理所有任务的熔断器实例，提供统一的配置和状态查询接口。

#### 3. CircuitBreakerTask (任务基类)
继承自Celery的Task类，提供自动化的熔断器集成。

#### 4. 监控服务
- `CeleryMonitoringService`: 提供API接口查询熔断器状态
- Prometheus指标收集: 任务执行时间、失败率、超时次数等

## 配置参数

### 全局默认配置 (settings.py)
```python
# Celery任务熔断器配置
CELERY_TASK_CIRCUIT_BREAKER_ENABLED: bool = True
CELERY_TASK_DEFAULT_TIMEOUT: int = 30      # 秒，默认任务超时时间
CELERY_TASK_SOFT_TIMEOUT: int = 25         # 秒，默认软超时时间
CELERY_TASK_HARD_TIMEOUT: int = 60         # 秒，默认硬超时时间
CELERY_TASK_FAILURE_THRESHOLD: int = 3     # 任务失败阈值
CELERY_TASK_CIRCUIT_TIMEOUT: int = 30      # 秒，熔断超时时间
CELERY_TASK_HALF_OPEN_ATTEMPTS: int = 2    # 半开状态尝试次数
CELERY_ENABLE_TIMEOUT_PROTECTION: bool = True
CELERY_ENABLE_FAILURE_PROTECTION: bool = True
```

### 任务级别配置
可通过装饰器为特定任务定制配置：
```python
@task_circuit_breaker(
    failure_threshold=5,
    timeout=30,
    soft_time_limit=25,
    time_limit=60,
    half_open_attempts=3
)
def my_task():
    pass
```

## 实现细节

### 1. 超时处理机制

**软超时 (Soft Timeout):**
- 任务收到SIGUSR1信号
- 允许任务优雅处理和清理
- 不会强制终止进程

**硬超时 (Hard Timeout):**
- 任务收到SIGTERM信号
- 强制终止任务执行
- 可能导致数据不一致

### 2. 熔断策略

**失败检测:**
- 自动识别任务异常类型
- 区分预期异常（如超时）和非预期异常
- 只有非预期异常会计入失败统计

**状态转换条件:**
- CLOSED → OPEN: 连续失败次数 ≥ 失败阈值
- OPEN → HALF_OPEN: 熔断超时时间到达
- HALF_OPEN → CLOSED: 连续成功次数 ≥ 半开尝试次数
- HALF_OPEN → OPEN: 出现任何失败

### 3. 监控指标

**Prometheus指标:**
```python
# 任务请求总数
celery_task_circuit_breaker_requests_total

# 任务失败率
celery_task_circuit_breaker_failure_rate

# 熔断器状态
celery_task_circuit_breaker_state

# 任务执行耗时
celery_task_circuit_breaker_duration_seconds

# 任务超时次数
celery_task_timeouts_total
```

## API接口

### 监控端点

**获取所有任务状态:**
```
GET /api/v1/celery-monitoring/states
```

**获取特定任务状态:**
```
GET /api/v1/celery-monitoring/states/{task_name}
```

**重置任务熔断器:**
```
POST /api/v1/celery-monitoring/reset/{task_name}
```

**配置任务参数:**
```
PUT /api/v1/celery-monitoring/configure/{task_name}
```

**获取全局统计:**
```
GET /api/v1/celery-monitoring/statistics
```

## 使用示例

### 1. 基础使用
```python
from middleware.celery_circuit_breaker import task_circuit_breaker

@task_circuit_breaker()
def process_video(video_id):
    # 任务逻辑
    pass
```

### 2. 自定义配置
```python
@task_circuit_breaker(
    failure_threshold=10,    # 更高的失败容忍度
    timeout=60,              # 更长的熔断时间
    soft_time_limit=45,      # 更长的软超时
    time_limit=90            # 更长的硬超时
)
def heavy_computation(data):
    # 重量级计算任务
    pass
```

### 3. 禁用特定保护
```python
@task_circuit_breaker(
    enable_timeout_protection=False,  # 禁用超时保护
    enable_failure_protection=True    # 保留失败保护
)
def critical_operation():
    # 关键操作，不允许因超时被熔断
    pass
```

## 部署配置

### 环境变量配置
```bash
# Celery配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# 熔断器配置
CELERY_TASK_CIRCUIT_BREAKER_ENABLED=true
CELERY_TASK_DEFAULT_TIMEOUT=30
CELERY_TASK_FAILURE_THRESHOLD=3
```

### Worker启动参数
```bash
celery -A celery_app worker \
    --loglevel=info \
    --pool=prefork \
    --concurrency=4 \
    --max-tasks-per-child=1000 \
    --prefetch-multiplier=1
```

## 性能考虑

### 1. 内存使用
- 每个任务维护独立的熔断器实例
- 状态信息定期清理
- 支持大量并发任务

### 2. 性能影响
- 状态检查开销：< 1ms
- 监控指标收集频率: 每次任务执行
- 对正常任务执行影响最小

### 3. 扩展性
- 支持水平扩展
- 熔断器状态可持久化
- 支持分布式部署

## 故障排除

### 常见问题

**1. 任务频繁被熔断**
- 检查任务实际执行时间
- 调整超时配置
- 分析失败原因

**2. 熔断器不工作**
- 确认配置已启用
- 检查装饰器是否正确应用
- 查看日志输出

**3. 监控数据不准确**
- 验证Prometheus配置
- 检查指标收集间隔
- 确认网络连接正常

### 调试命令

```bash
# 查看当前熔断器状态
curl http://localhost:8000/api/v1/celery-monitoring/states

# 重置特定任务熔断器
curl -X POST http://localhost:8000/api/v1/celery-monitoring/reset/my_task

# 查看全局统计
curl http://localhost:8000/api/v1/celery-monitoring/statistics
```

## 测试验证

### 回测脚本
使用提供的回测脚本验证功能：
```bash
python scripts/celery_circuit_breaker_backtest.py
```

### 测试覆盖范围
- ✅ 基础熔断器功能
- ✅ 超时保护机制
- ✅ 失败检测逻辑
- ✅ 状态转换流程
- ✅ 监控集成验证
- ✅ 配置管理功能

## 最佳实践

### 1. 配置建议
- 根据任务特性调整超时时间
- 设置合理的失败阈值
- 生产环境启用所有保护机制

### 2. 监控建议
- 设置失败率告警
- 监控熔断器状态变化
- 跟踪超时趋势

### 3. 运维建议
- 定期检查熔断器状态
- 及时处理持续熔断的任务
- 建立应急恢复流程

## 版本历史

### v1.0.0 (2026-03-01)
- 初始版本发布
- 实现基础熔断器功能
- 集成监控指标
- 提供API管理接口

---

*文档最后更新: 2026年3月1日*