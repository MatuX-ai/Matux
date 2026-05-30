#!/usr/bin/env node

/**
 * iMato 营销页面自动修复工具
 * 根据监控报告自动修复常见问题
 */

const fs = require('fs');
const path = require('path');

// 常见错误修复模式
const FIX_PATTERNS = {
  // 空值检查修复
  'null-check': {
    detect: /(\w+)(\.(\w+))+;/g,
    fix: (match, obj, prop) => {
      const properties = prop.split('.');
      let safeAccess = obj;
      
      for (let i = 0; i < properties.length; i++) {
        if (i === 0) continue; // 跳过第一个点
        const propName = properties[i];
        if (!propName) continue;
        
        safeAccess += `?.${propName}`;
      }
      
      return `${safeAccess} ?? null;`;
    }
  },
  
  // 函数调用检查
  'function-check': {
    detect: /(\w+)\.(\w+)\(\)/g,
    fix: (match, obj, method) => {
      return `typeof ${obj}.${method} === 'function' ? ${obj}.${method}() : null`;
    }
  },
  
  // 图片404修复 - 添加备用图片
  'missing-image': {
    detect: /<img([^>]*)src="([^"]+)"([^>]*)>/g,
    fix: (match, before, src, after) => {
      // 如果已经有onerror，则不重复添加
      if (match.includes('onerror')) {
        return match;
      }
      return `<img${before}src="${src}"${after} onerror="this.src='assets/images/placeholder.png'">`;
    }
  },
  
  // 未处理的Promise错误
  'unhandled-promise': {
    detect: /async\s+(\w+)\s*\([^)]*\)\s*\{([^}]+)\}/g,
    fix: (match, funcName, body) => {
      // 简单的Promise错误处理包装
      if (body.includes('try') || body.includes('catch')) {
        return match; // 已经有错误处理
      }
      
      return `async ${funcName}() {\n  try {\n    ${body.trim()}\n  } catch (error) {\n    console.error('Error in ${funcName}:', error);\n  }\n}`;
    }
  },
  
  // 事件监听器移除
  'event-listener-cleanup': {
    detect: /(addEventListener\(['"](\w+)['"])/g,
    fix: (match, addEvent, eventName) => {
      const removeEvent = addEvent.replace('addEventListener', 'removeEventListener');
      return `// 确保在组件销毁时移除监听器\n    // ${removeEvent}, ...);\n    ${addEvent}`;
    }
  }
};

// 错误类型到修复模式的映射
const ERROR_FIX_MAPPING = {
  'js_error': ['null-check', 'function-check', 'unhandled-promise'],
  'resource_error': ['missing-image'],
  'console_error': ['null-check', 'function-check'],
  'unhandled_promise': ['unhandled-promise']
};

class MarketingPageFixer {
  constructor(reportPath) {
    this.reportPath = reportPath;
    this.report = null;
    this.fixesApplied = [];
  }

  // 加载监控报告
  loadReport() {
    try {
      const reportContent = fs.readFileSync(this.reportPath, 'utf8');
      this.report = JSON.parse(reportContent);
      console.log(`✅ 已加载报告: ${this.reportPath}`);
      console.log(`📊 发现 ${this.report.summary.totalErrors} 个错误`);
      return true;
    } catch (error) {
      console.error(`❌ 加载报告失败: ${error.message}`);
      return false;
    }
  }

  // 分析错误并生成修复计划
  analyzeErrors() {
    if (!this.report) {
      throw new Error('报告未加载');
    }

    const fixPlan = {
      timestamp: new Date().toISOString(),
      files: new Map(), // 使用Map避免重复
      totalFixes: 0
    };

    // 遍历所有页面的错误
    this.report.results.forEach(pageResult => {
      if (pageResult.errors.length === 0) return;

      pageResult.errors.forEach(error => {
        const applicableFixes = ERROR_FIX_MAPPING[error.type] || [];
        
        applicableFixes.forEach(fixType => {
          // 这里需要根据错误信息推断可能的文件位置
          // 实际项目中需要更智能的文件路径推断
          const possibleFiles = this.inferFilesFromError(error, pageResult);
          
          possibleFiles.forEach(file => {
            if (!fixPlan.files.has(file)) {
              fixPlan.files.set(file, []);
            }
            
            fixPlan.files.get(file).push({
              type: fixType,
              error: error.message,
              page: pageResult.name,
              confidence: this.calculateConfidence(error, fixType)
            });
            
            fixPlan.totalFixes++;
          });
        });
      });
    });

    // 将Map转换为普通对象
    fixPlan.files = Object.fromEntries(fixPlan.files);
    
    return fixPlan;
  }

  // 从错误推断可能的文件位置
  inferFilesFromError(error, pageResult) {
    const files = [];
    const projectRoot = path.join(__dirname, '..');
    
    // 根据页面路径推断组件文件
    const pagePath = pageResult.path.replace('/marketing/', '');
    if (pagePath) {
      files.push(path.join(projectRoot, `src/app/marketing/${pagePath}/${pagePath}.component.ts`));
      files.push(path.join(projectRoot, `src/app/marketing/${pagePath}/${pagePath}.component.html`));
    }
    
    // 根据错误消息中的文件名
    if (error.stack) {
      const fileMatches = error.stack.match(/\/(src[\/\w\.-]+)/g);
      if (fileMatches) {
        fileMatches.forEach(file => {
          files.push(path.join(projectRoot, file));
        });
      }
    }
    
    // 默认检查共享文件
    files.push(path.join(projectRoot, 'src/app/marketing/shared/marketing-layout/marketing-layout.component.ts'));
    
    // 去重并过滤不存在的文件
    return [...new Set(files)].filter(file => {
      try {
        return fs.existsSync(file);
      } catch {
        return false;
      }
    });
  }

  // 计算修复置信度
  calculateConfidence(error, fixType) {
    let confidence = 0.5; // 基础置信度
    
    // 根据错误消息关键词提高置信度
    const keywords = {
      'null-check': ['undefined', 'null', 'cannot read'],
      'function-check': ['is not a function', 'not a function'],
      'missing-image': ['404', 'not found'],
      'unhandled-promise': ['Promise', 'uncaught']
    };
    
    const fixKeywords = keywords[fixType] || [];
    const errorMessage = (error.message || '').toLowerCase();
    
    fixKeywords.forEach(keyword => {
      if (errorMessage.includes(keyword.toLowerCase())) {
        confidence += 0.2;
      }
    });
    
    return Math.min(confidence, 0.95); // 最大置信度95%
  }

  // 应用修复
  async applyFixes(fixPlan) {
    console.log(`🛠️  开始应用修复...`);
    console.log(`📊 计划修复 ${fixPlan.totalFixes} 个问题`);

    const results = {
      applied: 0,
      skipped: 0,
      failed: 0,
      details: []
    };

    for (const [filePath, fixes] of Object.entries(fixPlan.files)) {
      console.log(`\n📄 处理文件: ${path.relative(process.cwd(), filePath)}`);
      
      try {
        let content = fs.readFileSync(filePath, 'utf8');
        let fileModified = false;
        const appliedFixes = [];

        for (const fix of fixes) {
          // 只应用置信度较高的修复
          if (fix.confidence < 0.7) {
            console.log(`  ⚠️  跳过修复 (置信度: ${(fix.confidence * 100).toFixed(1)}%): ${fix.type}`);
            results.skipped++;
            continue;
          }

          const pattern = FIX_PATTERNS[fix.type];
          if (!pattern) {
            console.log(`  ❌ 未知的修复类型: ${fix.type}`);
            results.failed++;
            continue;
          }

          // 应用修复
          const originalContent = content;
          content = content.replace(pattern.detect, (match, ...groups) => {
            console.log(`  ✅ 应用修复: ${fix.type}`);
            console.log(`     原因: ${fix.error}`);
            fileModified = true;
            appliedFixes.push(fix.type);
            return pattern.fix(match, ...groups);
          });

          if (content !== originalContent) {
            results.applied++;
          }
        }

        // 保存修改后的文件
        if (fileModified) {
          // 创建备份
          const backupPath = `${filePath}.backup-${Date.now()}`;
          fs.copyFileSync(filePath, backupPath);
          console.log(`  💾 已创建备份: ${path.basename(backupPath)}`);

          fs.writeFileSync(filePath, content, 'utf8');
          console.log(`  ✅ 文件已更新`);

          results.details.push({
            file: filePath,
            fixes: appliedFixes,
            backup: backupPath
          });
        }

      } catch (error) {
        console.log(`  ❌ 处理文件失败: ${error.message}`);
        results.failed++;
      }
    }

    return results;
  }

  // 生成修复报告
  generateFixReport(fixPlan, results) {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalFixes: fixPlan.totalFixes,
        applied: results.applied,
        skipped: results.skipped,
        failed: results.failed
      },
      fixPlan,
      results
    };

    const reportPath = path.join(
      path.dirname(this.reportPath), 
      `fix-report-${Date.now()}.json`
    );

    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    console.log(`\n📊 修复报告已保存: ${reportPath}`);

    return reportPath;
  }

  // 打印修复摘要
  printFixSummary(results) {
    console.log('\n' + '='.repeat(80));
    console.log('🔧 修复摘要');
    console.log('='.repeat(80));
    console.log(`✅ 应用修复: ${results.applied}`);
    console.log(`⚠️  跳过修复: ${results.skipped}`);
    console.log(`❌ 失败修复: ${results.failed}`);
    
    if (results.details.length > 0) {
      console.log('\n📄 修改的文件:');
      results.details.forEach(detail => {
        console.log(`  - ${path.basename(detail.file)}`);
        console.log(`    应用修复: ${detail.fixes.join(', ')}`);
        console.log(`    备份文件: ${path.basename(detail.backup)}`);
      });
    }
    
    console.log('\n⚠️  重要提示:');
    console.log('  1. 请仔细检查所有修改');
    console.log('  2. 运行测试验证功能正常');
    console.log('  3. 如需回滚，使用备份文件恢复');
    console.log('='.repeat(80));
  }
}

