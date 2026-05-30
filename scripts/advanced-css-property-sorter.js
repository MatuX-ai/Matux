#!/usr/bin/env node

/**
 * 高级CSS属性排序工具
 * 
 * 使用PostCSS进行精确的CSS解析和重排序
 * 支持复杂的嵌套结构和各种CSS特性
 */

const fs = require('fs');
const path = require('path');
const postcss = require('postcss');
const scss = require('postcss-scss');

// CSS 属性分类和排序规则
const PROPERTY_CATEGORIES = {
  // 1. CSS自定义属性
  customProperties: [/^--/],
  
  // 2. 定位属性
  positioning: ['position', 'inset', 'top', 'right', 'bottom', 'left', 'z-index'],
  
  // 3. 显示和布局
  displayLayout: [
    'display', 'visibility', 'float', 'clear', 'overflow', 'overflow-x', 'overflow-y',
    '-ms-overflow-x', '-ms-overflow-y', '-webkit-overflow-scrolling',
    'clip', 'clip-path', 'zoom'
  ],
  
  // 4. Flexbox
  flexbox: [
    'flex', 'flex-grow', 'flex-shrink', 'flex-basis', 'flex-direction', 
    'flex-wrap', 'flex-flow', 'order', 'justify-content', 'align-items',
    'align-content', 'align-self'
  ],
  
  // 5. Grid
  grid: [
    'grid', 'grid-area', 'grid-template', 'grid-template-columns', 
    'grid-template-rows', 'grid-template-areas', 'grid-auto-columns',
    'grid-auto-rows', 'grid-auto-flow', 'grid-column', 'grid-column-start',
    'grid-column-end', 'grid-row', 'grid-row-start', 'grid-row-end',
    'gap', 'grid-gap', 'grid-column-gap', 'grid-row-gap'
  ],
  
  // 6. 表格布局
  table: [
    'table-layout', 'empty-cells', 'caption-side', 'border-spacing', 
    'border-collapse', 'list-style', 'list-style-position', 'list-style-type',
    'list-style-image'
  ],
  
  // 7. 盒模型
  boxModel: [
    'box-sizing', 'width', 'min-width', 'max-width', 'height', 'min-height',
    'max-height', 'margin', 'margin-top', 'margin-right', 'margin-bottom',
    'margin-left', 'padding', 'padding-top', 'padding-right', 'padding-bottom',
    'padding-left'
  ],
  
  // 8. 边框
  border: [
    'border', 'border-width', 'border-style', 'border-color', 'border-top',
    'border-top-width', 'border-top-style', 'border-top-color', 'border-right',
    'border-right-width', 'border-right-style', 'border-right-color',
    'border-bottom', 'border-bottom-width', 'border-bottom-style',
    'border-bottom-color', 'border-left', 'border-left-width', 'border-left-style',
    'border-left-color', 'border-radius', 'border-top-left-radius',
    'border-top-right-radius', 'border-bottom-right-radius', 'border-bottom-left-radius',
    'border-image', 'border-image-source', 'border-image-slice', 'border-image-width',
    'border-image-outset', 'border-image-repeat'
  ],
  
  // 9. 轮廓
  outline: ['outline', 'outline-width', 'outline-style', 'outline-color', 'outline-offset'],
  
  // 10. 背景
  background: [
    'background', 'background-color', 'background-image', 'background-repeat',
    'background-attachment', 'background-position', 'background-position-x',
    'background-position-y', 'background-clip', 'background-origin', 'background-size',
    'box-decoration-break', 'box-shadow'
  ],
  
  // 11. 颜色和视觉效果
  colorVisual: ['color', 'opacity', 'filter', 'backdrop-filter'],
  
  // 12. 字体
  font: [
    'font', 'font-family', 'font-size', 'font-weight', 'font-style', 'font-variant',
    'font-size-adjust', 'font-stretch', 'font-effect', 'font-emphasize',
    'font-emphasize-position', 'font-emphasize-style', 'font-smooth', 'line-height'
  ],
  
  // 13. 文本
  text: [
    'text-align', 'text-align-last', 'vertical-align', 'white-space', 'text-decoration',
    'text-emphasis', 'text-emphasis-color', 'text-emphasis-style', 'text-emphasis-position',
    'text-indent', 'text-justify', 'letter-spacing', 'word-spacing', 'text-outline',
    'text-transform', 'text-wrap', 'text-overflow', 'text-overflow-ellipsis',
    'text-overflow-mode', 'word-wrap', 'word-break', 'tab-size', 'hyphens', 'unicode-bidi',
    'direction'
  ],
  
  // 14. 内容
  content: ['content', 'quotes', 'counter-reset', 'counter-increment'],
  
  // 15. 交互
  interaction: [
    'resize', 'cursor', 'pointer-events', 'user-select', 'touch-action',
    'nav-index', 'nav-up', 'nav-right', 'nav-down', 'nav-left'
  ],
  
  // 16. 过渡和变换
  transitionsTransforms: [
    'transition', 'transition-delay', 'transition-timing-function', 'transition-duration',
    'transition-property', 'transform', 'transform-origin', 'transform-style',
    'perspective', 'perspective-origin', 'backface-visibility'
  ],
  
  // 17. 动画
  animation: [
    'animation', 'animation-name', 'animation-duration', 'animation-play-state',
    'animation-timing-function', 'animation-delay', 'animation-iteration-count',
    'animation-direction', 'animation-fill-mode'
  ],
  
  // 18. 性能和其他
  performance: ['will-change', 'contain'],
  
  // 19. 打印和列
  printColumns: [
    'page-break-before', 'page-break-after', 'page-break-inside', 'orphans', 'widows',
    'columns', 'column-span', 'column-width', 'column-count', 'column-fill',
    'column-gap', 'column-rule', 'column-rule-width', 'column-rule-style', 'column-rule-color'
  ]
};

