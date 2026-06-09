# OpenMTSciEd API 实施指南

## 📁 已创建的目录结构

```
G:\OpenMTSciEd\backend-next\app\api\
├── health/
│   └── route.ts          ✅ 已创建
└── v1/
    ├── tutorials/
    │   ├── route.ts      ⏳ 待创建
    │   └── [id]/
    │       └── route.ts  ⏳ 待创建
    ├── coursewares/
    │   └── route.ts      ⏳ 待创建
    ├── knowledge-graph/
    │   ├── path/
    │   │   └── route.ts  ⏳ 待创建
    │   └── recommend/
    │       └── route.ts  ⏳ 待创建
    └── hardware-projects/
        └── route.ts      ⏳ 待创建
```

## 🔧 需要创建的文件

### 1. lib/neo4j.ts (Neo4j 连接工具)

**路径**: `G:\OpenMTSciEd\backend-next\lib\neo4j.ts`

```typescript
import neo4j from 'neo4j-driver';

const NEO4J_URI = process.env.NEO4J_URI || 'bolt://localhost:7687';
const NEO4J_USER = process.env.NEO4J_USER || 'neo4j';
const NEO4J_PASSWORD = process.env.NEO4J_PASSWORD || 'password';

let driver: neo4j.Driver | null = null;

export function getNeo4jDriver(): neo4j.Driver {
  if (!driver) {
    driver = neo4j.driver(NEO4J_URI, neo4j.auth.basic(NEO4J_USER, NEO4J_PASSWORD), {
      maxConnectionPoolSize: 50,
      connectionTimeout: 30000,
    });

    driver.verifyConnectivity()
      .then(() => console.log('✅ Neo4j connected successfully'))
      .catch((error) => console.error('❌ Neo4j connection failed:', error));
  }

  return driver;
}

export async function closeNeo4jDriver(): Promise<void> {
  if (driver) {
    await driver.close();
    driver = null;
    console.log('Neo4j driver closed');
  }
}
```

### 2. app/api/v1/tutorials/route.ts (教程列表)

```typescript
import { NextResponse } from 'next/server';
import { getNeo4jDriver } from '@/lib/neo4j';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const page = parseInt(searchParams.get('page') || '1');
  const size = parseInt(searchParams.get('size') || '20');
  const subject = searchParams.get('subject');
  
  const driver = getNeo4jDriver();
  const session = driver.session();
  
  try {
    let whereClause = '';
    const params: any = { skip: (page - 1) * size, limit: size };
    
    if (subject) {
      whereClause = ' WHERE t.subject = $subject';
      params.subject = subject;
    }
    
    const query = `
      MATCH (t:Tutorial)
      ${whereClause}
      RETURN t
      ORDER BY t.created_at DESC
      SKIP $skip LIMIT $limit
    `;
    
    const result = await session.run(query, params);
    const tutorials = result.records.map(record => {
      const node = record.get('t');
      return {
        id: node.properties.id,
        title: node.properties.title,
        description: node.properties.description,
        grade_level: node.properties.grade_level,
        subject: node.properties.subject,
        duration_minutes: node.properties.duration_minutes,
      };
    });
    
    return NextResponse.json({ items: tutorials, total: tutorials.length, page, size });
  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json({ error: 'Failed' }, { status: 500 });
  } finally {
    await session.close();
  }
}
```

### 3. app/api/v1/knowledge-graph/path/route.ts (学习路径)

```typescript
import { NextResponse } from 'next/server';
import { getNeo4jDriver } from '@/lib/neo4j';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { user_id, current_grade, subjects } = body;
    
    if (!user_id || !current_grade || !subjects) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }
    
    const driver = getNeo4jDriver();
    const session = driver.session();
    
    const query = `
      MATCH (start:Tutorial)
      WHERE start.grade_level = $grade AND start.subject IN $subjects
      MATCH path = (start)-[:PROGRESSES_TO*1..5]->(end)
      WITH path, length(path) as pathLength
      ORDER BY pathLength ASC LIMIT 1
      UNWIND nodes(path) as node
      RETURN node ORDER BY node.order_index
    `;
    
    const result = await session.run(query, { grade: current_grade, subjects });
    
    const nodes = result.records.map((record, index) => ({
      id: `node_${index}`,
      type: 'tutorial',
      resource_id: record.get('node').properties.id,
      title: record.get('node').properties.title,
      prerequisites: index > 0 ? [`node_${index - 1}`] : [],
      next_steps: []
    }));
    
    return NextResponse.json({
      path_id: `path_${user_id}_${Date.now()}`,
      nodes,
      estimated_duration_hours: nodes.length * 2,
      difficulty_progression: 'adaptive'
    });
  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json({ error: 'Failed' }, { status: 500 });
  }
}
```

## 🚀 启动步骤

1. **配置环境变量** (`G:\OpenMTSciEd\backend-next\.env.local`):
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

2. **安装依赖**:
```bash
cd G:\OpenMTSciEd\backend-next
npm install neo4j-driver
```

3. **启动开发服务器**:
```bash
npm run dev
```

4. **测试 API**:
```bash
# 健康检查
curl http://localhost:3000/api/health

# 获取教程列表
curl http://localhost:3000/api/v1/tutorials?page=1&size=10

# 生成学习路径
curl -X POST http://localhost:3000/api/v1/knowledge-graph/path \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"current_grade":"9-12","subjects":["physics"]}'
```

## 📝 iMato 前端集成

修改 `g:\iMato\src\environments\environment.ts`:
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  openMtSciEdApiUrl: 'http://localhost:3000/api/v1',  // 新增
};
```

创建服务 `g:\iMato\src\app\services\openmt-scied.service.ts` (见之前的方案)

---

**下一步**: 手动创建上述文件，或告诉我您希望我如何帮助您继续。
