/**
 * MatuX 设备能力评估引擎
 *
 * 职责：
 * 1. 硬件能力检测（CPU / 内存 / GPU / 存储 / 外设 / 网络 / 显示器）
 * 2. 软件环境检测（Python / Docker / Redis / CLI 工具）
 * 3. 设备评级算法（Basic / Standard / Advanced / Professional）
 * 4. 评估报告持久化
 */

const os = require('os');
const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');
const { app } = require('electron');

// ==================== 常量 ====================

const DEVICE_PROFILE_FILE = path.join(
  app.getPath('userData'),
  'device-profile.json'
);

/**
 * 设备评级枚举
 */
const DeviceClass = {
  BASIC: 'basic',
  STANDARD: 'standard',
  ADVANCED: 'advanced',
  PROFESSIONAL: 'professional',
};

/**
 * 各评级所需的最低硬件阈值
 */
const DEVICE_THRESHOLDS = {
  [DeviceClass.BASIC]: {
    minMemoryMB: 4096,
    minCores: 2,
    minStorageGB: 10,
    minBandwidthMbps: 1,
    requireGPU: false,
    requireDedicatedGPU: false,
    minVRAM_MB: 0,
    requireCUDA: false,
    requireCamera: false,
    requireDocker: false,
  },
  [DeviceClass.STANDARD]: {
    minMemoryMB: 8192,
    minCores: 4,
    minStorageGB: 20,
    minBandwidthMbps: 5,
    requireGPU: false,
    requireDedicatedGPU: false,
    minVRAM_MB: 0,
    requireCUDA: false,
    requireCamera: false,
    requireDocker: false,
  },
  [DeviceClass.ADVANCED]: {
    minMemoryMB: 16384,
    minCores: 6,
    minStorageGB: 50,
    minBandwidthMbps: 10,
    requireGPU: true,
    requireDedicatedGPU: true,
    minVRAM_MB: 2048,
    requireCUDA: false,
    requireCamera: false,
    requireDocker: false,
  },
  [DeviceClass.PROFESSIONAL]: {
    minMemoryMB: 32768,
    minCores: 8,
    minStorageGB: 100,
    minBandwidthMbps: 50,
    requireGPU: true,
    requireDedicatedGPU: true,
    minVRAM_MB: 6144,
    requireCUDA: true,
    requireCamera: false,
    requireDocker: false,
  },
};

// ==================== 硬件检测 ====================

/**
 * 检测 CPU 信息
 * @returns {{ arch: string, cores: number, model: string, benchmarkScore: number }}
 */
function detectCPU() {
  const cpus = os.cpus();
  const model = cpus.length > 0 ? cpus[0].model.trim() : 'Unknown';
  const cores = cpus.length;
  const arch = process.arch; // x64, arm64

  // 内部基准分 (0~1000)
  // 基于核心数 × 单核频率估算
  const avgSpeedMHz = cpus.reduce((sum, c) => sum + c.speed, 0) / cores;
  const benchmarkScore = Math.min(
    1000,
    Math.round(cores * avgSpeedMHz * 0.12)
  );

  return { arch, cores, model, benchmarkScore };
}

/**
 * 检测内存信息
 * @returns {{ totalMB: number, availableMB: number }}
 */
function detectMemory() {
  const totalBytes = os.totalmem();
  const freeBytes = os.freemem();
  return {
    totalMB: Math.round(totalBytes / (1024 * 1024)),
    availableMB: Math.round(freeBytes / (1024 * 1024)),
  };
}

/**
 * 检测 GPU 信息
 * 通过 Electron app.getGPUInfo() 获取
 * @returns {Promise<{hasDedicatedGPU: boolean, gpuName: string, vramMB: number, supportsWebGL2: boolean, supportsWebGPU: boolean, supportsCUDA: boolean, supportsOpenCL: boolean}>}
 */