// 构建完整的排序映射
const PROPERTY_ORDER_MAP = new Map();
let orderIndex = 0;

Object.entries(PROPERTY_CATEGORIES).forEach(([category, properties]) => {
  properties.forEach(prop => {
    if (typeof prop === 'string') {
      PROPERTY_ORDER_MAP.set(prop, orderIndex++);
    } else if (prop instanceof RegExp) {
      // 正则表达式的优先级稍低
      PROPERTY_ORDER_MAP.set(prop, orderIndex++);
    }
  });
});

// 获取属性排序优先级
function getPropertyOrder(property) {
  // 精确匹配
  if (PROPERTY_ORDER_MAP.has(property)) {
    return PROPERTY_ORDER_MAP.get(property);
  }
  
  // 正则匹配
  for (const [key, value] of PROPERTY_ORDER_MAP.entries()) {
    if (key instanceof RegExp && key.test(property)) {
      return value;
    }
  }
  
  // 未知属性放在最后
  return Infinity;
}

// 对声明数组进行排序
function sortDeclarations(declarations) {
  return [...declarations].sort((a, b) => {
    const orderA = getPropertyOrder(a.prop);
    const orderB = getPropertyOrder(b.prop);
    
    if (orderA !== orderB) {
      return orderA - orderB;
    }
    
    // 相同类别内按字母顺序
    return a.prop.localeCompare(b.prop);
  });
}

// PostCSS插件：重新排序CSS属性
const propertyOrderPlugin = postcss.plugin('property-order', () => {
  return (root) => {
    root.walkRules((rule) => {
      // 收集所有声明
      const declarations = [];
      const otherNodes = [];
      
      rule.each((node) => {
        if (node.type === 'decl') {
          declarations.push(node);
        } else {
          otherNodes.push(node);
        }
      });
      
      // 如果有多个声明，进行排序
      if (declarations.length > 1) {
        const sortedDeclarations = sortDeclarations(declarations);
        
        // 检查是否需要重排
        const needsSorting = declarations.some((decl, index) => 
          decl !== sortedDeclarations[index]
        );
        
        if (needsSorting) {
          // 清空规则内的所有节点
          rule.removeAll();
          
          // 按排序后的顺序添加声明
          sortedDeclarations.forEach(decl => {
            rule.append(decl);
          });
          
          // 添加其他节点（如嵌套规则、注释等）
          otherNodes.forEach(node => {
            rule.append(node);
          });
        }
      }
    });
  };
});

// 优化单个CSS文件
async function optimizeCssFile(filePath) {
  try {
    console.log(`正在处理: ${filePath}`);
    
    const content = fs.readFileSync(filePath, 'utf8');
    
    // 使用PostCSS处理SCSS
    const result = await postcss([
      propertyOrderPlugin()
    ]).process(content, {
      from: filePath,
      to: filePath,
      parser: scss
    });
    
    // 检查是否有变化
    if (result.css !== content) {
      fs.writeFileSync(filePath, result.css, 'utf8');
      console.log(`✅ 已优化: ${filePath}`);
      return { filePath, modified: true, changes: 1 };
    } else {
      console.log(`✅ 无需修改: ${filePath}`);
      return { filePath, modified: false, changes: 0 };
    }
    
  } catch (error) {
    console.error(`❌ 处理失败 ${filePath}:`, error.message);
    return { filePath, modified: false, error: error.message };
  }
}

// 主函数
async function main() {
  console.log('🚀 启动高级CSS属性排序优化...\n');
  
  // 要处理的文件列表
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
  
  // 逐个处理文件
  for (const file of cssFiles) {
    const fullPath = path.join(process.cwd(), file);
    if (fs.existsSync(fullPath)) {
      const result = await optimizeCssFile(fullPath);
      results.push(result);
    } else {
      console.log(`⚠️  文件不存在: ${file}`);
    }
  }
  
  // 统计结果
  const totalFiles = results.length;
  const modifiedFiles = results.filter(r => r.modified).length;
  const errorFiles = results.filter(r => r.error).length;
  const totalChanges = results.reduce((sum, r) => sum + (r.changes || 0), 0);
  
  console.log('\n📊 优化完成统计:');
  console.log('==================');
  console.log(`总文件数: ${totalFiles}`);
  console.log(`修改文件数: ${modifiedFiles}`);
  console.log(`总变更数: ${totalChanges}`);
  console.log(`错误文件数: ${errorFiles}`);
  
  if (errorFiles > 0) {
    console.log('\n❌ 错误详情:');
    results.filter(r => r.error).forEach(r => {
      console.log(`  ${r.filePath}: ${r.error}`);
    });
  }
  
  console.log('\n✨ 高级属性排序优化完成！');
  
  return errorFiles === 0;
}

// 执行
if (require.main === module) {
  main().then(success => {
    process.exit(success ? 0 : 1);
  }).catch(error => {
    console.error('执行出错:', error);
    process.exit(1);
  });
}

module.exports = { optimizeCssFile, main, PROPERTY_CATEGORIES, getPropertyOrder };