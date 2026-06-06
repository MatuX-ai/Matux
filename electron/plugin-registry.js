/**
 * 本地插件注册表
 * 
 * 功能:
 * 1. 管理已安装插件的元数据
 * 2. 插件版本跟踪
 * 3. 插件状态持久化
 * 4. 插件依赖关系图
 * 5. 插件搜索和过滤
 * 6. 插件配置管理
 * 
 * 存储位置: ~/.imato/plugin-registry.json
 * 
 * 用法:
 *   const registry = new PluginRegistry();
 *   await registry.initialize();
 *   registry.addPlugin(pluginInfo);
 */

const fs = require('fs');
const path = require('path');
const { app } = require('electron');

// ==================== 类型定义 ====================

/**
 * 插件注册表条目
 */
class PluginRegistryEntry {
  constructor({
    id = '',
    name = '',
    version = '',
    description = '',
    author = {},
    license = '',
    icon = null,
    categories = [],
    keywords = [],
    installPath = '',
    dataDir = '',
    enabled = true,
    installedAt = '',
    updatedAt = null,
    lastLoadedAt = null,
    manifest = {},
    dependencies = [],
    settings = {},
    state = 'installed', // installed, loaded, enabled, disabled, error
    error = null,
  } = {}) {
    this.id = id;
    this.name = name;
    this.version = version;
    this.description = description;
    this.author = author;
    this.license = license;
    this.icon = icon;
    this.categories = categories;
    this.keywords = keywords;
    this.installPath = installPath;
    this.dataDir = dataDir;
    this.enabled = enabled;
    this.installedAt = installedAt;
    this.updatedAt = updatedAt;
    this.lastLoadedAt = lastLoadedAt;
    this.manifest = manifest;
    this.dependencies = dependencies;
    this.settings = settings;
    this.state = state;
    this.error = error;
  }
}

/**
 * 插件注册表数据结构
 */
class PluginRegistryData {
  constructor() {
    this.version = '1.0';
    this.updatedAt = new Date().toISOString();
    this.plugins = [];
    this.metadata = {
      totalInstalled: 0,
      totalEnabled: 0,
      totalDisabled: 0,
      categories: {},
    };
  }
}

// ==================== 常量定义 ====================

const REGISTRY_FILE = 'plugin-registry.json';
const REGISTRY_BACKUP_FILE = 'plugin-registry.backup.json';

// ==================== 插件注册表类 ====================

class PluginRegistry {
  constructor() {
    /** @type {PluginRegistryData} 注册表数据 */
    this.data = new PluginRegistryData();
    
    /** @type {string} 注册表文件路径 */
    this.registryPath = path.join(app.getPath('userData'), REGISTRY_FILE);
    
    /** @type {string} 备份文件路径 */
    this.backupPath = path.join(app.getPath('userData'), REGISTRY_BACKUP_FILE);
    
    /** @type {Map<string, PluginRegistryEntry>} 插件索引（按 ID） */
    this.index = new Map();
  }
  
  /**
   * 初始化注册表
   */
  async initialize() {
    console.log('初始化插件注册表...');
    
    try {
      // 1. 加载注册表
      await this.load();
      
      // 2. 构建索引
      this._buildIndex();
      
      // 3. 更新元数据
      this._updateMetadata();
      
      // 4. 验证完整性
      await this._validateRegistry();
      
      console.log(`✓ 插件注册表初始化完成，共 ${this.data.plugins.length} 个插件`);
    } catch (err) {
      console.error(`插件注册表初始化失败: ${err.message}`);
      
      // 尝试从备份恢复
      if (fs.existsSync(this.backupPath)) {
        console.log('尝试从备份恢复...');
        await this._restoreFromBackup();
      }
    }
  }
  
  /**
   * 加载注册表数据
   */
  async load() {
    if (!fs.existsSync(this.registryPath)) {
      console.log('注册表文件不存在，创建新注册表');
      this.data = new PluginRegistryData();
      await this.save();
      return;
    }
    
    try {
      const content = fs.readFileSync(this.registryPath, 'utf-8');
      this.data = JSON.parse(content);
      
      // 版本迁移（如果需要）
      if (this.data.version !== '1.0') {
        console.log(`迁移注册表版本: ${this.data.version} → 1.0`);
        await this._migrateRegistry();
      }
      
      console.log(`✓ 注册表加载成功，共 ${this.data.plugins.length} 个插件`);
    } catch (err) {
      console.error(`注册表加载失败: ${err.message}`);
      throw err;
    }
  }
  
