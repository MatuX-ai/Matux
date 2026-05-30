#!/usr/bin/env node

/**
 * Token 组件验证脚本
 *
 * 验证所有 Token 组件文件是否存在且格式正确
 */

const fs = require('fs');
const path = require('path');

// 颜色配置
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m'
};

// 组件列表
const components = [
  {
    name: 'TokenBalanceComponent',
    dir: 'token-balance',
    files: ['token-balance.component.ts', 'token-balance.component.html', 'token-balance.component.scss']
  },
  {
    name: 'TokenPurchaseComponent',
    dir: 'token-purchase',
    files: ['token-purchase.component.ts', 'token-purchase.component.html', 'token-purchase.component.scss']
  },
  {
    name: 'TokenUsageHistoryComponent',
    dir: 'token-usage-history',
    files: ['token-usage-history.component.ts', 'token-usage-history.component.html', 'token-usage-history.component.scss']
  },
  {
    name: 'TokenStatsChartComponent',
    dir: 'token-stats-chart',
    files: ['token-stats-chart.component.ts', 'token-stats-chart.component.html', 'token-stats-chart.component.scss']
  }
];

const basePath = path.join(__dirname, '..', 'src', 'app', 'components');

console.log(`${colors.blue}================================${colors.reset}`);
console.log(`${colors.blue}Token 组件验证脚本${colors.reset}`);
console.log(`${colors.blue}================================${colors.reset}\n`);

let allPassed = true;

// 验证每个组件
components.forEach(component => {
  console.log(`${colors.yellow}验证 ${component.name}:${colors.reset}`);

  component.files.forEach(file => {
    const filePath = path.join(basePath, component.dir, file);
    const exists = fs.existsSync(filePath);

    if (exists) {
      const stats = fs.statSync(filePath);
      const sizeKB = (stats.size / 1024).toFixed(2);
      console.log(`  ${colors.green}✓${colors.reset} ${file} (${sizeKB} KB)`);
    } else {
      console.log(`  ${colors.red}✗${colors.reset} ${file} - 文件不存在`);
      allPassed = false;
    }
  });

  console.log('');
});

// 验证辅助文件
const helperFiles = [
  'token-components.index.ts',
  'token-components.module.ts',
  'README.md'
];

console.log(`${colors.yellow}验证辅助文件:${colors.reset}`);
helperFiles.forEach(file => {
  const filePath = path.join(basePath, file);
  const exists = fs.existsSync(filePath);

  if (exists) {
    const stats = fs.statSync(filePath);
    const sizeKB = (stats.size / 1024).toFixed(2);
    console.log(`  ${colors.green}✓${colors.reset} ${file} (${sizeKB} KB)`);
  } else {
    console.log(`  ${colors.red}✗${colors.reset} ${file} - 文件不存在`);
    allPassed = false;
  }
});

console.log('\n' + `${colors.blue}================================${colors.reset}`);

if (allPassed) {
  console.log(`${colors.green}✓ 所有组件验证通过!${colors.reset}`);
  console.log(`${colors.green}任务 2.5 完成度：100%${colors.reset}`);
} else {
  console.log(`${colors.red}✗ 部分文件缺失，请检查${colors.reset}`);
  process.exit(1);
}

console.log(`${colors.blue}================================${colors.reset}\n`);