async function detectGPU() {
  const result = {
    hasDedicatedGPU: false,
    gpuName: 'Unknown',
    vramMB: 0,
    supportsWebGL2: false,
    supportsWebGPU: false,
    supportsCUDA: false,
    supportsOpenCL: false,
  };

  try {
    // Electron API 获取 GPU 信息
    const gpuInfo = await app.getGPUInfo('complete');
    const devices = gpuInfo?.gpuDevice || gpuInfo?.auxAttributes || [];

    if (Array.isArray(devices) && devices.length > 0) {
      // 查找独显（通常 deviceName 包含 NVIDIA/AMD）
      for (const dev of devices) {
        const name = dev.deviceString || dev.deviceName || dev.vendorString || '';
        if (
          name.match(/nvidia|amd|radeon|geforce|rtx|gtx|rx\s?\d{4}/i) &&
          !name.match(/intel|uhd|iris|hd graphics/i)
        ) {
          result.hasDedicatedGPU = true;
          result.gpuName = name;
          break;
        }
      }

      // 如果没有独显，取第一个 GPU
      if (!result.hasDedicatedGPU && devices.length > 0) {
        const first = devices[0];
        result.gpuName =
          first.deviceString || first.deviceName || first.vendorString || 'Unknown';
      }

      // VRAM 估算 (driverInfo 中可能有)
      if (gpuInfo?.auxAttributes?.adapterRam) {
        result.vramMB = Math.round(gpuInfo.auxAttributes.adapterRam / (1024 * 1024));
      }
    }

    // 尝试通过 nvidia-smi 获取更精确的 GPU 信息 (Windows)
    if (process.platform === 'win32') {
      try {
        const nvidiaOutput = execSync(
          'nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>&1',
          { encoding: 'utf-8', timeout: 5000 }
        ).trim();
        if (nvidiaOutput && !nvidiaOutput.startsWith('NVIDIA-SMI')) {
          const parts = nvidiaOutput.split(',').map((s) => s.trim());
          if (parts.length >= 2) {
            result.hasDedicatedGPU = true;
            result.gpuName = parts[0];
            // memory.total 格式如 "6144 MiB"
            const vramMatch = parts[1].match(/(\d+)/);
            if (vramMatch) result.vramMB = parseInt(vramMatch[1], 10);
            result.supportsCUDA = true;
          }
        }
      } catch {
        // nvidia-smi 不可用
      }
    }
  } catch (err) {
    console.warn('[WARN] GPU 检测失败:', err.message);
  }

  // WebGL2/WebGPU 支持判断 (基于 GPU 型号推断)
  // 精确判断需要在渲染进程中执行，这里做保守估计
  result.supportsWebGL2 = true; // 现代 GPU 基本都支持
  result.supportsWebGPU = result.hasDedicatedGPU; // WebGPU 需要较新 GPU

  // OpenCL：NVIDIA 和 AMD 独显通常支持
  result.supportsOpenCL = result.hasDedicatedGPU;

  return result;
}

/**
 * 检测存储信息
 * @returns {{ totalGB: number, freeGB: number, type: 'hdd' | 'ssd' }}
 */
function detectStorage() {
  const result = { totalGB: 0, freeGB: 0, type: 'ssd' };

  try {
    if (process.platform === 'win32') {
      // 使用 wmic 获取系统盘信息
      const output = execSync(
        'wmic logicaldisk where "DeviceID=\'C:\'" get Size,FreeSpace,MediaType /format:csv 2>&1',
        { encoding: 'utf-8', timeout: 10000 }
      ).trim();

      const lines = output.split('\n').filter((l) => l.trim());
      if (lines.length >= 2) {
        const parts = lines[lines.length - 1].split(',').map((s) => s.trim());
        // CSV 格式: Node,DeviceID,FreeSpace,MediaType,Size
        // 不同系统列顺序可能不同，尝试解析
        for (const part of parts) {
          const num = parseInt(part, 10);
          if (!isNaN(num) && num > 1e10) {
            // 大于 10GB 的数值
            if (result.totalGB === 0) {
              result.totalGB = Math.round(num / (1024 * 1024 * 1024));
            } else if (result.freeGB === 0) {
              result.freeGB = Math.round(num / (1024 * 1024 * 1024));
            }
          }
        }

        // 修正：确保 freeGB <= totalGB
        if (result.freeGB > result.totalGB) {
          [result.totalGB, result.freeGB] = [result.freeGB, result.totalGB];
        }

        // 推断 SSD/HDD（通过 MediaType 或读写速度）
        const mediaStr = output.toLowerCase();
        if (mediaStr.includes('ssd') || mediaStr.includes('solid state')) {
          result.type = 'ssd';
        } else if (mediaStr.includes('hdd') || mediaStr.includes('hard disk')) {
          result.type = 'hdd';
        } else {
          // 通过简单读写速度推断
          result.type = inferDiskType();
        }
      }
    } else {
      // Linux/macOS: 使用 df
      const output = execSync("df -BG / | tail -1", {
        encoding: 'utf-8',
        timeout: 5000,
      }).trim();
      const parts = output.split(/\s+/);
      if (parts.length >= 4) {
        result.totalGB = parseInt(parts[1], 10) || 0;
        result.freeGB = parseInt(parts[3], 10) || 0;
      }
    }
  } catch (err) {
    console.warn('[WARN] 存储检测失败:', err.message);
    // 兜底：至少报告可用空间
    try {
      const stats = fs.statfsSync
        ? fs.statfsSync(app.getPath('userData'))
        : null;
      if (stats) {
        result.freeGB = Math.round(
          (stats.bfree * stats.bsize) / (1024 * 1024 * 1024)
        );
        result.totalGB = Math.round(
          (stats.blocks * stats.bsize) / (1024 * 1024 * 1024)
        );
      }
    } catch { /* ignore */ }
  }

  return result;
}

