#!/usr/bin/env node

/**
 * iMato Marketing Pages Monitor
 * 营销页面自动化监控脚本
 * 
 * 功能：
 * 1. 自动打开所有营销页面
 * 2. 捕获控制台错误和警告
 * 3. 检测资源加载失败
 * 4. 生成详细的错误报告和修复建议
 * 
 * 使用方法：
 * node scripts/marketing-page-monitor.js [--headless] [--timeout=30000] [--output=report.json]
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// 配置
const CONFIG = {
  // 营销页面列表
  pages: [
    { path: '/marketing', name: '营销首页', critical: true },
    { path: '/marketing/product', name: '产品展示页', critical: true },
    { path: '/marketing/education', name: '教育页面', critical: true },
    { path: '/marketing/pricing', name: '定价页面', critical: true },
    { path: '/marketing/features', name: '特性页面', critical: false },
    { path: '/marketing/about', name: '关于我们', critical: false },
    { path: '/marketing/contact', name: '联系我们', critical: true },
    { path: '/marketing/tech-stack', name: '技术栈', critical: false },
    { path: '/marketing/roadmap', name: '路线图', critical: false }
  ],
  
  // 默认配置
  baseUrl: 'http://localhost:4200',
  headless: true,
  timeout: 30000,
  viewport: { width: 1920, height: 1080 },
  mobileViewport: { width: 375, height: 667 },
  
  // 输出配置
  outputDir: path.join(__dirname, '../monitoring-reports'),
  screenshotsDir: path.join(__dirname, '../monitoring-reports/screenshots')
};

// 解析命令行参数
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    headless: CONFIG.headless,
    timeout: CONFIG.timeout,
    output: path.join(CONFIG.outputDir, `monitor-report-${Date.now()}.json`),
    mobile: false
  };

  args.forEach(arg => {
    if (arg === '--headless') options.headless = true;
    if (arg === '--no-headless') options.headless = false;
    if (arg === '--mobile') options.mobile = true;
    if (arg.startsWith('--timeout=')) {
      options.timeout = parseInt(arg.split('=')[1]);
    }
    if (arg.startsWith('--output=')) {
      options.output = arg.split('=')[1];
    }
    if (arg.startsWith('--base-url=')) {
      CONFIG.baseUrl = arg.split('=')[1];
    }
  });

  return options;
}

// 创建输出目录
function ensureOutputDirs() {
  if (!fs.existsSync(CONFIG.outputDir)) {
    fs.mkdirSync(CONFIG.outputDir, { recursive: true });
  }
  if (!fs.existsSync(CONFIG.screenshotsDir)) {
    fs.mkdirSync(CONFIG.screenshotsDir, { recursive: true });
  }
}

// 生成修复建议
function generateFixSuggestion(error) {
  const suggestions = [];
  
  // JavaScript错误修复建议
  if (error.type === 'js_error') {
    if (error.message.includes('undefined') || error.message.includes('null')) {
      suggestions.push({
        type: 'null-check',
        title: '添加空值检查',
        description: '在访问对象属性前添加空值检查',
        example: `// 修复前
const value = obj.property;

// 修复后
const value = obj?.property ?? '默认值';`
      });
    }
    
    if (error.message.includes('is not a function')) {
      suggestions.push({
        type: 'function-check',
        title: '验证函数存在性',
        description: '在调用函数前验证其类型',
        example: `// 修复前
obj.method();

// 修复后
if (typeof obj.method === 'function') {
  obj.method();
}`
      });
    }
    
    if (error.stack && error.stack.includes('async')) {
      suggestions.push({
        type: 'async-error',
        title: '添加错误处理',
        description: '为异步操作添加try-catch块',
        example: `// 修复前
async function fetchData() {
  const data = await apiCall();
}

// 修复后
async function fetchData() {
  try {
    const data = await apiCall();
  } catch (error) {
    console.error('API调用失败:', error);
    // 添加降级处理
  }
}`
      });
    }
  }
  
  // 资源加载错误
  if (error.type === 'resource_error') {
    if (error.message.includes('404')) {
      suggestions.push({
        type: 'missing-resource',
        title: '检查资源路径',
        description: '验证资源文件是否存在于指定路径',
        example: `// 检查文件路径
// 错误路径: assets/images/missing.png
// 正确路径: assets/images/exists.png

// 添加备用资源
<img src="assets/images/logo.png" 
     onerror="this.src='assets/images/placeholder.png'" />`
      });
    }
    
    if (error.message.includes('net::ERR_CONNECTION')) {
      suggestions.push({
        type: 'network-error',
        title: '添加网络错误处理',
        description: '为外部资源添加错误处理',
        example: `// 添加超时和重试机制
async function loadExternalScript(url) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = url;
    script.onload = resolve;
    script.onerror = () => {
      setTimeout(() => {
        document.head.appendChild(script); // 重试
      }, 1000);
    };
    
    setTimeout(() => reject(new Error('加载超时')), 5000);
    document.head.appendChild(script);
  });
}`
      });
    }
  }
  
  // CORS错误
  if (error.message.includes('CORS')) {
    suggestions.push({
      type: 'cors-error',
      title: '处理CORS问题',
      description: '处理跨域资源共享问题',
      example: `// 方案1: 使用代理
const proxyUrl = '/api/proxy?url=';
fetch(proxyUrl + encodeURIComponent(externalUrl));

// 方案2: 添加CORS头（服务器端）
// Access-Control-Allow-Origin: *

// 方案3: 使用JSONP
<script src="https://api.example.com/data?callback=handleData"></script>`
    });
  }
  
  return suggestions;
}

// 监控单个页面
async function monitorPage(page, pageConfig, options) {
  const pageName = pageConfig.name;
  const pageUrl = CONFIG.baseUrl + pageConfig.path;
  const timestamp = new Date().toISOString();
  
  console.log(`📄 正在监控: ${pageName} (${pageUrl})`);
  
  const pageResult = {
    name: pageName,
    path: pageConfig.path,
    url: pageUrl,
    timestamp,
    critical: pageConfig.critical,
    status: 'pending',
    errors: [],
    warnings: [],
    resources: {
      total: 0,
      failed: 0,
      details: []
    },
    performance: {
      loadTime: 0,
      domContentLoaded: 0,
      firstPaint: 0
    },
    screenshot: null
  };
  
  try {
    // 设置视口
    const viewport = options.mobile ? CONFIG.mobileViewport : CONFIG.viewport;
    await page.setViewportSize(viewport);
    
    // 监听控制台消息
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      const location = msg.location();
      
      if (type === 'error') {
        pageResult.errors.push({
          type: 'console_error',
          message: text,
          location: location,
          timestamp: new Date().toISOString()
        });
      } else if (type === 'warning') {
        pageResult.warnings.push({
          type: 'console_warning',
          message: text,
          location: location,
          timestamp: new Date().toISOString()
        });
      }
    });
    
    // 监听页面错误
    page.on('pageerror', error => {
      pageResult.errors.push({
        type: 'js_error',
        message: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString()
      });
    });
    
    // 监听资源加载失败
    page.on('response', response => {
      const status = response.status();
      const url = response.url();
      const resourceType = response.request().resourceType();
      
      pageResult.resources.total++;
      
      if (status >= 400) {
        pageResult.resources.failed++;
        pageResult.resources.details.push({
          url,
          status,
          type: resourceType,
          error: `HTTP ${status}`,
          timestamp: new Date().toISOString()
        });
        
        pageResult.errors.push({
          type: 'resource_error',
          message: `资源加载失败: ${url}`,
          status,
          url,
          resourceType,
          timestamp: new Date().toISOString()
        });
      }
    });
    
    // 监听未处理的Promise拒绝
    page.on('pageerror', error => {
      if (error.message.includes('Promise')) {
        pageResult.errors.push({
          type: 'unhandled_promise',
          message: error.message,
          timestamp: new Date().toISOString()
        });
      }
    });
    
    // 记录性能数据
    const startTime = Date.now();
    
    // 导航到页面
    const response = await page.goto(pageUrl, {
      waitUntil: 'networkidle',
      timeout: options.timeout
    });
    
    pageResult.performance.loadTime = Date.now() - startTime;
    
    // 获取性能指标
    const performanceData = await page.evaluate(() => {
      const timing = performance.timing;
      const navigation = performance.navigation;
      
      return {
        loadTime: timing.loadEventEnd - timing.navigationStart,
        domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
        firstPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-paint')?.startTime || 0,
        redirectCount: navigation.redirectCount,
        navigationType: navigation.type
      };
    });
    
    pageResult.performance = { ...pageResult.performance, ...performanceData };
    
    // 检查响应状态
    if (response) {
      const status = response.status();
      if (status >= 400) {
        pageResult.errors.push({
          type: 'http_error',
          message: `HTTP ${status} - ${response.statusText()}`,
          status,
          timestamp: new Date().toISOString()
        });
      }
      pageResult.status = status < 400 ? 'success' : 'failed';
    } else {
      pageResult.status = 'no_response';
    }
    
    // 截图
    const screenshotPath = path.join(CONFIG.screenshotsDir, `${pageName.replace(/[^a-zA-Z0-9]/g, '_')}-${Date.now()}.png`);
    await page.screenshot({ 
      path: screenshotPath,
      fullPage: true 
    });
    pageResult.screenshot = screenshotPath;
    
    // 等待一下确保所有资源加载完成
    await page.waitForTimeout(2000);
    
    console.log(`✅ 完成: ${pageName} - 发现 ${pageResult.errors.length} 个错误, ${pageResult.warnings.length} 个警告`);
    
  } catch (error) {
    console.error(`❌ 监控失败: ${pageName}`, error.message);
    pageResult.status = 'error';
    pageResult.errors.push({
      type: 'monitoring_error',
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    });
  }
  
  return pageResult;
}

// 生成报告
function generateReport(results, options) {
  const totalPages = results.length;
  const criticalPages = results.filter(r => r.critical).length;
  const totalErrors = results.reduce((sum, r) => sum + r.errors.length, 0);
  const totalWarnings = results.reduce((sum, r) => sum + r.warnings.length, 0);
  const criticalErrors = results.filter(r => r.critical && r.errors.length > 0).length;
  
  const report = {
    summary: {
      timestamp: new Date().toISOString(),
      totalPages,
      criticalPages,
      totalErrors,
      totalWarnings,
      criticalErrors,
      successRate: ((totalPages - results.filter(r => r.errors.length > 0).length) / totalPages * 100).toFixed(2) + '%',
      avgLoadTime: (results.reduce((sum, r) => sum + r.performance.loadTime, 0) / totalPages).toFixed(0) + 'ms'
    },
    configuration: {
      baseUrl: CONFIG.baseUrl,
      viewport: options.mobile ? CONFIG.mobileViewport : CONFIG.viewport,
      mobile: options.mobile,
      timeout: options.timeout
    },
    results: results.map(result => ({
      ...result,
      fixSuggestions: result.errors.flatMap(error => generateFixSuggestion(error))
    }))
  };
  
  // 添加严重错误摘要
  report.criticalIssues = report.results
    .filter(r => r.critical && r.errors.length > 0)
    .map(r => ({
      page: r.name,
      path: r.path,
      errors: r.errors.map(e => ({
        type: e.type,
        message: e.message
      }))
    }));
  
  // 保存报告
  fs.writeFileSync(options.output, JSON.stringify(report, null, 2));
  
  return report;
}

// 打印报告摘要
function printReportSummary(report) {
  console.log('\n' + '='.repeat(80));
  console.log('📊 监控报告摘要');
  console.log('='.repeat(80));
  console.log(`⏰ 测试时间: ${report.summary.timestamp}`);
  console.log(`📄 监控页面: ${report.summary.totalPages} 个 (关键页面: ${report.summary.criticalPages})`);
  console.log(`❌ 总错误数: ${report.summary.totalErrors}`);
  console.log(`⚠️  总警告数: ${report.summary.totalWarnings}`);
  console.log(`🔴 关键错误: ${report.summary.criticalErrors}`);
  console.log(`✅ 成功率: ${report.summary.successRate}`);
  console.log(`⚡ 平均加载时间: ${report.summary.avgLoadTime}`);
  
  if (report.criticalIssues.length > 0) {
    console.log('\n🔥 关键问题页面:');
    report.criticalIssues.forEach(issue => {
      console.log(`  ❌ ${issue.page} (${issue.path})`);
      issue.errors.forEach(error => {
        console.log(`     - ${error.type}: ${error.message}`);
      });
    });
  }
  
  // 错误类型统计
  const errorTypes = {};
  report.results.forEach(result => {
    result.errors.forEach(error => {
      errorTypes[error.type] = (errorTypes[error.type] || 0) + 1;
    });
  });
  
  if (Object.keys(errorTypes).length > 0) {
    console.log('\n📈 错误类型分布:');
    Object.entries(errorTypes).forEach(([type, count]) => {
      console.log(`  ${type}: ${count}`);
    });
  }
  
  console.log(`\n💾 详细报告已保存至: ${report.configuration.output}`);
  console.log('='.repeat(80));
}

// 生成修复脚本
function generateFixScript(report) {
  const scriptContent = `#!/bin/bash
# iMato 营销页面问题自动修复脚本
# 生成时间: ${new Date().toISOString()}

echo "🛠️  开始执行自动修复..."

# 常见修复操作
${report.results.map((result, index) => `
echo "修复 ${result.name} 的问题..."
# TODO: 根据具体问题实现自动修复
# - 检查资源路径
# - 验证API端点
# - 更新依赖包
`).join('')}

echo "✅ 修复完成！请手动验证关键功能。"
`;
  
  const scriptPath = path.join(CONFIG.outputDir, `fix-script-${Date.now()}.sh`);
  fs.writeFileSync(scriptPath, scriptContent);
  
  return scriptPath;
}

// 主函数
async function main() {
  const options = parseArgs();
  ensureOutputDirs();
  
  console.log('🚀 iMato 营销页面监控开始');
  console.log(`📡 目标: ${CONFIG.baseUrl}`);
  console.log(`👁️  模式: ${options.headless ? '无头模式' : '可视化模式'}`);
  console.log(`📱 设备: ${options.mobile ? '移动端' : '桌面端'}`);
  console.log(`⏱️  超时: ${options.timeout}ms`);
  console.log('');
  
  let browser;
  let context;
  
  try {
    // 检查Playwright是否安装
    try {
      require.resolve('playwright');
    } catch (e) {
      console.log('📦 Playwright 未安装，正在安装...');
      execSync('npm install playwright', { stdio: 'inherit' });
    }
    
    // 启动浏览器
    browser = await chromium.launch({ 
      headless: options.headless,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    context = await browser.newContext({
      viewport: options.mobile ? CONFIG.mobileViewport : CONFIG.viewport,
      userAgent: options.mobile 
        ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
        : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    });
    
    // 监控所有页面
    const results = [];
    for (const pageConfig of CONFIG.pages) {
      const page = await context.newPage();
      const result = await monitorPage(page, pageConfig, options);
      results.push(result);
      await page.close();
    }
    
    // 生成报告
    const report = generateReport(results, options);
    
    // 打印摘要
    printReportSummary(report);
    
    // 生成修复脚本（如果需要）
    if (report.summary.totalErrors > 0) {
      const scriptPath = generateFixScript(report);
      console.log(`🔧 修复脚本已生成: ${scriptPath}`);
    }
    
    // 生成HTML报告
    await generateHtmlReport(report, options);
    
    console.log('\n✅ 监控完成！');
    
  } catch (error) {
    console.error('❌ 监控失败:', error);
    process.exit(1);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// 生成HTML报告
async function generateHtmlReport(report, options) {
  const htmlContent = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>iMato 营销页面监控报告</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 3px solid #667eea; padding-bottom: 10px; }
        h2 { color: #667eea; margin-top: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }
        .card.error { border-left-color: #dc3545; }
        .card.warning { border-left-color: #ffc107; }
        .card.success { border-left-color: #28a745; }
        .metric { font-size: 2em; font-weight: bold; color: #333; }
        .label { color: #666; font-size: 0.9em; }
        .page-result { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
        .page-result.success { border-color: #28a745; background: #d4edda; }
        .page-result.error { border-color: #dc3545; background: #f8d7da; }
        .error-item { background: #fff; padding: 10px; margin: 10px 0; border-left: 4px solid #dc3545; border-radius: 4px; }
        .warning-item { background: #fff; padding: 10px; margin: 10px 0; border-left: 4px solid #ffc107; border-radius: 4px; }
        .fix-suggestion { background: #e7f3ff; padding: 15px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #667eea; }
        .code-block { background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 0.9em; overflow-x: auto; }
        .screenshot { max-width: 100%; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }
        .status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: bold; }
        .status-badge.success { background: #28a745; color: white; }
        .status-badge.error { background: #dc3545; color: white; }
        .status-badge.warning { background: #ffc107; color: #333; }
        .critical-badge { background: #dc3545; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75em; margin-left: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 iMato 营销页面监控报告</h1>
        
        <div class="summary">
            <div class="card">
                <div class="metric">${report.summary.totalPages}</div>
                <div class="label">监控页面</div>
            </div>
            <div class="card ${report.summary.totalErrors > 0 ? 'error' : 'success'}">
                <div class="metric">${report.summary.totalErrors}</div>
                <div class="label">总错误数</div>
            </div>
            <div class="card warning">
                <div class="metric">${report.summary.totalWarnings}</div>
                <div class="label">总警告数</div>
            </div>
            <div class="card">
                <div class="metric">${report.summary.successRate}</div>
                <div class="label">成功率</div>
            </div>
            <div class="card">
                <div class="metric">${report.summary.avgLoadTime}</div>
                <div class="label">平均加载时间</div>
            </div>
        </div>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <strong>测试时间:</strong> ${new Date(report.summary.timestamp).toLocaleString()}<br>
            <strong>测试环境:</strong> ${report.configuration.baseUrl} | 
            ${report.configuration.mobile ? '移动端' : '桌面端'} | 
            ${report.configuration.headless ? '无头模式' : '可视化模式'}
        </div>
        
        ${report.criticalIssues.length > 0 ? `
        <h2>🔥 关键问题</h2>
        <div style="background: #f8d7da; padding: 15px; border-radius: 8px; border: 1px solid #dc3545;">
            <strong>发现 ${report.criticalIssues.length} 个关键页面的错误！</strong>
        </div>
        ` : ''}
        
        <h2>📄 页面详细结果</h2>
        ${report.results.map(result => `
            <div class="page-result ${result.errors.length > 0 ? 'error' : 'success'}">
                <h3>
                    ${result.name}
                    <span class="status-badge ${result.errors.length > 0 ? 'error' : 'success'}">
                        ${result.errors.length > 0 ? `${result.errors.length} 个错误` : '正常'}
                    </span>
                    ${result.critical ? '<span class="critical-badge">关键</span>' : ''}
                </h3>
                <p><strong>路径:</strong> ${result.path}</p>
                <p><strong>加载时间:</strong> ${result.performance.loadTime}ms</p>
                
                ${result.screenshot ? `<img src="${path.basename(result.screenshot)}" alt="${result.name}截图" class="screenshot">` : ''}
                
                ${result.errors.length > 0 ? `
                    <h4>❌ 错误详情</h4>
                    ${result.errors.map(error => `
                        <div class="error-item">
                            <strong>${error.type}:</strong> ${error.message}
                            ${error.stack ? `<div class="code-block">${error.stack}</div>` : ''}
                        </div>
                    `).join('')}
                ` : ''}
                
                ${result.warnings.length > 0 ? `
                    <h4>⚠️ 警告详情</h4>
                    ${result.warnings.map(warning => `
                        <div class="warning-item">
                            <strong>${warning.type}:</strong> ${warning.message}
                        </div>
                    `).join('')}
                ` : ''}
                
                ${result.fixSuggestions.length > 0 ? `
                    <h4>🔧 修复建议</h4>
                    ${result.fixSuggestions.map((suggestion, idx) => `
                        <div class="fix-suggestion">
                            <strong>${idx + 1}. ${suggestion.title}</strong>
                            <p>${suggestion.description}</p>
                            <div class="code-block">${suggestion.example}</div>
                        </div>
                    `).join('')}
                ` : ''}
            </div>
        `).join('')}
        
        <div style="text-align: center; margin-top: 40px; color: #666; font-size: 0.9em;">
            <p>此报告由 iMato 营销页面监控脚本自动生成</p>
        </div>
    </div>
</body>
</html>`;
  
  const htmlPath = options.output.replace('.json', '.html');
  fs.writeFileSync(htmlPath, htmlContent);
  
  return htmlPath;
}

// 运行主函数
if (require.main === module) {
  main().catch(error => {
    console.error('❌ 监控脚本执行失败:', error);
    process.exit(1);
  });
}

module.exports = { monitorPage, generateReport, generateFixSuggestion };
