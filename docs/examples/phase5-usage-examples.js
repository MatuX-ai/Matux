/**
 * Phase 5 功能使用示例
 * 
 * 展示如何在前端使用 Phase 5 的新功能
 */

// ==================== 1. 推荐引擎使用示例 ====================

/**
 * 获取个性化推荐
 */
async function getPersonalizedRecommendations() {
  try {
    const result = await window.pluginAPI.getRecommendations({
      maxRecommendations: 10,
      includeBundles: true,
      excludeInstalled: true,
    });
    
    if (result.success) {
      console.log('推荐结果:', result.data);
      console.log('推荐插件:', result.data.recommendations);
      console.log('推荐捆绑包:', result.data.bundles);
      console.log('推荐理由:', result.data.reason);
      console.log('置信度:', result.data.confidence);
    }
  } catch (err) {
    console.error('获取推荐失败:', err);
  }
}

/**
 * 记录插件使用事件
 */
async function recordPluginUsageExample() {
  try {
    // 记录打开插件
    await window.pluginAPI.recordPluginUsage('ai-tutor', 'open');
    
    // 记录使用功能（带时长）
    await window.pluginAPI.recordPluginUsage(
      'ai-tutor',
      'use_feature',
      120, // 使用 120 秒
      {
        'chat': 5,      // 使用聊天功能 5 次
        'quiz': 3,      // 使用测验功能 3 次
        'progress': 2,  // 查看进度 2 次
      }
    );
    
    // 记录关闭插件
    await window.pluginAPI.recordPluginUsage('ai-tutor', 'close', 120);
  } catch (err) {
    console.error('记录使用事件失败:', err);
  }
}

/**
 * 设置插件评分
 */
async function ratePluginExample() {
  try {
    await window.pluginAPI.setPluginRating(
      'ai-tutor',
      5, // 5 星评分
      '非常好用的 AI 教学助手！' // 反馈
    );
    console.log('评分成功');
  } catch (err) {
    console.error('评分失败:', err);
  }
}

/**
 * 获取热门插件
 */
async function getPopularPluginsExample() {
  try {
    const result = await window.pluginAPI.getPopularPlugins(10);
    
    if (result.success) {
      console.log('热门插件:', result.data);
      // [
      //   { pluginId: 'ai-tutor', installCount: 15000, rating: 4.8 },
      //   { pluginId: 'exam-pro', installCount: 12000, rating: 4.6 },
      //   ...
      // ]
    }
  } catch (err) {
    console.error('获取热门插件失败:', err);
  }
}

// ==================== 2. 安装包精简使用示例 ====================

/**
 * 检查首次运行
 */
async function checkFirstRunExample() {
  try {
    const result = await window.pluginAPI.isFirstRunCompleted();
    
    if (result.success && !result.data) {
      console.log('首次运行，显示引导界面');
      showFirstRunGuide();
    } else {
      console.log('非首次运行，直接进入主界面');
    }
  } catch (err) {
    console.error('检查首次运行失败:', err);
  }
}

/**
 * 显示首次运行引导
 */
async function showFirstRunGuide() {
  try {
    const result = await window.pluginAPI.getFirstRunGuide();
    
    if (result.success) {
      console.log('引导步骤:', result.data.steps);
      // 按步骤显示引导界面
      for (const step of result.data.steps) {
        console.log(`步骤 ${step.order}: ${step.title}`);
        console.log(`  ${step.description}`);
      }
    }
  } catch (err) {
    console.error('获取引导步骤失败:', err);
  }
}

/**
 * 获取推荐模块
 */
async function getRecommendedModulesExample() {
  try {
    // 假设设备等级为 'advanced'
    const result = await window.pluginAPI.getRecommendedModules('advanced');
    
    if (result.success) {
      console.log('推荐模块:', result.data);
      // 显示推荐模块列表供用户选择
    }
  } catch (err) {
    console.error('获取推荐模块失败:', err);
  }
}

/**
 * 安装模块
 */
async function installModuleExample(moduleId) {
  try {
    // 标记模块已安装
    await window.pluginAPI.addInstalledModule(moduleId);
    console.log(`模块 ${moduleId} 已标记为已安装`);
  } catch (err) {
    console.error('标记模块失败:', err);
  }
}

/**
 * 获取安装统计
 */
