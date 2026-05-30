#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

console.log('🔍 iMato 监控脚本验证工具\n');

// 检查文件
const files = [
  { name: '监控脚本', file: 'marketing-page-monitor.js' },
  { name: '修复工具', file: 'marketing-page-fixes.js' },
  { name: '持续监控', file: 'continuous-monitor.js' },
  { name: '测试运行器', file: 'test-runner.js' },
  { name: '配置文件', file: 'monitor-config.json' },
  { name: 'Package', file: 'package.json' }
];

console.log('📋 文件完整性检查:');
let allFilesExist = true;
files.forEach(({ name, file }) => {
  const exists = fs.existsSync(file);
  console.log(`${exists ? '✅' : '❌'} ${name}: ${file}`);
  if (!exists) allFilesExist = false;
});

if (!allFilesExist) {
  console.error('\n❌ 部分文件缺失，请检查！');
  process.exit(1);
}

// 检查JSON配置
console.log('\n⚙️  配置文件检查:');
try {
  const config = JSON.parse(fs.readFileSync('monitor-config.json', 'utf8'));
  console.log(`✅ 配置解析成功`);
  console.log(`   监控页面: ${config.pages.length} 个`);
  console.log(`   基础URL: ${config.baseUrl}`);
  console.log(`   输出目录: ${config.output.dir}`);
} catch (e) {
  console.error(`❌ 配置文件错误: ${e.message}`);
  process.exit(1);
}

// 检查Playwright
console.log('\n🔍 Playwright 检查:');
try {
  require.resolve('playwright');
  console.log('✅ Playwright 已安装');
} catch (e) {
  console.warn('⚠️  Playwright 未安装，运行时将自动安装');
}

// 检查输出目录
console.log('\n📂 输出目录检查:');
const outputDir = path.join(__dirname, '../monitoring-reports');
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
  console.log(`✅ 创建输出目录: ${outputDir}`);
} else {
  console.log(`✅ 输出目录已存在: ${outputDir}`);
}

// 检查应用是否在运行
console.log('\n🌐 应用状态检查:');
const http = require('http');
const config = JSON.parse(fs.readFileSync('monitor-config.json', 'utf8'));

http.get(config.baseUrl, (res) => {
  console.log(`✅ 应用正在运行: ${config.baseUrl} (状态: ${res.statusCode})`);
  console.log('\n🎉 所有检查通过！准备就绪。');
  console.log('\n📢 运行以下命令开始监控:');
  console.log('   node marketing-page-monitor.js');
  console.log('\n或查看快速开始指南:');
  console.log('   cat QUICKSTART.md');
}).on('error', (err) => {
  console.warn(`⚠️  应用未在 ${config.baseUrl} 运行`);
  console.log('   请先在另一个终端运行: npm start');
  console.log('\n🎉 其他检查通过！');
});
