/**
 * 插件推荐引擎
 * 
 * 功能:
 * 1. 基于设备评级推荐插件
 * 2. 基于使用习惯推荐
 * 3. 插件捆绑推荐
 * 4. 个性化推荐算法
 */

const path = require('path');
const fs = require('fs');
const { app } = require('electron');

// ==================== 常量定义 ====================

const RECOMMENDATION_DATA_FILE = path.join(
  app.getPath('userData'),
  'plugin-recommendations.json'
);

const USAGE_STATS_FILE = path.join(
  app.getPath('userData'),
  'plugin-usage-stats.json'
);

// ==================== 类型定义 ====================

/**
 * 插件使用统计
 */
class PluginUsageStats {
  constructor() {
    this.pluginId = '';
    this.totalUsageTime = 0; // 总使用时间（秒）
    this.usageCount = 0; // 使用次数
    this.lastUsedAt = null; // 最后使用时间
    this.averageSessionTime = 0; // 平均会话时间
    this.featureUsage = {}; // 功能使用统计
    this.userRating = 0; // 用户评分 (1-5)
    this.userFeedback = ''; // 用户反馈
  }
}

/**
 * 推荐结果
 */
class RecommendationResult {
  constructor() {
    this.recommendations = [];
    this.bundles = [];
    this.reason = '';
    this.confidence = 0; // 推荐置信度 (0-1)
    this.generatedAt = new Date().toISOString();
  }
}

/**
 * 插件捆绑包
 */
class PluginBundle {
  constructor({
    id = '',
    name = '',
    description = '',
    plugins = [],
    discount = 0,
    category = '',
    targetDeviceClass = '',
    priority = 0,
  } = {}) {
    this.id = id;
    this.name = name;
    this.description = description;
    this.plugins = plugins;
    this.discount = discount;
    this.category = category;
    this.targetDeviceClass = targetDeviceClass;
    this.priority = priority;
    this.createdAt = new Date().toISOString();
  }
}

// ==================== 推荐引擎类 ====================

class PluginRecommendationEngine {
  constructor() {
    /** @type {Map<string, PluginUsageStats>} 插件使用统计 */
    this.usageStatsMap = new Map();
    
    /** @type {PluginBundle[]} 预定义捆绑包 */
    this.bundles = [];
    
    /** @type {object|null} 设备评估报告 */
    this.deviceProfile = null;
    
    // 初始化
    this._initialize();
  }

  /**
   * 初始化推荐引擎
   */
  async _initialize() {
    try {
      // 加载使用统计
      await this._loadUsageStats();
      
      // 加载预定义捆绑包
      this._loadBundles();
      
      // 加载设备评估报告
      await this._loadDeviceProfile();
      
      console.log('[INFO] ✓ 插件推荐引擎初始化完成');
    } catch (err) {
      console.error('[ERROR] 插件推荐引擎初始化失败:', err.message);
    }
  }

  /**
   * 加载插件使用统计
   */
  async _loadUsageStats() {
    try {
      if (fs.existsSync(USAGE_STATS_FILE)) {
        const data = fs.readFileSync(USAGE_STATS_FILE, 'utf-8');
        const statsArray = JSON.parse(data);
        
        this.usageStatsMap.clear();
        for (const stat of statsArray) {
          this.usageStatsMap.set(stat.pluginId, stat);
        }
        
        console.log(`[INFO] 加载了 ${this.usageStatsMap.size} 个插件的使用统计`);
      }
    } catch (err) {
      console.warn('[WARN] 加载使用统计失败:', err.message);
    }
  }

  /**
   * 保存插件使用统计
   */
  async _saveUsageStats() {
    try {
      const statsArray = Array.from(this.usageStatsMap.values());
      fs.writeFileSync(USAGE_STATS_FILE, JSON.stringify(statsArray, null, 2), 'utf-8');
    } catch (err) {
      console.error('[ERROR] 保存使用统计失败:', err.message);
    }
  }

