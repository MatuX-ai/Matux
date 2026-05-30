# iMato Cloud - 监控系统集成指南

## 📊 概述

本目录包含完整的 Prometheus + Grafana 监控系统配置，支持自动告警和多渠道通知。

## 🎯 监控架构

```
应用层（/metrics）
     ↓
Prometheus Server（抓取 + 存储）
     ↓
┌─────────────┬──────────────┐
│             │              │
Grafana   AlertManager   Thanos(可选)
可视化     告警通知       长期存储
```

## 📁 文件结构

```
docker/
├── prometheus.yml           # Prometheus 主配置
├── prometheus-rules.yml     # 告警规则定义
├── alertmanager.yml         # AlertManager 通知配置
└── grafana-dashboards/      # Grafana 仪表盘 JSON
    ├── backend-overview.json
    └── ...
```

## 🚀 快速开始

### 步骤 1: 配置 Prometheus

编辑 `docker/prometheus.yml`，已包含：
- ✅ Backend 服务自动发现
- ✅ Nginx 指标抓取
- ✅ PostgreSQL/Redis 监控
- ✅ Celery Worker 监控

### 步骤 2: 配置告警规则

编辑 `docker/prometheus-rules.yml`，包含 5 大类告警：

#### a) Backend 应用告警
- **HighAPIErrorRate**: API 错误率 > 5%（持续 2 分钟）→ Critical
- **HighAPILatency**: P95 响应时间 > 1 秒（持续 5 分钟）→ Warning
- **PodFrequentRestarts**: Pod 1 小时重启 > 3 次 → Warning
- **PodMemoryPressure**: 内存使用率 > 90% → Warning
- **PodCPUOverload**: CPU 使用率 > 80% → Warning

#### b) 数据库告警
- **PostgresHighConnections**: 连接数使用率 > 80%
- **PostgresReplicationLag**: 复制延迟 > 30 秒
- **PostgresDiskSpaceLow**: 磁盘剩余空间 < 10%

#### c) Redis 缓存告警
- **RedisHighMemory**: 内存使用率 > 80%
- **RedisHighKeyEviction**: 每秒驱逐键 > 10 个
- **RedisPersistenceFailed**: 持久化失败

#### d) 系统资源告警
- **NodeDiskSpaceLow**: 节点磁盘 < 10%
- **NodeMemoryPressure**: 节点内存 > 90%
- **NodeNetworkReceiveErrors**: 网络接收错误率高

#### e) 业务指标告警
- **AbnormalTokenConsumption**: Token 消耗速率异常（>10000/h）
- **AIFallbackTriggered**: AI 服务降级触发

### 步骤 3: 配置 AlertManager

编辑 `docker/alertmanager.yml`，配置通知渠道：

#### 邮件通知
```yaml
global:
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alertmanager@imato.cloud'
  smtp_auth_username: 'your-username'
  smtp_auth_password: 'your-password'
```

#### Slack 通知
```yaml
slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
```

#### 钉钉通知
```yaml
wechat_api_secret: 'your-corp-secret'
wechat_api_url: 'https://qyapi.weixin.qq.com/cgi-bin/'
```

### 步骤 4: 导入 Grafana 仪表盘

```bash
# 方式一：手动导入
1. 访问 Grafana: http://localhost:3000
2. 登录：admin/admin123
3. Dashboards → Import
4. 上传 backend-overview.json
5. 选择 Prometheus 数据源

# 方式二：自动配置（推荐）
通过 ConfigMap 自动加载仪表盘
```

## 🔍 监控指标说明

### Backend 核心指标

| 指标名称 | 类型 | 说明 |
|---------|------|------|
| `http_requests_total` | Counter | HTTP 请求总数 |
| `http_request_duration_seconds` | Histogram | 请求耗时分布 |
| `http_requests_in_progress` | Gauge | 正在处理的请求数 |
| `token_consumed_total` | Counter | Token 消耗总量 |
| `ai_fallback_triggered_total` | Counter | AI 降级触发次数 |

### 数据库指标

| 指标名称 | 类型 | 说明 |
|---------|------|------|
| `pg_stat_activity_count` | Gauge | 当前连接数 |
| `pg_database_size_bytes` | Gauge | 数据库大小 |
| `pg_replication_lag_seconds` | Gauge | 复制延迟 |
| `redis_memory_used_bytes` | Gauge | Redis 内存使用量 |
| `redis_connected_clients` | Gauge | Redis 客户端连接数 |

### 系统指标

| 指标名称 | 类型 | 说明 |
|---------|------|------|
| `node_cpu_usage_percent` | Gauge | CPU 使用率 |
| `node_memory_usage_percent` | Gauge | 内存使用率 |
| `node_disk_usage_percent` | Gauge | 磁盘使用率 |
| `node_network_receive_bytes` | Counter | 网络接收量 |

## 📊 Grafana 仪表盘

### Backend Overview 仪表盘

**面板布局**:
```
┌─────────────────────────────────────────────┐
│ Pod 状态 | API 成功率 | P95 延迟 | QPS      │
├─────────────────────────────────────────────┤
│ CPU/Memory 使用率趋势图 (8 小时)            │
├─────────────────────────────────────────────┤
│ API 请求量趋势图                            │
├─────────────────────────────────────────────┤
│ 响应时间分布（P50/P95/P99）                 │
├─────────────────────────────────────────────┤
│ Pod 资源使用 Top5 表格                      │
└─────────────────────────────────────────────┘
```

