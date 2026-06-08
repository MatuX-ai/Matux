/**
 * Electron 自动更新服务
 *
 * 使用 electron-updater 实现应用自动更新
 *
 * 基于 PRD F-16: 自动更新
 */

const { autoUpdater } = require('electron-updater');
const { ipcMain, BrowserWindow } = require('electron');
const log = require('electron-log');

class AutoUpdaterService {
  constructor() {
    // 配置日志
    autoUpdater.logger = log;
    autoUpdater.logger.transports.file.level = 'info';

    // 自动下载
    autoUpdater.autoDownload = false;

    // 自动安装
    autoUpdater.autoInstallOnAppQuit = true;

    // 事件绑定
    this.bindEvents();
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    autoUpdater.on('checking-for-update', () => {
      log.info('[AutoUpdater] 正在检查更新...');
      this.sendStatusToWindow('checking-for-update');
    });

    autoUpdater.on('update-available', (info) => {
      log.info('[AutoUpdater] 发现新版本:', info.version);
      this.sendStatusToWindow('update-available', info);
    });

    autoUpdater.on('update-not-available', (info) => {
      log.info('[AutoUpdater] 已是最新版本:', info.version);
      this.sendStatusToWindow('update-not-available', info);
    });

    autoUpdater.on('error', (err) => {
      log.error('[AutoUpdater] 更新错误:', err);
      this.sendStatusToWindow('error', { message: err.message });
    });

    autoUpdater.on('download-progress', (progressObj) => {
      const logMessage = `下载速度: ${progressObj.bytesPerSecond} - 下载进度: ${progressObj.percent.toFixed(2)}%`;
      log.info('[AutoUpdater]', logMessage);
      this.sendStatusToWindow('download-progress', progressObj);
    });

    autoUpdater.on('update-downloaded', (info) => {
      log.info('[AutoUpdater] 更新下载完成:', info.version);
      this.sendStatusToWindow('update-downloaded', info);

      // 显示通知
      this.showUpdateNotification(info);
    });
  }

  /**
   * 向渲染进程发送状态
   */
  sendStatusToWindow(status, data = {}) {
    const windows = BrowserWindow.getAllWindows();
    for (const window of windows) {
      if (!window.isDestroyed()) {
        window.webContents.send('auto-updater-status', { status, data });
      }
    }
  }

  /**
   * 显示更新通知
   */
  showUpdateNotification(info) {
    const { Notification } = require('electron');
    if (Notification.isSupported()) {
      const notification = new Notification({
        title: 'MatuX 更新可用',
        body: `新版本 ${info.version} 已下载完成，将在重启后自动安装。`,
        silent: false,
      });
      notification.show();
    }
  }

  /**
   * 获取自动更新器实例
   */
  getAutoUpdater() {
    return autoUpdater;
  }

  /**
   * 检查更新
   */
  async checkForUpdates() {
    try {
      log.info('[AutoUpdater] 开始检查更新...');
      return await autoUpdater.checkForUpdates();
    } catch (error) {
      log.error('[AutoUpdater] 检查更新失败:', error);
      return null;
    }
  }

  /**
   * 下载更新
   */
  async downloadUpdate() {
    try {
      log.info('[AutoUpdater] 开始下载更新...');
      return await autoUpdater.downloadUpdate();
    } catch (error) {
      log.error('[AutoUpdater] 下载更新失败:', error);
      return null;
    }
  }

  /**
   * 安装更新并重启
   */
  quitAndInstall() {
    log.info('[AutoUpdater] 安装更新并重启...');
    autoUpdater.quitAndInstall(false, true);
  }

  /**
   * 获取当前版本
   */
  getCurrentVersion() {
    return autoUpdater.currentVersion.version;
  }

  /**
   * 设置 Feed URL
   */
  setFeedURL(url) {
    autoUpdater.setFeedURL(url);
  }

  /**
   * 允许版本号
   */
  allowVersion(version) {
    autoUpdater.allowVersion(version);
  }

  /**
   * 禁用版本号
   */
  disableVersion() {
    autoUpdater.autoUpdater.disable();
  }
}

// 导出单例
module.exports = { AutoUpdaterService };