  /**
   * 加载预定义捆绑包
   */
  _loadBundles() {
    this.bundles = [
      new PluginBundle({
        id: 'starter-kit',
        name: '入门学习包',
        description: '适合初学者的核心插件组合',
        plugins: ['ai-tutor', 'exam-pro', 'offline-kit', 'code-editor'],
        discount: 0.15,
        category: 'education',
        targetDeviceClass: 'basic',
        priority: 10,
      }),
      new PluginBundle({
        id: 'ai-developer-kit',
        name: 'AI 开发工具包',
        description: 'AI 开发者的完整工具链',
        plugins: ['ai-coding-assistant', 'model-bench', 'federated-learning', 'creativity-engine'],
        discount: 0.20,
        category: 'development',
        targetDeviceClass: 'advanced',
        priority: 9,
      }),
      new PluginBundle({
        id: 'ar-vr-kit',
        name: 'AR/VR 实验包',
        description: '沉浸式学习体验工具',
        plugins: ['ar-vr-lab', 'vr-3d-editor', 'digital-twin', 'spatial-audio'],
        discount: 0.25,
        category: 'immersive',
        targetDeviceClass: 'professional',
        priority: 8,
      }),
      new PluginBundle({
        id: 'hardware-kit',
        name: '硬件开发包',
        description: '物联网和硬件开发工具',
        plugins: ['hardware-cert', 'tinyml-studio', 'iot-simulator', 'circuit-designer'],
        discount: 0.18,
        category: 'hardware',
        targetDeviceClass: 'standard',
        priority: 7,
      }),
      new PluginBundle({
        id: 'collaboration-kit',
        name: '协作学习包',
        description: '多人协作和知识共享工具',
        plugins: ['collab-editor', 'knowledge-graph', 'peer-review', 'discussion-forum'],
        discount: 0.12,
        category: 'collaboration',
        targetDeviceClass: 'standard',
        priority: 6,
      }),
    ];
  }

  /**
   * 加载设备评估报告
   */
  async _loadDeviceProfile() {
    try {
      const { loadDeviceProfile } = require('./device-profiler');
      this.deviceProfile = loadDeviceProfile();
    } catch (err) {
      console.warn('[WARN] 加载设备评估报告失败:', err.message);
    }
  }

  /**
   * 记录插件使用事件
   */
  recordPluginUsage(pluginId, eventType, duration = 0, features = {}) {
    if (!this.usageStatsMap.has(pluginId)) {
      this.usageStatsMap.set(pluginId, new PluginUsageStats());
    }
    
    const stats = this.usageStatsMap.get(pluginId);
    stats.pluginId = pluginId;
    stats.usageCount += 1;
    stats.totalUsageTime += duration;
    stats.lastUsedAt = new Date().toISOString();
    
    if (stats.usageCount > 0) {
      stats.averageSessionTime = stats.totalUsageTime / stats.usageCount;
    }
    
    // 更新功能使用统计
    for (const [feature, count] of Object.entries(features)) {
      stats.featureUsage[feature] = (stats.featureUsage[feature] || 0) + count;
    }
    
    // 异步保存
    this._saveUsageStats();
  }

  /**
   * 设置用户评分
   */
  setUserRating(pluginId, rating, feedback = '') {
    if (!this.usageStatsMap.has(pluginId)) {
      this.usageStatsMap.set(pluginId, new PluginUsageStats());
    }
    
    const stats = this.usageStatsMap.get(pluginId);
    stats.pluginId = pluginId;
    stats.userRating = Math.max(1, Math.min(5, rating));
    stats.userFeedback = feedback;
    
    this._saveUsageStats();
  }