/**
 * 通过简单读写测试推断磁盘类型
 * @returns {'hdd' | 'ssd'}
 */
function inferDiskType() {
  const testFile = path.join(app.getPath('temp'), 'matu-disk-test.tmp');
  const data = Buffer.alloc(4 * 1024 * 1024); // 4MB

  try {
    const start = process.hrtime.bigint();
    fs.writeFileSync(testFile, data);
    fs.readFileSync(testFile);
    fs.unlinkSync(testFile);
    const elapsed = Number(process.hrtime.bigint() - start) / 1e6; // ms

    // SSD 通常 < 50ms 完成 4MB 读写, HDD > 100ms
    return elapsed < 80 ? 'ssd' : 'hdd';
  } catch {
    return 'ssd'; // 默认假设 SSD
  }
}

/**
 * 检测外设（摄像头/麦克风/USB/手柄）
 * 注意：精确检测需要在渲染进程中执行，这里做基础检测
 * @returns {{ hasCamera: boolean, hasMicrophone: boolean, hasUSBDevices: boolean, hasGamepad: boolean }}
 */
function detectPeripherals() {
  const result = {
    hasCamera: false,
    hasMicrophone: false,
    hasUSBDevices: false,
    hasGamepad: false,
  };

  if (process.platform === 'win32') {
    try {
      // 检查摄像头设备
      const cameraOutput = execSync(
        'powershell -Command "Get-PnpDevice -Class Camera -Status OK | Select-Object -Property FriendlyName | Format-List" 2>&1',
        { encoding: 'utf-8', timeout: 8000 }
      );
      result.hasCamera =
        cameraOutput.includes('FriendlyName') &&
        !cameraOutput.includes('No devices');

      // 检查音频输入设备
      const audioOutput = execSync(
        'powershell -Command "Get-PnpDevice -Class AudioEndpoint -Status OK | Where-Object { $_.FriendlyName -match \'mic|microphone|麦\' } | Select-Object FriendlyName | Format-List" 2>&1',
        { encoding: 'utf-8', timeout: 8000 }
      );
      result.hasMicrophone = audioOutput.includes('FriendlyName');

      // 检查 USB 设备（非集线器）
      const usbOutput = execSync(
        'powershell -Command "Get-PnpDevice -Class USB -Status OK | Where-Object { $_.FriendlyName -notmatch \'Hub|Root|Controller\' } | Measure-Object | Select-Object Count" 2>&1',
        { encoding: 'utf-8', timeout: 8000 }
      );
      const usbCount = parseInt(
        (usbOutput.match(/Count\s*:\s*(\d+)/) || [])[1] || '0',
        10
      );
      result.hasUSBDevices = usbCount > 0;
    } catch (err) {
      console.warn('[WARN] 外设检测失败:', err.message);
    }
  }

  return result;
}

/**
 * 检测网络信息
 * @returns {{ type: string, bandwidthMbps: number, isMetered: boolean }}
 */
