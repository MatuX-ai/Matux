/**
 * i18n功能测试脚本
 * 
 * 用于验证翻译文件格式和基本功能
 */

const fs = require('fs');
const path = require('path');

// 检查翻译文件是否存在
function checkFileExists(filePath) {
  try {
    fs.accessSync(filePath, fs.constants.F_OK);
    console.log(`✅ ${path.basename(filePath)} 文件存在`);
    return true;
  } catch (err) {
    console.log(`❌ ${path.basename(filePath)} 文件不存在`);
    return false;
  }
}

// 检查JSON格式
function checkJsonFormat(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    JSON.parse(content);
    console.log(`✅ ${path.basename(filePath)} JSON格式正确`);
    return true;
  } catch (err) {
    console.log(`❌ ${path.basename(filePath)} JSON格式错误:`, err.message);
    return false;
  }
}

// 检查翻译文件结构一致性
function checkStructureConsistency(files) {
  const structures = [];
  
  files.forEach(filePath => {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const data = JSON.parse(content);
      structures.push({
        file: path.basename(filePath),
        keys: getAllKeys(data)
      });
    } catch (err) {
      console.log(`❌ 无法解析 ${path.basename(filePath)}`);
    }
  });
  
  if (structures.length < 2) {
    console.log('⚠️  需要至少两个文件进行比较');
    return;
  }
  
  // 比较键结构
  const baseKeys = structures[0].keys;
  let allConsistent = true;
  
  for (let i = 1; i < structures.length; i++) {
    const diff = compareKeys(baseKeys, structures[i].keys);
    if (diff.missing.length > 0 || diff.extra.length > 0) {
      console.log(`❌ ${structures[i].file} 与 ${structures[0].file} 结构不一致`);
      if (diff.missing.length > 0) {
        console.log(`   缺少键: ${diff.missing.join(', ')}`);
      }
      if (diff.extra.length > 0) {
        console.log(`   额外键: ${diff.extra.join(', ')}`);
      }
      allConsistent = false;
    }
  }
  
  if (allConsistent) {
    console.log('✅ 所有翻译文件结构一致');
  }
}

// 获取所有嵌套键
function getAllKeys(obj, prefix = '') {
  const keys = [];
  
  for (const key in obj) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    
    if (typeof obj[key] === 'object' && !Array.isArray(obj[key])) {
      keys.push(...getAllKeys(obj[key], fullKey));
    } else {
      keys.push(fullKey);
    }
  }
  
  return keys;
}

// 比较键集合
function compareKeys(keys1, keys2) {
  const set1 = new Set(keys1);
  const set2 = new Set(keys2);
  
  const missing = keys1.filter(key => !set2.has(key));
  const extra = keys2.filter(key => !set1.has(key));
  
  return { missing, extra };
}

// 运行测试
function runTests() {
  console.log('🧪 开始测试 i18n 功能...\n');
  
  const i18nDir = __dirname;
  const files = [
    path.join(i18nDir, 'zh-CN.json'),
    path.join(i18nDir, 'en-US.json')
  ];
  
  // 检查文件存在
  console.log('📁 检查文件存在:');
  const allFilesExist = files.every(filePath => checkFileExists(filePath));
  
  if (!allFilesExist) {
    console.log('\n❌ 部分文件缺失，终止测试');
    return;
  }
  
  console.log('\n📋 检查JSON格式:');
  const allJsonValid = files.every(filePath => checkJsonFormat(filePath));
  
  if (!allJsonValid) {
    console.log('\n❌ 部分JSON格式错误，终止测试');
    return;
  }
  
  console.log('\n🔍 检查结构一致性:');
  checkStructureConsistency(files);
  
  // 检查文件大小
  console.log('\n📊 检查文件大小:');
  files.forEach(filePath => {
    try {
      const stats = fs.statSync(filePath);
      const sizeKB = (stats.size / 1024).toFixed(2);
      console.log(`   ${path.basename(filePath)}: ${sizeKB} KB`);
    } catch (err) {
      console.log(`   ${path.basename(filePath)}: 无法获取大小`);
    }
  });
  
  console.log('\n🎉 i18n测试完成！');
}

// 执行测试
try {
  runTests();
} catch (error) {
  console.error('❌ 测试过程中发生错误:', error.message);
  process.exit(1);
}