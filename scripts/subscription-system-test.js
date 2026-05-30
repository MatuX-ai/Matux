/**
 * 订阅系统功能测试脚本
 */

const fs = require('fs');
const path = require('path');

// 颜色输出函数
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m'
};

function log(message, color = 'reset') {
  console.log(colors[color] + message + colors.reset);
}

function logSuccess(message) {
  log('✓ ' + message, 'green');
}

function logError(message) {
  log('✗ ' + message, 'red');
}

function logWarning(message) {
  log('⚠ ' + message, 'yellow');
}

function logInfo(message) {
  log('ℹ ' + message, 'blue');
}

// 测试1: 检查必要文件是否存在
log('\n📋 测试1: 文件完整性检查', 'yellow');

const requiredFiles = [
  'backend/models/subscription.py',
  'backend/services/subscription_service.py',
  'backend/routes/subscription_routes.py',
  'src/app/core/models/subscription.models.ts',
  'src/app/core/services/subscription.service.ts',
  'scripts/subscription-migration.sql',
  'scripts/run-subscription-migration.py'
];

let allFilesExist = true;
requiredFiles.forEach(file => {
  const fullPath = path.join(__dirname, '..', file);
  const exists = fs.existsSync(fullPath);
  if (exists) {
    logSuccess(file);
  } else {
    logError(file);
    allFilesExist = false;
  }
});

// 测试2: 检查后端模型定义
log('\n📋 测试2: 后端模型定义检查', 'yellow');

try {
  const modelContent = fs.readFileSync(
    path.join(__dirname, '../backend/models/subscription.py'),
    'utf8'
  );
  
  const requiredClasses = [
    'SubscriptionPlan',
    'UserSubscription', 
    'SubscriptionPayment',
    'SubscriptionCycle'
  ];
  
  const requiredEnums = [
    'BillingCycle',
    'SubscriptionStatus',
    'SubscriptionPlanType'
  ];
  
  let modelCheckPassed = true;
  
  requiredClasses.forEach(className => {
    if (modelContent.includes(`class ${className}`)) {
      logSuccess(`找到模型类: ${className}`);
    } else {
      logError(`缺少模型类: ${className}`);
      modelCheckPassed = false;
    }
  });
  
  requiredEnums.forEach(enumName => {
    if (modelContent.includes(`class ${enumName}`)) {
      logSuccess(`找到枚举类: ${enumName}`);
    } else {
      logError(`缺少枚举类: ${enumName}`);
      modelCheckPassed = false;
    }
  });
  
} catch (error) {
  logError('无法读取后端模型文件: ' + error.message);
}

// 测试3: 检查前端模型定义
log('\n📋 测试3: 前端模型定义检查', 'yellow');

try {
  const frontendModelContent = fs.readFileSync(
    path.join(__dirname, '../src/app/core/models/subscription.models.ts'),
    'utf8'
  );
  
  const requiredInterfaces = [
    'SubscriptionPlan',
    'UserSubscription',
    'SubscriptionPayment',
    'SubscriptionCycle'
  ];
  
  const requiredEnums = [
    'BillingCycle',
    'SubscriptionStatus',
    'SubscriptionPlanType'
  ];
  
  requiredInterfaces.forEach(interfaceName => {
    if (frontendModelContent.includes(`interface ${interfaceName}`) || 
        frontendModelContent.includes(`export interface ${interfaceName}`)) {
      logSuccess(`找到接口定义: ${interfaceName}`);
    } else {
      logError(`缺少接口定义: ${interfaceName}`);
    }
  });
  
  requiredEnums.forEach(enumName => {
    if (frontendModelContent.includes(`enum ${enumName}`) || 
        frontendModelContent.includes(`export enum ${enumName}`)) {
      logSuccess(`找到枚举定义: ${enumName}`);
    } else {
      logError(`缺少枚举定义: ${enumName}`);
    }
  });
  
} catch (error) {
  logError('无法读取前端模型文件: ' + error.message);
}

// 测试4: 检查服务层实现
log('\n📋 测试4: 服务层实现检查', 'yellow');

