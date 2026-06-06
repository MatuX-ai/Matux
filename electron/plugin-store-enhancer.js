/**
 * 插件商店增强组件
 * 
 * 功能:
 * 1. 评分和评论系统
 * 2. 使用统计展示
 * 3. 更新通知
 * 4. 用户反馈收集
 */

const path = require('path');
const fs = require('fs');
const { app } = require('electron');

// ==================== 常量定义 ====================

const REVIEWS_FILE = path.join(
  app.getPath('userData'),
  'plugin-reviews.json'
);

const UPDATE_NOTIFICATIONS_FILE = path.join(
  app.getPath('userData'),
  'plugin-update-notifications.json'
);

// ==================== 类型定义 ====================

/**
 * 插件评论
 */
class PluginReview {
  constructor({
    id = '',
    pluginId = '',
    userId = '',
    userName = '',
    rating = 0,
    title = '',
    content = '',
    pros = [],
    cons = [],
    createdAt = new Date().toISOString(),
    updatedAt = null,
    helpfulCount = 0,
    verified = false,
  } = {}) {
    this.id = id;
    this.pluginId = pluginId;
    this.userId = userId;
    this.userName = userName;
    this.rating = rating;
    this.title = title;
    this.content = content;
    this.pros = pros;
    this.cons = cons;
    this.createdAt = createdAt;
    this.updatedAt = updatedAt;
    this.helpfulCount = helpfulCount;
    this.verified = verified;
  }
}

/**
 * 更新通知
 */
class UpdateNotification {
  constructor({
    id = '',
    pluginId = '',
    pluginName = '',
    currentVersion = '',
    newVersion = '',
    releaseNotes = '',
    severity = 'info', // info, warning, critical
    notifiedAt = null,
    dismissed = false,
    dismissedAt = null,
    installed = false,
    installedAt = null,
  } = {}) {
    this.id = id;
    this.pluginId = pluginId;
    this.pluginName = pluginName;
    this.currentVersion = currentVersion;
    this.newVersion = newVersion;
    this.releaseNotes = releaseNotes;
    this.severity = severity;
    this.notifiedAt = notifiedAt;
    this.dismissed = dismissed;
    this.dismissedAt = dismissedAt;
    this.installed = installed;
    this.installedAt = installedAt;
  }
}

// ==================== 插件商店增强类 ====================

class PluginStoreEnhancer {
  constructor() {
    /** @type {Map<string, PluginReview[]>} 插件评论 */
    this.reviewsMap = new Map();
    
    /** @type {UpdateNotification[]} 更新通知 */
    this.updateNotifications = [];
    
    // 初始化
    this._initialize();
  }

  /**
   * 初始化
   */
  async _initialize() {
    try {
      await this._loadReviews();
      await this._loadUpdateNotifications();
      console.log('[INFO] ✓ 插件商店增强组件初始化完成');
    } catch (err) {
      console.error('[ERROR] 插件商店增强组件初始化失败:', err.message);
    }
  }

  /**
   * 加载评论数据
   */
  async _loadReviews() {
    try {
      if (fs.existsSync(REVIEWS_FILE)) {
        const data = fs.readFileSync(REVIEWS_FILE, 'utf-8');
        const reviewsArray = JSON.parse(data);
        
        this.reviewsMap.clear();
        for (const review of reviewsArray) {
          if (!this.reviewsMap.has(review.pluginId)) {
            this.reviewsMap.set(review.pluginId, []);
          }
          this.reviewsMap.get(review.pluginId).push(review);
        }
        
        console.log(`[INFO] 加载了 ${reviewsArray.length} 条评论`);
      }
    } catch (err) {
      console.warn('[WARN] 加载评论数据失败:', err.message);
    }
  }

  /**
   * 保存评论数据
   */
  async _saveReviews() {
    try {
      const reviewsArray = [];
      for (const reviews of this.reviewsMap.values()) {
        reviewsArray.push(...reviews);
      }
      
      fs.writeFileSync(REVIEWS_FILE, JSON.stringify(reviewsArray, null, 2), 'utf-8');
    } catch (err) {
      console.error('[ERROR] 保存评论数据失败:', err.message);
    }
  }

  /**
   * 加载更新通知
   */
  async _loadUpdateNotifications() {
    try {
      if (fs.existsSync(UPDATE_NOTIFICATIONS_FILE)) {
        const data = fs.readFileSync(UPDATE_NOTIFICATIONS_FILE, 'utf-8');
        this.updateNotifications = JSON.parse(data);
        
        console.log(`[INFO] 加载了 ${this.updateNotifications.length} 条更新通知`);
      }
    } catch (err) {
      console.warn('[WARN] 加载更新通知失败:', err.message);
    }
  }

  /**
   * 保存更新通知
   */
  async _saveUpdateNotifications() {
    try {
      fs.writeFileSync(
        UPDATE_NOTIFICATIONS_FILE,
        JSON.stringify(this.updateNotifications, null, 2),
        'utf-8'
      );
    } catch (err) {
      console.error('[ERROR] 保存更新通知失败:', err.message);
    }
  }

  // ==================== 评分和评论系统 ====================

