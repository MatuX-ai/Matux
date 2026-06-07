/**
 * 插件管理 IPC Handlers
 * @module ipc/handlers/plugin-handlers
 *
 * 处理设备评估、插件安装/下载/推荐等 IPC 通信
 */

const { ipcMain } = require('electron');

/**
 * 创建插件 IPC Handlers
 * @param {object} options 配置选项
 * @param {object} options.appState AppState 实例
 * @param {function} options.assessDevice 设备评估函数
 * @param {function} options.loadDeviceProfile 加载设备配置函数
 * @param {function} options.saveDeviceProfile 保存设备配置函数
 * @param {function} options.shouldReassess 判断是否需要重新评估函数
 * @param {object} options.pluginInstaller 插件安装器实例
 * @param {object} options.pluginDownloader 插件下载器实例
 * @param {object} options.pluginRecommender 推荐引擎实例
 * @param {object} options.installConfigManager 安装配置管理器实例
 * @param {object} options.pluginStoreEnhancer 插件商店增强实例
 * @param {object} options.pluginRegistry 插件注册表实例
 * @param {function} options.registerPluginInstallerIPC 注册安装器 IPC 函数
 * @param {function} options.registerPluginDownloaderIPC 注册下载器 IPC 函数
 * @returns {object} handlers 对象
 */
