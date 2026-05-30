#!/bin/bash
# 企业API网关初始化脚本

echo "开始初始化企业API网关数据库..."

# 等待数据库就绪
until pg_isready -h enterprise-db -p 5432 -U enterprise_user; do
  echo "等待数据库连接..."
  sleep 2
done

echo "数据库已就绪，开始执行初始化..."

# 创建数据库表
echo "创建数据库表..."
python -c "
import sys
sys.path.append('/app')
from enterprise_gateway.utils.database import create_enterprise_tables_sync
create_enterprise_tables_sync()
print('数据库表创建完成')
"

# 创建初始企业客户端
echo "创建初始企业客户端..."
python -c "
import sys
sys.path.append('/app')
from sqlalchemy.orm import Session
from enterprise_gateway.services.enterprise_oauth_service import enterprise_oauth_service
from enterprise_gateway.utils.database import get_db

db_gen = get_db()
db = next(db_gen)

try:
    # 创建示例企业客户端
    client = enterprise_oauth_service.create_enterprise_client(
        client_name='示例企业客户',
        redirect_uris='https://example.com/callback',
        api_quota_limit=10000,
        contact_email='admin@example.com',
        company_info={'company_name': '示例公司', 'industry': '科技'},
        db=db
    )
    print(f'创建企业客户端成功:')
    print(f'  客户端名称: {client.client_name}')
    print(f'  客户端ID: {client.client_id}')
    print(f'  配额限制: {client.api_quota_limit}')

except Exception as e:
    print(f'创建企业客户端失败: {e}')

finally:
    try:
        next(db_gen, None)
    except:
        pass
"

echo "数据库初始化完成！"