try {
  const serviceContent = fs.readFileSync(
    path.join(__dirname, '../backend/services/subscription_service.py'),
    'utf8'
  );
  
  const requiredMethods = [
    'create_subscription_plan',
    'get_subscription_plans',
    'subscribe_user',
    'cancel_subscription',
    'get_user_subscriptions',
    'process_recurring_payments'
  ];
  
  requiredMethods.forEach(methodName => {
    if (serviceContent.includes(`async ${methodName}`) || 
        serviceContent.includes(`def ${methodName}`)) {
      logSuccess(`找到服务方法: ${methodName}`);
    } else {
      logError(`缺少服务方法: ${methodName}`);
    }
  });
  
} catch (error) {
  logError('无法读取服务文件: ' + error.message);
}

// 测试5: 检查路由定义
log('\n📋 测试5: API路由定义检查', 'yellow');

try {
  const routeContent = fs.readFileSync(
    path.join(__dirname, '../backend/routes/subscription_routes.py'),
    'utf8'
  );
  
  const requiredEndpoints = [
    'POST /subscriptions/plans',
    'GET /subscriptions/plans',
    'POST /subscriptions',
    'GET /subscriptions',
    'POST /subscriptions/{subscription_id}/cancel'
  ];
  
  requiredEndpoints.forEach(endpoint => {
    if (routeContent.includes(endpoint.split(' ')[1])) {
      logSuccess(`找到路由端点: ${endpoint}`);
    } else {
      logWarning(`可能缺少路由端点: ${endpoint}`);
    }
  });
  
} catch (error) {
  logError('无法读取路由文件: ' + error.message);
}

// 测试6: 检查前端服务实现
log('\n📋 测试6: 前端服务实现检查', 'yellow');

try {
  const frontendServiceContent = fs.readFileSync(
    path.join(__dirname, '../src/app/core/services/subscription.service.ts'),
    'utf8'
  );
  
  // 检查是否包含参考的示例代码结构
  if (frontendServiceContent.includes('createSubscription') && 
      frontendServiceContent.includes('planId: string')) {
    logSuccess('找到参考的订阅创建方法实现');
  } else {
    logWarning('未找到参考的订阅创建方法实现');
  }
  
  const requiredMethods = [
    'createSubscriptionPlan',
    'getSubscriptionPlans',
    'createSubscription',
    'getUserSubscriptions',
    'cancelSubscription'
  ];
  
  requiredMethods.forEach(methodName => {
    if (frontendServiceContent.includes(methodName)) {
      logSuccess(`找到前端服务方法: ${methodName}`);
    } else {
      logError(`缺少前端服务方法: ${methodName}`);
    }
  });
  
} catch (error) {
  logError('无法读取前端服务文件: ' + error.message);
}

// 测试7: 显示项目结构
log('\n📋 测试7: 订阅系统项目结构', 'yellow');

const subscriptionStructure = {
  '后端模型': [
    'backend/models/subscription.py'
  ],
  '后端服务': [
    'backend/services/subscription_service.py'
  ],
  'API路由': [
    'backend/routes/subscription_routes.py'
  ],
  '前端模型': [
    'src/app/core/models/subscription.models.ts'
  ],
  '前端服务': [
    'src/app/core/services/subscription.service.ts'
  ],
  '数据库迁移': [
    'scripts/subscription-migration.sql',
    'scripts/run-subscription-migration.py'
  ]
};

Object.keys(subscriptionStructure).forEach(category => {
  log(`  ${category}:`, 'blue');
  subscriptionStructure[category].forEach(file => {
    const exists = fs.existsSync(path.join(__dirname, '..', file));
    log(`    ${exists ? '✅' : '❌'} ${file}`);
  });
});

// 测试总结
log('\n🎉 订阅系统功能测试完成！', 'green');
log('', 'reset');

const totalTests = 7;
let passedTests = 0;

if (allFilesExist) passedTests++;
// 其他测试的通过判断可以进一步完善

const successRate = Math.round((passedTests / totalTests) * 100);

log(`📊 测试摘要:`, 'yellow');
log(`   总测试数: ${totalTests}`);
log(`   通过测试: ${passedTests}`);
log(`   成功率: ${successRate}%`);
log('', 'reset');

if (successRate >= 80) {
  log('✅ 订阅系统基本功能已实现完成！', 'green');
  log('下一步建议:', 'blue');
  log('1. 运行数据库迁移脚本');
  log('2. 启动后端服务测试API');
  log('3. 集成到前端应用中');
} else {
  log('⚠️  订阅系统还需要进一步完善', 'yellow');
}

log('\n💡 使用说明:', 'blue');
log('- 运行数据库迁移: python scripts/run-subscription-migration.py');
log('- 启动后端服务: python backend/main.py');
log('- 测试API端点: 查看 /docs API文档');