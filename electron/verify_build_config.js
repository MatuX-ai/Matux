#!/usr/bin/env node

/**
 * Electron Builder 配置验证脚本
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

console.log('🔍 验证 Electron Builder 配置...\n');

// 检查 electron-builder.yml
console.log('1️⃣ 检查配置文件...');
const configPath = path.join(__dirname, 'electron-builder.yml');
if (!fs.existsSync(configPath)) {
  console.log('❌ electron-builder.yml - 文件不存在');
  process.exit(1);
}

try {
  const config = yaml.load(fs.readFileSync(configPath, 'utf8'));
  console.log('✅ electron-builder.yml - 格式正确');
  
  // 验证关键配置
  const checks = [
    { name: 'appId', value: config.appId },
    { name: 'productName', value: config.productName },
    { name: 'win.target', value: config.win?.target ? '✅' : '❌' },
    { name: 'nsis.oneClick', value: config.nsis ? '✅' : '❌' },
  ];
  
  console.log('\n2️⃣ 检查关键配置...');
  checks.forEach(check => {
    if (check.value) {
      console.log(`✅ ${check.name}: ${check.value}`);
    } else {
      console.log(`❌ ${check.name} - 未配置`);
    }
  });
} catch (error) {
  console.log('❌ YAML 解析失败:', error.message);
  process.exit(1);
}

// 检查 package.json
console.log('\n3️⃣ 检查 package.json...');
const pkgPath = path.join(__dirname, 'package.json');
const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));

const scripts = pkg.scripts || {};
if (scripts.build && scripts.build.includes('electron-builder')) {
  console.log('✅ build 脚本已配置');
} else {
  console.log('❌ build 脚本未正确配置');
}

if (scripts['build:portable'] && scripts['build:portable'].includes('portable')) {
  console.log('✅ portable 构建已配置');
} else {
  console.log('❌ portable 构建未配置');
}

// 检查 build 目录
console.log('\n4️⃣ 检查构建资源...');
const buildDir = path.join(__dirname, 'build');
if (fs.existsSync(buildDir)) {
  console.log('✅ build 目录存在');
  
  const iconPath = path.join(buildDir, 'icon.ico');
  if (fs.existsSync(iconPath)) {
    console.log('✅ icon.ico - 已找到');
  } else {
    console.log('⚠️  icon.ico - 缺失（需要添加）');
  }
} else {
  console.log('❌ build 目录不存在');
}

// 总结
console.log('\n' + '='.repeat(50));
console.log('✅ Electron Builder 配置验证完成！');
console.log('\n下一步操作：');
console.log('1. 准备 icon.ico 图标文件（放入 build/ 目录）');
console.log('2. npm install');
console.log('3. npm run build');
console.log('\n注意事项：');
console.log('- 首次构建会自动下载依赖，可能需要几分钟');
console.log('- 安装包将生成在 dist/ 目录');
console.log('- 确保有足够的磁盘空间（约 500MB）');
