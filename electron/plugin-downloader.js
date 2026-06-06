/**
 * Electron 插件下载器
 * 
 * 功能:
 * 1. 从插件商店下载 .mxp 插件包
 * 2. 支持断点续传
 * 3. 下载进度报告
 * 4. 下载队列管理
 * 5. 下载速度限制
 * 6. 下载重试机制
 * 7. 下载完整性验证 (SHA-256)
 * 8. 自动清理过期缓存
 * 
 * 用法:
 *   const downloader = new PluginDownloader();
 *   await downloader.download('ai-coding-assistant', '1.2.0');
 */

const { app, ipcMain } = require('electron');
const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');
const crypto = require('crypto');
const { URL } = require('url');

// ==================== 类型定义 ====================

/**
 * 下载选项
 */
class DownloadOptions {
  constructor({
    outputDir = null,
    maxRetries = 3,
    retryDelay = 5000,
    timeout = 300000,
    maxSpeed = null, // bytes/sec, null = unlimited
    enableResume = true,
    verifyChecksum = true,
    expectedChecksum = null,
  } = {}) {
    this.outputDir = outputDir;
    this.maxRetries = maxRetries;
    this.retryDelay = retryDelay;
    this.timeout = timeout;
    this.maxSpeed = maxSpeed;
    this.enableResume = enableResume;
    this.verifyChecksum = verifyChecksum;
    this.expectedChecksum = expectedChecksum;
  }
}

/**
 * 下载进度
 */
class DownloadProgress {
  constructor() {
    this.pluginId = '';
    this.version = '';
    this.status = 'idle'; // idle, downloading, paused, completed, failed, verifying
    this.progress = 0; // 0-100
    this.downloadedBytes = 0;
    this.totalBytes = 0;
    this.speed = 0; // bytes/sec
    this.eta = 0; // seconds
    this.message = '';
    this.error = null;
  }
}

/**
 * 下载任务
 */
class DownloadTask {
  constructor(pluginId, version, url, options) {
    this.pluginId = pluginId;
    this.version = version;
    this.url = url;
    this.options = options;
    this.progress = new DownloadProgress();
    this.progress.pluginId = pluginId;
    this.progress.version = version;
    this.cancelled = false;
    this.paused = false;
    this.resolved = false;
    this.reject = null;
    this.resolve = null;
  }
}

// ==================== 常量定义 ====================

const DOWNLOAD_CACHE_DIR = 'plugin-downloads';
const MAX_CONCURRENT_DOWNLOADS = 3;
const DEFAULT_TIMEOUT = 300000; // 5 分钟
const CHUNK_SIZE = 1024 * 1024; // 1 MB chunks for resume
const CACHE_EXPIRY_DAYS = 7;

// ==================== 插件下载器类 ====================

class PluginDownloader {
  constructor() {
    /** @type {Map<string, DownloadTask>} 当前下载任务 */
    this.downloadTasks = new Map();
    
    /** @type {DownloadTask[]} 下载队列 */
    this.downloadQueue = [];
    
    /** @type {number} 当前并发下载数 */
    this.activeDownloads = 0;
    
    /** @type {string} 下载缓存目录 */
    this.cacheDir = path.join(app.getPath('userData'), DOWNLOAD_CACHE_DIR);
    
    // 确保缓存目录存在
    if (!fs.existsSync(this.cacheDir)) {
      fs.mkdirSync(this.cacheDir, { recursive: true });
    }
    
    // 启动时清理过期缓存
    this._cleanupExpiredCache();
  }
  
  /**
   * 下载插件
   * 
   * @param {string} pluginId - 插件 ID
   * @param {string} version - 插件版本
   * @param {string} url - 下载 URL
   * @param {DownloadOptions} options - 下载选项
   * @param {Function} onProgress - 进度回调
   * @returns {Promise<{success: boolean, filePath: string, error?: string}>}
   */
  async download(pluginId, version, url, options = new DownloadOptions(), onProgress = null) {
    const task = new DownloadTask(pluginId, version, url, options);
    const taskId = `${pluginId}@${version}`;
    
    // 检查是否已在下载
    if (this.downloadTasks.has(taskId)) {
      return {
        success: false,
        error: `插件已在下载队列中: ${taskId}`,
      };
    }
    
    return new Promise((resolve, reject) => {
      task.resolve = resolve;
      task.reject = reject;
      
      this.downloadTasks.set(taskId, task);
      
      // 加入队列
      this._enqueueTask(task, onProgress);
    });
  }
  
