#!/usr/bin/env node

/**
 * 验证营销页面重命名是否成功
 * 检查所有路由和文件引用是否正确
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 验证 Marketing 页面重命名...\n');

const marketingDir = path.join(__dirname, 'src/app/marketing');
const issues = [];

// 检查文件是否存在
const expectedFiles = [
  'marketing-home/home.ts',
  'marketing-home/home.html',
  'marketing-home/home.scss',
  'marketing-pricing/pricing.ts',
  'marketing-features/features.ts',
  'marketing-about/about.ts',
  'marketing-contact/contact.ts',
  'marketing-routing.module.ts'
];

console.log('📂 检查文件结构...');
expectedFiles.forEach(file => {
  const fullPath = path.join(marketingDir, file);
  if (fs.existsSync(fullPath)) {
    console.log(`   ✅ ${file}`);
  } else {
    console.log(`   ❌ ${file} 不存在`);
    issues.push(`文件缺失: ${file}`);
  }
});

// 检查路由配置
console.log('\n🛣️  检查路由配置...');
const routingPath = path.join(marketingDir, 'marketing-routing.module.ts');
if (fs.existsSync(routingPath)) {
  const content = fs.readFileSync(routingPath, 'utf-8');
  
  const expectedImports = [
    "import('./marketing-home/home')",
    "import('./marketing-pricing/pricing')",
    "import('./marketing-features/features')",
    "import('./marketing-about/about')",
    "import('./marketing-contact/contact')"
  ];
  
  expectedImports.forEach(imp => {
    if (content.includes(imp)) {
      console.log(`   ✅ ${imp}`);
    } else {
      console.log(`   ❌ 路由配置中未找到: ${imp}`);
      issues.push(`路由配置错误: ${imp}`);
    }
  });
} else {
  console.log('   ❌ marketing-routing.module.ts 不存在');
  issues.push('路由配置文件不存在');
}

// 检查home.ts的templateUrl和styleUrls
console.log('\n🎨 检查模板路径...');
const homeTsPath = path.join(marketingDir, 'marketing-home/home.ts');
if (fs.existsSync(homeTsPath)) {
  const content = fs.readFileSync(homeTsPath, 'utf-8');
  
  if (content.includes("templateUrl: './home.html'")) {
    console.log("   ✅ home.ts templateUrl 正确");
  } else {
    console.log("   ❌ home.ts templateUrl 错误");
    issues.push("home.ts templateUrl 需要修复");
  }
  
  if (content.includes("styleUrls: ['./home.scss']")) {
    console.log("   ✅ home.ts styleUrls 正确");
  } else {
    console.log("   ❌ home.ts styleUrls 错误");
    issues.push("home.ts styleUrls 需要修复");
  }
}

// 总结
console.log('\n' + '='.repeat(50));
if (issues.length === 0) {
  console.log('✅ 所有检查通过！重命名成功完成。');
  console.log('\n📝 下一步操作:');
  console.log('   1. 运行: npm start');
  console.log('   2. 访问: http://localhost:4200');
  console.log('   3. 验证所有页面加载正常');
  process.exit(0);
} else {
  console.log(`❌ 发现 ${issues.length} 个问题:`);
  issues.forEach(issue => console.log(`   - ${issue}`));
  console.log('\n🔧 需要手动修复上述问题');
  process.exit(1);
}
