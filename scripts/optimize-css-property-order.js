#!/usr/bin/env node

/**
 * CSS 属性顺序优化脚本
 * 
 * 功能：
 * 1. 分析CSS文件中的属性顺序
 * 2. 根据最佳实践重新排序属性
 * 3. 生成优化报告
 * 4. 自动修复常见排序问题
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

// CSS 属性排序规则（按照最佳实践）
const PROPERTY_ORDER = [
  // CSS 自定义属性
  /^--.*/,
  
  // 定位属性
  'position', 'inset', 'top', 'right', 'bottom', 'left', 'z-index',
  
  // 显示和盒模型
  'display', 'visibility', 'float', 'clear', 'overflow', 'overflow-x', 'overflow-y',
  '-ms-overflow-x', '-ms-overflow-y', '-webkit-overflow-scrolling',
  'clip', 'clip-path', 'zoom',
  
  // Flexbox 属性
  'flex', 'flex-grow', 'flex-shrink', 'flex-basis', 'flex-direction', 
  'flex-wrap', 'flex-flow', 'order', 'justify-content', 'align-items',
  'align-content', 'align-self',
  
  // Grid 属性
  'grid', 'grid-area', 'grid-template', 'grid-template-columns', 
  'grid-template-rows', 'grid-template-areas', 'grid-auto-columns',
  'grid-auto-rows', 'grid-auto-flow', 'grid-column', 'grid-column-start',
  'grid-column-end', 'grid-row', 'grid-row-start', 'grid-row-end',
  'gap', 'grid-gap', 'grid-column-gap', 'grid-row-gap',
  
  // 表格布局
  'table-layout', 'empty-cells', 'caption-side', 'border-spacing', 
  'border-collapse', 'list-style', 'list-style-position', 'list-style-type',
  'list-style-image',
  
  // 盒模型
  'box-sizing', 'width', 'min-width', 'max-width', 'height', 'min-height',
  'max-height', 'margin', 'margin-top', 'margin-right', 'margin-bottom',
  'margin-left', 'padding', 'padding-top', 'padding-right', 'padding-bottom',
  'padding-left',
  
  // 边框
  'border', 'border-width', 'border-style', 'border-color', 'border-top',
  'border-top-width', 'border-top-style', 'border-top-color', 'border-right',
  'border-right-width', 'border-right-style', 'border-right-color',
  'border-bottom', 'border-bottom-width', 'border-bottom-style',
  'border-bottom-color', 'border-left', 'border-left-width', 'border-left-style',
  'border-left-color', 'border-radius', 'border-top-left-radius',
  'border-top-right-radius', 'border-bottom-right-radius', 'border-bottom-left-radius',
  'border-image', 'border-image-source', 'border-image-slice', 'border-image-width',
  'border-image-outset', 'border-image-repeat',
  
  // 轮廓
  'outline', 'outline-width', 'outline-style', 'outline-color', 'outline-offset',
  
  // 背景
  'background', 'background-color', 'background-image', 'background-repeat',
  'background-attachment', 'background-position', 'background-position-x',
  'background-position-y', 'background-clip', 'background-origin', 'background-size',
  'box-decoration-break', 'box-shadow',
  
  // 颜色和透明度
  'color', 'opacity', 'filter', 'backdrop-filter',
  
  // 字体排版
  'font', 'font-family', 'font-size', 'font-weight', 'font-style', 'font-variant',
  'font-size-adjust', 'font-stretch', 'font-effect', 'font-emphasize',
  'font-emphasize-position', 'font-emphasize-style', 'font-smooth', 'line-height',
  
  // 文本
  'text-align', 'text-align-last', 'vertical-align', 'white-space', 'text-decoration',
  'text-emphasis', 'text-emphasis-color', 'text-emphasis-style', 'text-emphasis-position',
  'text-indent', 'text-justify', 'letter-spacing', 'word-spacing', 'text-outline',
  'text-transform', 'text-wrap', 'text-overflow', 'text-overflow-ellipsis',
  'text-overflow-mode', 'word-wrap', 'word-break', 'tab-size', 'hyphens', 'unicode-bidi',
  'direction',
  
  // 内容
  'content', 'quotes', 'counter-reset', 'counter-increment',
  
  // 交互
  'resize', 'cursor', 'pointer-events', 'user-select', 'touch-action',
  
  // 导航
  'nav-index', 'nav-up', 'nav-right', 'nav-down', 'nav-left',
  
  // 过渡和动画
  'transition', 'transition-delay', 'transition-timing-function', 'transition-duration',
  'transition-property', 'transform', 'transform-origin', 'transform-style',
  'perspective', 'perspective-origin', 'backface-visibility',
  
  // 动画
  'animation', 'animation-name', 'animation-duration', 'animation-play-state',
  'animation-timing-function', 'animation-delay', 'animation-iteration-count',
  'animation-direction', 'animation-fill-mode',
  
  // 性能
  'will-change', 'contain',
  
  // 打印
  'page-break-before', 'page-break-after', 'page-break-inside', 'orphans', 'widows',
  
  // 列
  'columns', 'column-span', 'column-width', 'column-count', 'column-fill',
  'column-gap', 'column-rule', 'column-rule-width', 'column-rule-style', 'column-rule-color'
];

