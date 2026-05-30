#!/usr/bin/env node

/**
 * 样式规范自动修复脚本
 * 批量修复颜色格式、!important使用等问题
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

console.log('🚀 开始样式规范自动修复...\n');

// 配置需要修复的文件模式
const CSS_FILES = [
  'src/styles/**/*.scss',
  'shared-styles/**/*.scss'
];

// 颜色转换映射表
const COLOR_FIXES = {
  '#4CAF50': '#4caf50',
  '#81C784': '#81c784', 
  '#388E3C': '#388e3c',
  '#ffffff': '#fff',
  '#FF9800': '#ff9800',
  '#FFB74D': '#ffb74d',
  '#F57C00': '#f57c00',
  '#000000': '#000',
  '#CF6679': '#cf6679',
  '#EF9A9A': '#ef9a9a',
  '#B00020': '#b00020',
  '#2196F3': '#2196f3',
  '#64B5F6': '#64b5f6',
  '#1976D2': '#1976d2',
  '#333333': '#333',
  '#444444': '#444',
  '#555555': '#555',
  '#666666': '#666',
  '#777777': '#777',
  '#888888': '#888',
  '#999999': '#999',
  '#AAAAAA': '#aaa',
  '#BBBBBB': '#bbb',
  '#CCCCCC': '#ccc',
  '#DDDDDD': '#ddd',
  '#EEEEEE': '#eee'
};

// 修复函数
function fixColorFormat(content) {
  let fixedContent = content;
  
  // 修复颜色十六进制格式
  Object.entries(COLOR_FIXES).forEach(([oldColor, newColor]) => {
    const regex = new RegExp(oldColor, 'gi');
    fixedContent = fixedContent.replace(regex, newColor);
  });
  
  return fixedContent;
}

function removeImportantDeclarations(content) {
  // 移除 !important 声明（需要谨慎处理）
  // 这里只是标记需要手动处理的位置
  const importantRegex = /(!important)/g;
  if (importantRegex.test(content)) {
    console.log('⚠️  发现 !important 声明，需要手动处理');
  }
  return content;
}

function fixPropertyOrder(content) {
  // 这个比较复杂，建议使用 stylelint --fix
  return content;
}

function fixMediaQueries(content) {
  // 修复媒体查询中的变量引用
  const mediaQueryFixes = {
    '\\$breakpoint-tablet': '768px',
    '\\$breakpoint-mobile': '480px',
    '\\$breakpoint-desktop': '1024px'
  };
  
  let fixedContent = content;
  Object.entries(mediaQueryFixes).forEach(([oldBreakpoint, newBreakpoint]) => {
    const regex = new RegExp(`\\(max-width:\\s*${oldBreakpoint}\\)`, 'g');
    fixedContent = fixedContent.replace(regex, `(max-width: ${newBreakpoint})`);
    
    const minRegex = new RegExp(`\\(min-width:\\s*${oldBreakpoint}\\)`, 'g');
    fixedContent = fixedContent.replace(minRegex, `(min-width: ${newBreakpoint})`);
  });
  
  return fixedContent;
}

// 处理单个文件
function processFile(filePath) {
  try {
    console.log(`📄 处理文件: ${filePath}`);
    
    const content = fs.readFileSync(filePath, 'utf8');
    let fixedContent = content;
    
    // 应用各种修复
    fixedContent = fixColorFormat(fixedContent);
    fixedContent = removeImportantDeclarations(fixedContent);
    fixedContent = fixMediaQueries(fixedContent);
    
    // 如果内容有变化，则写入文件
    if (fixedContent !== content) {
      fs.writeFileSync(filePath, fixedContent, 'utf8');
      console.log('✅ 已修复');
    } else {
      console.log('➖ 无需修改');
    }
    
  } catch (error) {
    console.error(`❌ 处理文件 ${filePath} 时出错:`, error.message);
  }
}

// 主执行函数
function main() {
  console.log('🔍 查找需要修复的样式文件...\n');
  
  CSS_FILES.forEach(pattern => {
    const files = glob.sync(pattern);
    console.log(`📁 找到 ${files.length} 个文件匹配模式: ${pattern}`);
    
    files.forEach(processFile);
  });
  
  console.log('\n✨ 样式规范修复完成！');
  console.log('💡 建议运行以下命令进行进一步检查:');
  console.log('   npm run lint:css');
  console.log('   npm run lint:css-fix');
}

// 执行主函数
main();