  /**
   * 保存注册表数据
   */
  async save() {
    try {
      // 更新时间戳
      this.data.updatedAt = new Date().toISOString();
      
      // 更新元数据
      this._updateMetadata();
      
      // 创建备份
      if (fs.existsSync(this.registryPath)) {
        fs.copyFileSync(this.registryPath, this.backupPath);
      }
      
      // 写入文件
      const content = JSON.stringify(this.data, null, 2);
      fs.writeFileSync(this.registryPath, content, 'utf-8');
      
      console.log(`✓ 注册表已保存 (${this.data.plugins.length} 个插件)`);
    } catch (err) {
      console.error(`注册表保存失败: ${err.message}`);
      throw err;
    }
  }
  
  /**
   * 添加插件
   */
  async addPlugin(pluginInfo) {
    // 检查是否已存在
    const existing = this.index.get(pluginInfo.id);
    
    if (existing) {
      console.log(`插件已存在: ${pluginInfo.id} v${existing.version}，更新为 v${pluginInfo.version}`);
      await this.updatePlugin(pluginInfo.id, pluginInfo);
      return;
    }
    
    // 创建注册表条目
    const entry = new PluginRegistryEntry({
      id: pluginInfo.id,
      name: pluginInfo.name,
      version: pluginInfo.version,
      description: pluginInfo.description || '',
      author: pluginInfo.author || {},
      license: pluginInfo.license || '',
      icon: pluginInfo.icon || null,
      categories: pluginInfo.categories || [],
      keywords: pluginInfo.keywords || [],
      installPath: pluginInfo.installPath || '',
      dataDir: pluginInfo.dataDir || '',
      enabled: pluginInfo.enabled !== undefined ? pluginInfo.enabled : true,
      installedAt: pluginInfo.installedAt || new Date().toISOString(),
      manifest: pluginInfo.manifest || {},
      dependencies: this._extractDependencies(pluginInfo.manifest),
      settings: this._extractDefaultSettings(pluginInfo.manifest),
      state: 'installed',
    });
    
    // 添加到列表
    this.data.plugins.push(entry);
    
    // 更新索引
    this.index.set(entry.id, entry);
    
    // 保存
    await this.save();
    
    console.log(`✓ 插件已添加到注册表: ${entry.name} (${entry.id})`);
  }
  
  /**
   * 更新插件
   */
  async updatePlugin(pluginId, updates) {
    const entry = this.index.get(pluginId);
    
    if (!entry) {
      throw new Error(`插件不存在: ${pluginId}`);
    }
    
    // 更新字段
    Object.assign(entry, updates, {
      updatedAt: new Date().toISOString(),
    });
    
    // 重新提取依赖和设置
    if (updates.manifest) {
      entry.dependencies = this._extractDependencies(updates.manifest);
      entry.settings = this._extractDefaultSettings(updates.manifest);
    }
    
    // 保存
    await this.save();
    
    console.log(`✓ 插件已更新: ${entry.name} (${entry.id})`);
  }
  
  /**
   * 移除插件
   */
  async removePlugin(pluginId) {
    const entry = this.index.get(pluginId);
    
    if (!entry) {
      throw new Error(`插件不存在: ${pluginId}`);
    }
    
    // 从列表移除
    this.data.plugins = this.data.plugins.filter(p => p.id !== pluginId);
    
    // 从索引移除
    this.index.delete(pluginId);
    
    // 保存
    await this.save();
    
    console.log(`✓ 插件已从注册表移除: ${entry.name} (${entry.id})`);
  }
  
  /**
   * 获取插件
   */
  getPlugin(pluginId) {
    return this.index.get(pluginId) || null;
  }
  
  /**
   * 获取所有插件
   */
  getAllPlugins() {
    return Array.from(this.index.values());
  }
  