// 获取属性在排序中的优先级
function getPropertyPriority(property) {
  for (let i = 0; i < PROPERTY_ORDER.length; i++) {
    const rule = PROPERTY_ORDER[i];
    if (typeof rule === 'string' && rule === property) {
      return i;
    } else if (rule instanceof RegExp && rule.test(property)) {
      return i;
    }
  }
  return PROPERTY_ORDER.length; // 未找到的属性放到最后
}

// 解析CSS声明块
function parseDeclarationBlock(cssContent, startIndex) {
  let braceCount = 0;
  let endIndex = startIndex;
  
  for (let i = startIndex; i < cssContent.length; i++) {
    const char = cssContent[i];
    if (char === '{') {
      braceCount++;
    } else if (char === '}') {
      braceCount--;
      if (braceCount === 0) {
        endIndex = i;
        break;
      }
    }
  }
  
  return endIndex;
}

// 提取声明块中的属性
function extractDeclarations(blockContent) {
  const declarations = [];
  const declarationRegex = /([^;\{\}]+?):([^;\{\}]+?);/g;
  let match;
  
  while ((match = declarationRegex.exec(blockContent)) !== null) {
    const property = match[1].trim();
    const value = match[2].trim();
    declarations.push({ property, value, index: match.index });
  }
  
  return declarations;
}

// 对属性进行排序
function sortDeclarations(declarations) {
  return [...declarations].sort((a, b) => {
    const priorityA = getPropertyPriority(a.property);
    const priorityB = getPropertyPriority(b.property);
    
    if (priorityA !== priorityB) {
      return priorityA - priorityB;
    }
    return a.property.localeCompare(b.property); // 相同优先级按字母排序
  });
}

// 优化单个CSS文件
function optimizeCssFile(filePath) {
  console.log(`正在优化文件: ${filePath}`);
  
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    let optimizedContent = content;
    let modifications = 0;
    
    // 查找所有的声明块
    const blockRegex = /\{[^{}]*\}/g;
    let match;
    
    while ((match = blockRegex.exec(content)) !== null) {
      const blockStart = match.index;
      const blockEnd = blockStart + match[0].length;
      const blockContent = match[0];
      
      // 提取声明
      const declarations = extractDeclarations(blockContent);
      
      if (declarations.length > 1) {
        // 排序声明
        const sortedDeclarations = sortDeclarations(declarations);
        
        // 检查是否需要重排
        const isSorted = declarations.every((decl, index) => 
          decl.property === sortedDeclarations[index].property
        );
        
        if (!isSorted) {
          // 重构声明块
          let newBlockContent = '{\n';
          sortedDeclarations.forEach(decl => {
            newBlockContent += `  ${decl.property}: ${decl.value};\n`;
          });
          newBlockContent += '}';
          
          // 替换原内容
          const beforeBlock = optimizedContent.substring(0, blockStart);
          const afterBlock = optimizedContent.substring(blockEnd);
          optimizedContent = beforeBlock + newBlockContent + afterBlock;
          
          modifications++;
        }
      }
    }
    
    // 如果有修改，保存文件
    if (modifications > 0) {
      fs.writeFileSync(filePath, optimizedContent, 'utf8');
      console.log(`✅ 已优化 ${modifications} 个声明块`);
    } else {
      console.log('✅ 文件已符合属性排序要求');
    }
    
    return { filePath, modifications };
    
  } catch (error) {
    console.error(`❌ 优化文件失败 ${filePath}:`, error.message);
    return { filePath, modifications: 0, error: error.message };
  }
}

// 主函数
async function main() {
  console.log('🚀 开始CSS属性顺序优化...\n');
  
  // 定义要优化的文件路径
  const cssFiles = [
    'src/styles/components/button.scss',
    'src/styles/components/card.scss',
    'src/styles/components/input.scss',
    'src/styles/components/icon.scss',
    'src/styles/layout.scss',
    'src/styles/main.scss',
    'src/styles/reset.scss',
    'src/styles/typography.scss',
    'src/styles/breakpoints.scss'
  ];
  
  const results = [];
  
  // 优化每个文件
  for (const file of cssFiles) {
    const fullPath = path.join(process.cwd(), file);
    if (fs.existsSync(fullPath)) {
      const result = optimizeCssFile(fullPath);
      results.push(result);
    } else {
      console.log(`⚠️  文件不存在: ${file}`);
    }
  }
  
  // 生成报告
  console.log('\n📊 优化完成统计:');
  console.log('===================');
  
  const totalModifications = results.reduce((sum, result) => sum + result.modifications, 0);
  const optimizedFiles = results.filter(r => r.modifications > 0).length;
  const errorFiles = results.filter(r => r.error).length;
  
  console.log(`总文件数: ${results.length}`);
  console.log(`优化文件数: ${optimizedFiles}`);
  console.log(`总修改次数: ${totalModifications}`);
  console.log(`错误文件数: ${errorFiles}`);
  
  if (errorFiles > 0) {
    console.log('\n❌ 错误详情:');
    results.filter(r => r.error).forEach(result => {
      console.log(`  ${result.filePath}: ${result.error}`);
    });
  }
  
  console.log('\n✨ 属性排序优化完成！');
}

// 执行主函数
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { optimizeCssFile, PROPERTY_ORDER, getPropertyPriority };