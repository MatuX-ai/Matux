/**
 * 安装包精简配置
 * 
 * 功能:
 * 1. 定义核心包必需模块
 * 2. 定义可选插件模块
 * 3. 首次启动引导配置
 * 4. 按需下载管理
 */

const path = require('path');
const fs = require('fs');
const { app } = require('electron');

// ==================== 常量定义 ====================

const INSTALL_CONFIG_FILE = path.join(
  app.getPath('userData'),
  'install-config.json'
);

const FIRST_RUN_FLAG_FILE = path.join(
  app.getPath('userData'),
  'first-run-completed.flag'
);

// ==================== 核心包配置 ====================

/**
 * 核心包必需模块（首次安装必须包含）
 */
const CORE_MODULES = [
  {
    id: 'core-runtime',
    name: '核心运行时',
    description: '应用基础运行环境',
    required: true,
    size: '15MB',
    category: 'system',
  },
  {
    id: 'ui-framework',
    name: 'UI 框架',
    description: 'Angular Material UI 组件库',
    required: true,
    size: '8MB',
    category: 'system',
  },
  {
    id: 'auth-service',
    name: '认证服务',
    description: '用户登录和权限管理',
    required: true,
    size: '2MB',
    category: 'system',
  },
  {
    id: 'plugin-manager',
    name: '插件管理器',
    description: '插件安装和管理核心',
    required: true,
    size: '3MB',
    category: 'system',
  },
  {
    id: 'device-profiler',
    name: '设备评估器',
    description: '硬件能力检测引擎',
    required: true,
    size: '1MB',
    category: 'system',
  },
];

/**
 * 可选插件模块（首次启动后按需下载）
 */
const OPTIONAL_MODULES = [
  // AI 教学类
  {
    id: 'ai-tutor',
    name: 'AI 教学助手',
    description: '智能个性化教学引擎',
    required: false,
    size: '25MB',
    category: 'education',
    deviceClass: 'basic',
    recommended: true,
  },
  {
    id: 'exam-pro',
    name: '考试系统',
    description: '在线考试和测验平台',
    required: false,
    size: '12MB',
    category: 'education',
    deviceClass: 'basic',
    recommended: true,
  },
  {
    id: 'creativity-engine',
    name: '创意引擎',
    description: 'AI 创意生成工具',
    required: false,
    size: '45MB',
    category: 'education',
    deviceClass: 'advanced',
    recommended: true,
  },
  
  // 开发工具类
  {
    id: 'code-editor',
    name: '代码编辑器',
    description: '轻量级代码编辑器',
    required: false,
    size: '8MB',
    category: 'development',
    deviceClass: 'basic',
    recommended: true,
  },
  {
    id: 'ai-coding-assistant',
    name: 'AI 编程助手',
    description: '智能代码补全和审查',
    required: false,
    size: '35MB',
    category: 'development',
    deviceClass: 'standard',
    recommended: true,
  },
  {
    id: 'code-sandbox',
    name: '代码沙箱',
    description: '云端代码执行环境',
    required: false,
    size: '50MB',
    category: 'development',
    deviceClass: 'professional',
    recommended: false,
  },
  
  // AR/VR 类
  {
    id: 'ar-vr-lab',
    name: 'AR/VR 实验室',
    description: '沉浸式实验环境',
    required: false,
    size: '120MB',
    category: 'immersive',
    deviceClass: 'advanced',
    recommended: true,
  },
  {
    id: 'vr-3d-editor',
    name: '3D VR 编辑器',
    description: '虚拟现实内容编辑器',
    required: false,
    size: '200MB',
    category: 'immersive',
    deviceClass: 'professional',
    recommended: false,
  },
  {
    id: 'digital-twin',
    name: '数字孪生',
    description: '物理系统数字映射',
    required: false,
    size: '150MB',
    category: 'immersive',
    deviceClass: 'professional',
    recommended: false,
  },
  
  // 硬件开发类
  {
    id: 'hardware-cert',
    name: '硬件认证',
    description: '硬件兼容性测试工具',
    required: false,
    size: '18MB',
    category: 'hardware',
    deviceClass: 'standard',
    recommended: false,
  },
  {
    id: 'tinyml-studio',
    name: 'TinyML 工作室',
    description: '嵌入式机器学习开发',
    required: false,
    size: '40MB',
    category: 'hardware',
    deviceClass: 'standard',
    recommended: false,
  },
  {
    id: 'iot-simulator',
    name: 'IoT 模拟器',
    description: '物联网设备模拟平台',
    required: false,
    size: '30MB',
    category: 'hardware',
    deviceClass: 'standard',
    recommended: false,
  },
  
  // 协作工具类
  {
    id: 'collab-editor',
    name: '协作编辑器',
    description: '多人实时协作编辑',
    required: false,
    size: '15MB',
    category: 'collaboration',
    deviceClass: 'standard',
    recommended: true,
  },
  {
    id: 'knowledge-graph',
    name: '知识图谱',
    description: '知识可视化管理',
    required: false,
    size: '22MB',
    category: 'collaboration',
    deviceClass: 'standard',
    recommended: false,
  },
  
  // AI/ML 工具类
  {
    id: 'model-bench',
    name: '模型评测',
    description: 'AI 模型性能测试平台',
    required: false,
    size: '35MB',
    category: 'ai-ml',
    deviceClass: 'advanced',
    recommended: true,
  },
  {
    id: 'federated-learning',
    name: '联邦学习',
    description: '分布式机器学习框架',
    required: false,
    size: '80MB',
    category: 'ai-ml',
    deviceClass: 'advanced',
    recommended: false,
  },
];

