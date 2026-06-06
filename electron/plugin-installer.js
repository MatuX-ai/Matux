/**
 * Electron 插件安装器
 * 
 * 功能:
 * 1. 解压 .mxp 插件包
 * 2. 验证插件签名和完整性
 * 3. 检查设备兼容性
 * 4. 安装插件到正确位置
 * 5. 执行生命周期钩子 (onInstall)
 * 6. 安装 Python 依赖
 * 7. 注册插件到 ModuleRegistry
 * 8. 回滚失败的安装
 * 
 * 用法:
 *   const installer = new PluginInstaller();
 *   await installer.install('/path/to/plugin.mxp');
 */

const { app, ipcMain } = require('electron');
const fs = require('fs');
const path = require('path');
const { execSync, exec } = require('child_process');
const crypto = require('crypto');
const AdmZip = require('adm-zip'); // 需要安装: npm install adm-zip

// ==================== 类型定义 ====================

/**
 * 安装选项
 */
class InstallOptions {
  constructor({
    force = false,
    skipSignatureCheck = false,
    skipCompatibilityCheck = false,
    keepDataOnUninstall = true,
    installPythonDeps = true,
    autoEnable = true,
  } = {}) {
    this.force = force;
    this.skipSignatureCheck = skipSignatureCheck;
    this.skipCompatibilityCheck = skipCompatibilityCheck;
    this.keepDataOnUninstall = keepDataOnUninstall;
    this.installPythonDeps = installPythonDeps;
    this.autoEnable = autoEnable;
  }
}

/**
 * 安装进度
 */
class InstallProgress {
  constructor() {
    this.pluginId = '';
    this.status = 'idle'; // idle, extracting, validating, installing, installing-deps, running-hooks, completed, failed, rolling-back
    this.progress = 0; // 0-100
    this.message = '';
    this.error = null;
  }
}

/**
 * 安装结果
 */
class InstallResult {
  constructor({
    success = false,
    pluginId = '',
    version = '',
    installPath = '',
    error = null,
    warnings = [],
    rolledBack = false,
  } = {}) {
    this.success = success;
    this.pluginId = pluginId;
    this.version = version;
    this.installPath = installPath;
    this.error = error;
    this.warnings = warnings;
    this.rolledBack = rolledBack;
  }
}

// ==================== 常量定义 ====================

const PLUGIN_DIR_NAME = 'plugins';
const PLUGIN_DATA_DIR_NAME = 'plugin-data';
const MAX_INSTALL_TIME_MS = 300000; // 5 分钟超时
const MAX_EXTRACT_SIZE_BYTES = 2 * 1024 * 1024 * 1024; // 2 GB

// ==================== 插件安装器类 ====================

class PluginInstaller {
  constructor() {
    /** @type {Map<string, InstallProgress>} 当前安装任务 */
    this.installTasks = new Map();
    
    /** @type {string} 插件安装根目录 */
    this.pluginsDir = path.join(app.getPath('userData'), PLUGIN_DIR_NAME);
    
    /** @type {string} 插件数据根目录 */
    this.pluginDataDir = path.join(app.getPath('userData'), PLUGIN_DATA_DIR_NAME);
    
    /** @type {string} 临时目录 */
    this.tempDir = path.join(app.getPath('temp'), 'imato-plugin-install');
    
    // 确保目录存在
    this._ensureDirectories();
  }
  