function detectNetwork() {
  const result = {
    type: 'ethernet',
    bandwidthMbps: 100,
    isMetered: false,
  };

  if (process.platform === 'win32') {
    try {
      // 检查网络连接类型
      const netOutput = execSync(
        'powershell -Command "Get-NetConnectionProfile | Select-Object -First 1 Name,NetworkCategory | Format-List" 2>&1',
        { encoding: 'utf-8', timeout: 8000 }
      );

      if (netOutput.toLowerCase().includes('wi-fi') || netOutput.toLowerCase().includes('wireless')) {
        result.type = 'wifi';
      }

      // 计量网络检测
      const meteredOutput = execSync(
        'powershell -Command "[Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime] | Out-Null; $profile = [Windows.Networking.Connectivity.NetworkInformation]::GetInternetConnectionProfile(); if ($profile) { $cost = $profile.GetConnectionCost(); Write-Output $cost.NetworkCostType } 2>&1"',
        { encoding: 'utf-8', timeout: 8000 }
      );
      result.isMetered =
        meteredOutput.includes('Fixed') || meteredOutput.includes('Variable');
    } catch {
      // 无法检测时使用默认值
    }
  }

  return result;
}

/**
 * 检测显示器信息
 * @returns {{ resolution: { width: number, height: number }, pixelRatio: number, refreshRateHz: number }}
 */
function detectDisplay() {
  const { screen: electronScreen } = require('electron');
  const primaryDisplay = electronScreen.getPrimaryDisplay();

  return {
    resolution: {
      width: primaryDisplay.size.width,
      height: primaryDisplay.size.height,
    },
    pixelRatio: primaryDisplay.scaleFactor || 1,
    refreshRateHz: primaryDisplay.displayFrequency || 60,
  };
}

// ==================== 软件环境检测 ====================

/**
 * 检测 Docker 环境
 * @returns {{ dockerInstalled: boolean, dockerRunning: boolean, dockerVersion: string }}
 */
function detectDocker() {
  const result = {
    dockerInstalled: false,
    dockerRunning: false,
    dockerVersion: '',
  };

  try {
    const versionOutput = execSync('docker --version 2>&1', {
      encoding: 'utf-8',
      timeout: 5000,
    }).trim();
    const versionMatch = versionOutput.match(/(\d+\.\d+\.\d+)/);
    if (versionMatch) {
      result.dockerInstalled = true;
      result.dockerVersion = versionMatch[1];

      // 检查 Docker 是否正在运行
      try {
        execSync('docker info 2>&1', {
          encoding: 'utf-8',
          timeout: 8000,
        });
        result.dockerRunning = true;
      } catch {
        result.dockerRunning = false;
      }
    }
  } catch {
    // Docker 未安装
  }

  return result;
}

/**
 * 检测 K8s CLI (kubectl)
 * @returns {boolean}
 */
function detectKubectl() {
  try {
    execSync('kubectl version --client 2>&1', {
      encoding: 'utf-8',
      timeout: 5000,
    });
    return true;
  } catch {
    return false;
  }
}

/**
 * 检测硬件开发工具
 * @returns {{ arduinoCliInstalled: boolean, platformioInstalled: boolean, edgeImpulseCli: boolean }}
 */
function detectHardwareTools() {
  const result = {
    arduinoCliInstalled: false,
    platformioInstalled: false,
    edgeImpulseCli: false,
  };

  // Arduino CLI
  try {
    execSync('arduino-cli version 2>&1', { encoding: 'utf-8', timeout: 5000 });
    result.arduinoCliInstalled = true;
  } catch { /* not installed */ }

  // PlatformIO
  try {
    execSync('platformio --version 2>&1', { encoding: 'utf-8', timeout: 5000 });
    result.platformioInstalled = true;
  } catch { /* not installed */ }

  // Edge Impulse CLI
  try {
    execSync('edge-impulse-deploy --version 2>&1', {
      encoding: 'utf-8',
      timeout: 5000,
    });
    result.edgeImpulseCli = true;
  } catch { /* not installed */ }

  return result;
}

/**
 * 检测外部服务可用性（Redis / Neo4j / Hyperledger / Vircadia）
 * 通过端口探测
 * @returns {{ redisAvailable: boolean, neo4jAvailable: boolean, hyperledgerAvailable: boolean, vircadiaAvailable: boolean }}
 */
function detectExternalServices() {
  const net = require('net');

  /**
   * 检查 TCP 端口是否可达
   * @param {string} host
   * @param {number} port
   * @param {number} timeout
   * @returns {Promise<boolean>}
   */
  function checkPort(host, port, timeout = 2000) {
    return new Promise((resolve) => {
      const socket = new net.Socket();
      socket.setTimeout(timeout);
      socket.on('connect', () => {
        socket.destroy();
        resolve(true);
      });
      socket.on('timeout', () => {
        socket.destroy();
        resolve(false);
      });
      socket.on('error', () => {
        resolve(false);
      });
      socket.connect(port, host);
    });
  }

  return Promise.all([
    checkPort('localhost', 6379), // Redis
    checkPort('localhost', 7687), // Neo4j Bolt
    checkPort('localhost', 7051), // Hyperledger Peer
    checkPort('localhost', 443),  // Vircadia (default HTTPS)
  ]).then(([redis, neo4j, hyperledger, vircadia]) => ({
    redisAvailable: redis,
    neo4jAvailable: neo4j,
    hyperledgerAvailable: hyperledger,
    vircadiaAvailable: vircadia,
  }));
}