// ==================== 首次启动引导配置 ====================

const FIRST_RUN_GUIDE = {
  steps: [
    {
      id: 'welcome',
      title: '欢迎使用 iMato',
      description: '让我们为您配置最佳的学习环境',
      icon: 'waving_hand',
      order: 1,
    },
    {
      id: 'device-assessment',
      title: '设备能力评估',
      description: '检测您的硬件配置以推荐合适的插件',
      icon: 'memory',
      order: 2,
      action: 'assess_device',
    },
    {
      id: 'plugin-selection',
      title: '选择插件',
      description: '基于设备评级为您推荐插件组合',
      icon: 'extension',
      order: 3,
      action: 'show_recommendations',
    },
    {
      id: 'bundle-selection',
      title: '选择捆绑包（可选）',
      description: '一键安装常用插件组合，享受折扣',
      icon: 'inventory_2',
      order: 4,
      action: 'show_bundles',
      optional: true,
    },
    {
      id: 'download-install',
      title: '下载和安装',
      description: '开始下载选中的插件',
      icon: 'download',
      order: 5,
      action: 'start_download',
    },
    {
      id: 'complete',
      title: '设置完成',
      description: '开始您的学习之旅！',
      icon: 'check_circle',
      order: 6,
    },
  ],
};

// ==================== 安装配置类 ====================

class InstallConfigManager {
  constructor() {
    /** @type {object} 安装配置 */
    this.config = {
      coreModules: CORE_MODULES,
      optionalModules: OPTIONAL_MODULES,
      installedModules: [],
      skippedModules: [],
      firstRunCompleted: false,
      firstRunCompletedAt: null,
      lastUpdatedAt: null,
    };
    
    // 初始化
    this._initialize();
  }

  /**
   * 初始化配置管理器
   */
  async _initialize() {
    try {
      await this._loadConfig();
      await this._checkFirstRun();
      console.log('[INFO] ✓ 安装配置管理器初始化完成');
    } catch (err) {
      console.error('[ERROR] 安装配置管理器初始化失败:', err.message);
    }
  }

  /**
   * 加载配置
   */
  async _loadConfig() {
    try {
      if (fs.existsSync(INSTALL_CONFIG_FILE)) {
        const data = fs.readFileSync(INSTALL_CONFIG_FILE, 'utf-8');
        const savedConfig = JSON.parse(data);
        
        // 合并配置
        this.config = {
          ...this.config,
          ...savedConfig,
        };
        
        console.log('[INFO] 加载了安装配置');
      }
    } catch (err) {
      console.warn('[WARN] 加载安装配置失败:', err.message);
    }
  }

  /**
   * 保存配置
   */
  async _saveConfig() {
    try {
      this.config.lastUpdatedAt = new Date().toISOString();
      fs.writeFileSync(INSTALL_CONFIG_FILE, JSON.stringify(this.config, null, 2), 'utf-8');
    } catch (err) {
      console.error('[ERROR] 保存安装配置失败:', err.message);
    }
  }

  /**
   * 检查是否首次运行
   */
  async _checkFirstRun() {
    try {
      this.config.firstRunCompleted = fs.existsSync(FIRST_RUN_FLAG_FILE);
      
      if (this.config.firstRunCompleted) {
        const flagData = fs.readFileSync(FIRST_RUN_FLAG_FILE, 'utf-8');
        this.config.firstRunCompletedAt = flagData;
      }
    } catch (err) {
      console.warn('[WARN] 检查首次运行状态失败:', err.message);
    }
  }

  /**
   * 标记首次运行完成
   */
  async markFirstRunCompleted() {
    try {
      const now = new Date().toISOString();
      fs.writeFileSync(FIRST_RUN_FLAG_FILE, now, 'utf-8');
      
      this.config.firstRunCompleted = true;
      this.config.firstRunCompletedAt = now;
      
      await this._saveConfig();
      
      console.log('[INFO] ✓ 首次运行引导已完成');
    } catch (err) {
      console.error('[ERROR] 标记首次运行完成失败:', err.message);
    }
  }