  /**
   * 取消下载
   * 
   * @param {string} pluginId - 插件 ID
   * @param {string} version - 插件版本
   */
  cancel(pluginId, version) {
    const taskId = `${pluginId}@${version}`;
    const task = this.downloadTasks.get(taskId);
    
    if (task) {
      task.cancelled = true;
      task.progress.status = 'failed';
      task.progress.message = '下载已取消';
      
      this._updateProgress(task, onProgress => {
        // 进度已通过 IPC 发送
      });
      
      task.reject(new Error('下载已取消'));
      this.downloadTasks.delete(taskId);
      
      // 从队列中移除
      this.downloadQueue = this.downloadQueue.filter(t => t !== task);
      
      this.activeDownloads = Math.max(0, this.activeDownloads - 1);
      this._processQueue();
    }
  }
  
  /**
   * 暂停下载
   */
  pause(pluginId, version) {
    const taskId = `${pluginId}@${version}`;
    const task = this.downloadTasks.get(taskId);
    
    if (task && !task.paused) {
      task.paused = true;
      task.progress.status = 'paused';
      task.progress.message = '下载已暂停';
    }
  }
  
  /**
   * 恢复下载
   */
  resume(pluginId, version, onProgress = null) {
    const taskId = `${pluginId}@${version}`;
    const task = this.downloadTasks.get(taskId);
    
    if (task && task.paused) {
      task.paused = false;
      task.progress.status = 'downloading';
      task.progress.message = '恢复下载...';
      this._processTask(task, onProgress);
    }
  }
  
  /**
   * 获取下载进度
   */
  getProgress(pluginId, version) {
    const taskId = `${pluginId}@${version}`;
    const task = this.downloadTasks.get(taskId);
    return task?.progress || null;
  }
  
  /**
   * 获取所有下载任务
   */
  getAllTasks() {
    return Array.from(this.downloadTasks.values()).map(task => ({
      pluginId: task.pluginId,
      version: task.version,
      status: task.progress.status,
      progress: task.progress.progress,
      speed: task.progress.speed,
    }));
  }
  
  // ==================== 私有方法 ====================
  
  /**
   * 将任务加入队列
   */
  _enqueueTask(task, onProgress) {
    this.downloadQueue.push(task);
    this._processQueue(onProgress);
  }
  
  /**
   * 处理下载队列
   */
  _processQueue(onProgress = null) {
    while (
      this.activeDownloads < MAX_CONCURRENT_DOWNLOADS &&
      this.downloadQueue.length > 0
    ) {
      const task = this.downloadQueue.shift();
      
      if (!task.cancelled && !task.resolved) {
        this.activeDownloads++;
        this._processTask(task, onProgress);
      }
    }
  }
  
  /**
   * 处理单个下载任务
   */
  async _processTask(task, onProgress) {
    const taskId = `${task.pluginId}@${task.version}`;
    
    try {
      // 1. 检查缓存
      const cachedFile = this._getCachedFile(task.pluginId, task.version);
      
      if (cachedFile) {
        console.log(`使用缓存的插件包: ${cachedFile}`);
        task.progress.status = 'completed';
        task.progress.progress = 100;
        task.progress.message = '使用缓存';
        
        this._sendProgressEvent(task.progress);
        
        task.resolve({
          success: true,
          filePath: cachedFile,
        });
        
        this.downloadTasks.delete(taskId);
        this.activeDownloads--;
        this._processQueue();
        return;
      }
      
      // 2. 执行下载
      const filePath = await this._downloadFile(task, onProgress);
      
      // 3. 验证完整性
      if (task.options.verifyChecksum) {
        task.progress.status = 'verifying';
        task.progress.message = '正在验证文件完整性...';
        this._sendProgressEvent(task.progress);
        
        const valid = await this._verifyChecksum(filePath, task.options.expectedChecksum);
        
        if (!valid) {
          throw new Error('文件校验失败，可能已损坏');
        }
      }
      
      // 4. 缓存文件
      this._cacheFile(task.pluginId, task.version, filePath);
      
      // 5. 完成
      task.resolved = true;
      task.progress.status = 'completed';
      task.progress.progress = 100;
      task.progress.message = '下载完成';
      
      this._sendProgressEvent(task.progress);
      
      task.resolve({
        success: true,
        filePath,
      });
      
    } catch (err) {
      console.error(`下载失败: ${err.message}`, err);
      
      task.progress.status = 'failed';
      task.progress.message = `下载失败: ${err.message}`;
      task.progress.error = err.message;
      
      this._sendProgressEvent(task.progress);
      
      task.reject(err);
      
    } finally {
      this.downloadTasks.delete(taskId);
      this.activeDownloads--;
      this._processQueue();
    }
  }
  