/**
 * 检测 Python 环境（复用 main.js 中的检测逻辑简化版）
 * @returns {{ pythonVersion: string, pythonPath: string, nodeVersion: string }}
 */
function detectRuntime() {
  const result = {
    pythonVersion: '',
    pythonPath: '',
    nodeVersion: process.version, // 内嵌 Node.js 版本
  };

  const candidates =
    process.platform === 'win32'
      ? ['python', 'python3', 'py', 'py -3']
      : ['python3', 'python'];

  for (const cmd of candidates) {
    try {
      const output = execSync(`"${cmd}" --version 2>&1`, {
        encoding: 'utf-8',
        timeout: 5000,
      }).trim();
      const match = output.match(/Python\s+(\d+\.\d+(?:\.\d+)?)/);
      if (match) {
        result.pythonVersion = match[1];
        result.pythonPath = cmd;
        break;
      }
    } catch { /* try next */ }
  }

  return result;
}

// ==================== 评级算法 ====================

/**
 * 计算各维度评分 (0~100)
 * @param {object} hardware - HardwareProfile
 * @param {object} software - SoftwareProfile
 * @returns {object}
 */
function calculateScores(hardware, software) {
  const { cpu, memory, gpu, storage } = hardware;

  // CPU 评分: 基于核心数和基准分
  const cpuScore = Math.min(100, Math.round((cpu.benchmarkScore / 1000) * 100));

  // 内存评分: 4GB=20, 8GB=40, 16GB=70, 32GB=90, 64GB+=100
  const memGB = memory.totalMB / 1024;
  let memoryScore;
  if (memGB >= 64) memoryScore = 100;
  else if (memGB >= 32) memoryScore = 90;
  else if (memGB >= 16) memoryScore = 70;
  else if (memGB >= 8) memoryScore = 40;
  else if (memGB >= 4) memoryScore = 20;
  else memoryScore = 5;

  // GPU 评分
  let gpuScore = 0;
  if (gpu.hasDedicatedGPU) {
    if (gpu.vramMB >= 8192) gpuScore = 100;
    else if (gpu.vramMB >= 6144) gpuScore = 85;
    else if (gpu.vramMB >= 4096) gpuScore = 70;
    else if (gpu.vramMB >= 2048) gpuScore = 50;
    else gpuScore = 30;
    if (gpu.supportsCUDA) gpuScore = Math.min(100, gpuScore + 10);
  } else {
    gpuScore = 10; // 集成显卡
  }

  // 存储评分: 容量 + 速度
  let storageScore = 0;
  if (storage.freeGB >= 100) storageScore = 60;
  else if (storage.freeGB >= 50) storageScore = 45;
  else if (storage.freeGB >= 20) storageScore = 30;
  else if (storage.freeGB >= 10) storageScore = 15;
  else storageScore = 5;
  if (storage.type === 'ssd') storageScore += 30;
  storageScore = Math.min(100, storageScore);

  // 网络评分: 保守默认
  const networkScore = 50;

  // 外设评分
  const { peripherals } = hardware;
  let peripheralScore = 0;
  if (peripherals.hasCamera) peripheralScore += 30;
  if (peripherals.hasMicrophone) peripheralScore += 30;
  if (peripherals.hasUSBDevices) peripheralScore += 20;
  if (peripherals.hasGamepad) peripheralScore += 20;

  return {
    cpuScore,
    memoryScore,
    gpuScore,
    storageScore,
    networkScore,
    peripheralScore,
  };
}

/**
 * 基于各维度分数确定设备等级
 * @param {object} scores - calculateScores 的返回值
 * @param {object} hardware - HardwareProfile
 * @param {object} software - SoftwareProfile
 * @returns {{ deviceClass: string, score: number }}
 */