  /**
   * 获取推荐结果
   */
  async getRecommendations(options = {}) {
    const result = new RecommendationResult();
    
    try {
      const {
        deviceClass = this.deviceProfile?.assessment?.deviceClass || 'basic',
        maxRecommendations = 10,
        includeBundles = true,
        excludeInstalled = true,
      } = options;
      
      // 1. 基于设备评级的推荐
      const deviceBasedRecs = this._getDeviceBasedRecommendations(deviceClass);
      
      // 2. 基于使用习惯的推荐
      const usageBasedRecs = this._getUsageBasedRecommendations();
      
      // 3. 合并和排序推荐
      const allRecommendations = this._mergeAndRankRecommendations(
        deviceBasedRecs,
        usageBasedRecs
      );
      
      // 4. 获取适用的捆绑包
      if (includeBundles) {
        result.bundles = this._getApplicableBundles(deviceClass);
      }
      
      // 5. 过滤已安装插件
      if (excludeInstalled) {
        const installedPlugins = this.deviceProfile?.installedPlugins || [];
        result.recommendations = allRecommendations.filter(
          rec => !installedPlugins.includes(rec.pluginId)
        );
      } else {
        result.recommendations = allRecommendations;
      }
      
      // 6. 限制数量
      result.recommendations = result.recommendations.slice(0, maxRecommendations);
      
      // 7. 设置元数据
      result.reason = this._generateRecommendationReason(deviceClass);
      result.confidence = this._calculateConfidence(deviceClass);
      
      console.log(`[INFO] 生成了 ${result.recommendations.length} 个推荐和 ${result.bundles.length} 个捆绑包`);
      
    } catch (err) {
      console.error('[ERROR] 生成推荐失败:', err.message);
    }
    
    return result;
  }

  /**
   * 基于设备评级的推荐
   */
  _getDeviceBasedRecommendations(deviceClass) {
    const recommendations = [];
    
    // 设备评级推荐映射
    const deviceRecommendations = {
      basic: [
        { pluginId: 'ai-tutor', score: 0.9, reason: '适合基础设备，轻量级AI教学' },
        { pluginId: 'exam-pro', score: 0.85, reason: '考试系统，资源占用低' },
        { pluginId: 'offline-kit', score: 0.8, reason: '离线学习包，无需网络' },
        { pluginId: 'code-editor', score: 0.75, reason: '基础代码编辑器' },
      ],
      standard: [
        { pluginId: 'ai-tutor', score: 0.9, reason: 'AI 教学助手' },
        { pluginId: 'collab-editor', score: 0.85, reason: '协作编辑，需要中等内存' },
        { pluginId: 'knowledge-graph', score: 0.8, reason: '知识图谱可视化' },
        { pluginId: 'exam-pro', score: 0.75, reason: '完整考试系统' },
      ],
      advanced: [
        { pluginId: 'creativity-engine', score: 0.95, reason: '创意引擎，需要独显支持' },
        { pluginId: 'ar-vr-lab', score: 0.9, reason: 'AR/VR 实验室，需要 GPU 支持' },
        { pluginId: 'model-bench', score: 0.85, reason: '模型评测平台' },
        { pluginId: 'federated-learning', score: 0.8, reason: '联邦学习框架' },
      ],
      professional: [
        { pluginId: 'digital-twin', score: 0.95, reason: '数字孪生，需要高性能硬件' },
        { pluginId: 'vr-3d-editor', score: 0.9, reason: '3D VR 编辑器' },
        { pluginId: 'code-sandbox', score: 0.85, reason: '云端代码沙箱' },
        { pluginId: 'federated-learning', score: 0.8, reason: '分布式机器学习' },
      ],
    };
    
    // 获取当前设备等级的推荐
    const recs = deviceRecommendations[deviceClass] || deviceRecommendations.basic;
    recommendations.push(...recs);
    
    // 根据具体硬件能力调整推荐
    if (this.deviceProfile?.hardware) {
      const { memory, gpu, peripherals } = this.deviceProfile.hardware;
      
      // 大内存设备推荐
      if (memory.totalMB >= 16384) {
        recommendations.push({
          pluginId: 'multi-task-manager',
          score: 0.7,
          reason: '多任务管理器，适合大内存设备',
        });
      }
      
      // GPU 能力强
      if (gpu.hasDedicatedGPU && gpu.vramMB >= 4096) {
        recommendations.push({
          pluginId: 'gpu-accelerated-ai',
          score: 0.8,
          reason: 'GPU 加速 AI，需要 4GB+ 显存',
        });
      }
      
      // 有摄像头
      if (peripherals.hasCamera) {
        recommendations.push({
          pluginId: 'computer-vision-lab',
          score: 0.65,
          reason: '计算机视觉实验室，需要摄像头',
        });
      }
    }
    
    return recommendations;
  }