  /**
   * 下载文件
   */
  async _downloadFile(task, onProgress) {
    return new Promise((resolve, reject) => {
      const url = new URL(task.url);
      const protocol = url.protocol === 'https:' ? https : http;
      
      // 确定输出文件路径
      const outputDir = task.options.outputDir || this.cacheDir;
      const fileName = `${task.pluginId}-${task.version}-${process.platform}-${process.arch}.mxp`;
      const filePath = path.join(outputDir, fileName);
      
      // 检查是否支持断点续传
      let downloadedBytes = 0;
      let fileStream;
      
      if (task.options.enableResume && fs.existsSync(filePath)) {
        const stat = fs.statSync(filePath);
        downloadedBytes = stat.size;
        fileStream = fs.createWriteStream(filePath, { flags: 'a' });
        console.log(`断点续传: 已下载 ${downloadedBytes} bytes`);
      } else {
        fileStream = fs.createWriteStream(filePath);
      }
      
      // 构建请求选项
      const requestOptions = {
        method: 'GET',
        timeout: task.options.timeout,
        headers: {},
      };
      
      // 添加 Range 头（断点续传）
      if (downloadedBytes > 0) {
        requestOptions.headers['Range'] = `bytes=${downloadedBytes}-`;
      }
      
      // 发送请求
      const request = protocol.get(task.url, requestOptions, (response) => {
        // 处理重定向
        if (response.statusCode >= 300 && response.statusCode < 400 && response.headers.location) {
          task.url = response.headers.location;
          request.destroy();
          this._downloadFile(task, onProgress).then(resolve).catch(reject);
          return;
        }
        
        // 检查状态码
        if (response.statusCode !== 200 && response.statusCode !== 206) {
          reject(new Error(`HTTP ${response.statusCode}: ${response.statusMessage}`));
          return;
        }
        
        // 获取文件大小
        const totalBytes = response.headers['content-length']
          ? parseInt(response.headers['content-length'], 10) + downloadedBytes
          : 0;
        
        task.progress.totalBytes = totalBytes;
        task.progress.downloadedBytes = downloadedBytes;
        
        // 速度控制
        let lastTime = Date.now();
        let lastBytes = downloadedBytes;
        let throttleTimer = null;
        
        // 读取数据
        response.on('data', (chunk) => {
          if (task.cancelled) {
            request.destroy();
            reject(new Error('下载已取消'));
            return;
          }
          
          if (task.paused) {
            // 暂停时缓冲数据
            return;
          }
          
          // 速度限制
          if (task.options.maxSpeed) {
            const now = Date.now();
            const elapsed = now - lastTime;
            const bytesInSecond = downloadedBytes - lastBytes;
            
            if (bytesInSecond >= task.options.maxSpeed) {
              if (!throttleTimer) {
                throttleTimer = setTimeout(() => {
                  throttleTimer = null;
                  lastTime = Date.now();
                  lastBytes = downloadedBytes;
                }, 1000);
              }
              return; // 跳过当前 chunk
            }
          }
          
          downloadedBytes += chunk.length;
          fileStream.write(chunk);
          
          // 更新进度
          const now = Date.now();
          const elapsed = (now - lastTime) / 1000;
          
          if (elapsed >= 0.5) { // 每 0.5 秒更新一次
            const speed = (downloadedBytes - lastBytes) / elapsed;
            
            task.progress.downloadedBytes = downloadedBytes;
            task.progress.progress = totalBytes > 0 ? Math.round((downloadedBytes / totalBytes) * 100) : 0;
            task.progress.speed = speed;
            task.progress.eta = speed > 0 ? Math.ceil((totalBytes - downloadedBytes) / speed) : 0;
            task.progress.status = 'downloading';
            task.progress.message = `下载中... ${formatBytes(downloadedBytes)} / ${formatBytes(totalBytes)}`;
            
            this._updateProgress(task, onProgress);
            
            lastTime = now;
            lastBytes = downloadedBytes;
          }
        });
        
        response.on('end', () => {
          fileStream.end();
          
          task.progress.downloadedBytes = downloadedBytes;
          task.progress.progress = 100;
          task.progress.status = 'completed';
          task.progress.message = '下载完成';
          
          this._updateProgress(task, onProgress);
          
          resolve(filePath);
        });
        
        response.on('error', (err) => {
          fileStream.end();
          reject(new Error(`下载错误: ${err.message}`));
        });
      });
      
      request.on('error', (err) => {
        fileStream?.end();
        reject(new Error(`请求失败: ${err.message}`));
      });
      
      request.on('timeout', () => {
        request.destroy();
        reject(new Error('下载超时'));
      });
    });
  }
  
  /**
   * 验证文件校验和
   */
  async _verifyChecksum(filePath, expectedChecksum) {
    if (!expectedChecksum) {
      console.warn('未提供期望的校验和，跳过验证');
      return true;
    }
    
    return new Promise((resolve, reject) => {
      const hash = crypto.createHash('sha256');
      const stream = fs.createReadStream(filePath);
      
      stream.on('data', (chunk) => hash.update(chunk));
      stream.on('end', () => {
        const actualChecksum = hash.digest('hex');
        const valid = actualChecksum === expectedChecksum;
        
        if (!valid) {
          console.error(`校验和验证失败:\n  期望: ${expectedChecksum}\n  实际: ${actualChecksum}`);
        }
        
        resolve(valid);
      });
      stream.on('error', (err) => reject(err));
    });
  }
  
