#!/usr/bin/env node

/**
 * CSS 属性排序验证脚本
 * 
 * 用于验证CSS文件是否遵循正确的属性排序规则
 */

const fs = require('fs');
const path = require('path');

// CSS 属性排序规则（简化版本用于验证）
const PROPERTY_ORDER = [
  // CSS 自定义属性
  /^--.*/,
  
  // 定位属性
  'position', 'inset', 'top', 'right', 'bottom', 'left', 'z-index',
  
  // 显示和盒模型
  'display', 'visibility', 'float', 'clear', 'overflow', 'overflow-x', 'overflow-y',
  
  // Flexbox 属性
  'flex', 'flex-grow', 'flex-shrink', 'flex-basis', 'flex-direction', 
  'flex-wrap', 'flex-flow', 'order', 'justify-content', 'align-items',
  'align-content', 'align-self',
  
  // Grid 属性
  'grid', 'grid-area', 'grid-template', 'grid-template-columns', 
  'grid-template-rows', 'grid-auto-columns', 'grid-auto-rows',
  'grid-column', 'grid-row', 'gap',
  
  // 盒模型
  'box-sizing', 'width', 'min-width', 'max-width', 'height', 'min-height',
  'max-height', 'margin', 'padding', 'border', 'border-radius',
  
  // 背景
  'background', 'background-color', 'background-image', 'box-shadow',
  
  // 字体排版
  'font', 'font-family', 'font-size', 'font-weight', 'line-height',
  
  // 文本
  'color', 'text-align', 'text-decoration', 'white-space',
  
  // 交互
  'cursor', 'user-select', 'pointer-events',
  
  // 过渡和动画
  'transition', 'transform', 'animation',
  
  // 其他
  'opacity', 'filter', 'content'
];

// 获取属性优先级
function getPropertyPriority(property) {
  for (let i = 0; i < PROPERTY_ORDER.length; i++) {
    const rule = PROPERTY_ORDER[i];
    if (typeof rule === 'string' && rule === property) {
      return i;
    } else if (rule instanceof RegExp && rule.test(property)) {
      return i;
    }
  }
  return PROPERTY_ORDER.length;
}

// 验证单个CSS文件
function validateCssFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    
    // 简单的属性提取正则（适用于验证）
    const propertyRegex = /([a-zA-Z\-]+):\s*[^;]+;/g;
    const properties = [];
    let match;
    
    while ((match = propertyRegex.exec(content)) !== null) {
      const property = match[1].trim();
      properties.push({
        property,
        priority: getPropertyPriority(property),
        line: (content.substr(0, match.index).match(/\n/g) || []).length + 1
      });
    }
    
    // 检查排序问题
    const issues = [];
    for (let i = 0; i < properties.length - 1; i++) {
      const current = properties[i];
      const next = properties[i + 1];
      
      if (current.priority > next.priority) {
        issues.push({
          line: current.line,
          current: current.property,
          next: next.property,
          message: `属性 "${current.property}" 应该在 "${next.property}" 之后`
        });
      }
    }
    
    return {
      filePath: path.relative(process.cwd(), filePath),
      totalProperties: properties.length,
      issues: issues.slice(0, 10), // 只显示前10个问题
      hasIssues: issues.length > 0
    };
    
  } catch (error) {
    return {
      filePath: path.relative(process.cwd(), filePath),
      error: error.message,
      hasIssues: true
    };
  }
}

// 主验证函数
async function validateAllCssFiles() {
  console.log('🔍 开始验证CSS属性排序...\n');
  
  // 要验证的核心文件
  const cssFiles = [
    'src/styles/components/button.scss',
    'src/styles/components/card.scss',
    'src/styles/components/input.scss',
    'src/styles/components/icon.scss',
    'src/styles/layout.scss',
    'src/styles/main.scss',
    'src/styles/reset.scss',
    'src/styles/typography.scss'
  ];
  
  const results = [];
  let totalIssues = 0;
  
  for (const file of cssFiles) {
    const fullPath = path.join(process.cwd(), file);
    if (fs.existsSync(fullPath)) {
      const result = validateCssFile(fullPath);
      results.push(result);
      if (result.hasIssues) {
        totalIssues++;
      }
    }
  }
  
  // 输出结果
  console.log('📋 验证结果:');
  console.log('=============');
  
  results.forEach(result => {
    if (result.error) {
      console.log(`❌ ${result.filePath}: ${result.error}`);
    } else if (result.hasIssues) {
      console.log(`⚠️  ${result.filePath}: 发现 ${result.issues.length} 个排序问题 (${result.totalProperties} 个属性)`);
      result.issues.forEach(issue => {
        console.log(`   第${issue.line}行: ${issue.message}`);
      });
    } else {
      console.log(`✅ ${result.filePath}: 属性排序正确 (${result.totalProperties} 个属性)`);
    }
  });
  
  console.log(`\n📊 总结:`);
  console.log(`验证文件数: ${results.length}`);
  console.log(`有问题文件: ${totalIssues}`);
  console.log(`通过文件数: ${results.length - totalIssues}`);
  
  if (totalIssues === 0) {
    console.log('\n🎉 所有CSS文件属性排序均符合规范！');
  } else {
    console.log('\n🔧 建议运行优化脚本修复排序问题');
  }
  
  return totalIssues === 0;
}

// 执行验证
if (require.main === module) {
  validateAllCssFiles().then(success => {
    process.exit(success ? 0 : 1);
  }).catch(error => {
    console.error('验证过程出错:', error);
    process.exit(1);
  });
}

module.exports = { validateCssFile, validateAllCssFiles };