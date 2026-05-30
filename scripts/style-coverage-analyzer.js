#!/usr/bin/env node

/**
 * 样式覆盖率检测工具
 * 分析CSS类在项目中的使用情况，识别未使用的样式
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');
const chalk = require('chalk');

// 配置
const CONFIG = {
  // CSS 文件路径
  cssFiles: ['dist/styles/**/*.css', 'src/styles/**/*.scss'],
  // 需要检查的源文件
  sourceFiles: ['src/**/*.{ts,html,js,jsx}', 'shared-styles/**/*.{ts,html}'],
  // 忽略的类名模式
  ignorePatterns: [
    /^c-/,           // 组件类名
    /^u-/,           // 工具类名
    /^t-/,           // 主题类名
    /^js-/,          // JavaScript 钩子
    /^is-/,          // 状态类名
    /^has-/,         // 父级状态类名
    /^mat-/,         // Angular Material 类名
    /^ng-/,          // Angular 类名
    /^demo-/,        // 演示类名
    // 动画和过渡类
    /animation/,
    /transition/,
    /fade/,
    /slide/,
    /scale/,
    // 响应式类名
    /@(mobile|tablet|desktop)/,
    // CSS 变量和属性选择器
    /^\[.*\]$/,
    /^:/,
    /^::/,
    // SCSS Mixins 和 Functions
    /^@include/,
    /^@mixin/,
    /^@function/
  ]
};

class StyleCoverageAnalyzer {
  constructor(config = CONFIG) {
    this.config = config;
    this.cssClasses = new Set();
    this.usedClasses = new Set();
    this.unusedClasses = new Set();
    this.ignoredClasses = new Set();
  }

  /**
   * 提取 CSS 文件中的类名
   */
  extractCssClasses() {
    console.log(chalk.blue('🔍 正在提取 CSS 类名...'));
    
    this.config.cssFiles.forEach(pattern => {
      const files = glob.sync(pattern);
      files.forEach(filePath => {
        try {
          const content = fs.readFileSync(filePath, 'utf8');
          // 提取类选择器
          const classRegex = /\.([a-zA-Z_-][\w-]*)/g;
          let match;
          while ((match = classRegex.exec(content)) !== null) {
            const className = match[1];
            if (this.shouldIncludeClass(className)) {
              this.cssClasses.add(className);
            } else {
              this.ignoredClasses.add(className);
            }
          }
        } catch (error) {
          console.warn(chalk.yellow(`⚠️  无法读取文件: ${filePath}`));
        }
      });
    });
    
    console.log(chalk.green(`✅ 提取到 ${this.cssClasses.size} 个 CSS 类名`));
    console.log(chalk.gray(`⏭️  忽略了 ${this.ignoredClasses.size} 个类名`));
  }

  /**
   * 判断是否应该包含该类名
   */
  shouldIncludeClass(className) {
    return !this.config.ignorePatterns.some(pattern => 
      typeof pattern === 'string' ? 
        className.includes(pattern) : 
        pattern.test(className)
    );
  }

