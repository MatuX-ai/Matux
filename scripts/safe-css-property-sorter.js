#!/usr/bin/env node

/**
 * 安全的CSS属性排序脚本
 * 
 * 采用保守策略，只处理明显可以安全重排的情况
 */

const fs = require('fs');
const path = require('path');

// 简化的属性排序规则（只处理最明显的案例）
const SIMPLE_PROPERTY_ORDER = [
  'position', 'top', 'right', 'bottom', 'left', 'z-index',
  'display', 'visibility', 'float', 'clear',
  'width', 'height', 'min-width', 'max-width', 'min-height', 'max-height',
  'margin', 'padding', 'border', 'border-radius',
  'background', 'background-color', 'box-shadow',
  'color', 'font-family', 'font-size', 'font-weight', 'line-height',
  'text-align', 'text-decoration',
  'cursor', 'user-select', 'pointer-events',
  'transition', 'transform', 'animation',
  'opacity'
];

// 获取属性优先级
function getPropertyPriority(property) {
  const index = SIMPLE_PROPERTY_ORDER.indexOf(property);
  return index === -1 ? SIMPLE_PROPERTY_ORDER.length : index;
}

// 安全地重新排序属性块
function safelySortProperties(lines, startIndex, endIndex) {
  const propertyLines = [];
  const otherLines = [];
  
  // 分离属性行和其他行
  for (let i = startIndex; i <= endIndex; i++) {
    const line = lines[i].trim();
    if (line && line.includes(':') && line.endsWith(';') && !line.includes('@')) {
      const property = line.split(':')[0].trim();
      propertyLines.push({
        line: lines[i],
        property,
        priority: getPropertyPriority(property),
        originalIndex: i
      });
    } else {
      otherLines.push({
        line: lines[i],
        originalIndex: i
      });
    }
  }
  
  // 只有当有足够多的属性且确实需要重排时才进行排序
  if (propertyLines.length < 3) {
    return false; // 太少属性，不值得重排
  }
  
  // 检查是否已经基本有序
  let disorderCount = 0;
  for (let i = 0; i < propertyLines.length - 1; i++) {
    if (propertyLines[i].priority > propertyLines[i + 1].priority) {
      disorderCount++;
    }
  }
  
  // 如果大部分已经有序，则不重排
  if (disorderCount < propertyLines.length * 0.3) {
    return false;
  }
  
  // 排序属性行
  propertyLines.sort((a, b) => {
    if (a.priority !== b.priority) {
      return a.priority - b.priority;
    }
    return a.property.localeCompare(b.property);
  });
  
  // 重建行数组
  const sortedLines = [];
  let propIndex = 0;
  let otherIndex = 0;
  
  for (let i = startIndex; i <= endIndex; i++) {
    const currentProp = propertyLines[propIndex];
    const currentOther = otherLines[otherIndex];
    
    if (currentProp && currentProp.originalIndex === i) {
      sortedLines.push(currentProp.line);
      propIndex++;
    } else if (currentOther && currentOther.originalIndex === i) {
      sortedLines.push(currentOther.line);
      otherIndex++;
    }
  }
  
  // 应用到原数组
  for (let i = 0; i < sortedLines.length; i++) {
    lines[startIndex + i] = sortedLines[i];
  }
  
  return true;
}

// 处理单个文件
function processFile(filePath) {
  try {
    console.log(`处理文件: ${filePath}`);
    
    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    let modified = false;
    
    // 查找SCSS声明块
    let inBlock = false;
    let blockStart = -1;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // 检测块开始
      if ((line.endsWith('{') && !line.startsWith('@')) || 
          (line.includes('{') && line.includes(':') && !line.includes('@mixin'))) {
        if (!inBlock) {
          inBlock = true;
          blockStart = i;
        }
      }
      
      // 检测块结束
      if (line === '}' && inBlock) {
        // 处理这个块
        if (i - blockStart > 3) { // 只处理有一定复杂度的块
          const wasModified = safelySortProperties(lines, blockStart + 1, i - 1);
          if (wasModified) {
            modified = true;
          }
        }
        inBlock = false;
        blockStart = -1;
      }
    }
    
    // 如果有修改，保存文件
    if (modified) {
      const newContent = lines.join('\n');
      fs.writeFileSync(filePath, newContent, 'utf8');
      console.log(`✅ 已优化: ${filePath}`);
      return { filePath, modified: true };
    } else {
      console.log(`✅ 无需修改: ${filePath}`);
      return { filePath, modified: false };
    }
    
  } catch (error) {
    console.error(`❌ 处理失败 ${filePath}:`, error.message);
    return { filePath, modified: false, error: error.message };
  }
}

// 主函数
async function main() {
  console.log('🛡️ 启动安全CSS属性排序...\n');
  
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
  
  for (const file of cssFiles) {
    const fullPath = path.join(process.cwd(), file);
    if (fs.existsSync(fullPath)) {
      const result = processFile(fullPath);
      results.push(result);
    }
  }
  
  // 统计
  const modifiedCount = results.filter(r => r.modified).length;
  const errorCount = results.filter(r => r.error).length;
  
  console.log('\n📊 处理结果:');
  console.log('=============');
  console.log(`总文件数: ${results.length}`);
  console.log(`修改文件数: ${modifiedCount}`);
  console.log(`错误文件数: ${errorCount}`);
  
  if (errorCount > 0) {
    console.log('\n❌ 错误文件:');
    results.filter(r => r.error).forEach(r => {
      console.log(`  ${r.filePath}: ${r.error}`);
    });
  }
  
  console.log('\n✨ 安全属性排序完成！');
}

// 执行
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { processFile, safelySortProperties };