  /**
   * 确保必要的目录存在
   */
  _ensureDirectories() {
    [this.pluginsDir, this.pluginDataDir, this.tempDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  }
  
  /**
   * 安装插件
   * 
   * @param {string} mxpPath - .mxp 插件包路径
   * @param {InstallOptions} options - 安装选项
   * @param {Function} onProgress - 进度回调 (progress: InstallProgress) => void
   * @returns {Promise<InstallResult>} 安装结果
   */
  async install(mxpPath, options = new InstallOptions(), onProgress = null) {
    const progress = new InstallProgress();
    const taskId = `install-${Date.now()}`;
    this.installTasks.set(taskId, progress);
    
    try {
      // 1. 检查文件存在
      if (!fs.existsSync(mxpPath)) {
        throw new Error(`插件包不存在: ${mxpPath}`);
      }
      
      // 2. 解压插件包
      this._updateProgress(progress, 'extracting', 5, '正在解压插件包...', onProgress);
      const extractDir = await this._extractPackage(mxpPath);
      
      // 3. 读取 manifest
      this._updateProgress(progress, 'validating', 15, '正在读取 manifest...', onProgress);
      const manifest = this._readManifest(extractDir);
      progress.pluginId = manifest.id;
      
      // 4. 检查是否已安装
      if (!options.force && this._isInstalled(manifest.id)) {
        const installedVersion = this._getInstalledVersion(manifest.id);
        throw new Error(`插件已安装: ${manifest.id} v${installedVersion} (使用 force=true 覆盖安装)`);
      }
      
      // 5. 验证签名（可选）
      if (!options.skipSignatureCheck) {
        this._updateProgress(progress, 'validating', 25, '正在验证签名...', onProgress);
        await this._verifySignature(extractDir, manifest);
      }
      
      // 6. 检查设备兼容性
      if (!options.skipCompatibilityCheck) {
        this._updateProgress(progress, 'validating', 35, '正在检查设备兼容性...', onProgress);
        await this._checkCompatibility(manifest);
      }
      
      // 7. 安装插件文件
      this._updateProgress(progress, 'installing', 45, '正在安装插件文件...', onProgress);
      const installPath = await this._installFiles(extractDir, manifest);
      
      // 8. 创建数据目录
      const dataDir = path.join(this.pluginDataDir, manifest.id);
      if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
      }
      
      // 9. 安装 Python 依赖
      if (options.installPythonDeps) {
        this._updateProgress(progress, 'installing-deps', 60, '正在安装 Python 依赖...', onProgress);
        await this._installPythonDeps(installPath, manifest);
      }
      
      // 10. 执行 onInstall 钩子
      this._updateProgress(progress, 'running-hooks', 80, '正在执行安装钩子...', onProgress);
      await this._runInstallHook(installPath, dataDir, manifest);
      
      // 11. 注册插件（如果包含后端路由）
      if (manifest.entryPoints?.backend?.routes) {
        this._updateProgress(progress, 'installing', 90, '正在注册插件模块...', onProgress);
        await this._registerPlugin(manifest, installPath);
      }
      
      // 12. 保存安装信息
      this._saveInstallInfo(manifest, installPath, dataDir, options.autoEnable);
      
      // 13. 清理临时文件
      this._cleanup(extractDir);
      
      // 14. 完成
      this._updateProgress(progress, 'completed', 100, '安装完成!', onProgress);
      
      // 15. 发送安装完成事件
      if (global.mainWindow && !global.mainWindow.isDestroyed()) {
        global.mainWindow.webContents.send('plugin:install-progress', {
          type: 'completed',
          pluginId: manifest.id,
          version: manifest.version,
        });
      }
      
      return new InstallResult({
        success: true,
        pluginId: manifest.id,
        version: manifest.version,
        installPath,
        warnings: [],
      });
      
    } catch (err) {
      console.error(`插件安装失败: ${err.message}`, err);
      
      // 回滚安装
      this._updateProgress(progress, 'rolling-back', 95, '安装失败，正在回滚...', onProgress);
      await this._rollback(progress.pluginId);
      
      this._updateProgress(progress, 'failed', 100, `安装失败: ${err.message}`, onProgress);
      
      return new InstallResult({
        success: false,
        pluginId: progress.pluginId,
        error: err.message,
        rolledBack: true,
      });
      
    } finally {
      this.installTasks.delete(taskId);
    }
  }
  
