# APM监控系统技术文档

## 概述

本文档描述了iMato平台AI推荐服务的APM(Application Performance Monitoring)监控系统实现，包括SkyWalking分布式追踪、Prometheus指标收集和OpenTelemetry标准化监控。

## 系统架构

### 监控层次结构

```
┌─────────────────────────────────────────────────────────┐
│                    应用层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ FastAPI应用  │  │ 推荐引擎     │  │ AI服务      │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                    中间件层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ APM中间件    │  │ 追踪装饰器   │  │ 指标收集器   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                    监控后端                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ SkyWalking  │  │ Prometheus  │  │ OpenTelemetry│    │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. APM监控中间件 (`middleware/apm_middleware.py`)

#### 功能特性
- HTTP请求全程追踪
- 自动记录请求延迟、状态码等指标
- 错误自动捕获和记录
- 支持自定义标签和属性

#### 使用示例
```python
from middleware.apm_middleware import APMMiddleware

app.add_middleware(APMMiddleware, service_name="imato-backend")
```

### 2. 追踪装饰器 (`middleware/apm_monitoring.py`)

#### 主要装饰器

**@trace_endpoint**
```python
@router.get("/recommend")
@trace_endpoint("ai.recommend")
async def get_ai_recommendations(...):
    # 自动追踪此端点的执行
    pass
```

**@monitor_recommendation_endpoint**
```python
@monitor_recommendation_endpoint
async def recommendation_function():
    # 自动记录推荐相关指标
    pass
```

**@monitor_ai_operation**
```python
@monitor_ai_operation("gpt-4-model")
async def ai_model_call():
    # 自动记录AI模型调用指标
    pass
```

### 3. 指标收集器 (`utils/metrics_collector.py`)

#### 支持的指标类型

**HTTP指标**
- `http_requests_total`: HTTP请求数量
- `http_request_duration_seconds`: HTTP请求延迟分布
- `http_request_errors_total`: HTTP错误统计

**推荐系统指标**
- `recommendation_requests_total`: 推荐请求数量
- `recommendation_duration_seconds`: 推荐处理延迟
- `recommendation_success_total`: 推荐成功统计
- `recommendation_errors_total`: 推荐错误统计

**AI模型指标**
- `ai_model_calls_total`: AI模型调用次数
- `ai_model_duration_seconds`: AI模型调用延迟
- `ai_model_tokens_used`: AI模型token使用量

**数据库指标**
- `db_operations_total`: 数据库操作次数
- `db_operation_duration_seconds`: 数据库操作延迟

## 新增核心接口

### `/api/v1/ai/recommend` - AI智能推荐接口

#### 接口详情
- **方法**: GET
- **路径**: `/api/v1/ai/recommend`
- **认证**: 需要JWT Token
- **功能**: 统一的AI推荐服务入口

#### 请求参数
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| num_recommendations | integer | 否 | 5 | 推荐数量(1-20) |
| algorithm | string | 否 | hybrid | 算法类型 |
| include_metadata | boolean | 否 | true | 是否包含元数据 |
| user_context | string | 否 | null | 用户上下文 |

#### 支持的算法类型
- `hybrid`: 混合推荐（协同过滤+内容推荐）
- `collaborative`: 协同过滤推荐
- `content`: 内容推荐
- `adaptive`: 自适应推荐

#### 响应示例
```json
{
  "user_id": "user123",
  "recommendations": [
    {
      "course_id": "course_python_basics",
      "score": 0.95,
      "type": "hybrid"
    }
  ],
  "algorithm_used": "hybrid",
  "total_recommendations": 1,
  "include_metadata": true,
  "timestamp": "2026-03-01T15:00:00Z"
}
```

## 部署配置

### 环境变量配置

```bash
# APM基础配置
SERVICE_NAME=imato-backend
ENABLE_TRACING=true
ENABLE_METRICS=true
SAMPLING_RATE=1.0

# SkyWalking配置
SKYWALKING_COLLECTOR=localhost:11800

# OpenTelemetry配置
OTEL_COLLECTOR=localhost:4317

# Prometheus配置
PROMETHEUS_PORT=9090
```

### Docker配置示例

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    environment:
      - SERVICE_NAME=imato-backend
      - SKYWALKING_COLLECTOR=skywalking-oap:11800
      - OTEL_COLLECTOR=otel-collector:4317
    depends_on:
      - skywalking-oap
      - otel-collector
  
  skywalking-oap:
    image: apache/skywalking-oap-server:9.3.0
    ports:
      - "11800:11800"
      - "12800:12800"
  
  skywalking-ui:
    image: apache/skywalking-ui:9.3.0
    ports:
      - "8080:8080"
    environment:
      - SW_OAP_ADDRESS=skywalking-oap:12800
  
  otel-collector:
    image: otel/opentelemetry-collector:0.88.0
    ports:
      - "4317:4317"
      - "8888:8888"
```

## 监控面板配置

### Prometheus指标查询示例

```promql
# 推荐服务成功率
rate(recommendation_success_total[5m]) / rate(recommendation_requests_total[5m])

# 平均推荐延迟
rate(recommendation_duration_seconds_sum[5m]) / rate(recommendation_duration_seconds_count[5m])

# HTTP错误率
rate(http_request_errors_total[5m]) / rate(http_requests_total[5m])

# AI模型调用频率
rate(ai_model_calls_total[5m])
```

### Grafana仪表板配置

推荐创建以下仪表板面板：

1. **服务概览面板**
   - 总请求数
   - 错误率
   - 平均响应时间
   - 95th百分位延迟

2. **推荐系统面板**
   - 推荐成功率趋势
   - 不同算法性能对比
   - 推荐延迟分布
   - 用户活跃度统计

3. **AI模型面板**
   - 模型调用次数
   - Token消耗统计
   - 模型响应时间
   - 成本分析

## 测试验证

### 单元测试
```bash
cd backend
python -m pytest tests/test_apm_monitoring.py -v
```

### 集成测试
```bash
python scripts/validate_apm_monitoring.py
```

### 压力测试
```bash
# 使用locust进行压力测试
locust -f tests/locustfile.py --headless -u 100 -r 10
```

## 故障排除

### 常见问题

1. **SkyWalking连接失败**
   ```
   解决方案: 检查collector地址和网络连通性
   ```

2. **指标收集不工作**
   ```
   解决方案: 确认Prometheus客户端库已安装
   ```

3. **追踪数据丢失**
   ```
   解决方案: 检查采样率配置和网络延迟
   ```

### 日志监控
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 监控关键操作
logger.info("Recommendation processed successfully")
logger.error("Failed to process recommendation", exc_info=True)
```

## 性能优化建议

1. **采样策略**
   - 生产环境建议使用0.1-0.5的采样率
   - 关键业务流程保持100%采样

2. **指标聚合**
   - 使用Histogram进行延迟统计
   - 合理设置bucket边界

3. **资源监控**
   - 监控内存和CPU使用情况
   - 设置合理的超时和重试机制

## 版本历史

- **v1.0.0** (2026-03-01): 初始版本，实现基础APM监控功能
- **v1.1.0** (计划): 添加更多业务指标和告警规则

---

*本文档最后更新时间: 2026-03-01*