/**
 * MatuX Electron 系统托盘管理器
 * 
 * 负责托盘图标的创建、菜单管理和状态更新
 */

const { Tray, Menu, Notification, nativeImage } = require('electron');
const fs = require('fs');
const { APP_PATHS } = require('../config/constants');

class TrayManager {
  /**
   * @param {object} options 配置选项
   * @param {BrowserWindow} options.mainWindow 主窗口引用
   * @param {function} options.onRestartBackend 重启后端回调
   * @param {function} options.onShowNotification 显示通知回调
   * @param {function} options.onCheckUpdates 检查更新回调
   * @param {function} options.onQuit 退出回调
   */
  constructor(options) {
    this.mainWindow = options.mainWindow;
    this.onRestartBackend = options.onRestartBackend || (() => {});
    this.onShowNotification = options.onShowNotification || (() => {});
    this.onCheckUpdates = options.onCheckUpdates || (() => {});
    this.onQuit = options.onQuit || (() => {});

    this.tray = null;
    this.backendStatus = 'unknown'; // 'healthy' | 'degraded' | 'unhealthy' | 'unknown'
    this.moduleSummary = null;
  }

  /**
   * 创建托盘图标
   */
  create() {
    if (this.tray) {
      return this.tray;
    }

    const iconPath = APP_PATHS.icon;
    // 如果图标不存在，跳过创建
    if (!fs.existsSync(iconPath)) {
      console.warn('[WARN] 托盘图标不存在，跳过创建系统托盘');
      return null;
    }

    this.tray = new Tray(iconPath);
    this.tray.setToolTip('MatuX - AI 编程学习平台');

    // 双击显示主窗口
    this.tray.on('double-click', () => {
      if (this.mainWindow && !this.mainWindow.isDestroyed()) {
        this.mainWindow.show();
        this.mainWindow.focus();
      }
    });

    this.updateMenu();

    return this.tray;
  }

  /**
   * 更新托盘菜单
   */
  updateMenu() {
    if (!this.tray) return;

    const { label, emoji } = this.getStatusInfo();

    const contextMenu = Menu.buildFromTemplate([
      {
        label: '显示主窗口',
        click: () => {
          if (this.mainWindow && !this.mainWindow.isDestroyed()) {
            this.mainWindow.show();
            this.mainWindow.focus();
          }
        },
      },
      { type: 'separator' },
      {
        label: `${emoji} ${label}`,
        enabled: false,
      },
      ...this.buildModuleSummaryItems(),
      { type: 'separator' },
      {
        label: '重启后端',
        click: () => this.onRestartBackend(),
      },
      {
        label: '学习提醒',
        click: () => this.onShowNotification('学习提醒', '该继续今天的学习啦！坚持就是胜利'),
      },
      { type: 'separator' },
      {
        label: '检查更新',
        click: () => this.onCheckUpdates(),
      },
      { type: 'separator' },
      {
        label: '退出 MatuX',
        click: () => this.onQuit(),
      },
    ]);

    this.tray.setContextMenu(contextMenu);
  }

  /**
   * 构建模块摘要菜单项
   */
  buildModuleSummaryItems() {
    if (!this.moduleSummary) return [];

    const items = [];
    const { active, total, degraded, failed } = this.moduleSummary;

    items.push({
      label: `模块: ${active}/${total} 活跃`,
      enabled: false,
    });

    if (degraded > 0) {
      items.push({ label: `${degraded} 个模块降级`, enabled: false });
    }

    if (failed > 0) {
      items.push({ label: `${failed} 个模块失败`, enabled: false });
    }

    return items;
  }

  /**
   * 获取状态信息
   */
  getStatusInfo() {
    let label, emoji;

    switch (this.backendStatus) {
      case 'healthy':
        label = '所有服务正常';
        emoji = '🟢';
        break;
      case 'degraded':
        label = '部分模块降级运行';
        emoji = '🟡';
        break;
      case 'unhealthy':
        label = '核心服务异常';
        emoji = '🔴';
        break;
      default:
        label = '状态未知';
        emoji = '⚪';
    }

    return { label, emoji };
  }

  /**
   * 更新后端状态
   * @param {string} status 'healthy' | 'degraded' | 'unhealthy' | 'unknown'
   * @param {object} moduleSummary 模块摘要
   */
  updateStatus(status, moduleSummary = null) {
    this.backendStatus = status;
    if (moduleSummary) {
      this.moduleSummary = moduleSummary;
    }
    this.updateMenu();

    // 更新 tooltip
    const { label } = this.getStatusInfo();
    if (this.tray) {
      this.tray.setToolTip(`MatuX - ${label}`);
    }
  }

  /**
   * 更新模块摘要
   * @param {object} summary { active, total, degraded, failed }
   */
  updateModuleSummary(summary) {
    this.moduleSummary = summary;
    this.updateMenu();
  }

  /**
   * 销毁托盘
   */
  destroy() {
    if (this.tray) {
      this.tray.destroy();
      this.tray = null;
    }
  }

  /**
   * 获取托盘实例
   */
  getTray() {
    return this.tray;
  }

  /**
   * 检查托盘是否已创建
   */
  isCreated() {
    return !!this.tray;
  }
}

/**
 * 显示系统通知
 * @param {string} title 标题
 * @param {string} body 内容
 * @param {string} category 类别
 * @param {BrowserWindow} mainWindow 主窗口
 */
function showNotification(title, body, category = 'learning', mainWindow = null) {
  if (!Notification.isSupported()) {
    console.log('[INFO] 系统不支持原生通知');
    return;
  }

  const notification = new Notification({
    title,
    body,
    icon: fs.existsSync(APP_PATHS.icon) ? APP_PATHS.icon : undefined,
    silent: false,
  });

  notification.on('click', () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.show();
      mainWindow.focus();
    }
  });

  notification.show();
  console.log(`[NOTIFICATION] [${category}] ${title}: ${body}`);
}

module.exports = { TrayManager, showNotification };