  /**
   * 基于使用习惯的推荐
   */
  _getUsageBasedRecommendations() {
    const recommendations = [];
    
    // 分析使用模式
    const usagePatterns = this._analyzeUsagePatterns();
    
    // 基于使用模式推荐
    if (usagePatterns.frequentAI) {
      recommendations.push({
        pluginId: 'advanced-ml-tools',
        score: 0.8,
        reason: '您经常使用 AI 功能，推荐高级 ML 工具',
      });
    }
    
    if (usagePatterns.frequentCoding) {
      recommendations.push({
        pluginId: 'ai-coding-assistant',
        score: 0.85,
        reason: '您经常编写代码，推荐 AI 编程助手',
      });
    }
    
    if (usagePatterns.frequentHardware) {
      recommendations.push({
        pluginId: 'iot-simulator',
        score: 0.75,
        reason: '您经常使用硬件功能，推荐 IoT 模拟器',
      });
    }
    
    // 基于高评分插件推荐相似插件
    const highRatedPlugins = Array.from(this.usageStatsMap.values())
      .filter(stat => stat.userRating >= 4)
      .map(stat => stat.pluginId);
    
    if (highRatedPlugins.length > 0) {
      // 可以基于协同过滤推荐相似插件
      // 这里简化处理
    }
    
    return recommendations;
  }

  /**
   * 分析使用模式
   */
  _analyzeUsagePatterns() {
    const patterns = {
      frequentAI: false,
      frequentCoding: false,
      frequentHardware: false,
      powerUser: false,
    };
    
    const totalUsageTime = Array.from(this.usageStatsMap.values())
      .reduce((sum, stat) => sum + stat.totalUsageTime, 0);
    
    // AI 使用模式
    const aiPlugins = ['ai-tutor', 'creativity-engine', 'model-bench'];
    const aiUsageTime = Array.from(this.usageStatsMap.values())
      .filter(stat => aiPlugins.includes(stat.pluginId))
      .reduce((sum, stat) => sum + stat.totalUsageTime, 0);
    
    patterns.frequentAI = aiUsageTime > totalUsageTime * 0.3;
    
    // 编程使用模式
    const codingPlugins = ['code-editor', 'ai-coding-assistant', 'code-sandbox'];
    const codingUsageCount = Array.from(this.usageStatsMap.values())
      .filter(stat => codingPlugins.includes(stat.pluginId))
      .reduce((sum, stat) => sum + stat.usageCount, 0);
    
    patterns.frequentCoding = codingUsageCount > 10;
    
    // 硬件使用模式
    const hardwarePlugins = ['hardware-cert', 'tinyml-studio', 'iot-simulator'];
    const hardwareUsageCount = Array.from(this.usageStatsMap.values())
      .filter(stat => hardwarePlugins.includes(stat.pluginId))
      .reduce((sum, stat) => sum + stat.usageCount, 0);
    
    patterns.frequentHardware = hardwareUsageCount > 5;
    
    // 高级用户
    patterns.powerUser = totalUsageTime > 3600 && this.usageStatsMap.size > 5;
    
    return patterns;
  }

  /**
   * 合并和排序推荐
   */
  _mergeAndRankRecommendations(deviceBased, usageBased) {
    const merged = new Map();
    
    // 添加设备推荐
    for (const rec of deviceBased) {
      merged.set(rec.pluginId, {
        pluginId: rec.pluginId,
        score: rec.score,
        reason: rec.reason,
        sources: ['device'],
      });
    }
    
    // 添加使用习惯推荐，合并分数
    for (const rec of usageBased) {
      if (merged.has(rec.pluginId)) {
        const existing = merged.get(rec.pluginId);
        existing.score = Math.min(1, existing.score * 0.6 + rec.score * 0.4);
        existing.sources.push('usage');
        existing.reason += ` + ${rec.reason}`;
      } else {
        merged.set(rec.pluginId, {
          pluginId: rec.pluginId,
          score: rec.score,
          reason: rec.reason,
          sources: ['usage'],
        });
      }
    }
    
    // 转换为数组并排序
    return Array.from(merged.values())
      .sort((a, b) => b.score - a.score);
  }