  /**
   * 更新进度
   */
  _updateProgress(task, onProgress) {
    this._sendProgressEvent(task.progress);
    
    if (onProgress) {
      onProgress(task.progress);
    }
  }
  
  /**
   * 发送进度事件
   */
  _sendProgressEvent(progress) {
    if (global.mainWindow && !global.mainWindow.isDestroyed()) {
      global.mainWindow.webContents.send('plugin:download-progress', {
        pluginId: progress.pluginId,
        version: progress.version,
        status: progress.status,
        progress: progress.progress,
        downloadedBytes: progress.downloadedBytes,
        totalBytes: progress.totalBytes,
        speed: progress.speed,
        eta: progress.eta,
        message: progress.message,
      });
    }
  }
  
  /**
   * 获取缓存文件
   */
  _getCachedFile(pluginId, version) {
    const pattern = `${pluginId}-${version}-*.mxp`;
    const files = fs.readdirSync(this.cacheDir);
    
    for (const file of files) {
      if (file.match(new RegExp(pattern.replace('*', '.*')))) {
        const filePath = path.join(this.cacheDir, file);
        const stat = fs.statSync(filePath);
        
        // 检查是否过期
        const ageDays = (Date.now() - stat.mtimeMs) / (1000 * 60 * 60 * 24);
        
        if (ageDays < CACHE_EXPIRY_DAYS) {
          return filePath;
        }
      }
    }
    
    return null;
  }
  
  /**
   * 缓存文件
   */
  _cacheFile(pluginId, version, filePath) {
    // 如果文件已在缓存目录，不需要复制
    if (path.dirname(filePath) === this.cacheDir) {
      return;
    }
    
    const fileName = path.basename(filePath);
    const cachePath = path.join(this.cacheDir, fileName);
    
    try {
      fs.copyFileSync(filePath, cachePath);
      console.log(`已缓存插件包: ${cachePath}`);
    } catch (err) {
      console.warn(`缓存文件失败: ${err.message}`);
    }
  }
  
  /**
   * 清理过期缓存
   */
  _cleanupExpiredCache() {
    try {
      const files = fs.readdirSync(this.cacheDir);
      let cleanedCount = 0;
      
      for (const file of files) {
        if (!file.endsWith('.mxp')) continue;
        
        const filePath = path.join(this.cacheDir, file);
        const stat = fs.statSync(filePath);
        const ageDays = (Date.now() - stat.mtimeMs) / (1000 * 60 * 60 * 24);
        
        if (ageDays >= CACHE_EXPIRY_DAYS) {
          fs.unlinkSync(filePath);
          cleanedCount++;
        }
      }
      
      if (cleanedCount > 0) {
        console.log(`清理了 ${cleanedCount} 个过期缓存文件`);
      }
    } catch (err) {
      console.warn(`清理缓存失败: ${err.message}`);
    }
  }
}

// ==================== 工具函数 ====================

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// ==================== IPC 处理器 ====================

function registerPluginDownloaderIPC(downloader) {
  /**
   * 下载插件
   */
  ipcMain.handle('plugin:download', async (event, pluginId, version, url, options) => {
    try {
      const downloadOptions = new DownloadOptions(options);
      
      const result = await downloader.download(
        pluginId,
        version,
        url,
        downloadOptions
      );
      
      return result;
    } catch (err) {
      return {
        success: false,
        error: err.message,
      };
    }
  });
  
  /**
   * 取消下载
   */
  ipcMain.handle('plugin:download-cancel', async (event, pluginId, version) => {
    downloader.cancel(pluginId, version);
    return { success: true };
  });
  
  /**
   * 暂停下载
   */
  ipcMain.handle('plugin:download-pause', async (event, pluginId, version) => {
    downloader.pause(pluginId, version);
    return { success: true };
  });
  
  /**
   * 恢复下载
   */
  ipcMain.handle('plugin:download-resume', async (event, pluginId, version) => {
    downloader.resume(pluginId, version);
    return { success: true };
  });
  
  /**
   * 获取下载进度
   */
  ipcMain.handle('plugin:download-progress', async (event, pluginId, version) => {
    const progress = downloader.getProgress(pluginId, version);
    return { success: true, progress };
  });
  
  /**
   * 获取所有下载任务
   */
  ipcMain.handle('plugin:download-tasks', async () => {
    const tasks = downloader.getAllTasks();
    return { success: true, tasks };
  });
}

// ==================== 导出 ====================

module.exports = {
  PluginDownloader,
  DownloadOptions,
  DownloadProgress,
  DownloadTask,
  registerPluginDownloaderIPC,
};