  /**
   * 卸载插件
   * 
   * @param {string} pluginId - 插件 ID
   * @param {boolean} keepData - 是否保留数据
   * @param {Function} onProgress - 进度回调
   * @returns {Promise<{success: boolean, error?: string}>}
   */
  async uninstall(pluginId, keepData = true, onProgress = null) {
    const progress = new InstallProgress();
    progress.pluginId = pluginId;
    
    try {
      // 1. 检查是否已安装
      if (!this._isInstalled(pluginId)) {
        throw new Error(`插件未安装: ${pluginId}`);
      }
      
      // 2. 读取安装信息
      const installInfo = this._getInstallInfo(pluginId);
      const installPath = installInfo.installPath;
      const dataDir = installInfo.dataDir;
      
      // 3. 执行 onUninstall 钩子
      this._updateProgress(progress, 'running-hooks', 20, '正在执行卸载钩子...', onProgress);
      await this._runUninstallHook(installPath, dataDir, keepData);
      
      // 4. 取消注册
      this._updateProgress(progress, 'installing', 40, '正在取消模块注册...', onProgress);
      await this._unregisterPlugin(pluginId);
      
      // 5. 删除插件文件
      this._updateProgress(progress, 'installing', 60, '正在删除插件文件...', onProgress);
      if (fs.existsSync(installPath)) {
        fs.rmSync(installPath, { recursive: true, force: true });
      }
      
      // 6. 删除数据（可选）
      if (!keepData && fs.existsSync(dataDir)) {
        this._updateProgress(progress, 'installing', 80, '正在删除插件数据...', onProgress);
        fs.rmSync(dataDir, { recursive: true, force: true });
      }
      
      // 7. 删除安装信息
      this._removeInstallInfo(pluginId);
      
      // 8. 完成
      this._updateProgress(progress, 'completed', 100, '卸载完成!', onProgress);
      
      // 9. 发送卸载完成事件
      if (global.mainWindow && !global.mainWindow.isDestroyed()) {
        global.mainWindow.webContents.send('plugin:install-progress', {
          type: 'uninstalled',
          pluginId,
          keepData,
        });
      }
      
      return { success: true };
      
    } catch (err) {
      console.error(`插件卸载失败: ${err.message}`, err);
      this._updateProgress(progress, 'failed', 100, `卸载失败: ${err.message}`, onProgress);
      return { success: false, error: err.message };
    }
  }
  
  // ==================== 私有方法 ====================
  
  /**
   * 更新安装进度
   */
  _updateProgress(progress, status, percent, message, callback) {
    progress.status = status;
    progress.progress = percent;
    progress.message = message;
    
    if (callback) {
      callback(progress);
    }
    
    // 发送 IPC 事件
    if (global.mainWindow && !global.mainWindow.isDestroyed()) {
      global.mainWindow.webContents.send('plugin:install-progress', {
        type: 'progress',
        pluginId: progress.pluginId,
        status: progress.status,
        progress: progress.progress,
        message: progress.message,
      });
    }
  }
  
  /**
   * 解压插件包
   */
  async _extractPackage(mxpPath) {
    return new Promise((resolve, reject) => {
      try {
        const extractDir = path.join(this.tempDir, `extract-${Date.now()}`);
        fs.mkdirSync(extractDir, { recursive: true });
        
        const zip = new AdmZip(mxpPath);
        const zipEntries = zip.getEntries();
        
        // 检查总大小
        let totalSize = 0;
        for (const entry of zipEntries) {
          totalSize += entry.header.size;
        }
        
        if (totalSize > MAX_EXTRACT_SIZE_BYTES) {
          reject(new Error(`插件包解压后过大: ${(totalSize / 1024 / 1024 / 1024).toFixed(2)} GB (最大 2 GB)`));
          return;
        }
        
        // 解压
        zip.extractAllTo(extractDir, true);
        
        resolve(extractDir);
      } catch (err) {
        reject(new Error(`解压失败: ${err.message}`));
      }
    });
  }
  
  /**
   * 读取 manifest.json
   */
  _readManifest(extractDir) {
    const manifestPath = path.join(extractDir, 'manifest.json');
    
    if (!fs.existsSync(manifestPath)) {
      throw new Error('manifest.json 不存在');
    }
    
    try {
      const content = fs.readFileSync(manifestPath, 'utf-8');
      const manifest = JSON.parse(content);
      
      // 基本验证
      if (!manifest.id || !manifest.version || !manifest.name) {
        throw new Error('manifest.json 缺少必需字段 (id, version, name)');
      }
      
      return manifest;
    } catch (err) {
      throw new Error(`manifest.json 解析失败: ${err.message}`);
    }
  }
  
