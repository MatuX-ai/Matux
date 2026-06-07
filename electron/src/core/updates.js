/**
 * 自动更新模块
 * @module updates
 *
 * 负责检查和下载应用更新
 */

const { dialog } = require('electron');

/**
 * 检查应用更新
 * @param {Object} options - 配置选项
 * @param {BrowserWindow|null} options.mainWindow - 主窗口引用
 * @param {Function} options.showNotification - 显示通知回调
 */
async function checkForUpdates({ mainWindow, showNotification }) {
  try {
    // 动态导入 electron-updater（可选依赖）
    const updaterModule = require('electron-updater');
    const autoUpdater = updaterModule && updaterModule.autoUpdater;
    
    if (!autoUpdater) {
      console.warn('[WARN] electron-updater 模块结构异常，跳过更新检查');
      return;
    }

    autoUpdater.autoDownload = false;
    autoUpdater.autoInstallOnAppQuit = true;

    // 发现新版本
    autoUpdater.on('update-available', (info) => {
      console.log('[UPDATE] 发现新版本:', info.version);
      showNotification('发现新版本', `v${info.version} 可用，点击更新`, 'update');

      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('app-event', {
          type: 'update-available',
          version: info.version,
          releaseNotes: info.releaseNotes,
        });
      }

      // 提示用户下载
      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: '发现新版本',
        message: `MatuX v${info.version} 已发布`,
        detail: '是否立即下载更新？',
        buttons: ['下载更新', '稍后提醒'],
        defaultId: 0,
      }).then(({ response }) => {
        if (response === 0) {
          autoUpdater.downloadUpdate();
        }
      });
    });

    // 下载进度
    autoUpdater.on('download-progress', (progress) => {
      console.log(`[UPDATE] 下载进度: ${progress.percent.toFixed(1)}%`);
    });

    // 下载完成
    autoUpdater.on('update-downloaded', () => {
      console.log('[UPDATE] 更新下载完成');
      showNotification('更新就绪', '新版本已下载，重启后生效', 'update');

      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: '更新就绪',
        message: '新版本已下载完成',
        detail: '需要重启应用以完成安装。',
        buttons: ['立即重启', '稍后'],
        defaultId: 0,
      }).then(({ response }) => {
        if (response === 0) {
          autoUpdater.quitAndInstall();
        }
      });
    });

    autoUpdater.on('error', (err) => {
      console.error('[UPDATE] 更新检查失败:', err.message);
    });

    await autoUpdater.checkForUpdates();
  } catch (err) {
    // electron-updater 未安装
    console.warn('[WARN] electron-updater 未安装，跳过自动更新检查');
    console.warn('[WARN] 安装方式: cd electron && npm install electron-updater');
  }
}

module.exports = {
  checkForUpdates,
};
