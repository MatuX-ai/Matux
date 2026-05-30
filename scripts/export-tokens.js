/**
 * Design Token JSON Exporter
 * 将TypeScript格式的Design Tokens转换为JSON格式供多平台使用
 */

const fs = require('fs');
const path = require('path');

// 确保输出目录存在
function ensureOutputDir() {
  const outputDir = path.join(__dirname, '../dist/tokens');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  return outputDir;
}

// 解析TS文件中的export const对象
function parseTsExport(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  
  // 简单的正则表达式匹配export const对象
  // 注意：这只是基础实现，实际项目中可能需要更复杂的AST解析
  const exportMatches = content.match(/export\s+const\s+(\w+)\s*=\s*({[\s\S]*?});?\s*(as const)?/g);
  
  if (!exportMatches) {
    console.warn(`未找到export const声明在文件: ${filePath}`);
    return {};
  }
  
  const result = {};
  
  exportMatches.forEach(match => {
    const nameMatch = match.match(/export\s+const\s+(\w+)\s*=/);
    if (nameMatch) {
      const varName = nameMatch[1];
      
      // 提取对象内容并尝试解析
      const objMatch = match.match(/=\s*({[\s\S]*?})\s*;?\s*(as const)?/);
      if (objMatch) {
        try {
          // 移除注释和多余的空白
          let objStr = objMatch[1]
            .replace(/\/\*[\s\S]*?\*\//g, '') // 块注释
            .replace(/\/\/.*$/gm, '') // 行注释
            .trim();
          
          // 处理简单的值引用（如 ...primaryColors）
          objStr = objStr.replace(/\.\.\.(\w+)/g, '"SPREAD_$1"');
          
          // 解析JSON-like字符串
          const parsedObj = eval(`(${objStr})`);
          result[varName] = parsedObj;
        } catch (error) {
          console.warn(`解析对象失败 ${varName} in ${filePath}:`, error.message);
          // 如果解析失败，保存原始字符串
          result[varName] = objMatch[1];
        }
      }
    }
  });
  
  return result;
}

// 从现有TS tokens生成JSON
function generateTokensFromExisting() {
  const tokensDir = path.join(__dirname, '../src/design-tokens');
  const outputDir = ensureOutputDir();
  
  const tokenFiles = [
    'colors',
    'fonts', 
    'spacing',
    'border-radius',
    'shadows'
  ];
  
  console.log('开始导出Design Tokens为JSON格式...\n');
  
  tokenFiles.forEach(fileName => {
    const tsPath = path.join(tokensDir, `${fileName}.ts`);
    
    if (fs.existsSync(tsPath)) {
      console.log(`处理文件: ${fileName}.ts`);
      
      try {
        const parsedData = parseTsExport(tsPath);
        
        // 合并所有导出的对象
        let mergedData = {};
        Object.keys(parsedData).forEach(key => {
          if (typeof parsedData[key] === 'object' && parsedData[key] !== null) {
            // 如果是对象，合并到根级别
            Object.assign(mergedData, parsedData[key]);
          } else {
            // 如果是简单值，直接赋值
            mergedData[key] = parsedData[key];
          }
        });
        
        // 特殊处理：展开spread操作符引用
        Object.keys(mergedData).forEach(key => {
          if (typeof mergedData[key] === 'string' && mergedData[key].startsWith('SPREAD_')) {
            const refName = mergedData[key].substring(7);
            if (parsedData[refName]) {
              mergedData = { ...mergedData, ...parsedData[refName] };
              delete mergedData[key];
            }
          }
        });
        
        const outputPath = path.join(outputDir, `${fileName}.json`);
        fs.writeFileSync(outputPath, JSON.stringify(mergedData, null, 2));
        console.log(`✅ 成功导出: ${fileName}.json (${Object.keys(mergedData).length} 个tokens)`);
        
      } catch (error) {
        console.error(`❌ 导出失败 ${fileName}.ts:`, error.message);
      }
    } else {
      console.warn(`⚠️ 文件不存在: ${tsPath}`);
    }
  });
  
  // 生成完整的tokens索引文件
  generateTokensIndex(outputDir, tokenFiles);
  
  console.log('\n🎉 所有Design Tokens导出完成！');
}

// 生成tokens索引文件
function generateTokensIndex(outputDir, tokenFiles) {
  const indexData = {
    metadata: {
      name: "iMatuProject Design Tokens",
      version: "1.0.0",
      exportedAt: new Date().toISOString(),
      format: "json"
    },
    tokens: {}
  };
  
  tokenFiles.forEach(fileName => {
    const jsonPath = path.join(outputDir, `${fileName}.json`);
    if (fs.existsSync(jsonPath)) {
      try {
        const fileData = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
        indexData.tokens[fileName] = fileData;
      } catch (error) {
        console.warn(`无法读取tokens文件 ${fileName}:`, error.message);
      }
    }
  });
  
  const indexPath = path.join(outputDir, 'index.json');
  fs.writeFileSync(indexPath, JSON.stringify(indexData, null, 2));
  console.log(`✅ 生成索引文件: index.json`);
}

// 运行导出
if (require.main === module) {
  generateTokensFromExisting();
}

module.exports = {
  generateTokensFromExisting,
  parseTsExport,
  ensureOutputDir
};