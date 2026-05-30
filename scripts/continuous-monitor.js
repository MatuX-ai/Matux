#!/usr/bin/env node

/**
 * iMato 持续监控服务
 * 定时自动执行营销页面监控并发送通知
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const nodemailer = require('nodemailer');

// 配置
const CONFIG_PATH = path.join(__dirname, 'monitor-config.json');
let CONFIG = {};

// 加载配置
function loadConfig() {
  try {
    const configContent = fs.readFileSync(CONFIG_PATH, 'utf8');
    CONFIG = JSON.parse(configContent);
    console.log('✅ 配置加载成功');
    return true;
  } catch (error) {
    console.error('❌ 加载配置失败:', error.message);
    return false;
  }
}

// 执行监控命令
function runMonitor(options = {}) {
  return new Promise((resolve, reject) => {
    const args = ['marketing-page-monitor.js'];
    
    // 添加选项
    if (CONFIG.headless) args.push('--headless');
    if (options.mobile) args.push('--mobile');
    if (options.baseUrl) args.push(`--base-url=${options.baseUrl}`);
    
    const outputFile = path.join(
      CONFIG.output.dir, 
      `continuous-monitor-${Date.now()}.json`
    );
    args.push(`--output=${outputFile}`);
    
    console.log(`🚀 执行监控: node ${args.join(' ')}`);
    
    const monitor = spawn('node', args, {
      cwd: __dirname,
      stdio: 'pipe'
    });
    
    let stdout = '';
    let stderr = '';
    
    monitor.stdout.on('data', (data) => {
      const output = data.toString();
      stdout += output;
      console.log(output.trim());
    });
    
    monitor.stderr.on('data', (data) => {
      const error = data.toString();
      stderr += error;
      console.error(error.trim());
    });
    
    monitor.on('close', (code) => {
      console.log(`⏹️  监控进程退出，代码: ${code}`);
      
      if (code === 0) {
        // 读取报告
        if (fs.existsSync(outputFile)) {
          const report = JSON.parse(fs.readFileSync(outputFile, 'utf8'));
          resolve({ report, outputFile });
        } else {
          reject(new Error('报告文件未生成'));
        }
      } else {
        reject(new Error(`监控失败: ${stderr}`));
      }
    });
  });
}

// 发送通知
async function sendNotification(report) {
  if (!CONFIG.notifications.enabled) {
    console.log('📢 通知已禁用');
    return false;
  }
  
  const hasCriticalErrors = report.criticalIssues && report.criticalIssues.length > 0;
  const totalErrors = report.summary.totalErrors;
  
  // 如果只通知关键错误且没有关键错误，则跳过
  if (CONFIG.notifications.notifyOnCriticalOnly && !hasCriticalErrors) {
    console.log('✅ 无关键错误，跳过通知');
    return false;
  }
  
  const webhookUrl = CONFIG.notifications.webhookUrl;
  
  if (!webhookUrl) {
    console.log('⚠️  Webhook URL未配置');
    return false;
  }
  
  try {
    console.log('📤 发送通知...');
    
    // 构建消息
    const message = {
      text: '📊 iMato 营销页面监控报告',
      blocks: [
        {
          type: 'header',
          text: {
            type: 'plain_text',
            text: '📊 iMato 营销页面监控报告',
            emoji: true
          }
        },
        {
          type: 'section',
          fields: [
            {
              type: 'mrkdwn',
              text: `*监控时间*\n${new Date().toLocaleString()}`
            },
            {
              type: 'mrkdwn',
              text: `*监控页面*\n${report.summary.totalPages} 个`
            }
          ]
        },
        {
          type: 'section',
          fields: [
            {
              type: 'mrkdwn',
              text: `*总错误数*\n${report.summary.totalErrors}`
            },
            {
              type: 'mrkdwn',
              text: `*成功率*\n${report.summary.successRate}`
            }
          ]
        }
      ]
    };
    
    // 添加关键错误信息
    if (hasCriticalErrors) {
      message.blocks.push({
        type: 'divider'
      });
      
      message.blocks.push({
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `🔥 *关键错误 (${report.criticalIssues.length} 个)*`
        }
      });
      
      report.criticalIssues.slice(0, 5).forEach(issue => {
        const errorMessages = issue.errors.map(e => `• ${e.type}: ${e.message}`).join('\n');
        message.blocks.push({
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*${issue.page}*\n${errorMessages}`
          }
        });
      });
    }
    
    // 添加操作按钮
    message.blocks.push({
      type: 'actions',
      elements: [
        {
          type: 'button',
          text: {
            type: 'plain_text',
            text: '查看详细报告',
            emoji: true
          },
          url: `${CONFIG.baseUrl}/monitoring-reports`
        }
      ]
    });
    
    // 发送请求
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(message)
    });
    
    if (response.ok) {
      console.log('✅ 通知发送成功');
      return true;
    } else {
      console.error(`❌ 通知发送失败: ${response.status} ${response.statusText}`);
      return false;
    }
    
  } catch (error) {
    console.error('❌ 发送通知失败:', error.message);
    return false;
  }
}

// 清理旧报告
function cleanupOldReports() {
  const outputDir = CONFIG.output.dir;
  
  if (!fs.existsSync(outputDir)) {
    return;
  }
  
  const files = fs.readdirSync(outputDir);
  const now = Date.now();
  const maxAge = (CONFIG.output.keepReportsForDays || 30) * 24 * 60 * 60 * 1000;
  
  let deletedCount = 0;
  
  files.forEach(file => {
    if (!file.startsWith('monitor-report-') && !file.startsWith('continuous-monitor-')) {
      return;
    }
    
    const filePath = path.join(outputDir, file);
    const stats = fs.statSync(filePath);
    const age = now - stats.mtime.getTime();
    
    if (age > maxAge) {
      fs.unlinkSync(filePath);
      deletedCount++;
    }
  });
  
  if (deletedCount > 0) {
    console.log(`🗑️  清理了 ${deletedCount} 个旧报告`);
  }
}

// 生成趋势报告
function generateTrendReport() {
  const outputDir = CONFIG.output.dir;
  
  if (!fs.existsSync(outputDir)) {
    return null;
  }
  
  const files = fs.readdirSync(outputDir);
  const reports = [];
  
  // 收集最近30天的报告
  files.forEach(file => {
    if (file.endsWith('.json') && (file.startsWith('monitor-report-') || file.startsWith('continuous-monitor-'))) {
      const filePath = path.join(outputDir, file);
      try {
        const report = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        reports.push({
          timestamp: report.summary.timestamp,
          totalErrors: report.summary.totalErrors,
          totalWarnings: report.summary.totalWarnings,
          successRate: parseFloat(report.summary.successRate),
          avgLoadTime: parseInt(report.summary.avgLoadTime)
        });
      } catch (e) {
        // 忽略解析失败的文件
      }
    }
  });
  
  // 按时间排序
  reports.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
  
  if (reports.length === 0) {
    return null;
  }
  
  // 计算趋势
  const recent = reports.slice(-5); // 最近5次
  const oldest = recent[0];
  const latest = recent[recent.length - 1];
  
  const trend = {
    errorTrend: latest.totalErrors - oldest.totalErrors,
    warningTrend: latest.totalWarnings - oldest.totalWarnings,
    successRateTrend: latest.successRate - oldest.successRate,
    loadTimeTrend: latest.avgLoadTime - oldest.avgLoadTime,
    reports: recent
  };
  
  return trend;
}

// 主监控循环
async function runContinuousMonitor() {
  console.log('🔄 启动持续监控服务');
  console.log(`⏰ 当前时间: ${new Date().toLocaleString()}`);
  
  let hasErrors = false;
  
  try {
    // 执行桌面端监控
    console.log('\n💻 执行桌面端监控...');
    const desktopResult = await runMonitor({ mobile: false });
    
    // 执行移动端监控
    console.log('\n📱 执行移动端监控...');
    const mobileResult = await runMonitor({ mobile: true });
    
    // 合并报告
    const combinedReport = {
      summary: {
        timestamp: new Date().toISOString(),
        desktop: desktopResult.report.summary,
        mobile: mobileResult.report.summary,
        totalErrors: desktopResult.report.summary.totalErrors + mobileResult.report.summary.totalErrors,
        hasCriticalErrors: desktopResult.report.criticalIssues.length > 0 || mobileResult.report.criticalIssues.length > 0
      },
      desktop: desktopResult.report,
      mobile: mobileResult.report
    };
    
    // 发送通知
    const notified = await sendNotification(combinedReport);
    
    // 清理旧报告
    cleanupOldReports();
    
    // 生成趋势分析
    const trend = generateTrendReport();
    if (trend) {
      console.log('\n\n📈 趋势分析:');
      console.log(`   错误变化: ${trend.errorTrend >= 0 ? '+' : ''}${trend.errorTrend}`);
      console.log(`   成功率变化: ${trend.successRateTrend >= 0 ? '+' : ''}${trend.successRateTrend.toFixed(2)}%`);
      console.log(`   加载时间变化: ${trend.loadTimeTrend >= 0 ? '+' : ''}${trend.loadTimeTrend}ms`);
    }
    
    // 判断是否有错误
    hasErrors = combinedReport.summary.hasCriticalErrors;
    
    console.log('\n✅ 监控完成');
    console.log(`📊 桌面端错误: ${desktopResult.report.summary.totalErrors}`);
    console.log(`📊 移动端错误: ${mobileResult.report.summary.totalErrors}`);
    
    if (notified) {
      console.log('📢 通知已发送');
    }
    
  } catch (error) {
    console.error('❌ 监控失败:', error.message);
    hasErrors = true;
    
    // 发送失败通知
    if (CONFIG.notifications.enabled) {
      await sendNotification({
        summary: {
          timestamp: new Date().toISOString(),
          hasCriticalErrors: true
        },
        error: error.message
      });
    }
  }
  
  return hasErrors;
}

// 守护进程模式
async function runDaemon() {
  if (!loadConfig()) {
    process.exit(1);
  }
  
  console.log('👻 启动守护进程模式');
  console.log(`⏰ 运行时间: ${new Date().toLocaleString()}`);
  console.log(`📡 监控URL: ${CONFIG.baseUrl}`);
  console.log(`📊 监控页面: ${CONFIG.pages.length} 个`);
  console.log(`📦 输出目录: ${CONFIG.output.dir}`);
  
  if (CONFIG.notifications.enabled) {
    console.log(`📢 通知: 已启用${CONFIG.notifications.notifyOnCriticalOnly ? ' (仅关键错误)' : ''}`);
  }
  
  console.log('\n' + '='.repeat(60));
  console.log('服务运行中... 按 Ctrl+C 停止');
  console.log('='.repeat(60));
  console.log();
  
  // 立即执行一次
  await runContinuousMonitor();
  
  // 定时执行（每6小时）
  const interval = 6 * 60 * 60 * 1000;
  
  setInterval(async () => {
    console.log('\n' + '='.repeat(60));
    console.log(`⏰ 定时任务执行: ${new Date().toLocaleString()}`);
    console.log('='.repeat(60));
    
    await runContinuousMonitor();
    
    console.log();
    console.log('⏳ 等待下一次执行...');
    console.log();
  }, interval);
}

// 单次执行模式
async function runOnce() {
  if (!loadConfig()) {
    process.exit(1);
  }
  
  const hasErrors = await runContinuousMonitor();
  process.exit(hasErrors ? 1 : 0);
}

// 命令行接口
async function main() {
  const args = process.argv.slice(2);
  
  if (args.includes('--daemon') || args.includes('-d')) {
    // 守护进程模式
    await runDaemon();
  } else if (args.includes('--help') || args.includes('-h')) {
    console.log(`
iMato 持续监控服务

使用方法:
  node continuous-monitor.js [options]

选项:
  --daemon, -d      守护进程模式（定时执行）
  --once            单次执行模式（默认）
  --help, -h        显示帮助信息

示例:
  # 单次执行
  node continuous-monitor.js
  
  # 守护进程模式（每6小时执行一次）
  node continuous-monitor.js --daemon
  
  # 使用pm2运行守护进程
  pm2 start continuous-monitor.js -- --daemon
`);
  } else if (args.includes('--once')) {
    // 单次执行
    await runOnce();
  } else {
    // 默认单次执行
    await runOnce();
  }
}

// 运行主函数
if (require.main === module) {
  main().catch(error => {
    console.error('❌ 执行失败:', error);
    process.exit(1);
  });
}

module.exports = { runContinuousMonitor, sendNotification };