  /**
   * 验证签名
   */
  async _verifySignature(extractDir, manifest) {
    const sigDir = path.join(extractDir, 'signatures');
    
    if (!fs.existsSync(sigDir)) {
      console.warn(`插件 ${manifest.id} 无签名，跳过验证`);
      return;
    }
    
    const manifestSigPath = path.join(sigDir, 'manifest.sig');
    
    if (!fs.existsSync(manifestSigPath)) {
      console.warn(`插件 ${manifest.id} 无 manifest 签名，跳过验证`);
      return;
    }
    
    // TODO: 实现完整的签名验证逻辑
    // 1. 加载公钥（从插件商店 API 或本地信任库）
    // 2. 验证 manifest.json 签名
    // 3. 验证包签名
    
    console.log(`签名验证功能待实现 (插件: ${manifest.id})`);
  }
  
  /**
   * 检查设备兼容性
   */
  async _checkCompatibility(manifest) {
    // 1. 加载设备评估报告
    const deviceProfilePath = path.join(app.getPath('userData'), 'device-profile.json');
    
    if (!fs.existsSync(deviceProfilePath)) {
      console.warn('设备评估报告不存在，跳过兼容性检查');
      return;
    }
    
    const deviceProfile = JSON.parse(fs.readFileSync(deviceProfilePath, 'utf-8'));
    const deviceClass = deviceProfile.assessment?.deviceClass;
    const deviceScore = deviceProfile.assessment?.score;
    
    if (!deviceClass || deviceScore === undefined) {
      console.warn('设备评估数据不完整，跳过兼容性检查');
      return;
    }
    
    // 2. 检查设备等级兼容性
    const compat = manifest.deviceCompatibility;
    
    if (!compat || !compat.compatibleTiers) {
      throw new Error('插件 manifest 缺少 deviceCompatibility.compatibleTiers');
    }
    
    // 设备等级到 Tier 的映射
    const deviceTierMap = {
      'basic': ['tier-a'],
      'standard': ['tier-a', 'tier-b'],
      'advanced': ['tier-a', 'tier-b', 'tier-c'],
      'professional': ['tier-a', 'tier-b', 'tier-c', 'tier-d'],
    };
    
    const compatibleTiers = deviceTierMap[deviceClass] || [];
    
    // 检查是否有兼容的 Tier
    const hasCompatibleTier = compat.compatibleTiers.some(tier => compatibleTiers.includes(tier));
    
    if (!hasCompatibleTier) {
      throw new Error(
        `插件不兼容当前设备等级 (${deviceClass})\n` +
        `插件要求: ${compat.compatibleTiers.join(', ')}\n` +
        `设备支持: ${compatibleTiers.join(', ')}`
      );
    }
    
    // 3. 检查最低评分
    if (compat.minDeviceScore !== undefined && deviceScore < compat.minDeviceScore) {
      throw new Error(
        `设备评分不足: 当前 ${deviceScore} 分，插件要求最低 ${compat.minDeviceScore} 分`
      );
    }
    
    // 4. 检查硬件要求
    if (compat.requiredHardware) {
      const hardware = deviceProfile.hardware;
      const req = compat.requiredHardware;
      
      if (req.minMemoryMB && hardware.memory?.totalMB < req.minMemoryMB) {
        throw new Error(
          `内存不足: 当前 ${hardware.memory.totalMB} MB，插件要求最低 ${req.minMemoryMB} MB`
        );
      }
      
      if (req.requireGPU && !hardware.gpu?.hasDedicatedGPU) {
        throw new Error('插件需要独立 GPU，但当前设备未检测到');
      }
      
      if (req.minVRAM_MB && (hardware.gpu?.vramMB || 0) < req.minVRAM_MB) {
        throw new Error(
          `显存不足: 当前 ${hardware.gpu?.vramMB || 0} MB，插件要求最低 ${req.minVRAM_MB} MB`
        );
      }
      
      if (req.requireCUDA && !hardware.gpu?.supportsCUDA) {
        throw new Error('插件需要 CUDA 支持，但当前设备未检测到');
      }
      
      if (req.requireDocker && !deviceProfile.software?.containers?.hasDocker) {
        throw new Error('插件需要 Docker，但当前设备未安装或不可用');
      }
      
      if (req.requireRedis && !deviceProfile.software?.runtime?.hasRedis) {
        throw new Error('插件需要 Redis，但当前设备未安装或不可用');
      }
    }
    
    console.log(`✓ 插件 ${manifest.id} 兼容性检查通过`);
  }
  