  /**
   * 获取启用的插件
   */
  getEnabledPlugins() {
    return this.data.plugins.filter(p => p.enabled);
  }
  
  /**
   * 获取禁用的插件
   */
  getDisabledPlugins() {
    return this.data.plugins.filter(p => !p.enabled);
  }
  
  /**
   * 搜索插件
   */
  searchPlugins(query, options = {}) {
    const queryLower = query.toLowerCase();
    const { category, tier, enabled } = options;
    
    return this.data.plugins.filter(plugin => {
      // 关键词匹配
      const matchQuery = 
        plugin.name.toLowerCase().includes(queryLower) ||
        plugin.description.toLowerCase().includes(queryLower) ||
        plugin.keywords.some(kw => kw.toLowerCase().includes(queryLower));
      
      if (!matchQuery) return false;
      
      // 分类过滤
      if (category && !plugin.categories.includes(category)) {
        return false;
      }
      
      // Tier 过滤
      if (tier) {
        const compat = plugin.manifest.deviceCompatibility || {};
        const tiers = compat.compatibleTiers || [];
        if (!tiers.includes(tier)) {
          return false;
        }
      }
      
      // 启用状态过滤
      if (enabled !== undefined && plugin.enabled !== enabled) {
        return false;
      }
      
      return true;
    });
  }
  
  /**
   * 获取插件依赖图
   */
  getDependencyGraph() {
    const graph = {};
    
    for (const plugin of this.data.plugins) {
      graph[plugin.id] = {
        dependencies: plugin.dependencies,
        dependents: [],
      };
    }
    
    // 计算反向依赖（谁依赖我）
    for (const plugin of this.data.plugins) {
      for (const depId of plugin.dependencies) {
        if (graph[depId]) {
          graph[depId].dependents.push(plugin.id);
        }
      }
    }
    
    return graph;
  }
  
  /**
   * 检查依赖完整性
   */
  checkDependencies() {
    const issues = [];
    
    for (const plugin of this.data.plugins) {
      for (const depId of plugin.dependencies) {
        const dep = this.index.get(depId);
        
        if (!dep) {
          issues.push({
            type: 'missing',
            pluginId: plugin.id,
            dependencyId: depId,
            message: `插件 ${plugin.id} 依赖的 ${depId} 不存在`,
          });
        } else if (!dep.enabled) {
          issues.push({
            type: 'disabled',
            pluginId: plugin.id,
            dependencyId: depId,
            message: `插件 ${plugin.id} 依赖的 ${depId} 已禁用`,
          });
        }
      }
    }
    
    return issues;
  }
  
  /**
   * 更新插件状态
   */
  async updatePluginState(pluginId, state, error = null) {
    const entry = this.index.get(pluginId);
    
    if (!entry) {
      throw new Error(`插件不存在: ${pluginId}`);
    }
    
    entry.state = state;
    entry.error = error;
    
    if (state === 'loaded' || state === 'enabled') {
      entry.lastLoadedAt = new Date().toISOString();
    }
    
    await this.save();
  }
  
  /**
   * 更新插件设置
   */
  async updatePluginSettings(pluginId, settings) {
    const entry = this.index.get(pluginId);
    
    if (!entry) {
      throw new Error(`插件不存在: ${pluginId}`);
    }
    
    entry.settings = { ...entry.settings, ...settings };
    
    await this.save();
  }
  
  /**
   * 获取插件设置
   */
  getPluginSettings(pluginId) {
    const entry = this.index.get(pluginId);
    return entry?.settings || {};
  }
  
  /**
   * 获取统计信息
   */
  getStats() {
    return {
      totalInstalled: this.data.plugins.length,
      totalEnabled: this.data.plugins.filter(p => p.enabled).length,
      totalDisabled: this.data.plugins.filter(p => !p.enabled).length,
      categories: this.data.metadata.categories,
      lastUpdated: this.data.updatedAt,
    };
  }
  
  /**
   * 导出注册表
   */
  async exportRegistry(outputPath) {
    const content = JSON.stringify(this.data, null, 2);
    fs.writeFileSync(outputPath, content, 'utf-8');
    console.log(`✓ 注册表已导出到: ${outputPath}`);
  }
  