function determineDeviceClass(scores, hardware, software) {
  // 综合得分 (加权)
  const score = Math.round(
    scores.cpuScore * 0.2 +
    scores.memoryScore * 0.25 +
    scores.gpuScore * 0.25 +
    scores.storageScore * 0.15 +
    scores.networkScore * 0.05 +
    scores.peripheralScore * 0.1
  );

  // 从高到低逐级检查是否满足
  const classes = [
    DeviceClass.PROFESSIONAL,
    DeviceClass.ADVANCED,
    DeviceClass.STANDARD,
    DeviceClass.BASIC,
  ];

  for (const cls of classes) {
    const threshold = DEVICE_THRESHOLDS[cls];
    if (
      hardware.memory.totalMB >= threshold.minMemoryMB &&
      hardware.cpu.cores >= threshold.minCores &&
      hardware.storage.freeGB >= threshold.minStorageGB &&
      (!threshold.requireGPU || hardware.gpu.hasDedicatedGPU) &&
      (!threshold.requireDedicatedGPU || hardware.gpu.hasDedicatedGPU) &&
      (!threshold.minVRAM_MB || hardware.gpu.vramMB >= threshold.minVRAM_MB) &&
      (!threshold.requireCUDA || hardware.gpu.supportsCUDA)
    ) {
      return { deviceClass: cls, score };
    }
  }

  return { deviceClass: DeviceClass.BASIC, score };
}

/**
 * 生成兼容/推荐/不兼容插件层级列表
 * @param {string} deviceClass
 * @param {object} hardware
 * @param {object} software
 * @returns {{ compatiblePluginTiers: string[], recommendedPlugins: string[], incompatiblePlugins: string[], warnings: string[] }}
 */
function generatePluginCompatibility(deviceClass, hardware, software) {
  const warnings = [];
  const compatiblePluginTiers = ['tier-a']; // 所有设备都可以

  if (
    deviceClass === DeviceClass.STANDARD ||
    deviceClass === DeviceClass.ADVANCED ||
    deviceClass === DeviceClass.PROFESSIONAL
  ) {
    compatiblePluginTiers.push('tier-b');
  }
  if (
    deviceClass === DeviceClass.ADVANCED ||
    deviceClass === DeviceClass.PROFESSIONAL
  ) {
    compatiblePluginTiers.push('tier-c');
  }
  if (deviceClass === DeviceClass.PROFESSIONAL) {
    compatiblePluginTiers.push('tier-d');
  }

  // 推荐插件（基于设备能力）
  const recommendedPlugins = [];
  const incompatiblePlugins = [];

  // Tier A 通用推荐
  recommendedPlugins.push('ai-tutor', 'exam-pro', 'offline-kit');

  // 根据内存推荐
  if (hardware.memory.totalMB >= 8192) {
    recommendedPlugins.push('collab-editor', 'knowledge-graph');
  }

  // 根据 GPU 推荐
  if (hardware.gpu.hasDedicatedGPU && hardware.gpu.vramMB >= 2048) {
    recommendedPlugins.push('creativity-engine');
    if (hardware.peripherals.hasCamera) {
      recommendedPlugins.push('ar-vr-lab');
    }
  } else if (hardware.gpu.hasDedicatedGPU) {
    incompatiblePlugins.push('ar-vr-lab', 'vr-3d-editor');
    warnings.push('GPU 显存不足 2GB，AR/VR 功能不兼容');
  }

  // 根据 Docker 推荐
  if (software.containers?.dockerInstalled && software.containers?.dockerRunning) {
    recommendedPlugins.push('digital-twin', 'code-sandbox');
  } else {
    incompatiblePlugins.push('ai-sandbox');
    if (deviceClass !== DeviceClass.PROFESSIONAL) {
      incompatiblePlugins.push('digital-twin');
    }
  }

  // 根据 CUDA 推荐
  if (hardware.gpu.supportsCUDA) {
    recommendedPlugins.push('federated-learning', 'model-bench');
  } else {
    incompatiblePlugins.push('federated-learning', 'model-bench');
  }

  // 根据 USB/硬件工具推荐
  if (software.hardware_tools?.platformioInstalled) {
    recommendedPlugins.push('hardware-cert', 'tinyml-studio');
  } else {
    incompatiblePlugins.push('hardware-cert', 'tinyml-studio');
  }

  // 低内存警告
  if (hardware.memory.totalMB < 4096) {
    warnings.push('内存低于 4GB，部分功能可能运行缓慢');
  }

  // HDD 警告
  if (hardware.storage.type === 'hdd') {
    warnings.push('使用机械硬盘，模块加载速度可能较慢');
  }

  return { compatiblePluginTiers, recommendedPlugins, incompatiblePlugins, warnings };
}

