# OpenMTSciEd API 集成实施脚本
# 此脚本将创建所有必要的 API 文件和配置

Write-Host "开始创建 OpenMTSciEd API 基础架构..." -ForegroundColor Green

$basePath = "G:\OpenMTSciEd\backend-next"

# 1. 创建 Neo4j 连接工具
$neo4jContent = @"
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
"@

$neo4jContent | Out-File -FilePath "$basePath\lib\neo4j.ts" -Encoding utf8
Write-Host "✅ 创建 lib/neo4j.ts" -ForegroundColor Green

# 2. 创建健康检查 API
$healthContent = @"
import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    service: 'OpenMTSciEd API',
    version: '1.0.0'
  });
}
"@

$healthContent | Out-File -FilePath "$basePath\app\api\health\route.ts" -Encoding utf8
Write-Host "✅ 创建 app/api/health/route.ts" -ForegroundColor Green

# 3. 创建教程列表 API
$tutorialsContent = @"
import { NextResponse } from 'next/server';
import { getNeo4jDriver } from '@/lib/neo4j';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const page = parseInt(searchParams.get('page') || '1');
  const size = parseInt(searchParams.get('size') || '20');
  const subject = searchParams.get('subject');
  const gradeLevel = searchParams.get('grade_level');

  const driver = getNeo4jDriver();
  const session = driver.session();

  try {
    let whereClause = '';
    const params: any = {
      skip: (page - 1) * size,
      limit: size
    };

    if (subject) {
      whereClause += ' WHERE t.subject = \$subject';
      params.subject = subject;
    }

    if (gradeLevel) {
      whereClause += whereClause ? ' AND' : ' WHERE';
      whereClause += ' t.grade_level = \$gradeLevel';
      params.gradeLevel = gradeLevel;
    }

    const query = \`
      MATCH (t:Tutorial)
      \${whereClause}
      RETURN t
      ORDER BY t.created_at DESC
      SKIP \$skip LIMIT \$limit
    \`;

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
        thumbnail_url: node.properties.thumbnail_url,
        created_at: node.properties.created_at
      };
    });

    // 获取总数
    const countQuery = \`
      MATCH (t:Tutorial)
      \${whereClause}
      RETURN count(t) as total
    \`;

    const countResult = await session.run(countQuery, params);
    const total = countResult.records[0].get('total').toNumber();

    return NextResponse.json({
      items: tutorials,
      total,
      page,
      size
    });
  } catch (error) {
    console.error('Error fetching tutorials:', error);
    return NextResponse.json(
      { error: 'Failed to fetch tutorials' },
      { status: 500 }
    );
  } finally {
    await session.close();
  }
}
"@

$tutorialsContent | Out-File -FilePath "$basePath\app\api\v1\tutorials\route.ts" -Encoding utf8
Write-Host "✅ 创建 app/api/v1/tutorials/route.ts" -ForegroundColor Green

# 4. 创建教程详情 API
$tutorialIdContent = @"
import { NextResponse } from 'next/server';
import { getNeo4jDriver } from '@/lib/neo4j';

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const { id } = params;
  const driver = getNeo4jDriver();
  const session = driver.session();

  try {
    const query = \`
      MATCH (t:Tutorial {id: \$id})
      OPTIONAL MATCH (t)-[:RELATED_TO]->(c:Courseware)
      OPTIONAL MATCH (t)-[:USES_PROJECT]->(h:HardwareProject)
      RETURN t, collect(DISTINCT c) as coursewares, collect(DISTINCT h) as hardware_projects
    \`;

    const result = await session.run(query, { id });

    if (result.records.length === 0) {
      return NextResponse.json(
        { error: 'Tutorial not found' },
        { status: 404 }
      );
    }

    const record = result.records[0];
    const tutorial = record.get('t');
    const coursewares = record.get('coursewares').map((c: any) => c.properties.id);
    const hardwareProjects = record.get('hardware_projects').map((h: any) => h.properties.id);

    return NextResponse.json({
      id: tutorial.properties.id,
      title: tutorial.properties.title,
      description: tutorial.properties.description,
      content: tutorial.properties.content,
      grade_level: tutorial.properties.grade_level,
      subject: tutorial.properties.subject,
      duration_minutes: tutorial.properties.duration_minutes,
      learning_objectives: tutorial.properties.learning_objectives || [],
      materials_needed: tutorial.properties.materials_needed || [],
      related_coursewares: coursewares,
      related_hardware_projects: hardwareProjects,
      thumbnail_url: tutorial.properties.thumbnail_url,
      created_at: tutorial.properties.created_at
    });
  } catch (error) {
    console.error('Error fetching tutorial:', error);
    return NextResponse.json(
      { error: 'Failed to fetch tutorial' },
      { status: 500 }
    );
  } finally {
    await session.close();
  }
}
"@

$tutorialIdContent | Out-File -FilePath "$basePath\app\api\v1\tutorials\[id]\route.ts" -Encoding utf8
Write-Host "✅ 创建 app/api/v1/tutorials/[id]/route.ts" -ForegroundColor Green

# 5. 创建知识图谱学习路径 API
$pathContent = @"
import { NextResponse } from 'next/server';
import { getNeo4jDriver } from '@/lib/neo4j';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { user_id, current_grade, subjects, learning_goals } = body;

    if (!user_id || !current_grade || !subjects) {
      return NextResponse.json(
        { error: 'Missing required fields: user_id, current_grade, subjects' },
        { status: 400 }
      );
    }

    const driver = getNeo4jDriver();
    const session = driver.session();

    // 基于知识图谱生成学习路径
    const query = \`
      MATCH (start:Tutorial)
      WHERE start.grade_level = \$grade
        AND start.subject IN \$subjects

      MATCH path = (start)-[:PROGRESSES_TO*1..5]->(end)
      WHERE end.grade_level <> \$grade

      WITH path, length(path) as pathLength
      ORDER BY pathLength ASC
      LIMIT 1

      UNWIND nodes(path) as node
      RETURN node
      ORDER BY node.order_index
    \`;

    const result = await session.run(query, {
      grade: current_grade,
      subjects: subjects
    });

    const nodes = result.records.map((record, index) => {
      const node = record.get('node');
      return {
        id: \`node_\${index}\`,
        type: node.labels[0].toLowerCase(),
        resource_id: node.properties.id,
        title: node.properties.title,
        prerequisites: index > 0 ? [\`node_\${index - 1}\`] : [],
        next_steps: []
      };
    });

    // 更新 next_steps
    for (let i = 0; i < nodes.length - 1; i++) {
      nodes[i].next_steps.push(nodes[i + 1].id);
    }

    const pathId = \`path_\${user_id}_\${Date.now()}\`;

    return NextResponse.json({
      path_id: pathId,
      nodes,
      estimated_duration_hours: nodes.length * 2,
      difficulty_progression: 'adaptive'
    });

  } catch (error) {
    console.error('Error generating learning path:', error);
    return NextResponse.json(
      { error: 'Failed to generate learning path' },
      { status: 500 }
    );
  }
}
"@

$pathContent | Out-File -FilePath "$basePath\app\api\v1\knowledge-graph\path\route.ts" -Encoding utf8
Write-Host "✅ 创建 app/api/v1/knowledge-graph/path/route.ts" -ForegroundColor Green

# 6. 创建推荐 API
$recommendContent = @"
import { NextResponse } from 'next/server';
import { getNeo4jDriver } from '@/lib/neo4j';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const userId = searchParams.get('user_id');

  if (!userId) {
    return NextResponse.json(
      { error: 'user_id is required' },
      { status: 400 }
    );
  }

  const driver = getNeo4jDriver();
  const session = driver.session();

  try {
    // 基于用户历史推荐相关资源
    const query = \`
      MATCH (u:User {id: \$userId})-[:COMPLETED]->(completed:Tutorial)
      MATCH (completed)-[:RELATED_TO]->(recommended:Tutorial)
      WHERE NOT (u)-[:COMPLETED]->(recommended)
      RETURN DISTINCT recommended
      LIMIT 10
    \`;

    const result = await session.run(query, { userId: parseInt(userId) });

    const recommendations = result.records.map(record => {
      const node = record.get('recommended');
      return {
        id: node.properties.id,
        title: node.properties.title,
        subject: node.properties.subject,
        reason: 'Based on your completed tutorials'
      };
    });

    return NextResponse.json({
      recommended_paths: [],
      suggested_resources: recommendations
    });
  } catch (error) {
    console.error('Error getting recommendations:', error);
    return NextResponse.json(
      { error: 'Failed to get recommendations' },
      { status: 500 }
    );
  } finally {
    await session.close();
  }
}
"@

$recommendContent | Out-File -FilePath "$basePath\app\api\v1\knowledge-graph\recommend\route.ts" -Encoding utf8
Write-Host "✅ 创建 app/api/v1/knowledge-graph/recommend/route.ts" -ForegroundColor Green

# 7. 创建硬件项目 API
$hardwareContent = @"
import { NextResponse } from 'next/server';
import { getNeo4jDriver } from '@/lib/neo4j';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const subject = searchParams.get('subject');

  const driver = getNeo4jDriver();
  const session = driver.session();

  try {
    let whereClause = '';
    const params: any = {};

    if (subject) {
      whereClause = ' WHERE h.subject = \$subject';
      params.subject = subject;
    }

    const query = \`
      MATCH (h:HardwareProject)
      \${whereClause}
      RETURN h
      ORDER BY h.budget_yuan ASC
    \`;

    const result = await session.run(query, params);

    const projects = result.records.map(record => {
      const node = record.get('h');
      return {
        id: node.properties.id,
        title: node.properties.title,
        description: node.properties.description,
        budget_yuan: node.properties.budget_yuan,
        hardware_list: node.properties.hardware_list || [],
        difficulty: node.properties.difficulty,
        estimated_time_hours: node.properties.estimated_time_hours,
        tutorial_id: node.properties.tutorial_id
      };
    });

    return NextResponse.json({
      items: projects,
      total: projects.length
    });
  } catch (error) {
    console.error('Error fetching hardware projects:', error);
    return NextResponse.json(
      { error: 'Failed to fetch hardware projects' },
      { status: 500 }
    );
  } finally {
    await session.close();
  }
}
"@

$hardwareContent | Out-File -FilePath "$basePath\app\api\v1\hardware-projects\route.ts" -Encoding utf8
Write-Host "✅ 创建 app/api/v1/hardware-projects/route.ts" -ForegroundColor Green

# 8. 创建课件库 API
$coursewaresContent = @"
import { NextResponse } from 'next/server';
import { getNeo4jDriver } from '@/lib/neo4j';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const topic = searchParams.get('topic');
  const grade = searchParams.get('grade');

  const driver = getNeo4jDriver();
  const session = driver.session();

  try {
    let whereClause = '';
    const params: any = {};

    if (topic) {
      whereClause += ' WHERE c.subject = \$topic';
      params.topic = topic;
    }

    if (grade) {
      whereClause += whereClause ? ' AND' : ' WHERE';
      whereClause += ' c.grade_level = \$grade';
      params.grade = grade;
    }

    const query = \`
      MATCH (c:Courseware)
      \${whereClause}
      RETURN c
      ORDER BY c.created_at DESC
      LIMIT 50
    \`;

    const result = await session.run(query, params);

    const coursewares = result.records.map(record => {
      const node = record.get('c');
      return {
        id: node.properties.id,
        title: node.properties.title,
        type: node.properties.type,
        subject: node.properties.subject,
        difficulty: node.properties.difficulty,
        url: node.properties.url,
        duration_minutes: node.properties.duration_minutes
      };
    });

    return NextResponse.json({
      items: coursewares,
      total: coursewares.length
    });
  } catch (error) {
    console.error('Error fetching coursewares:', error);
    return NextResponse.json(
      { error: 'Failed to fetch coursewares' },
      { status: 500 }
    );
  } finally {
    await session.close();
  }
}
"@

$coursewaresContent | Out-File -FilePath "$basePath\app\api\v1\coursewares\route.ts" -Encoding utf8
Write-Host "✅ 创建 app/api/v1/coursewares/route.ts" -ForegroundColor Green

Write-Host "`n🎉 OpenMTSciEd API 基础架构创建完成！" -ForegroundColor Green
Write-Host "`n下一步：" -ForegroundColor Yellow
Write-Host "1. 配置 .env.local 文件中的 Neo4j 连接信息" -ForegroundColor White
Write-Host "2. 启动开发服务器: npm run dev" -ForegroundColor White
Write-Host "3. 测试 API: http://localhost:3000/api/health" -ForegroundColor White