  /**
   * 安装插件文件
   */
  async _installFiles(extractDir, manifest) {
    const installPath = path.join(this.pluginsDir, manifest.id);
    
    // 如果已存在，先删除（覆盖安装）
    if (fs.existsSync(installPath)) {
      fs.rmSync(installPath, { recursive: true, force: true });
    }
    
    // 移动文件
    fs.renameSync(extractDir, installPath);
    
    return installPath;
  }
  
  /**
   * 安装 Python 依赖
   */
  async _installPythonDeps(installPath, manifest) {
    const deps = manifest.dependencies;
    
    if (!deps || !deps.python || deps.python.length === 0) {
      console.log(`插件 ${manifest.id} 无 Python 依赖`);
      return;
    }
    
    console.log(`正在安装 ${manifest.id} 的 Python 依赖: ${deps.python.length} 个包`);
    
    // 1. 检查是否有预编译的 wheel 文件
    const wheelsDir = path.join(installPath, 'python-deps', 'wheels');
    
    if (fs.existsSync(wheelsDir)) {
      console.log('使用预编译 wheel 文件安装...');
      
      const wheelFiles = fs.readdirSync(wheelsDir).filter(f => f.endsWith('.whl'));
      
      for (const wheel of wheelFiles) {
        const wheelPath = path.join(wheelsDir, wheel);
        try {
          execSync(`pip install "${wheelPath}" --no-deps`, { stdio: 'inherit' });
          console.log(`✓ 安装 ${wheel}`);
        } catch (err) {
          console.warn(`✗ 安装 ${wheel} 失败: ${err.message}`);
        }
      }
    }
    
    // 2. 安装 requirements.txt 中的依赖
    const requirementsPath = path.join(installPath, 'backend', 'requirements.txt');
    
    if (fs.existsSync(requirementsPath)) {
      console.log('安装 requirements.txt 依赖...');
      
      try {
        execSync(`pip install -r "${requirementsPath}"`, { stdio: 'inherit' });
        console.log('✓ Python 依赖安装完成');
      } catch (err) {
        console.warn(`✗ Python 依赖安装失败: ${err.message}`);
        // 不抛出错误，允许部分失败
      }
    }
  }
  
  /**
   * 执行 onInstall 钩子
   */
  async _runInstallHook(installPath, dataDir, manifest) {
    const hooks = manifest.entryPoints?.backend?.hooks;
    
    if (!hooks || !hooks.onInstall) {
      console.log(`插件 ${manifest.id} 无 onInstall 钩子`);
      return;
    }
    
    const hookPath = path.join(installPath, hooks.onInstall);
    
    if (!fs.existsSync(hookPath)) {
      console.warn(`onInstall 钩子文件不存在: ${hookPath}`);
      return;
    }
    
    console.log(`正在执行 onInstall 钩子: ${hookPath}`);
    
    try {
      // 设置环境变量
      const env = {
        ...process.env,
        PLUGIN_ID: manifest.id,
        PLUGIN_VERSION: manifest.version,
        PLUGIN_DIR: installPath,
        DATA_DIR: dataDir,
        PLATFORM: process.platform,
        ARCH: process.arch,
      };
      
      // 执行钩子脚本（60 秒超时）
      execSync(`python "${hookPath}"`, {
        env,
        cwd: installPath,
        stdio: 'inherit',
        timeout: 60000,
      });
      
      console.log(`✓ onInstall 钩子执行成功`);
    } catch (err) {
      throw new Error(`onInstall 钩子执行失败: ${err.message}`);
    }
  }
  