async function getInstallStatsExample() {
  try {
    const result = await window.pluginAPI.getInstallStats();
    
    if (result.success) {
      const stats = result.data;
      console.log('安装统计:', stats);
      console.log(`核心模块: ${stats.coreModuleCount} 个`);
      console.log(`可选模块: ${stats.optionalModuleCount} 个`);
      console.log(`已安装: ${stats.installedModuleCount} 个`);
      console.log(`核心包大小: ${stats.totalCoreSizeMB}MB`);
      console.log(`可选包大小: ${stats.totalOptionalSizeMB}MB`);
      console.log(`已节省: ${stats.savedSizeMB}MB`);
    }
  } catch (err) {
    console.error('获取安装统计失败:', err);
  }
}

// ==================== 3. 插件商店增强使用示例 ====================

/**
 * 添加插件评论
 */
async function addReviewExample() {
  try {
    const result = await window.pluginAPI.addPluginReview({
      pluginId: 'ai-tutor',
      userId: 'user_123',
      userName: '张三',
      rating: 5,
      title: '非常好用的 AI 教学助手',
      content: '功能强大，界面友好，推荐使用！',
      pros: ['功能丰富', '易于使用', '性能优秀'],
      cons: ['学习曲线稍陡'],
    });
    
    if (result.success) {
      console.log('评论已添加:', result.data);
    }
  } catch (err) {
    console.error('添加评论失败:', err);
  }
}

/**
 * 获取插件评论
 */
async function getReviewsExample() {
  try {
    const result = await window.pluginAPI.getPluginReviews('ai-tutor', {
      sortBy: 'createdAt',
      sortOrder: 'desc',
      limit: 10,
      offset: 0,
      minRating: 0,
    });
    
    if (result.success) {
      console.log('评论列表:', result.data);
    }
  } catch (err) {
    console.error('获取评论失败:', err);
  }
}

/**
 * 获取插件平均评分
 */
async function getAverageRatingExample() {
  try {
    const result = await window.pluginAPI.getPluginAverageRating('ai-tutor');
    
    if (result.success) {
      const rating = result.data;
      console.log('平均评分:', rating.average);
      console.log('评论数:', rating.count);
      console.log('评分分布:', rating.distribution);
      // {
      //   average: 4.5,
      //   count: 128,
      //   distribution: { 1: 5, 2: 8, 3: 15, 4: 40, 5: 60 }
      // }
    }
  } catch (err) {
    console.error('获取评分失败:', err);
  }
}

/**
 * 检查插件更新
 */
async function checkForUpdatesExample() {
  try {
    const installedPlugins = [
      { id: 'ai-tutor', version: '1.0.0' },
      { id: 'exam-pro', version: '2.0.0' },
    ];
    
    const result = await window.pluginAPI.checkForUpdates(installedPlugins);
    
    if (result.success && result.data.length > 0) {
      console.log('发现更新:', result.data);
      // 显示更新通知
      showUpdateNotifications(result.data);
    }
  } catch (err) {
    console.error('检查更新失败:', err);
  }
}

/**
 * 获取待处理更新通知
 */
async function getPendingNotificationsExample() {
  try {
    const result = await window.pluginAPI.getPendingNotifications();
    
    if (result.success) {
      console.log('待处理更新:', result.data);
      // [
      //   {
      //     pluginId: 'ai-tutor',
      //     pluginName: 'AI 教学助手',
      //     currentVersion: '1.0.0',
      //     newVersion: '1.1.0',
      //     severity: 'warning',
      //     releaseNotes: '新增功能和错误修复'
      //   }
      // ]
    }
  } catch (err) {
    console.error('获取更新通知失败:', err);
  }
}

/**
 * 关闭更新通知
 */
async function dismissNotificationExample(notificationId) {
  try {
    await window.pluginAPI.dismissNotification(notificationId);
    console.log('通知已关闭');
  } catch (err) {
    console.error('关闭通知失败:', err);
  }
}

/**
 * 获取插件使用统计
 */
async function getPluginUsageStatsExample() {
  try {
    const result = await window.pluginAPI.getPluginUsageStats('ai-tutor');
    
    if (result.success) {
      const stats = result.data;
      console.log('使用统计:', stats);
      console.log(`总使用时间: ${stats.totalUsageTime} 秒`);
      console.log(`使用次数: ${stats.usageCount}`);
      console.log(`平均会话: ${stats.averageSessionTime} 秒`);
      console.log(`使用趋势: ${stats.trend}`);
    }
  } catch (err) {
    console.error('获取使用统计失败:', err);
  }
}

