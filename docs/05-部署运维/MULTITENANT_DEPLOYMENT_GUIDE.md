# 多租户架构升级部署指南

## 概述

本文档详细说明如何部署多租户架构升级功能，包括系统要求、部署步骤、配置说明和故障排除。

## 系统要求

### 硬件要求
- CPU: 2核以上
- 内存: 4GB以上
- 存储: 10GB可用空间
- 网络: 稳定的网络连接

### 软件要求
- Python 3.8或更高版本
- PostgreSQL 12或更高版本（推荐）或 SQLite 3.30+
- Redis 5.0或更高版本
- Node.js 14或更高版本（前端）
- Docker/Docker Compose（可选，用于容器化部署）

## 部署前准备

### 1. 备份现有系统
```bash
# 备份数据库
pg_dump -h localhost -U postgres imato_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 备份应用代码
tar -czf app_backup_$(date +%Y%m%d_%H%M%S).tar.gz /path/to/imato/backend
```

### 2. 检查依赖项
```bash
# 检查Python版本
python --version

# 检查数据库连接
psql -h localhost -U postgres -c "SELECT version();"

# 检查Redis连接
redis-cli ping
```

## 部署步骤

### 方式一：自动化部署（推荐）

```bash
# 1. 下载部署脚本
cd /path/to/imato/scripts

# 2. 运行部署脚本
python deploy_multitenant.py --project-root /path/to/imato

# 3. 预演模式（可选）
python deploy_multitenant.py --project-root /path/to/imato --dry-run

# 4. 跳过测试（快速部署）
python deploy_multitenant.py --project-root /path/to/imato --skip-tests
```

### 方式二：手动部署

#### 步骤1：安装依赖
```bash
cd /path/to/imato/backend

# 安装Python依赖
pip install -r requirements.txt

# 安装多租户特需依赖
pip install contextvars python-jose[cryptography] passlib[bcrypt]
```

#### 步骤2：更新数据库
```bash
# 运行数据库迁移
cd /path/to/imato/backend
alembic upgrade head

# 或者手动执行SQL迁移
psql -h localhost -U postgres -d imato_db -f migrations/multitenant_migration.sql
```

#### 步骤3：配置环境变量
```bash
# 编辑.env文件
cat >> .env << EOF
# 多租户配置
MULTITENANT_ENABLED=true
TENANT_ISOLATION_LEVEL=shared_schema
DEFAULT_TENANT_QUOTA_COURSES=100
DEFAULT_TENANT_QUOTA_STUDENTS=1000
EOF
```

#### 步骤4：更新应用配置
```python
# 在config/settings.py中添加
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # 多租户配置
    MULTITENANT_ENABLED: bool = True
    TENANT_ISOLATION_LEVEL: str = "shared_schema"
    DEFAULT_TENANT_QUOTA_COURSES: int = 100
    DEFAULT_TENANT_QUOTA_STUDENTS: int = 1000
```

#### 步骤5：重启服务
```bash
# 使用systemd
sudo systemctl restart imato-backend

# 使用supervisor
sudo supervisorctl restart imato-backend

# 使用docker-compose
docker-compose restart backend

# 开发环境
pkill -f uvicorn
cd /path/to/imato/backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 配置说明

### 多租户配置参数

| 参数 | 描述 | 默认值 | 可选值 |
|------|------|--------|--------|
| MULTITENANT_ENABLED | 是否启用多租户功能 | true | true/false |
| TENANT_ISOLATION_LEVEL | 租户隔离级别 | shared_schema | shared_schema/shared_database/separate_database |
| DEFAULT_TENANT_QUOTA_COURSES | 默认课程配额 | 100 | 整数 |
| DEFAULT_TENANT_QUOTA_STUDENTS | 默认学生配额 | 1000 | 整数 |

### 数据库配置

#### 共享数据库共享模式（推荐）
```python
# config/settings.py
DATABASE_URL = "postgresql://user:password@localhost:5432/imato_db"
```

#### 独立数据库模式
```python
# 需要为每个租户配置独立的数据库连接
DATABASE_URL_TEMPLATE = "postgresql://user:password@localhost:5432/imato_db_{org_id}"
```

### Redis配置
```python
# config/license_config.py
storage = RedisConfig(
    host="localhost",
    port=6379,
    db=1,
    password=None
)
```

## API使用示例

### 1. 创建组织
```bash
curl -X POST "http://localhost:8000/api/v1/organizations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试教育机构",
    "contact_email": "contact@test-edu.com",
    "max_users": 500
  }'
```

### 2. 课程管理（租户隔离）
```bash
# 为组织1创建课程
curl -X POST "http://localhost:8000/api/v1/org/1/courses" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "Python编程入门",
    "code": "PY101",
    "description": "Python基础课程",
    "max_students": 30
  }'