  /**
   * 获取适用的捆绑包
   */
  _getApplicableBundles(deviceClass) {
    const deviceClassOrder = ['basic', 'standard', 'advanced', 'professional'];
    const deviceLevel = deviceClassOrder.indexOf(deviceClass);
    
    return this.bundles
      .filter(bundle => {
        const bundleLevel = deviceClassOrder.indexOf(bundle.targetDeviceClass);
        return bundleLevel <= deviceLevel; // 设备等级 >= 捆绑包要求等级
      })
      .sort((a, b) => b.priority - a.priority);
  }

  /**
   * 生成推荐理由
   */
  _generateRecommendationReason(deviceClass) {
    const reasons = {
      basic: '基于您的设备配置，推荐轻量级插件以确保流畅体验',
      standard: '基于您的设备能力，推荐平衡性能和功能的插件组合',
      advanced: '基于您的高性能设备，推荐充分利用硬件能力的插件',
      professional: '基于您的专业级设备，推荐完整的开发和学习工具链',
    };
    
    return reasons[deviceClass] || reasons.basic;
  }

  /**
   * 计算推荐置信度
   */
  _calculateConfidence(deviceClass) {
    let confidence = 0.6; // 基础置信度
    
    // 设备等级越高，置信度越高
    const deviceClassConfidence = {
      basic: 0.6,
      standard: 0.7,
      advanced: 0.8,
      professional: 0.9,
    };
    
    confidence = deviceClassConfidence[deviceClass] || 0.6;
    
    // 使用数据越多，置信度越高
    const usageCount = Array.from(this.usageStatsMap.values())
      .reduce((sum, stat) => sum + stat.usageCount, 0);
    
    if (usageCount > 50) confidence += 0.1;
    if (usageCount > 100) confidence += 0.1;
    
    return Math.min(1, confidence);
  }

  /**
   * 获取热门插件（全局统计）
   */
  async getPopularPlugins(limit = 10) {
    // 这里可以对接后端 API 获取全局热门插件
    // 暂时返回模拟数据
    return [
      { pluginId: 'ai-tutor', installCount: 15000, rating: 4.8 },
      { pluginId: 'exam-pro', installCount: 12000, rating: 4.6 },
      { pluginId: 'ai-coding-assistant', installCount: 10000, rating: 4.9 },
      { pluginId: 'collab-editor', installCount: 8000, rating: 4.5 },
      { pluginId: 'ar-vr-lab', installCount: 6000, rating: 4.7 },
    ].slice(0, limit);
  }

  /**
   * 获取插件详情（包含评分和统计）
   */
  async getPluginDetails(pluginId) {
    const usageStats = this.usageStatsMap.get(pluginId);
    
    return {
      pluginId,
      usageStats: usageStats || null,
      // 可以从后端获取更多信息
      globalStats: {
        installCount: Math.floor(Math.random() * 10000) + 1000,
        averageRating: (Math.random() * 2 + 3).toFixed(1), // 3.0-5.0
        reviewCount: Math.floor(Math.random() * 1000) + 100,
      },
    };
  }

  /**
   * 更新设备评估报告
   */
  updateDeviceProfile(profile) {
    this.deviceProfile = profile;
  }

  /**
   * 导出使用统计数据
   */
  exportUsageStats() {
    return Array.from(this.usageStatsMap.values());
  }

  /**
   * 导入使用统计数据
   */
  importUsageStats(stats) {
    for (const stat of stats) {
      this.usageStatsMap.set(stat.pluginId, stat);
    }
    this._saveUsageStats();
  }
}

// ==================== 导出 ====================

module.exports = {
  PluginRecommendationEngine,
  PluginUsageStats,
  RecommendationResult,
  PluginBundle,
};
