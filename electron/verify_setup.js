#!/usr/bin/env node

/**
 * Electron 项目初始化验证脚本
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 验证 Electron 项目结构...\n');

const requiredFiles = [
  'package.json',
  'main.js',
  'preload.js',
  'README.md',
];

let allGood = true;

requiredFiles.forEach(file => {
  const filePath = path.join(__dirname, file);
  const exists = fs.existsSync(filePath);
  
  if (exists) {
    console.log(`✅ ${file}`);
  } else {
    console.log(`❌ ${file} - 缺失`);
    allGood = false;
  }
});

// 检查 package.json 内容
console.log('\n📋 检查 package.json 配置...');
try {
  const pkgPath = path.join(__dirname, 'package.json');
  const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
  
  const checks = [
    { name: 'name', value: pkg.name },
    { name: 'version', value: pkg.version },
    { name: 'main', value: pkg.main },
    { name: 'scripts.start', value: pkg.scripts?.start },
    { name: 'devDependencies.electron', value: pkg.devDependencies?.electron },
    { name: 'devDependencies.electron-builder', value: pkg.devDependencies?.['electron-builder'] },
  ];
  
  checks.forEach(check => {
    if (check.value) {
      console.log(`✅ ${check.name}: ${check.value}`);
    } else {
      console.log(`❌ ${check.name} - 未配置`);
      allGood = false;
    }
  });
} catch (error) {
  console.log('❌ package.json 解析失败:', error.message);
  allGood = false;
}

// 总结
console.log('\n' + '='.repeat(50));
if (allGood) {
  console.log('✅ Electron 项目初始化完成！');
  console.log('\n下一步：');
  console.log('1. cd electron');
  console.log('2. npm install');
  console.log('3. npm start');
} else {
  console.log('❌ 发现问题，请检查上述错误');
  process.exit(1);
}