// ==================== 主评估函数 ====================

/**
 * 执行完整设备评估
 * @returns {Promise<object>} 完整的 DeviceAssessment
 */
async function assessDevice() {
  console.log('[INFO] 🔍 开始设备能力评估...');
  const startTime = Date.now();

  // 1. 硬件检测
  const cpu = detectCPU();
  const memory = detectMemory();
  const gpu = await detectGPU();
  const storage = detectStorage();
  const peripherals = detectPeripherals();
  const network = detectNetwork();
  const display = detectDisplay();

  const hardware = { cpu, memory, gpu, storage, peripherals, network, display };

  // 2. 软件环境检测
  const runtime = detectRuntime();
  const containers = {
    ...detectDocker(),
    kubectlInstalled: detectKubectl(),
  };
  const hardware_tools = detectHardwareTools();
  const connectivity = await detectExternalServices();

  const software = {
    os: {
      platform: process.platform,
      version: os.release(),
      arch: process.arch,
    },
    runtime,
    containers,
    hardware_tools,
    connectivity,
  };

  // 3. 评分
  const scores = calculateScores(hardware, software);

  // 4. 评级
  const { deviceClass, score } = determineDeviceClass(scores, hardware, software);

  // 5. 兼容性分析
  const compat = generatePluginCompatibility(deviceClass, hardware, software);

  const elapsed = Date.now() - startTime;
  console.log(`[INFO] ✅ 设备评估完成 (${elapsed}ms): ${deviceClass} (${score}分)`);

  return {
    version: '1.0',
    assessedAt: new Date().toISOString(),
    assessmentDurationMs: elapsed,
    hardware,
    software,
    assessment: {
      deviceClass,
      score,
      scores,
      ...compat,
    },
    installedPlugins: [],
    pluginHistory: [],
  };
}

// ==================== 持久化 ====================

/**
 * 保存设备评估报告到文件
 * @param {object} profile - assessDevice 的返回值
 */
function saveDeviceProfile(profile) {
  try {
    fs.writeFileSync(DEVICE_PROFILE_FILE, JSON.stringify(profile, null, 2), 'utf-8');
    console.log('[INFO] 设备评估报告已保存:', DEVICE_PROFILE_FILE);
  } catch (err) {
    console.error('[ERROR] 保存设备评估报告失败:', err.message);
  }
}

/**
 * 加载已保存的设备评估报告
 * @returns {object|null}
 */
function loadDeviceProfile() {
  try {
    if (fs.existsSync(DEVICE_PROFILE_FILE)) {
      const data = fs.readFileSync(DEVICE_PROFILE_FILE, 'utf-8');
      return JSON.parse(data);
    }
  } catch (err) {
    console.warn('[WARN] 加载设备评估报告失败:', err.message);
  }
  return null;
}

/**
 * 检查是否需要重新评估（距上次评估超过 7 天）
 * @param {object} profile
 * @returns {boolean}
 */
function shouldReassess(profile) {
  if (!profile || !profile.assessedAt) return true;
  const lastAssess = new Date(profile.assessedAt).getTime();
  const sevenDays = 7 * 24 * 60 * 60 * 1000;
  return Date.now() - lastAssess > sevenDays;
}

/**
 * 更新已安装插件列表
 * @param {string[]} plugins
 */
function updateInstalledPlugins(plugins) {
  const profile = loadDeviceProfile();
  if (profile) {
    profile.installedPlugins = plugins;
    saveDeviceProfile(profile);
  }
}

// ==================== 导出 ====================

module.exports = {
  // 常量
  DeviceClass,
  DEVICE_THRESHOLDS,
  DEVICE_PROFILE_FILE,

  // 主函数
  assessDevice,

  // 持久化
  saveDeviceProfile,
  loadDeviceProfile,
  shouldReassess,
  updateInstalledPlugins,

  // 单独检测函数（用于调试/测试）
  detectCPU,
  detectMemory,
  detectGPU,
  detectStorage,
  detectPeripherals,
  detectNetwork,
  detectDisplay,
  detectDocker,
  detectKubectl,
  detectHardwareTools,
  detectExternalServices,
  detectRuntime,

  // 评级
  calculateScores,
  determineDeviceClass,
  generatePluginCompatibility,
};
