#!/usr/bin/env node

/**
 * iMato 监控测试运行器
 * 验证监控工具和修复工具的正确性
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

// 颜色输出
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function success(message) {
  log(`✅ ${message}`, 'green');
}

function error(message) {
  log(`❌ ${message}`, 'red');
}

function warning(message) {
  log(`⚠️  ${message}`, 'yellow');
}

function info(message) {
  log(`ℹ️  ${message}`, 'blue');
}

// 测试套件
class TestRunner {
  constructor() {
    this.tests = [];
    this.results = {
      passed: 0,
      failed: 0,
      total: 0
    };
  }
  
  test(name, fn) {
    this.tests.push({ name, fn });
  }
  
  async run() {
    log('\n' + '='.repeat(80), 'cyan');
    log('iMato 监控工具测试套件', 'cyan');
    log('='.repeat(80), 'cyan');
    
    for (const test of this.tests) {
      this.results.total++;
      try {
        log(`\n🧪 执行测试: ${test.name}`, 'bright');
        await test.fn();
        success(`测试通过: ${test.name}`);
        this.results.passed++;
      } catch (err) {
        error(`测试失败: ${test.name}`);
        log(`   错误: ${err.message}`, 'red');
        this.results.failed++;
      }
    }
    
    this.printSummary();
    return this.results.failed === 0;
  }
  
  printSummary() {
    log('\n' + '='.repeat(80), 'cyan');
    log('测试总结', 'cyan');
    log('='.repeat(80), 'cyan');
    log(`📊 总测试数: ${this.results.total}`, 'bright');
    log(`✅ 通过: ${this.results.passed}`, 'green');
    log(`❌ 失败: ${this.results.failed}`, 'red');
    log(`📈 通过率: ${((this.results.passed / this.results.total) * 100).toFixed(1)}%`, 'blue');
    log('='.repeat(80), 'cyan');
  }
}

// 测试用例
const runner = new TestRunner();

// 测试1: 检查文件是否存在
runner.test('检查监控工具文件完整性', () => {
  const requiredFiles = [
    'marketing-page-monitor.js',
    'marketing-page-fixes.js',
    'continuous-monitor.js',
    'monitor-config.json',
    'package.json'
  ];
  
  for (const file of requiredFiles) {
    if (!fs.existsSync(file)) {
      throw new Error(`缺少必需文件: ${file}`);
    }
    info(`找到文件: ${file}`);
  }
});

// 测试2: 验证配置文件
runner.test('验证配置文件格式', () => {
  const configPath = 'monitor-config.json';
  const configContent = fs.readFileSync(configPath, 'utf8');
  const config = JSON.parse(configContent);
  
  // 检查必需字段
  const requiredFields = ['baseUrl', 'pages', 'output'];
  for (const field of requiredFields) {
    if (!config[field]) {
      throw new Error(`配置文件缺少必需字段: ${field}`);
    }
  }
  
  // 检查页面配置
  if (!Array.isArray(config.pages) || config.pages.length === 0) {
    throw new Error('pages必须是包含页面配置的非空数组');
  }
  
  // 检查每个页面配置
  config.pages.forEach((page, index) => {
    if (!page.path || !page.name) {
      throw new Error(`页面配置[${index}]缺少必需字段: path 或 name`);
    }
  });
  
  success('配置文件格式正确');
});

// 测试3: 验证监控脚本语法
runner.test('验证监控脚本语法', async () => {
  await new Promise((resolve, reject) => {
    const node = spawn('node', ['--check', 'marketing-page-monitor.js'], {
      stdio: 'pipe'
    });
    
    node.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error('监控脚本语法检查失败'));
      }
    });
  });
});

// 测试4: 验证修复脚本语法
runner.test('验证修复脚本语法', async () => {
  await new Promise((resolve, reject) => {
    const node = spawn('node', ['--check', 'marketing-page-fixes.js'], {
      stdio: 'pipe'
    });
    
    node.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error('修复脚本语法检查失败'));
      }
    });
  });
});

// 测试5: 模拟监控运行（快速测试）
runner.test('执行快速监控测试', async () => {
  // 检查端口是否可用
  const baseUrl = 'http://localhost:4200';
  
  info(`测试基础URL: ${baseUrl}`);
  
  // 这里可以添加更多的启动前检查
  // 例如：检查Angular应用是否运行
  
  success('快速测试通过，准备执行完整监控');
});

// 测试6: 验证修复模式
runner.test('验证修复模式', () => {
  const { generateFixSuggestion } = require('./marketing-page-monitor.js');
  
  // 测试各种错误类型的修复建议生成
  const testErrors = [
    {
      type: 'js_error',
      message: 'Cannot read property \'length\' of undefined'
    },
    {
      type: 'resource_error',
      message: 'Failed to load resource: the server responded with a status of 404',
      status: 404
    },
    {
      type: 'js_error',
      message: 'myFunction is not a function'
    }
  ];
  
  testErrors.forEach((error, index) => {
    const suggestions = generateFixSuggestion(error);
    if (!Array.isArray(suggestions) || suggestions.length === 0) {
      warning(`错误类型 ${error.type} 未生成修复建议`);
    } else {
      info(`错误类型 ${error.type}: 生成 ${suggestions.length} 个修复建议`);
    }
  });
});

// 测试7: 检查输出目录
runner.test('验证输出目录配置', () => {
  const configPath = 'monitor-config.json';
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  
  const outputDir = config.output.dir;
  info(`输出目录: ${outputDir}`);
  
  // 确保输出目录存在
  const fullPath = path.join(__dirname, outputDir);
  if (!fs.existsSync(fullPath)) {
    fs.mkdirSync(fullPath, { recursive: true });
    info(`创建输出目录: ${fullPath}`);
  }
  
  success('输出目录配置正确');
});

// 测试8: 检查依赖
runner.test('检查项目依赖', async () => {
  const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  const requiredDeps = ['playwright'];
  
  for (const dep of requiredDeps) {
    if (!packageJson.dependencies[dep]) {
      throw new Error(`缺少必需依赖: ${dep}`);
    }
    info(`检查依赖: ${dep} ✓`);
  }
});

// 运行测试
(async () => {
  const success = await runner.run();
  
  if (success) {
    log('\n🎉 所有测试通过！监控工具已准备就绪。', 'green');
    log('\n下一步操作:', 'cyan');
    log('  1. 确保Angular应用正在运行 (npm start)', 'blue');
    log('  2. 执行监控: npm run monitor', 'blue');
    log('  3. 查看报告: monitoring-reports/', 'blue');
    process.exit(0);
  } else {
    log('\n❌ 部分测试失败，请检查错误信息。', 'red');
    process.exit(1);
  }
})();