  /**
   * 添加评论
   */
  async addReview(reviewData) {
    const review = new PluginReview({
      id: `review_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      ...reviewData,
    });
    
    if (!this.reviewsMap.has(review.pluginId)) {
      this.reviewsMap.set(review.pluginId, []);
    }
    
    this.reviewsMap.get(review.pluginId).push(review);
    
    await this._saveReviews();
    
    console.log(`[INFO] ✓ 添加评论: ${review.pluginId}`);
    return review;
  }

  /**
   * 获取插件评论
   */
  getReviews(pluginId, options = {}) {
    const reviews = this.reviewsMap.get(pluginId) || [];
    
    const {
      sortBy = 'createdAt', // createdAt, rating, helpfulCount
      sortOrder = 'desc',
      limit = 10,
      offset = 0,
      minRating = 0,
    } = options;
    
    // 过滤
    let filtered = reviews.filter(r => r.rating >= minRating);
    
    // 排序
    filtered.sort((a, b) => {
      let comparison = 0;
      
      if (sortBy === 'createdAt') {
        comparison = new Date(a.createdAt) - new Date(b.createdAt);
      } else if (sortBy === 'rating') {
        comparison = a.rating - b.rating;
      } else if (sortBy === 'helpfulCount') {
        comparison = a.helpfulCount - b.helpfulCount;
      }
      
      return sortOrder === 'desc' ? -comparison : comparison;
    });
    
    // 分页
    return filtered.slice(offset, offset + limit);
  }

  /**
   * 获取插件平均评分
   */
  getAverageRating(pluginId) {
    const reviews = this.reviewsMap.get(pluginId) || [];
    
    if (reviews.length === 0) {
      return {
        average: 0,
        count: 0,
        distribution: { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 },
      };
    }
    
    const sum = reviews.reduce((total, r) => total + r.rating, 0);
    const average = sum / reviews.length;
    
    // 评分分布
    const distribution = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
    for (const review of reviews) {
      distribution[review.rating]++;
    }
    
    return {
      average: Math.round(average * 10) / 10,
      count: reviews.length,
      distribution,
    };
  }

  /**
   * 标记评论为有帮助
   */
  async markReviewHelpful(reviewId, pluginId) {
    const reviews = this.reviewsMap.get(pluginId) || [];
    const review = reviews.find(r => r.id === reviewId);
    
    if (review) {
      review.helpfulCount += 1;
      await this._saveReviews();
      return true;
    }
    
    return false;
  }

  /**
   * 删除评论
   */
  async deleteReview(reviewId, pluginId, userId) {
    const reviews = this.reviewsMap.get(pluginId) || [];
    const index = reviews.findIndex(r => r.id === reviewId && r.userId === userId);
    
    if (index !== -1) {
      reviews.splice(index, 1);
      await this._saveReviews();
      return true;
    }
    
    return false;
  }

  // ==================== 使用统计 ====================

  /**
   * 获取插件使用统计
   */
  getPluginUsageStats(pluginId, usageStatsMap) {
    const stats = usageStatsMap.get(pluginId);
    
    if (!stats) {
      return {
        totalUsageTime: 0,
        usageCount: 0,
        lastUsedAt: null,
        averageSessionTime: 0,
        userRating: 0,
        trend: 'stable',
      };
    }
    
    // 计算使用趋势
    const trend = this._calculateUsageTrend(stats);
    
    return {
      totalUsageTime: stats.totalUsageTime,
      usageCount: stats.usageCount,
      lastUsedAt: stats.lastUsedAt,
      averageSessionTime: stats.averageSessionTime,
      userRating: stats.userRating,
      trend,
    };
  }

  /**
   * 计算使用趋势
   */
  _calculateUsageTrend(stats) {
    // 简化实现：基于最后使用时间
    if (!stats.lastUsedAt) return 'inactive';
    
    const lastUsed = new Date(stats.lastUsedAt);
    const now = new Date();
    const daysSinceLastUse = (now - lastUsed) / (1000 * 60 * 60 * 24);
    
    if (daysSinceLastUse < 7) return 'active';
    if (daysSinceLastUse < 30) return 'stable';
    if (daysSinceLastUse < 90) return 'declining';
    return 'inactive';
  }

  // ==================== 更新通知系统 ====================

  /**
   * 检查插件更新
   */
  async checkForUpdates(pluginCatalog, installedPlugins) {
    const newNotifications = [];
    
    for (const plugin of pluginCatalog) {
      const installed = installedPlugins.find(p => p.id === plugin.id);
      
      if (installed && installed.version !== plugin.version) {
        // 有可用更新
        const severity = this._determineUpdateSeverity(
          installed.version,
          plugin.version
        );
        
        const notification = new UpdateNotification({
          id: `update_${plugin.id}_${plugin.version}`,
          pluginId: plugin.id,
          pluginName: plugin.name,
          currentVersion: installed.version,
          newVersion: plugin.version,
          releaseNotes: plugin.releaseNotes || '错误修复和性能改进',
          severity,
          notifiedAt: new Date().toISOString(),
        });
        
        // 检查是否已经通知过
        const existing = this.updateNotifications.find(
          n => n.pluginId === plugin.id && n.newVersion === plugin.version
        );
        
        if (!existing) {
          newNotifications.push(notification);
        }
      }
    }
    
    // 添加新通知
    if (newNotifications.length > 0) {
      this.updateNotifications.push(...newNotifications);
      await this._saveUpdateNotifications();
      
      console.log(`[INFO] 发现 ${newNotifications.length} 个插件更新`);
    }
    
    return newNotifications;
  }

  /**
   * 确定更新严重程度
   */
  _determineUpdateSeverity(currentVersion, newVersion) {
    const currentParts = currentVersion.split('.').map(Number);
    const newParts = newVersion.split('.').map(Number);
    
    // 主版本更新
    if (newParts[0] > currentParts[0]) {
      return 'critical';
    }
    
    // 次版本更新
    if (newParts[1] > currentParts[1]) {
      return 'warning';
    }
    
    // 补丁更新
    return 'info';
  }

  /**
   * 获取待处理更新通知
   */
  getPendingNotifications() {
    return this.updateNotifications.filter(
      n => !n.dismissed && !n.installed
    );
  }

  /**
   * 获取所有更新通知
   */
  getAllNotifications(options = {}) {
    const {
      pluginId = null,
      severity = null,
      limit = 20,
      offset = 0,
    } = options;
    
    let notifications = this.updateNotifications;
    
    // 过滤
    if (pluginId) {
      notifications = notifications.filter(n => n.pluginId === pluginId);
    }
    
    if (severity) {
      notifications = notifications.filter(n => n.severity === severity);
    }
    
    // 排序（最新的在前）
    notifications.sort((a, b) => 
      new Date(b.notifiedAt) - new Date(a.notifiedAt)
    );
    
    // 分页
    return notifications.slice(offset, offset + limit);
  }

  /**
   * 关闭通知
   */
  async dismissNotification(notificationId) {
    const notification = this.updateNotifications.find(
      n => n.id === notificationId
    );
    
    if (notification) {
      notification.dismissed = true;
      notification.dismissedAt = new Date().toISOString();
      
      await this._saveUpdateNotifications();
      return true;
    }
    
    return false;
  }

  /**
   * 标记通知已安装
   */
  async markNotificationInstalled(notificationId) {
    const notification = this.updateNotifications.find(
      n => n.id === notificationId
    );
    
    if (notification) {
      notification.installed = true;
      notification.installedAt = new Date().toISOString();
      
      await this._saveUpdateNotifications();
      return true;
    }
    
    return false;
  }

  /**
   * 关闭所有通知
   */
  async dismissAllNotifications() {
    const now = new Date().toISOString();
    
    for (const notification of this.updateNotifications) {
      if (!notification.dismissed && !notification.installed) {
        notification.dismissed = true;
        notification.dismissedAt = now;
      }
    }
    
    await this._saveUpdateNotifications();
  }

  // ==================== 统计和分析 ====================

  /**
   * 获取商店统计
   */
  getStoreStats() {
    const totalReviews = Array.from(this.reviewsMap.values())
      .reduce((sum, reviews) => sum + reviews.length, 0);
    
    const pendingUpdates = this.updateNotifications.filter(
      n => !n.dismissed && !n.installed
    ).length;
    
    return {
      totalReviews,
      totalPlugins: this.reviewsMap.size,
      pendingUpdates,
      averageRating: this._calculateGlobalAverageRating(),
    };
  }

  /**
   * 计算全局平均评分
   */
  _calculateGlobalAverageRating() {
    let totalRating = 0;
    let totalCount = 0;
    
    for (const reviews of this.reviewsMap.values()) {
      for (const review of reviews) {
        totalRating += review.rating;
        totalCount++;
      }
    }
    
    return totalCount > 0 ? Math.round((totalRating / totalCount) * 10) / 10 : 0;
  }

  /**
   * 导出评论数据
   */
  exportReviews() {
    const allReviews = [];
    for (const reviews of this.reviewsMap.values()) {
      allReviews.push(...reviews);
    }
    return allReviews;
  }

  /**
   * 导入评论数据
   */
  async importReviews(reviews) {
    this.reviewsMap.clear();
    
    for (const review of reviews) {
      if (!this.reviewsMap.has(review.pluginId)) {
        this.reviewsMap.set(review.pluginId, []);
      }
      this.reviewsMap.get(review.pluginId).push(review);
    }
    
    await this._saveReviews();
  }

  /**
   * 清除旧通知（30天前）
   */
  async clearOldNotifications() {
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    
    const initialCount = this.updateNotifications.length;
    
    this.updateNotifications = this.updateNotifications.filter(n => {
      const notifiedAt = new Date(n.notifiedAt);
      return notifiedAt >= thirtyDaysAgo;
    });
    
    if (this.updateNotifications.length !== initialCount) {
      await this._saveUpdateNotifications();
      console.log(`[INFO] 清除了 ${initialCount - this.updateNotifications.length} 条旧通知`);
    }
  }
}

// ==================== 导出 ====================

module.exports = {
  PluginStoreEnhancer,
  PluginReview,
  UpdateNotification,
};