  /**
   * 导入注册表
   */
  async importRegistry(inputPath) {
    try {
      const content = fs.readFileSync(inputPath, 'utf-8');
      const importedData = JSON.parse(content);
      
      // 验证格式
      if (!importedData.plugins || !Array.isArray(importedData.plugins)) {
        throw new Error('无效的注册表格式');
      }
      
      // 备份当前注册表
      await this.save();
      
      // 替换数据
      this.data = importedData;
      
      // 重建索引
      this._buildIndex();
      
      // 保存
      await this.save();
      
      console.log(`✓ 注册表已导入，共 ${this.data.plugins.length} 个插件`);
    } catch (err) {
      console.error(`导入注册表失败: ${err.message}`);
      throw err;
    }
  }
  
  // ==================== 私有方法 ====================
  
  /**
   * 构建索引
   */
  _buildIndex() {
    this.index.clear();
    
    for (const plugin of this.data.plugins) {
      this.index.set(plugin.id, plugin);
    }
    
    console.log(`✓ 索引构建完成 (${this.index.size} 个插件)`);
  }
  
  /**
   * 更新元数据
   */
  _updateMetadata() {
    this.data.metadata.totalInstalled = this.data.plugins.length;
    this.data.metadata.totalEnabled = this.data.plugins.filter(p => p.enabled).length;
    this.data.metadata.totalDisabled = this.data.plugins.filter(p => !p.enabled).length;
    
    // 分类统计
    const categories = {};
    for (const plugin of this.data.plugins) {
      for (const cat of plugin.categories) {
        categories[cat] = (categories[cat] || 0) + 1;
      }
    }
    this.data.metadata.categories = categories;
  }
  
  /**
   * 提取依赖列表
   */
  _extractDependencies(manifest) {
    if (!manifest || !manifest.dependencies || !manifest.dependencies.plugins) {
      return [];
    }
    
    return manifest.dependencies.plugins
      .filter(dep => !dep.optional)
      .map(dep => dep.id);
  }
  
  /**
   * 提取默认设置
   */
  _extractDefaultSettings(manifest) {
    if (!manifest || !manifest.settings || !manifest.settings.defaults) {
      return {};
    }
    
    return { ...manifest.settings.defaults };
  }
  
  /**
   * 验证注册表完整性
   */
  async _validateRegistry() {
    const issues = [];
    
    for (const plugin of this.data.plugins) {
      // 检查安装路径是否存在
      if (plugin.installPath && !fs.existsSync(plugin.installPath)) {
        issues.push({
          pluginId: plugin.id,
          issue: 'install_path_missing',
          message: `插件安装路径不存在: ${plugin.installPath}`,
        });
      }
      
      // 检查版本号格式
      if (!/^\d+\.\d+\.\d+/.test(plugin.version)) {
        issues.push({
          pluginId: plugin.id,
          issue: 'invalid_version',
          message: `无效的版本号: ${plugin.version}`,
        });
      }
    }
    
    if (issues.length > 0) {
      console.warn(`注册表验证发现 ${issues.length} 个问题:`);
      for (const issue of issues) {
        console.warn(`  - ${issue.pluginId}: ${issue.message}`);
      }
    } else {
      console.log('✓ 注册表完整性验证通过');
    }
    
    return issues;
  }
  
  /**
   * 从备份恢复
   */
  async _restoreFromBackup() {
    try {
      const content = fs.readFileSync(this.backupPath, 'utf-8');
      this.data = JSON.parse(content);
      this._buildIndex();
      this._updateMetadata();
      
      console.log(`✓ 从备份恢复成功，共 ${this.data.plugins.length} 个插件`);
    } catch (err) {
      console.error(`从备份恢复失败: ${err.message}`);
      this.data = new PluginRegistryData();
    }
  }
  
  /**
   * 迁移注册表版本
   */
  async _migrateRegistry() {
    // 版本迁移逻辑（当前仅支持 1.0）
    this.data.version = '1.0';
    await this.save();
  }
}

// ==================== 导出 ====================

module.exports = {
  PluginRegistry,
  PluginRegistryEntry,
  PluginRegistryData,
};