/**
 * 获取商店统计
 */
async function getStoreStatsExample() {
  try {
    const result = await window.pluginAPI.getStoreStats();
    
    if (result.success) {
      console.log('商店统计:', result.data);
      // {
      //   totalReviews: 1500,
      //   totalPlugins: 50,
      //   pendingUpdates: 3,
      //   averageRating: 4.3
      // }
    }
  } catch (err) {
    console.error('获取商店统计失败:', err);
  }
}

// ==================== 完整使用流程示例 ====================

/**
 * 首次运行完整流程
 */
async function firstRunWorkflow() {
  try {
    console.log('=== 首次运行流程开始 ===');
    
    // 1. 检查是否首次运行
    const firstRunCheck = await window.pluginAPI.isFirstRunCompleted();
    if (firstRunCheck.success && firstRunCheck.data) {
      console.log('已完成首次运行');
      return;
    }
    
    // 2. 获取引导步骤
    const guideResult = await window.pluginAPI.getFirstRunGuide();
    if (!guideResult.success) {
      console.error('获取引导步骤失败');
      return;
    }
    
    console.log('引导步骤:', guideResult.data.steps);
    
    // 3. 获取推荐模块（假设设备等级为 advanced）
    const modulesResult = await window.pluginAPI.getRecommendedModules('advanced');
    if (modulesResult.success) {
      console.log('推荐模块:', modulesResult.data);
      
      // 用户选择要安装的模块
      const selectedModules = modulesResult.data.slice(0, 3); // 示例：选择前 3 个
      
      // 4. 安装选中的模块
      for (const module of selectedModules) {
        console.log(`安装模块: ${module.name}`);
        await window.pluginAPI.addInstalledModule(module.id);
      }
    }
    
    // 5. 标记首次运行完成
    await window.pluginAPI.markFirstRunCompleted();
    console.log('首次运行完成！');
    
    console.log('=== 首次运行流程结束 ===');
  } catch (err) {
    console.error('首次运行流程失败:', err);
  }
}

/**
 * 日常使用流程示例
 */
async function dailyUsageWorkflow() {
  try {
    console.log('=== 日常使用流程开始 ===');
    
    // 1. 获取个性化推荐
    const recommendations = await window.pluginAPI.getRecommendations({
      maxRecommendations: 5,
      includeBundles: true,
    });
    
    if (recommendations.success) {
      console.log('个性化推荐:', recommendations.data.recommendations);
    }
    
    // 2. 检查更新
    const installedPlugins = [
      { id: 'ai-tutor', version: '1.0.0' },
    ];
    
    const updates = await window.pluginAPI.checkForUpdates(installedPlugins);
    if (updates.success && updates.data.length > 0) {
      console.log('发现更新:', updates.data);
    }
    
    // 3. 记录插件使用
    await window.pluginAPI.recordPluginUsage('ai-tutor', 'open');
    
    // 模拟使用 5 分钟
    setTimeout(async () => {
      await window.pluginAPI.recordPluginUsage('ai-tutor', 'close', 300);
      console.log('使用记录已保存');
    }, 300000);
    
    console.log('=== 日常使用流程结束 ===');
  } catch (err) {
    console.error('日常使用流程失败:', err);
  }
}

// ==================== 辅助函数示例 ====================

/**
 * 显示更新通知
 */
function showUpdateNotifications(updates) {
  for (const update of updates) {
    console.log(`📦 ${update.pluginName} 有可用更新`);
    console.log(`   ${update.currentVersion} → ${update.newVersion}`);
    console.log(`   严重程度: ${update.severity}`);
    console.log(`   更新说明: ${update.releaseNotes}`);
  }
}

// 导出示例函数（如果在模块环境中）
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    getPersonalizedRecommendations,
    recordPluginUsageExample,
    ratePluginExample,
    getPopularPluginsExample,
    checkFirstRunExample,
    showFirstRunGuide,
    getRecommendedModulesExample,
    installModuleExample,
    getInstallStatsExample,
    addReviewExample,
    getReviewsExample,
    getAverageRatingExample,
    checkForUpdatesExample,
    getPendingNotificationsExample,
    dismissNotificationExample,
    getPluginUsageStatsExample,
    getStoreStatsExample,
    firstRunWorkflow,
    dailyUsageWorkflow,
  };
}
