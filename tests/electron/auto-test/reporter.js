/**
 * iMato 学习端自动化测试 - 日志与报告模块
 *
 * 提供：
 * 1. 分级日志记录（INFO/WARN/ERROR/DEBUG）
 * 2. 测试执行日志持久化
 * 3. HTML 测试报告生成
 * 4. JSON 测试数据导出
 */

const fs = require('fs');
const path = require('path');

// ==================== 日志级别 ====================

const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
};

const LOG_COLORS = {
  DEBUG: '\x1b[36m', // 青色
  INFO: '\x1b[32m',  // 绿色
  WARN: '\x1b[33m',  // 黄色
  ERROR: '\x1b[31m', // 红色
  RESET: '\x1b[0m',
  BOLD: '\x1b[1m',
  DIM: '\x1b[2m',
};

// ==================== Logger 类 ====================

class Logger {
  constructor(logFilePath, minLevel = 'DEBUG') {
    this.logFilePath = logFilePath;
    this.minLevel = LOG_LEVELS[minLevel] || 0;
    this.entries = [];

    // 确保日志目录存在
    const dir = path.dirname(logFilePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    // 清空旧日志
    fs.writeFileSync(logFilePath, '', 'utf-8');
  }

  _formatTime() {
    return new Date().toISOString().replace('T', ' ').replace('Z', '');
  }

  _log(level, message, data = null) {
    if (LOG_LEVELS[level] < this.minLevel) return;

    const timestamp = this._formatTime();
    const entry = { timestamp, level, message, data };
    this.entries.push(entry);

    // 控制台输出（带颜色）
    const color = LOG_COLORS[level] || '';
    const dataStr = data ? ` | ${JSON.stringify(data)}` : '';
    console.log(`${color}[${level}]${LOG_COLORS.RESET} ${LOG_COLORS.DIM}${timestamp}${LOG_COLORS.RESET} ${message}${dataStr}`);

    // 文件输出（纯文本）
    const fileLine = `[${level}] ${timestamp} ${message}${dataStr}\n`;
    fs.appendFileSync(this.logFilePath, fileLine, 'utf-8');
  }

  debug(message, data) { this._log('DEBUG', message, data); }
  info(message, data) { this._log('INFO', message, data); }
  warn(message, data) { this._log('WARN', message, data); }
  error(message, data) { this._log('ERROR', message, data); }

  /** 输出分隔线 */
  separator(char = '─', length = 70) {
    const line = char.repeat(length);
    console.log(`${LOG_COLORS.DIM}${line}${LOG_COLORS.RESET}`);
    fs.appendFileSync(this.logFilePath, `${line}\n`, 'utf-8');
  }

  /** 输出阶段标题 */
  phase(title) {
    const line = `\n${'═'.repeat(70)}\n  ${title}\n${'═'.repeat(70)}`;
    console.log(`${LOG_COLORS.BOLD}${LOG_COLORS.INFO}${line}${LOG_COLORS.RESET}`);
    fs.appendFileSync(this.logFilePath, `${line}\n`, 'utf-8');
  }

  /** 获取所有日志条目 */
  getEntries() {
    return this.entries;
  }
}

// ==================== TestReport 类 ====================

class TestReport {
  constructor(config) {
    this.config = config;
    this.startTime = null;
    this.endTime = null;
    this.pageResults = [];
    this.loginResult = null;
    this.summary = {
      total: 0,
      passed: 0,
      failed: 0,
      skipped: 0,
      warnings: 0,
    };
  }

  /** 记录登录结果 */
  setLoginResult(result) {
    this.loginResult = result;
  }

  /** 记录单页测试结果 */
  addPageResult(result) {
    this.pageResults.push(result);

    this.summary.total++;
    if (result.status === 'passed') this.summary.passed++;
    else if (result.status === 'failed') this.summary.failed++;
    else if (result.status === 'skipped') this.summary.skipped++;

    this.summary.warnings += (result.warnings || []).length;
  }

  /** 生成 JSON 报告 */
  toJSON() {
    return {
      title: 'iMato 学习端自动化测试报告',
      environment: {
        frontendUrl: this.config.frontendUrl,
        account: {
          username: this.config.account?.username,
          role: this.config.account?.role,
        },
        timestamp: new Date().toISOString(),
      },
      duration: {
        start: this.startTime?.toISOString(),
        end: this.endTime?.toISOString(),
        totalMs: this.endTime && this.startTime ? this.endTime - this.startTime : 0,
        totalSeconds: this.endTime && this.startTime ? Math.round((this.endTime - this.startTime) / 1000) : 0,
      },
      login: this.loginResult,
      summary: this.summary,
      pages: this.pageResults,
    };
  }