**关键指标卡**:
- **Pod 状态**: Running/Pending/Failed 数量
- **API 请求成功率**: 目标 > 99%
- **P95 响应时间**: 目标 < 500ms
- **QPS**: 实时请求速率

### 自定义仪表盘

可以通过以下方式扩展：
1. 复制 `backend-overview.json` 修改
2. 使用 Grafana UI 创建新仪表盘
3. 导出为 JSON 放入 `grafana-dashboards/` 目录

## 🚨 告警通知配置

### 告警级别定义

| 级别 | 说明 | 响应时间 | 通知渠道 |
|------|------|----------|----------|
| **Critical** | 服务不可用，需立即处理 | < 5 分钟 | 邮件 + Slack + 电话 |
| **Warning** | 潜在问题，需关注 | < 30 分钟 | 邮件 + Slack |
| **Info** | 信息提示，无需立即处理 | - | 仅记录日志 |

### 通知路由策略

```
告警触发
   ↓
按 severity 分组
   ↓
critical → critical-alerts（邮件+Slack）
warning  → default-receiver（邮件）
info     → info-logger（Webhook 记录）
   ↓
按 service 细分
   ↓
postgres → dba-team（DBA 邮箱 + 钉钉）
redis    → ops-team（运维 Slack）
```

### 告警抑制规则

防止告警风暴的机制：
1. **节点宕机** → 抑制该节点所有 Pod 告警
2. **集群不可用** → 抑制所有服务告警
3. **Critical 告警** → 抑制同名的 Warning 告警

### 维护窗口

在计划维护期间静音告警：
```yaml
mute_time_intervals:
  - name: 'weekend-maintenance'
    time_intervals:
      - weekdays: ['saturday', 'sunday']
        times:
          - start_time: '02:00'
            end_time: '06:00'
```

## 🔧 故障排查

### Prometheus 无法抓取指标

```bash
# 检查 targets 状态
kubectl port-forward svc/imato-prometheus -n imato-cloud 9090:9090
# 访问 http://localhost:9090/targets

# 查看 Prometheus 日志
kubectl logs -n imato-cloud deployment/imato-prometheus -f

# 测试后端 metrics 端点
curl http://backend:8000/metrics
```

### Grafana 无法显示数据

```bash
# 检查数据源配置
kubectl get configmap grafana-datasources -n imato-cloud -o yaml

# 验证 Prometheus 连接
kubectl exec -it deployment/imato-grafana -n imato-cloud -- \
  curl http://imato-prometheus:9090/api/v1/query?query=up
```

### 告警未触发

```bash
# 检查告警规则
kubectl port-forward svc/imato-prometheus -n imato-cloud 9090:9090
# 访问 http://localhost:9090/alerts

# 检查 AlertManager配置
kubectl logs -n imato-cloud deployment/imato-alertmanager -f

# 手动触发测试告警
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{"labels":{"alertname":"TestAlert","severity":"info"}}]'
```

## 📈 最佳实践

### 1. 指标命名规范

遵循 Prometheus 命名约定：
```
<app>_<component>_<metric>_<unit>
示例：
http_requests_total
http_request_duration_seconds
token_consumed_total
```

### 2. 告警阈值设置

基于 SLO（Service Level Objective）：
```yaml
# API 可用性 SLO: 99.9%
- alert: HighErrorRate
  expr: sum(rate(errors[5m])) / sum(rate(requests[5m])) > 0.001
  
# 响应时间 SLO: P95 < 500ms
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(duration_bucket[5m])) > 0.5
```

### 3. 仪表盘设计原则

- **少而精**: 每个仪表盘聚焦一个主题
- **层次分明**: 从概览到细节逐层深入
- ** actionable**: 每个面板都能指导行动
- **自动化**: 尽可能使用变量和模板

### 4. 告警优化

- **减少噪音**: 合理设置阈值和静默期
- **分级通知**: 根据严重程度选择渠道
- **明确描述**: 告警信息包含原因和建议
- **定期回顾**: 每月审查告警有效性

## 🔄 扩展方案

### 方案一：Thanos 长期存储

```yaml
# 部署 Thanos Sidecar
components:
  - thanos-sidecar
  - thanos-query
  - thanos-store
  - thanos-compactor
```

**优势**:
- 指标保留 > 1 年
- 全局查询视图
- 高可用架构

### 方案二：Loki 日志聚合

```yaml
components:
  - loki: 日志存储
  - promtail: 日志收集
  - grafana: 统一查询
```

**整合效果**:
```
Metrics (Prometheus) + Logs (Loki) = 完整可观测性
```

### 方案三：Jaeger 分布式追踪

```yaml
components:
  - jaeger-collector
  - jaeger-query
  - jaeger-ingester
```

**用途**:
- 请求链路追踪
- 性能瓶颈定位
- 依赖关系分析

## 📚 相关文档

- [Docker 部署指南](README.md)
- [Kubernetes 资源配置](../k8s/README.md)
- [Prometheus 官方文档](https://prometheus.io/docs/)
- [Grafana 官方文档](https://grafana.com/docs/)

## 🆘 获取帮助

如遇到问题：
1. 查看本文档的故障排查部分
2. 检查 Prometheus/Grafana 日志
3. 访问社区论坛（Prometheus Community）
4. 提交 Issue 到项目仓库

---

**最后更新**: 2026-03-14  
**维护者**: iMato Team