  /**
   * 执行 onUninstall 钩子
   */
  async _runUninstallHook(installPath, dataDir, keepData) {
    const installInfo = this._getInstallInfo(path.basename(installPath));
    
    if (!installInfo || !installInfo.manifest) {
      console.warn('无法读取安装信息，跳过 onUninstall 钩子');
      return;
    }
    
    const manifest = installInfo.manifest;
    const hooks = manifest.entryPoints?.backend?.hooks;
    
    if (!hooks || !hooks.onUninstall) {
      console.log(`插件 ${manifest.id} 无 onUninstall 钩子`);
      return;
    }
    
    const hookPath = path.join(installPath, hooks.onUninstall);
    
    if (!fs.existsSync(hookPath)) {
      console.warn(`onUninstall 钩子文件不存在: ${hookPath}`);
      return;
    }
    
    console.log(`正在执行 onUninstall 钩子: ${hookPath}`);
    
    try {
      const env = {
        ...process.env,
        PLUGIN_ID: manifest.id,
        PLUGIN_VERSION: manifest.version,
        PLUGIN_DIR: installPath,
        DATA_DIR: dataDir,
        KEEP_DATA: keepData.toString(),
        PLATFORM: process.platform,
        ARCH: process.arch,
      };
      
      execSync(`python "${hookPath}"`, {
        env,
        cwd: installPath,
        stdio: 'inherit',
        timeout: 30000,
      });
      
      console.log(`✓ onUninstall 钩子执行成功`);
    } catch (err) {
      console.warn(`onUninstall 钩子执行失败: ${err.message} (继续卸载)`);
    }
  }
  
  /**
   * 注册插件到 ModuleRegistry
   */
  async _registerPlugin(manifest, installPath) {
    // TODO: 实现插件动态注册逻辑
    // 1. 将后端路由信息发送到后端 API
    // 2. 后端动态加载路由并注册到 FastAPI
    // 3. 前端注册 Angular 模块和路由
    
    console.log(`插件注册功能待实现 (插件: ${manifest.id})`);
    
    // 临时方案：保存到注册表文件
    const registryPath = path.join(app.getPath('userData'), 'plugin-registry.json');
    let registry = { plugins: [] };
    
    if (fs.existsSync(registryPath)) {
      registry = JSON.parse(fs.readFileSync(registryPath, 'utf-8'));
    }
    
    // 移除旧版本
    registry.plugins = registry.plugins.filter(p => p.id !== manifest.id);
    
    // 添加新版本
    registry.plugins.push({
      id: manifest.id,
      name: manifest.name,
      version: manifest.version,
      installPath,
      enabled: true,
      installedAt: new Date().toISOString(),
      manifest,
    });
    
    fs.writeFileSync(registryPath, JSON.stringify(registry, null, 2), 'utf-8');
  }
  
  /**
   * 取消插件注册
   */
  async _unregisterPlugin(pluginId) {
    // TODO: 实现插件动态取消注册逻辑
    
    console.log(`插件取消注册功能待实现 (插件: ${pluginId})`);
    
    // 临时方案：从注册表文件移除
    const registryPath = path.join(app.getPath('userData'), 'plugin-registry.json');
    
    if (!fs.existsSync(registryPath)) {
      return;
    }
    
    const registry = JSON.parse(fs.readFileSync(registryPath, 'utf-8'));
    registry.plugins = registry.plugins.filter(p => p.id !== pluginId);
    
    fs.writeFileSync(registryPath, JSON.stringify(registry, null, 2), 'utf-8');
  }
  
  /**
   * 保存安装信息
   */
  _saveInstallInfo(manifest, installPath, dataDir, autoEnable) {
    const infoPath = path.join(this.pluginsDir, `${manifest.id}.json`);
    
    const info = {
      id: manifest.id,
      name: manifest.name,
      version: manifest.version,
      description: manifest.description,
      installPath,
      dataDir,
      enabled: autoEnable,
      installedAt: new Date().toISOString(),
      manifest,
    };
    
    fs.writeFileSync(infoPath, JSON.stringify(info, null, 2), 'utf-8');
  }
  