  /**
   * 获取核心模块列表
   */
  getCoreModules() {
    return this.config.coreModules;
  }

  /**
   * 获取可选模块列表
   */
  getOptionalModules(deviceClass = null) {
    let modules = this.config.optionalModules;
    
    // 按设备等级过滤
    if (deviceClass) {
      const deviceClassOrder = ['basic', 'standard', 'advanced', 'professional'];
      const deviceLevel = deviceClassOrder.indexOf(deviceClass);
      
      modules = modules.filter(module => {
        const moduleLevel = deviceClassOrder.indexOf(module.deviceClass);
        return moduleLevel <= deviceLevel;
      });
    }
    
    return modules;
  }

  /**
   * 获取已安装模块
   */
  getInstalledModules() {
    return this.config.installedModules;
  }

  /**
   * 添加已安装模块
   */
  async addInstalledModule(moduleId) {
    if (!this.config.installedModules.includes(moduleId)) {
      this.config.installedModules.push(moduleId);
      
      // 从跳过列表中移除
      this.config.skippedModules = this.config.skippedModules.filter(
        id => id !== moduleId
      );
      
      await this._saveConfig();
    }
  }

  /**
   * 跳过模块安装
   */
  async skipModule(moduleId) {
    if (!this.config.skippedModules.includes(moduleId)) {
      this.config.skippedModules.push(moduleId);
      await this._saveConfig();
    }
  }

  /**
   * 获取首次启动引导步骤
   */
  getFirstRunGuide() {
    return FIRST_RUN_GUIDE;
  }

  /**
   * 检查是否已完成首次运行
   */
  isFirstRunCompleted() {
    return this.config.firstRunCompleted;
  }

  /**
   * 获取安装统计
   */
  getInstallStats() {
    const totalCoreSize = this.config.coreModules
      .reduce((sum, m) => sum + parseInt(m.size), 0);
    
    const totalOptionalSize = this.config.optionalModules
      .reduce((sum, m) => sum + parseInt(m.size), 0);
    
    const installedSize = this.config.coreModules
      .filter(m => this.config.installedModules.includes(m.id))
      .reduce((sum, m) => sum + parseInt(m.size), 0);
    
    return {
      coreModuleCount: this.config.coreModules.length,
      optionalModuleCount: this.config.optionalModules.length,
      installedModuleCount: this.config.installedModules.length,
      skippedModuleCount: this.config.skippedModules.length,
      totalCoreSizeMB: totalCoreSize,
      totalOptionalSizeMB: totalOptionalSize,
      installedSizeMB: installedSize,
      savedSizeMB: totalOptionalSize - installedSize,
      firstRunCompleted: this.config.firstRunCompleted,
    };
  }

  /**
   * 获取推荐模块（基于设备评级）
   */
  getRecommendedModules(deviceClass) {
    const deviceClassOrder = ['basic', 'standard', 'advanced', 'professional'];
    const deviceLevel = deviceClassOrder.indexOf(deviceClass);
    
    return this.config.optionalModules
      .filter(module => {
        const moduleLevel = deviceClassOrder.indexOf(module.deviceClass);
        return moduleLevel <= deviceLevel && module.recommended;
      })
      .sort((a, b) => {
        // 推荐的排在前面
        if (a.recommended && !b.recommended) return -1;
        if (!a.recommended && b.recommended) return 1;
        return 0;
      });
  }

  /**
   * 检查模块是否已安装
   */
  isModuleInstalled(moduleId) {
    return this.config.installedModules.includes(moduleId);
  }

  /**
   * 检查模块是否被跳过
   */
  isModuleSkipped(moduleId) {
    return this.config.skippedModules.includes(moduleId);
  }

  /**
   * 重置安装配置（用于测试）
   */
  async resetConfig() {
    try {
      // 删除配置文件
      if (fs.existsSync(INSTALL_CONFIG_FILE)) {
        fs.unlinkSync(INSTALL_CONFIG_FILE);
      }
      
      // 删除首次运行标志
      if (fs.existsSync(FIRST_RUN_FLAG_FILE)) {
        fs.unlinkSync(FIRST_RUN_FLAG_FILE);
      }
      
      // 重置配置
      this.config = {
        coreModules: CORE_MODULES,
        optionalModules: OPTIONAL_MODULES,
        installedModules: [],
        skippedModules: [],
        firstRunCompleted: false,
        firstRunCompletedAt: null,
        lastUpdatedAt: null,
      };
      
      console.log('[INFO] ✓ 安装配置已重置');
    } catch (err) {
      console.error('[ERROR] 重置安装配置失败:', err.message);
    }
  }
}

// ==================== 导出 ====================

module.exports = {
  InstallConfigManager,
  CORE_MODULES,
  OPTIONAL_MODULES,
  FIRST_RUN_GUIDE,
};