// 命令行接口
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0 || args.includes('--help')) {
    console.log(`
iMato 营销页面自动修复工具

使用方法:
  node marketing-page-fixes.js <report-file> [options]

参数:
  <report-file>    监控报告文件路径 (JSON格式)

选项:
  --dry-run        仅分析，不应用修复
  --help           显示帮助信息

示例:
  node marketing-page-fixes.js ../monitoring-reports/monitor-report-12345.json
  node marketing-page-fixes.js ../monitoring-reports/monitor-report-12345.json --dry-run
`);
    return;
  }

  const reportPath = args[0];
  const dryRun = args.includes('--dry-run');

  if (!fs.existsSync(reportPath)) {
    console.error(`❌ 报告文件不存在: ${reportPath}`);
    process.exit(1);
  }

  const fixer = new MarketingPageFixer(reportPath);
  
  // 加载报告
  if (!fixer.loadReport()) {
    process.exit(1);
  }

  // 分析错误
  console.log('\n🔍 分析错误中...');
  const fixPlan = fixer.analyzeErrors();
  
  console.log(`📊 分析完成:`);
  console.log(`   受影响文件: ${Object.keys(fixPlan.files).length}`);
  console.log(`   计划修复: ${fixPlan.totalFixes}`);

  // 显示修复计划
  console.log('\n📋 修复计划:');
  for (const [file, fixes] of Object.entries(fixPlan.files)) {
    console.log(`\n  📄 ${path.relative(process.cwd(), file)}:`);
    fixes.forEach(fix => {
      console.log(`     - ${fix.type} (置信度: ${(fix.confidence * 100).toFixed(1)}%)`);
      console.log(`       问题: ${fix.error}`);
    });
  }

  if (dryRun) {
    console.log('\n✅ 干运行完成，未应用任何修复');
    return;
  }

  // 确认应用修复
  console.log('\n⚠️  即将应用修复，已创建备份文件');
  console.log('   按 Ctrl+C 取消，或等待5秒继续...');
  
  await new Promise(resolve => setTimeout(resolve, 5000));

  // 应用修复
  const results = await fixer.applyFixes(fixPlan);
  
  // 生成报告
  fixer.generateFixReport(fixPlan, results);
  
  // 打印摘要
  fixer.printFixSummary(results);

  console.log('\n✅ 修复完成！');
  console.log('   下一步: 运行监控脚本验证修复效果');
}

// 运行主函数
if (require.main === module) {
  main().catch(error => {
    console.error('❌ 修复失败:', error);
    process.exit(1);
  });
}

module.exports = MarketingPageFixer;