function createPluginHandlers(options = {}) {
  const {
    appState = null,
    assessDevice = null,
    loadDeviceProfile = null,
    saveDeviceProfile = null,
    shouldReassess = null,
    pluginInstaller = null,
    pluginDownloader = null,
    pluginRecommender = null,
    installConfigManager = null,
    pluginStoreEnhancer = null,
    pluginRegistry = null,
    registerPluginInstallerIPC = null,
    registerPluginDownloaderIPC = null,
  } = options;

  /**
   * 获取主窗口引用
   */
  function getMainWindow() {
    return appState ? appState.getMainWindow() : null;
  }

  /**
   * 注册所有插件相关 IPC 处理器
   */
  function register() {
    // ===== 设备评估 IPC =====
    registerDeviceHandlers();

    // ===== 插件管理 IPC =====
    registerPluginManagerHandlers();

    // ===== 推荐引擎 IPC =====
    registerRecommenderHandlers();

    // ===== 安装配置 IPC =====
    registerInstallConfigHandlers();

    // ===== 插件商店增强 IPC =====
    registerStoreEnhancerHandlers();
  }

  /**
   * 注册设备评估相关 handlers
   */
  function registerDeviceHandlers() {
    // 获取设备评估报告
    ipcMain.handle('plugin:device-profile', async () => {
      try {
        if (!loadDeviceProfile) {
          return { success: false, error: '设备评估模块未初始化' };
        }
        const profile = loadDeviceProfile();
        if (profile && (!shouldReassess || !shouldReassess(profile))) {
          return { success: true, profile };
        }
        // 需要重新评估
        if (assessDevice) {
          const newProfile = await assessDevice();
          if (saveDeviceProfile) {
            saveDeviceProfile(newProfile);
          }
          return { success: true, profile: newProfile };
        }
        return { success: false, error: '评估函数未初始化' };
      } catch (err) {
        console.error('[ERROR] 获取设备评估报告失败:', err.message);
        return { success: false, error: err.message };
      }
    });

    // 重新评估设备
    ipcMain.handle('plugin:reassess-device', async () => {
      try {
        if (!assessDevice) {
          return { success: false, error: '设备评估模块未初始化' };
        }
        console.log('[INFO] 用户请求重新评估设备');
        const profile = await assessDevice();
        if (saveDeviceProfile) {
          saveDeviceProfile(profile);
        }
        // 通知渲染进程
        const mainWindow = getMainWindow();
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('plugin:status-change', {
            type: 'device-reassessed',
            profile,
          });
        }
        return { success: true, profile };
      } catch (err) {
        console.error('[ERROR] 重新评估设备失败:', err.message);
        return { success: false, error: err.message };
      }
    });

    // 评估指定插件兼容性
    ipcMain.handle('plugin:assess', async (_event, pluginId) => {
      try {
        if (!loadDeviceProfile) {
          return { success: false, error: '设备评估模块未初始化' };
        }
        const profile = loadDeviceProfile();
        if (!profile) {
          return { success: false, error: '设备评估报告不存在，请先执行评估' };
        }
        return {
          success: true,
          deviceClass: profile.assessment?.deviceClass,
          score: profile.assessment?.score,
          hardware: profile.hardware,
          software: profile.software,
          compatibleTiers: profile.assessment?.compatiblePluginTiers || [],
          recommendedPlugins: profile.assessment?.recommendedPlugins || [],
          incompatiblePlugins: profile.assessment?.incompatiblePlugins || [],
        };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });
  }

  /**
   * 注册插件管理相关 handlers
   */
  function registerPluginManagerHandlers() {
    // 注册插件安装器 IPC
    if (registerPluginInstallerIPC && pluginInstaller) {
      registerPluginInstallerIPC(pluginInstaller);
    }

    // 注册插件下载器 IPC
    if (registerPluginDownloaderIPC && pluginDownloader) {
      registerPluginDownloaderIPC(pluginDownloader);
    }
  }

  /**
   * 注册推荐引擎相关 handlers
   */
  function registerRecommenderHandlers() {
    // 获取个性化推荐
    ipcMain.handle('plugin:recommendations', async (_event, options = {}) => {
      try {
        if (!pluginRecommender) {
          return { success: false, error: '推荐引擎未初始化' };
        }
        const recommendations = await pluginRecommender.getRecommendations(options);
        return { success: true, data: recommendations };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 记录插件使用事件
    ipcMain.handle('plugin:record-usage', async (_event, pluginId, eventType, duration = 0, features = {}) => {
      try {
        if (!pluginRecommender) {
          return { success: false, error: '推荐引擎未初始化' };
        }
        pluginRecommender.recordPluginUsage(pluginId, eventType, duration, features);
        return { success: true };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 设置插件评分
    ipcMain.handle('plugin:set-rating', async (_event, pluginId, rating, feedback = '') => {
      try {
        if (!pluginRecommender) {
          return { success: false, error: '推荐引擎未初始化' };
        }
        pluginRecommender.setUserRating(pluginId, rating, feedback);
        return { success: true };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 获取热门插件
    ipcMain.handle('plugin:popular', async (_event, limit = 10) => {
      try {
        if (!pluginRecommender) {
          return { success: false, error: '推荐引擎未初始化' };
        }
        const popular = await pluginRecommender.getPopularPlugins(limit);
        return { success: true, data: popular };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 获取插件详情
    ipcMain.handle('plugin:details', async (_event, pluginId) => {
      try {
        if (!pluginRecommender) {
          return { success: false, error: '推荐引擎未初始化' };
        }
        const details = await pluginRecommender.getPluginDetails(pluginId);
        return { success: true, data: details };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 获取插件使用统计
    ipcMain.handle('plugin:usage-stats', async (_event, pluginId) => {
      try {
        if (!pluginRecommender || !pluginStoreEnhancer) {
          return { success: false, error: '推荐引擎未初始化' };
        }
        const usageStatsMap = pluginRecommender.usageStatsMap;
        const stats = pluginStoreEnhancer.getPluginUsageStats(pluginId, usageStatsMap);
        return { success: true, data: stats };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });
  }

  /**
   * 注册安装配置相关 handlers
   */
  function registerInstallConfigHandlers() {
    // 获取首次运行引导步骤
    ipcMain.handle('plugin:first-run-guide', async () => {
      try {
        if (!installConfigManager) {
          return { success: false, error: '安装配置管理器未初始化' };
        }
        const guide = installConfigManager.getFirstRunGuide();
        return { success: true, data: guide };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 检查是否已完成首次运行
    ipcMain.handle('plugin:first-run-check', async () => {
      try {
        if (!installConfigManager) {
          return { success: false, error: '安装配置管理器未初始化' };
        }
        const isFirstRunCompleted = installConfigManager.isFirstRunCompleted();
        return { success: true, data: isFirstRunCompleted };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 标记首次运行完成
    ipcMain.handle('plugin:first-run-complete', async () => {
      try {
        if (!installConfigManager) {
          return { success: false, error: '安装配置管理器未初始化' };
        }
        await installConfigManager.markFirstRunCompleted();
        return { success: true };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 获取核心模块列表
    ipcMain.handle('plugin:core-modules', async () => {
      try {
        if (!installConfigManager) {
          return { success: false, error: '安装配置管理器未初始化' };
        }
        const modules = installConfigManager.getCoreModules();
        return { success: true, data: modules };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 获取可选模块列表
    ipcMain.handle('plugin:optional-modules', async (_event, deviceClass = null) => {
      try {
        if (!installConfigManager) {
          return { success: false, error: '安装配置管理器未初始化' };
        }
        const modules = installConfigManager.getOptionalModules(deviceClass);
        return { success: true, data: modules };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 获取推荐模块
    ipcMain.handle('plugin:recommended-modules', async (_event, deviceClass) => {
      try {
        if (!installConfigManager) {
          return { success: false, error: '安装配置管理器未初始化' };
        }
        const modules = installConfigManager.getRecommendedModules(deviceClass);
        return { success: true, data: modules };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 获取安装统计
    ipcMain.handle('plugin:install-stats', async () => {
      try {
        if (!installConfigManager) {
          return { success: false, error: '安装配置管理器未初始化' };
        }
        const stats = installConfigManager.getInstallStats();
        return { success: true, data: stats };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 添加已安装模块
    ipcMain.handle('plugin:installed-module', async (_event, moduleId) => {
      try {
        if (!installConfigManager) {
          return { success: false, error: '安装配置管理器未初始化' };
        }
        await installConfigManager.addInstalledModule(moduleId);
        return { success: true };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 跳过模块安装
    ipcMain.handle('plugin:skip-module', async (_event, moduleId) => {
      try {
        if (!installConfigManager) {
          return { success: false, error: '安装配置管理器未初始化' };
        }
        await installConfigManager.skipModule(moduleId);
        return { success: true };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });
  }

  /**
   * 注册插件商店增强相关 handlers
   */
  function registerStoreEnhancerHandlers() {
    // 添加插件评论
    ipcMain.handle('plugin:add-review', async (_event, reviewData) => {
      try {
        if (!pluginStoreEnhancer) {
          return { success: false, error: '插件商店增强组件未初始化' };
        }
        const review = await pluginStoreEnhancer.addReview(reviewData);
        return { success: true, data: review };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 获取插件评论
    ipcMain.handle('plugin:get-reviews', async (_event, pluginId, options = {}) => {
      try {
        if (!pluginStoreEnhancer) {
          return { success: false, error: '插件商店增强组件未初始化' };
        }
        const reviews = pluginStoreEnhancer.getReviews(pluginId, options);
        return { success: true, data: reviews };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 获取插件平均评分
    ipcMain.handle('plugin:average-rating', async (_event, pluginId) => {
      try {
        if (!pluginStoreEnhancer) {
          return { success: false, error: '插件商店增强组件未初始化' };
        }
        const rating = pluginStoreEnhancer.getAverageRating(pluginId);
        return { success: true, data: rating };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 标记评论为有帮助
    ipcMain.handle('plugin:mark-helpful', async (_event, reviewId, pluginId) => {
      try {
        if (!pluginStoreEnhancer) {
          return { success: false, error: '插件商店增强组件未初始化' };
        }
        const result = await pluginStoreEnhancer.markReviewHelpful(reviewId, pluginId);
        return { success: true, data: result };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 检查插件更新
    ipcMain.handle('plugin:check-updates', async (_event, installedPlugins) => {
      try {
        if (!pluginStoreEnhancer) {
          return { success: false, error: '插件商店增强组件未初始化' };
        }
        const pluginCatalog = pluginRegistry ? pluginRegistry.getCatalog() : [];
        const updates = await pluginStoreEnhancer.checkForUpdates(pluginCatalog, installedPlugins);
        return { success: true, data: updates };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 获取待处理更新通知
    ipcMain.handle('plugin:pending-notifications', async () => {
      try {
        if (!pluginStoreEnhancer) {
          return { success: false, error: '插件商店增强组件未初始化' };
        }
        const notifications = pluginStoreEnhancer.getPendingNotifications();
        return { success: true, data: notifications };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 关闭更新通知
    ipcMain.handle('plugin:dismiss-notification', async (_event, notificationId) => {
      try {
        if (!pluginStoreEnhancer) {
          return { success: false, error: '插件商店增强组件未初始化' };
        }
        const result = await pluginStoreEnhancer.dismissNotification(notificationId);
        return { success: true, data: result };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 标记通知已安装
    ipcMain.handle('plugin:mark-installed', async (_event, notificationId) => {
      try {
        if (!pluginStoreEnhancer) {
          return { success: false, error: '插件商店增强组件未初始化' };
        }
        const result = await pluginStoreEnhancer.markNotificationInstalled(notificationId);
        return { success: true, data: result };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 获取商店统计
    ipcMain.handle('plugin:store-stats', async () => {
      try {
        if (!pluginStoreEnhancer) {
          return { success: false, error: '插件商店增强组件未初始化' };
        }
        const stats = pluginStoreEnhancer.getStoreStats();
        return { success: true, data: stats };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });
  }

  return {
    register,
  };
}

module.exports = { createPluginHandlers };