  /**
   * 分析源文件中的类使用情况
   */
  analyzeSourceFiles() {
    console.log(chalk.blue('🔍 正在分析源文件中的类使用情况...'));
    
    this.config.sourceFiles.forEach(pattern => {
      const files = glob.sync(pattern);
      files.forEach(filePath => {
        try {
          const content = fs.readFileSync(filePath, 'utf8');
          // 查找 HTML 中的 class 属性
          const classAttrRegex = /class=["'](.*?)["']/g;
          let match;
          while ((match = classAttrRegex.exec(content)) !== null) {
            const classes = match[1].split(/\s+/).filter(c => c);
            classes.forEach(className => {
              this.usedClasses.add(className);
            });
          }
          
          // 查找模板字符串中的类名
          const templateClassRegex = /['"`]([\w\s-]+)['"`]/g;
          while ((match = templateClassRegex.exec(content)) !== null) {
            const classes = match[1].split(/\s+/).filter(c => c);
            classes.forEach(className => {
              this.usedClasses.add(className);
            });
          }
          
          // 查找 Angular 绑定中的类名
          const bindingRegex = /\[class(?:\.\w+)?\]=["'](.*?)["']/g;
          while ((bindingRegex.exec(content)) !== null) {
            // 这里可以进一步解析绑定表达式
          }
          
        } catch (error) {
          console.warn(chalk.yellow(`⚠️  无法读取文件: ${filePath}`));
        }
      });
    });
    
    console.log(chalk.green(`✅ 分析了 ${this.usedClasses.size} 个使用的类名`));
  }

  /**
   * 计算覆盖率
   */
  calculateCoverage() {
    console.log(chalk.blue('📊 正在计算样式覆盖率...'));
    
    // 找出未使用的类
    this.cssClasses.forEach(className => {
      if (!this.usedClasses.has(className)) {
        this.unusedClasses.add(className);
      }
    });
    
    const totalClasses = this.cssClasses.size;
    const usedClasses = this.cssClasses.size - this.unusedClasses.size;
    const coverage = totalClasses > 0 ? (usedClasses / totalClasses * 100) : 100;
    
    return {
      total: totalClasses,
      used: usedClasses,
      unused: this.unusedClasses.size,
      coverage: coverage.toFixed(2),
      unusedList: Array.from(this.unusedClasses)
    };
  }

  /**
   * 生成详细报告
   */
  generateReport() {
    const report = this.calculateCoverage();
    
    console.log('\n' + chalk.bold('=== 样式覆盖率分析报告 ==='));
    console.log(chalk.cyan(`总 CSS 类数: ${report.total}`));
    console.log(chalk.green(`已使用类数: ${report.used}`));
    console.log(chalk.red(`未使用类数: ${report.unused}`));
    console.log(chalk.yellow(`样式覆盖率: ${report.coverage}%`));
    
    if (report.unused > 0) {
      console.log('\n' + chalk.bold.red('❌ 未使用的 CSS 类:'));
      report.unusedList.slice(0, 20).forEach(className => {
        console.log(chalk.red(`  • .${className}`));
      });
      
      if (report.unusedList.length > 20) {
        console.log(chalk.gray(`  ... 还有 ${report.unusedList.length - 20} 个未使用的类`));
      }
    }
    
    // 覆盖率等级
    const level = report.coverage >= 90 ? '优秀' : 
                  report.coverage >= 80 ? '良好' : 
                  report.coverage >= 70 ? '一般' : '需要改进';
    
    const levelColor = report.coverage >= 90 ? chalk.green :
                       report.coverage >= 80 ? chalk.yellow :
                       report.coverage >= 70 ? chalk.orange : chalk.red;
    
    console.log('\n' + levelColor(`🎯 覆盖率等级: ${level}`));
    
    // 建议
    if (report.coverage < 80) {
      console.log('\n' + chalk.bold.yellow('💡 优化建议:'));
      console.log('  1. 删除未使用的 CSS 类');
      console.log('  2. 检查动态生成的类名是否被正确识别');
      console.log('  3. 审查第三方库的样式');
      console.log('  4. 考虑使用 CSS-in-JS 方案');
    }
    
    return report;
  }

  /**
   * 导出报告到文件
   */
  exportReport(report, outputPath = 'style-coverage-report.json') {
    const reportData = {
      timestamp: new Date().toISOString(),
      summary: {
        totalClasses: report.total,
        usedClasses: report.used,
        unusedClasses: report.unused,
        coveragePercentage: parseFloat(report.coverage)
      },
      unusedClasses: report.unusedList,
      ignoredClasses: Array.from(this.ignoredClasses)
    };
    
    fs.writeFileSync(outputPath, JSON.stringify(reportData, null, 2));
    console.log(chalk.green(`\n📄 详细报告已导出到: ${outputPath}`));
  }

  /**
   * 运行完整分析
   */
  async run() {
    try {
      console.log(chalk.bold.blue('🚀 开始样式覆盖率分析'));
      
      // 提取 CSS 类名
      this.extractCssClasses();
      
      // 分析源文件使用情况
      this.analyzeSourceFiles();
      
      // 生成报告
      const report = this.generateReport();
      
      // 导出详细报告
      this.exportReport(report);
      
      // 返回覆盖率用于 CI/CD
      process.exit(report.coverage >= 70 ? 0 : 1);
      
    } catch (error) {
      console.error(chalk.red('❌ 分析过程中发生错误:'), error.message);
      process.exit(1);
    }
  }
}

// 命令行接口
if (require.main === module) {
  const analyzer = new StyleCoverageAnalyzer();
  
  // 支持命令行参数
  const args = process.argv.slice(2);
  const options = {
    export: args.includes('--export') || args.includes('-e'),
    verbose: args.includes('--verbose') || args.includes('-v')
  };
  
  analyzer.run().then(() => {
    console.log(chalk.green('\n✅ 样式覆盖率分析完成！'));
  });
}

module.exports = StyleCoverageAnalyzer;