# 获取组织1的课程列表
curl -X GET "http://localhost:8000/api/v1/org/1/courses" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. 租户配置管理
```bash
# 初始化租户配置
curl -X POST "http://localhost:8000/api/v1/org/1/config/initialize" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取配置概览
curl -X GET "http://localhost:8000/api/v1/org/1/config/overview" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 验证部署

### 1. 健康检查
```bash
# 基础健康检查
curl http://localhost:8000/health

# API文档
curl http://localhost:8000/docs

# 多租户功能检查
curl -H "X-Org-ID: 1" http://localhost:8000/api/v1/org/1/courses
```

### 2. 功能测试
```bash
# 运行多租户测试
cd /path/to/imato/backend
python -m pytest tests/test_tenant_isolation.py -v
```

### 3. 数据库验证
```sql
-- 检查新表是否创建
SELECT table_name FROM information_schema.tables 
WHERE table_name LIKE '%tenant%' OR table_name LIKE '%course%';

-- 检查租户数据隔离
SELECT DISTINCT org_id FROM courses;
```

## 监控和维护

### 1. 日志监控
```bash
# 查看应用日志
tail -f /var/log/imato/backend.log

# 查看多租户相关日志
grep "tenant" /var/log/imato/backend.log
```

### 2. 性能监控
```bash
# 数据库查询性能
EXPLAIN ANALYZE SELECT * FROM courses WHERE org_id = 1;

# Redis缓存命中率
redis-cli info stats | grep "keyspace_hits\|keyspace_misses"
```

### 3. 定期维护任务
```bash
# 清理过期的租户数据
python /path/to/imato/scripts/cleanup_expired_tenants.py

# 重置资源配额
python /path/to/imato/scripts/reset_tenant_quotas.py

# 生成租户使用报告
python /path/to/imato/scripts/generate_tenant_report.py
```

## 故障排除

### 常见问题及解决方案

#### 1. 租户数据隔离失效
**现象**: 用户能看到其他租户的数据
**解决方案**:
```bash
# 检查租户中间件是否正确加载
curl -H "X-Org-ID: 1" http://localhost:8000/api/v1/org/1/courses

# 检查数据库查询是否包含租户过滤
# 在日志中查找SQL查询语句
```

#### 2. 权限验证失败
**现象**: 403 Forbidden错误
**解决方案**:
```bash
# 检查用户角色和权限
SELECT u.username, u.role FROM users u WHERE u.id = USER_ID;

# 检查功能开关配置
SELECT * FROM tenant_feature_flags WHERE org_id = ORG_ID;
```

#### 3. 数据库迁移失败
**现象**: 启动时报数据库错误
**解决方案**:
```bash
# 回滚到上一个版本
alembic downgrade -1

# 手动修复数据库结构
psql -h localhost -U postgres -d imato_db -f migrations/rollback.sql
```

#### 4. 性能问题
**现象**: API响应缓慢
**解决方案**:
```bash
# 添加数据库索引
CREATE INDEX idx_courses_org_id ON courses(org_id);
CREATE INDEX idx_enrollments_org_id ON course_enrollments(org_id);

# 优化查询语句
# 检查慢查询日志
```

### 日志分析
```bash
# 查找错误日志
grep "ERROR\|CRITICAL" /var/log/imato/backend.log

# 查找租户相关错误
grep "tenant\|org_id" /var/log/imato/backend.log

# 统计API调用频率
awk '/api\/v1\/org/ {print $0}' /var/log/imato/access.log | \
  cut -d' ' -f7 | sort | uniq -c | sort -nr
```

## 回滚方案

如果部署出现问题，可以按以下步骤回滚：

### 1. 快速回滚
```bash
# 停止当前服务
sudo systemctl stop imato-backend

# 恢复备份文件
cp /path/to/imato/backup/multitenant_upgrade/* /path/to/imato/backend/

# 重启服务
sudo systemctl start imato-backend
```

### 2. 数据库回滚
```bash
# 从备份恢复数据库
psql -h localhost -U postgres -d imato_db < backup_YYYYMMDD_HHMMSS.sql

# 或者运行回滚迁移
alembic downgrade base
```

## 后续优化建议

### 1. 性能优化
- 为频繁查询的字段添加数据库索引
- 实施查询缓存策略
- 考虑读写分离

### 2. 安全加固
- 实施更严格的输入验证
- 添加API调用频率限制
- 定期安全审计

### 3. 扩展性提升
- 实现租户级别的资源配额管理
- 添加租户间数据共享机制
- 支持动态扩缩容

## 支持和反馈

如有问题，请联系：
- 技术支持邮箱: support@imato.com
- 文档地址: https://docs.imato.com/multitenant
- GitHub Issues: https://github.com/imato-project/issues

---
*最后更新: 2024年1月*