  /** 生成 HTML 报告 */
  toHTML() {
    const data = this.toJSON();
    const passRate = data.summary.total > 0
      ? Math.round((data.summary.passed / data.summary.total) * 100)
      : 0;

    const statusBadge = (status) => {
      const colors = {
        passed: '#10b981',
        failed: '#ef4444',
        skipped: '#f59e0b',
        warning: '#f59e0b',
      };
      const labels = {
        passed: '通过',
        failed: '失败',
        skipped: '跳过',
        warning: '警告',
      };
      return `<span style="display:inline-block;padding:2px 10px;border-radius:12px;color:#fff;font-size:12px;background:${colors[status] || '#6b7280'}">${labels[status] || status}</span>`;
    };

    const loginStatusHtml = data.login
      ? statusBadge(data.login.success ? 'passed' : 'failed') +
        `<span style="margin-left:8px;color:#6b7280">${data.login.success ? '登录成功' : '登录失败: ' + (data.login.error || '')}</span>`
      : '<span style="color:#6b7280">未执行</span>';

    const durationStr = data.duration.totalSeconds > 0
      ? `${data.duration.totalSeconds} 秒`
      : '—';

    const pageRows = data.pages.map((p, i) => {
      const requiredHtml = (p.requiredChecks || []).map(c =>
        `<div style="margin:2px 0;font-size:13px">${c.found ? '✅' : '❌'} ${c.description} <code style="color:#6b7280;font-size:11px">${c.selector}</code></div>`
      ).join('');

      const optionalHtml = (p.optionalChecks || []).map(c =>
        `<div style="margin:2px 0;font-size:13px;color:#9ca3af">${c.found ? '✅' : '⚠️'} ${c.description} <code style="font-size:11px">${c.selector}</code></div>`
      ).join('');

      const interactionHtml = (p.interactionResults || []).map(ir =>
        `<div style="margin:2px 0;font-size:13px">${ir.success ? '✅' : '❌'} ${ir.name}${ir.error ? ': ' + ir.error : ''}</div>`
      ).join('');

      const errorHtml = p.error
        ? `<div style="margin-top:4px;padding:6px 10px;background:#fef2f2;border-radius:4px;font-size:12px;color:#dc2626">${p.error}</div>`
        : '';

      return `
        <tr>
          <td style="text-align:center;padding:8px;border-bottom:1px solid #e5e7eb">${i + 1}</td>
          <td style="padding:8px;border-bottom:1px solid #e5e7eb;font-weight:500">${p.name}</td>
          <td style="padding:8px;border-bottom:1px solid #e5e7eb"><code style="font-size:12px;background:#f1f5f9;padding:2px 6px;border-radius:3px">${p.path}</code></td>
          <td style="text-align:center;padding:8px;border-bottom:1px solid #e5e7eb">${statusBadge(p.status)}</td>
          <td style="padding:8px;border-bottom:1px solid #e5e7eb;font-size:13px">${p.loadTimeMs || '—'} ms</td>
          <td style="padding:8px;border-bottom:1px solid #e5e7eb">
            ${requiredHtml}${optionalHtml}${interactionHtml}${errorHtml}
          </td>
        </tr>`;
    }).join('');

    return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>iMato 学习端自动化测试报告</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.6; }
    .container { max-width: 1200px; margin: 0 auto; padding: 24px; }
    .header { text-align: center; padding: 32px 0; border-bottom: 2px solid #e2e8f0; margin-bottom: 24px; }
    .header h1 { font-size: 28px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }
    .header p { color: #64748b; font-size: 14px; }
    .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .summary-card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); text-align: center; }
    .summary-card .value { font-size: 32px; font-weight: 700; margin-bottom: 4px; }
    .summary-card .label { font-size: 13px; color: #64748b; }
    .summary-card.passed .value { color: #10b981; }
    .summary-card.failed .value { color: #ef4444; }
    .summary-card.skipped .value { color: #f59e0b; }
    .summary-card.rate .value { color: #3b82f6; }
    .info-bar { display: flex; flex-wrap: wrap; gap: 24px; background: #fff; border-radius: 12px; padding: 16px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 24px; font-size: 14px; }
    .info-bar .item { display: flex; align-items: center; gap: 6px; }
    .info-bar .item .key { color: #64748b; }
    .info-bar .item .val { font-weight: 500; }
    table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    thead th { background: #f1f5f9; padding: 12px 8px; font-size: 13px; font-weight: 600; color: #475569; text-align: left; border-bottom: 2px solid #e2e8f0; }
    tbody td { vertical-align: top; }
    code { font-family: 'Cascadia Code', 'Fira Code', monospace; }
    .footer { text-align: center; padding: 24px 0; color: #94a3b8; font-size: 12px; margin-top: 24px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>iMato 学习端自动化测试报告</h1>
      <p>基于 Electron + Playwright 的全页面遍历与功能校验</p>
    </div>

    <div class="summary-grid">
      <div class="summary-card passed"><div class="value">${data.summary.passed}</div><div class="label">通过</div></div>
      <div class="summary-card failed"><div class="value">${data.summary.failed}</div><div class="label">失败</div></div>
      <div class="summary-card skipped"><div class="value">${data.summary.skipped}</div><div class="label">跳过</div></div>
      <div class="summary-card rate"><div class="value">${passRate}%</div><div class="label">通过率</div></div>
    </div>

    <div class="info-bar">
      <div class="item"><span class="key">测试账号:</span><span class="val">${data.environment.account?.username || '—'} (${data.environment.account?.role || '—'})</span></div>
      <div class="item"><span class="key">前端地址:</span><span class="val">${data.environment.frontendUrl}</span></div>
      <div class="item"><span class="key">登录状态:</span>${loginStatusHtml}</div>
      <div class="item"><span class="key">总耗时:</span><span class="val">${durationStr}</span></div>
      <div class="item"><span class="key">测试时间:</span><span class="val">${data.duration.start || '—'}</span></div>
    </div>

    <table>
      <thead>
        <tr>
          <th style="width:40px">#</th>
          <th style="width:120px">页面</th>
          <th style="width:160px">路径</th>
          <th style="width:70px">状态</th>
          <th style="width:90px">加载耗时</th>
          <th>校验详情</th>
        </tr>
      </thead>
      <tbody>
        ${pageRows}
      </tbody>
    </table>

    <div class="footer">
      iMato Auto-Test Report · Generated at ${new Date().toISOString()}
    </div>
  </div>
</body>
</html>`;
  }

  /** 保存报告到文件 */
  save(reportDir) {
    if (!fs.existsSync(reportDir)) {
      fs.mkdirSync(reportDir, { recursive: true });
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

    // JSON 报告
    const jsonPath = path.join(reportDir, `test-report-${timestamp}.json`);
    fs.writeFileSync(jsonPath, JSON.stringify(this.toJSON(), null, 2), 'utf-8');

    // HTML 报告
    const htmlPath = path.join(reportDir, `test-report-${timestamp}.html`);
    fs.writeFileSync(htmlPath, this.toHTML(), 'utf-8');

    return { jsonPath, htmlPath };
  }
}

// ==================== 控制台摘要输出 ====================

function printSummary(report, logger) {
  const data = report.toJSON();
  const passRate = data.summary.total > 0
    ? Math.round((data.summary.passed / data.summary.total) * 100)
    : 0;

  logger.separator('═');
  logger.phase('测试结果摘要');

  console.log('');
  console.log(`  ${LOG_COLORS.BOLD}总计:${LOG_COLORS.RESET} ${data.summary.total} 个页面`);
  console.log(`  ${LOG_COLORS.INFO}✅ 通过:${LOG_COLORS.RESET} ${data.summary.passed}`);
  console.log(`  ${LOG_COLORS.ERROR}❌ 失败:${LOG_COLORS.RESET} ${data.summary.failed}`);
  console.log(`  ${LOG_COLORS.WARN}⚠️  跳过:${LOG_COLORS.RESET} ${data.summary.skipped}`);
  console.log(`  ${LOG_COLORS.BOLD}📊 通过率:${LOG_COLORS.RESET} ${passRate}%`);
  console.log('');

  // 失败详情
  const failedPages = data.pages.filter(p => p.status === 'failed');
  if (failedPages.length > 0) {
    console.log(`  ${LOG_COLORS.ERROR}${LOG_COLORS.BOLD}失败页面详情:${LOG_COLORS.RESET}`);
    failedPages.forEach(p => {
      console.log(`    ❌ ${p.name} (${p.path})`);
      if (p.error) console.log(`       错误: ${p.error}`);
      const failedChecks = (p.requiredChecks || []).filter(c => !c.found);
      failedChecks.forEach(c => {
        console.log(`       缺失元素: ${c.description} [${c.selector}]`);
      });
    });
    console.log('');
  }

  logger.separator('═');
}

module.exports = {
  Logger,
  TestReport,
  printSummary,
};