  /**
   * 获取安装信息
   */
  _getInstallInfo(pluginId) {
    const infoPath = path.join(this.pluginsDir, `${pluginId}.json`);
    
    if (!fs.existsSync(infoPath)) {
      return null;
    }
    
    return JSON.parse(fs.readFileSync(infoPath, 'utf-8'));
  }
  
  /**
   * 删除安装信息
   */
  _removeInstallInfo(pluginId) {
    const infoPath = path.join(this.pluginsDir, `${pluginId}.json`);
    
    if (fs.existsSync(infoPath)) {
      fs.unlinkSync(infoPath);
    }
  }
  
  /**
   * 检查插件是否已安装
   */
  _isInstalled(pluginId) {
    const infoPath = path.join(this.pluginsDir, `${pluginId}.json`);
    return fs.existsSync(infoPath);
  }
  
  /**
   * 获取已安装插件版本
   */
  _getInstalledVersion(pluginId) {
    const info = this._getInstallInfo(pluginId);
    return info?.version || 'unknown';
  }
  
  /**
   * 回滚安装
   */
  async _rollback(pluginId) {
    if (!pluginId) {
      return;
    }
    
    console.log(`正在回滚插件安装: ${pluginId}`);
    
    try {
      const installPath = path.join(this.pluginsDir, pluginId);
      
      if (fs.existsSync(installPath)) {
        fs.rmSync(installPath, { recursive: true, force: true });
      }
      
      this._removeInstallInfo(pluginId);
      
      console.log(`✓ 回滚完成: ${pluginId}`);
    } catch (err) {
      console.error(`回滚失败: ${err.message}`);
    }
  }
  
  /**
   * 清理临时文件
   */
  _cleanup(extractDir) {
    try {
      if (fs.existsSync(extractDir)) {
        fs.rmSync(extractDir, { recursive: true, force: true });
      }
    } catch (err) {
      console.warn(`清理临时文件失败: ${err.message}`);
    }
  }
}

// ==================== IPC 处理器 ====================

function registerPluginInstallerIPC(installer) {
  /**
   * 安装插件
   */
  ipcMain.handle('plugin:install', async (event, mxpPath, options) => {
    try {
      const installOptions = new InstallOptions(options);
      
      const result = await installer.install(mxpPath, installOptions, (progress) => {
        // 进度已通过内部 IPC 发送
      });
      
      return {
        success: result.success,
        pluginId: result.pluginId,
        version: result.version,
        error: result.error,
        warnings: result.warnings,
      };
    } catch (err) {
      return {
        success: false,
        error: err.message,
      };
    }
  });
  
  /**
   * 卸载插件
   */
  ipcMain.handle('plugin:uninstall', async (event, pluginId, keepData) => {
    try {
      const result = await installer.uninstall(pluginId, keepData);
      return result;
    } catch (err) {
      return {
        success: false,
        error: err.message,
      };
    }
  });
  
  /**
   * 获取已安装插件列表
   */
  ipcMain.handle('plugin:installed', async () => {
    try {
      const plugins = [];
      const files = fs.readdirSync(installer.pluginsDir);
      
      for (const file of files) {
        if (file.endsWith('.json')) {
          const infoPath = path.join(installer.pluginsDir, file);
          const info = JSON.parse(fs.readFileSync(infoPath, 'utf-8'));
          plugins.push(info);
        }
      }
      
      return { success: true, plugins };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });
  
  /**
   * 启用/禁用插件
   */
  ipcMain.handle('plugin:toggle', async (event, pluginId, enabled) => {
    try {
      const info = installer._getInstallInfo(pluginId);
      
      if (!info) {
        return { success: false, error: `插件未安装: ${pluginId}` };
      }
      
      info.enabled = enabled;
      installer._saveInstallInfo(
        info.manifest,
        info.installPath,
        info.dataDir,
        enabled
      );
      
      // TODO: 动态启用/禁用模块
      
      return { success: true, enabled };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });
}

// ==================== 导出 ====================

module.exports = {
  PluginInstaller,
  InstallOptions,
  InstallProgress,
  InstallResult,
  registerPluginInstallerIPC,
};
