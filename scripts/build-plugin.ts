/**
 * 插件打包 CLI 工具
 * 
 * 功能:
 * 1. 验证 manifest.json 格式和内容
 * 2. 打包插件目录为 .mxp 文件
 * 3. 生成数字签名（可选）
 * 4. 验证插件包完整性
 * 
 * 用法:
 *   npm run build-plugin <plugin-dir> [options]
 *   ts-node scripts/build-plugin.ts ./plugins/ai-coding-assistant --sign --output ./dist
 * 
 * 选项:
 *   --output, -o      输出目录 (默认: ./dist)
 *   --sign, -s        生成数字签名
 *   --key, -k         私钥文件路径 (与 --sign 配合使用)
 *   --compress, -c    压缩级别 1-9 (默认: 6)
 *   --platform, -p    平台标识 (默认: all)
 *   --validate, -v    仅验证不打包
 *   --help, -h        显示帮助信息
 */

import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';
import { execSync } from 'child_process';
import { createInterface } from 'readline';

// ==================== 类型定义 ====================

interface ManifestAuthor {
  name: string;
  email: string;
  url?: string;
  organization?: string;
}

interface DeviceCompatibility {
  compatibleTiers: string[];
  minDeviceScore?: number;
  requiredHardware?: {
    minMemoryMB?: number;
    minStorageMB?: number;
    requireGPU?: boolean;
    minVRAM_MB?: number;
    requireCUDA?: boolean;
    requireDocker?: boolean;
    requireRedis?: boolean;
  };
  incompatibleWith?: string[];
}

interface EntryPoint {
  backend?: any;
  frontend?: any;
  electron?: any;
}

interface Manifest {
  manifestVersion: string;
  id: string;
  name: string;
  version: string;
  description: string;
  author: ManifestAuthor;
  license: string;
  deviceCompatibility: DeviceCompatibility;
  entryPoints: EntryPoint;
  dependencies?: any;
  permissions?: string[];
  settings?: any;
  localization?: any;
  updateInfo?: any;
  [key: string]: any;
}

interface BuildOptions {
  outputDir: string;
  sign: boolean;
  keyFile?: string;
  compressLevel: number;
  platform: string;
  validateOnly: boolean;
}

interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

// ==================== 常量定义 ====================

const VALID_TIERS = ['tier-a', 'tier-b', 'tier-c', 'tier-d'];
const VALID_CATEGORIES = [
  'ai-assistant', 'ar-vr-lab', 'coding-tools', 'data-analysis',
  'education', 'gamification', 'hardware', 'ml-training',
  'visualization', 'productivity', 'other'
];
const VALID_PERMISSIONS = [
  'filesystem:read', 'filesystem:write', 'network:external',
  'database:read', 'database:write', 'electron:ipc',
  'electron:native', 'gpu:compute', 'docker:access',
  'redis:access', 'system:info'
];
const VALID_PLATFORMS = [
  'all', 'win32-x64', 'win32-arm64',
  'darwin-x64', 'darwin-arm64', 'linux-x64'
];

const EXCLUDE_PATTERNS = [
  '.git', '.gitignore', '.vscode', '.idea',
  '__pycache__', '*.pyc', '*.pyo',
  'node_modules', '.env', '.env.*',
  '*.log', '.DS_Store', 'Thumbs.db',
  'test-results', 'coverage', 'dist', 'build',
  '*.swp', '*.swo', '*~'
];

const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500 MB
const MAX_PACKAGE_SIZE = 2 * 1024 * 1024 * 1024; // 2 GB
const MAX_MANIFEST_SIZE = 50 * 1024; // 50 KB

// ==================== 工具函数 ====================

function log(message: string, type: 'info' | 'warn' | 'error' | 'success' = 'info'): void {
  const colors = {
    info: '\x1b[36m',    // Cyan
    warn: '\x1b[33m',    // Yellow
    error: '\x1b[31m',   // Red
    success: '\x1b[32m', // Green
  };
  const reset = '\x1b[0m';
  const prefix = type === 'info' ? 'ℹ' : type === 'warn' ? '⚠' : type === 'error' ? '✗' : '✓';
  console.log(`${colors[type]}${prefix} ${message}${reset}`);
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function readManifest(pluginDir: string): Manifest | null {
  const manifestPath = path.join(pluginDir, 'manifest.json');
  
  if (!fs.existsSync(manifestPath)) {
    log('manifest.json 不存在', 'error');
    return null;
  }
  
  const stat = fs.statSync(manifestPath);
  if (stat.size > MAX_MANIFEST_SIZE) {
    log(`manifest.json 过大 (${formatBytes(stat.size)}), 最大 ${formatBytes(MAX_MANIFEST_SIZE)}`, 'error');
    return null;
  }
  
  try {
    const content = fs.readFileSync(manifestPath, 'utf-8');
    const manifest = JSON.parse(content);
    return manifest;
  } catch (err) {
    log(`manifest.json 解析失败: ${(err as Error).message}`, 'error');
    return null;
  }
}

// ==================== Manifest 验证 ====================

function validateManifest(manifest: Manifest): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  
  // 1. 必需字段检查
  const requiredFields = [
    'manifestVersion', 'id', 'name', 'version', 'description',
    'author', 'license', 'deviceCompatibility', 'entryPoints'
  ];
  
  for (const field of requiredFields) {
    if (!manifest[field]) {
      errors.push(`缺少必需字段: ${field}`);
    }
  }
  
  if (errors.length > 0) {
    return { valid: false, errors, warnings };
  }
  
  // 2. manifestVersion 验证
  if (manifest.manifestVersion !== '1.0') {
    errors.push(`不支持的 manifestVersion: ${manifest.manifestVersion} (仅支持 1.0)`);
  }
  
  // 3. 插件 ID 验证
  const idPattern = /^[a-z0-9][a-z0-9-]{2,63}$/;
  if (!idPattern.test(manifest.id)) {
    errors.push(`插件 ID 格式错误: ${manifest.id} (必须为 3-64 字符的小写字母、数字、连字符)`);
  }
  
  // 4. 版本号验证 (SemVer)
  const versionPattern = /^\d+\.\d+\.\d+(-[a-z0-9.]+)?$/;
  if (!versionPattern.test(manifest.version)) {
    errors.push(`版本号格式错误: ${manifest.version} (必须为语义化版本，如 1.0.0 或 1.0.0-beta.1)`);
  }
  
  // 5. 作者信息验证
  if (!manifest.author.name || !manifest.author.email) {
    errors.push('作者信息缺少必需字段: name 或 email');
  }
  
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailPattern.test(manifest.author.email)) {
    errors.push(`作者邮箱格式错误: ${manifest.author.email}`);
  }
  
  // 6. 设备兼容性验证
  const compat = manifest.deviceCompatibility;
  if (!compat.compatibleTiers || compat.compatibleTiers.length === 0) {
    errors.push('deviceCompatibility.compatibleTiers 不能为空');
  } else {
    for (const tier of compat.compatibleTiers) {
      if (!VALID_TIERS.includes(tier)) {
        errors.push(`不支持的设备等级: ${tier} (有效值: ${VALID_TIERS.join(', ')})`);
      }
    }
  }
  
  if (compat.minDeviceScore !== undefined) {
    if (compat.minDeviceScore < 0 || compat.minDeviceScore > 100) {
      errors.push(`minDeviceScore 必须在 0-100 之间: ${compat.minDeviceScore}`);
    }
  }
  
  // 7. 入口点验证
  const entryPoints = manifest.entryPoints;
  const hasBackend = !!entryPoints.backend;
  const hasFrontend = !!entryPoints.frontend;
  const hasElectron = !!entryPoints.electron;
  
  if (!hasBackend && !hasFrontend && !hasElectron) {
    warnings.push('entryPoints 为空，插件可能无法正常工作');
  }
  
  if (hasBackend) {
    if (entryPoints.backend.routes && entryPoints.backend.routes.length > 0) {
      for (const route of entryPoints.backend.routes) {
        if (!route.file || !route.prefix || !route.tags) {
          errors.push(`后端路由缺少必需字段: file, prefix, 或 tags`);
        }
      }
    }
  }
  
  if (hasFrontend) {
    if (!entryPoints.frontend.module) {
      errors.push('前端入口缺少 module 文件路径');
    }
  }
  
  // 8. 权限验证
  if (manifest.permissions && manifest.permissions.length > 0) {
    for (const perm of manifest.permissions) {
      if (!VALID_PERMISSIONS.includes(perm)) {
        warnings.push(`未知权限: ${perm} (有效值: ${VALID_PERMISSIONS.join(', ')})`);
      }
    }
  }
  
  // 9. 分类验证
  if (manifest.categories && manifest.categories.length > 0) {
    for (const cat of manifest.categories) {
      if (!VALID_CATEGORIES.includes(cat)) {
        warnings.push(`未知分类: ${cat} (有效值: ${VALID_CATEGORIES.join(', ')})`);
      }
    }
  }
  
  // 10. 推荐检查
  if (!manifest.icon) {
    warnings.push('建议提供 icon.png (256x256)');
  }
  
  if (!manifest.keywords || manifest.keywords.length === 0) {
    warnings.push('建议提供 keywords 以提高搜索可见性');
  }
  
  if (!manifest.homepage) {
    warnings.push('建议提供 homepage URL');
  }
  
  if (!manifest.repository) {
    warnings.push('建议提供 repository 信息');
  }
  
  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
}

// ==================== 文件验证 ====================

function validatePluginFiles(pluginDir: string, manifest: Manifest): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  
  // 1. 检查必需文件
  const requiredFiles = ['README.md'];
  for (const file of requiredFiles) {
    const filePath = path.join(pluginDir, file);
    if (!fs.existsSync(filePath)) {
      warnings.push(`推荐文件不存在: ${file}`);
    }
  }
  
  // 2. 检查入口点文件是否存在
  const entryPoints = manifest.entryPoints;
  
  if (entryPoints.backend) {
    if (entryPoints.backend.routes) {
      for (const route of entryPoints.backend.routes) {
        const filePath = path.join(pluginDir, route.file);
        if (!fs.existsSync(filePath)) {
          errors.push(`后端路由文件不存在: ${route.file}`);
        }
      }
    }
    
    if (entryPoints.backend.services) {
      for (const service of entryPoints.backend.services) {
        const filePath = path.join(pluginDir, service.file);
        if (!fs.existsSync(filePath)) {
          errors.push(`后端服务文件不存在: ${service.file}`);
        }
      }
    }
    
    if (entryPoints.backend.hooks) {
      for (const [hookName, hookFile] of Object.entries(entryPoints.backend.hooks)) {
        const filePath = path.join(pluginDir, hookFile as string);
        if (!fs.existsSync(filePath)) {
          errors.push(`钩子文件不存在: ${hookFile}`);
        }
      }
    }
  }
  
  if (entryPoints.frontend) {
    if (entryPoints.frontend.module) {
      const filePath = path.join(pluginDir, entryPoints.frontend.module);
      if (!fs.existsSync(filePath)) {
        errors.push(`前端模块文件不存在: ${entryPoints.frontend.module}`);
      }
    }
  }
  
  if (entryPoints.electron) {
    if (entryPoints.electron.main) {
      const filePath = path.join(pluginDir, entryPoints.electron.main);
      if (!fs.existsSync(filePath)) {
        errors.push(`Electron 主进程文件不存在: ${entryPoints.electron.main}`);
      }
    }
  }
  
  // 3. 检查文件大小
  let totalSize = 0;
  const largeFiles: string[] = [];
  
  function checkFileSize(dir: string): void {
    const items = fs.readdirSync(dir);
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        // 跳过排除的目录
        if (EXCLUDE_PATTERNS.some(p => item.includes(p.replace('*', '')))) {
          continue;
        }
        checkFileSize(fullPath);
      } else {
        totalSize += stat.size;
        if (stat.size > MAX_FILE_SIZE) {
          largeFiles.push(`${item} (${formatBytes(stat.size)})`);
        }
      }
    }
  }
  
  checkFileSize(pluginDir);
  
  if (totalSize > MAX_PACKAGE_SIZE) {
    errors.push(`插件包总大小过大: ${formatBytes(totalSize)} (最大 ${formatBytes(MAX_PACKAGE_SIZE)})`);
  }
  
  if (largeFiles.length > 0) {
    warnings.push(`以下文件超过 ${formatBytes(MAX_FILE_SIZE)}: ${largeFiles.join(', ')}`);
  }
  
  // 4. 检查图标
  if (manifest.icon) {
    const iconPath = path.join(pluginDir, manifest.icon);
    if (!fs.existsSync(iconPath)) {
      warnings.push(`图标文件不存在: ${manifest.icon}`);
    }
  }
  
  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
}

// ==================== 打包功能 ====================

function buildPluginPackage(pluginDir: string, manifest: Manifest, options: BuildOptions): string | null {
  const pluginId = manifest.id;
  const version = manifest.version;
  const platform = options.platform;
  const packageName = `${pluginId}-${version}-${platform}.mxp`;
  const outputPath = path.join(options.outputDir, packageName);
  
  log(`开始打包插件: ${packageName}`, 'info');
  
  // 1. 确保输出目录存在
  if (!fs.existsSync(options.outputDir)) {
    fs.mkdirSync(options.outputDir, { recursive: true });
  }
  
  // 2. 构建 zip 命令
  const excludeArgs = EXCLUDE_PATTERNS.map(pattern => `-x "*${pattern}*"`).join(' ');
  const compressLevel = options.compressLevel;
  
  // 切换到插件目录
  const originalCwd = process.cwd();
  process.chdir(pluginDir);
  
  try {
    // 3. 执行打包
    const zipCommand = `zip -${compressLevel} -r "${outputPath}" . ${excludeArgs}`;
    log(`执行命令: ${zipCommand}`, 'info');
    
    execSync(zipCommand, { stdio: 'inherit' });
    
    // 4. 验证生成的文件
    if (!fs.existsSync(outputPath)) {
      log('打包失败: 输出文件不存在', 'error');
      return null;
    }
    
    const stat = fs.statSync(outputPath);
    log(`打包成功: ${formatBytes(stat.size)}`, 'success');
    
    return outputPath;
  } catch (err) {
    log(`打包失败: ${(err as Error).message}`, 'error');
    return null;
  } finally {
    process.chdir(originalCwd);
  }
}

// ==================== 签名功能 ====================

function generateSignature(mxpPath: string, keyFile: string): boolean {
  log('生成数字签名...', 'info');
  
  try {
    // 1. 读取私钥
    if (!fs.existsSync(keyFile)) {
      log(`私钥文件不存在: ${keyFile}`, 'error');
      return false;
    }
    
    const privateKey = fs.readFileSync(keyFile, 'utf-8');
    
    // 2. 提取 manifest.json
    const tempDir = fs.mkdtempSync('mxp-sign-');
    execSync(`unzip -q "${mxpPath}" manifest.json -d "${tempDir}"`);
    
    const manifestPath = path.join(tempDir, 'manifest.json');
    const manifestData = fs.readFileSync(manifestPath);
    
    // 3. 签名 manifest
    const sign = crypto.createSign('SHA256');
    sign.update(manifestData);
    sign.end();
    
    const manifestSig = sign.sign(privateKey);
    
    // 4. 创建 signatures 目录并写入签名
    const sigDir = path.join(tempDir, 'signatures');
    fs.mkdirSync(sigDir, { recursive: true });
    fs.writeFileSync(path.join(sigDir, 'manifest.sig'), manifestSig);
    
    // 5. 签名整个包（临时移除签名）
    // 简化实现：仅签名 manifest
    
    // 6. 更新 .mxp 文件
    execSync(`zip -j "${mxpPath}" "${sigDir}/manifest.sig"`);
    
    // 7. 清理临时文件
    fs.rmSync(tempDir, { recursive: true, force: true });
    
    log('签名生成成功', 'success');
    return true;
  } catch (err) {
    log(`签名失败: ${(err as Error).message}`, 'error');
    return false;
  }
}

// ==================== CLI 解析 ====================

function parseArgs(args: string[]): { pluginDir: string; options: BuildOptions } {
  const options: BuildOptions = {
    outputDir: './dist',
    sign: false,
    compressLevel: 6,
    platform: 'all',
    validateOnly: false,
  };
  
  let pluginDir = '';
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    if (arg === '--help' || arg === '-h') {
      printHelp();
      process.exit(0);
    } else if (arg === '--output' || arg === '-o') {
      options.outputDir = args[++i];
    } else if (arg === '--sign' || arg === '-s') {
      options.sign = true;
    } else if (arg === '--key' || arg === '-k') {
      options.keyFile = args[++i];
    } else if (arg === '--compress' || arg === '-c') {
      options.compressLevel = parseInt(args[++i], 10);
      if (options.compressLevel < 1 || options.compressLevel > 9) {
        log('压缩级别必须在 1-9 之间', 'error');
        process.exit(1);
      }
    } else if (arg === '--platform' || arg === '-p') {
      options.platform = args[++i];
      if (!VALID_PLATFORMS.includes(options.platform)) {
        log(`不支持的平台: ${options.platform} (有效值: ${VALID_PLATFORMS.join(', ')})`, 'error');
        process.exit(1);
      }
    } else if (arg === '--validate' || arg === '-v') {
      options.validateOnly = true;
    } else if (!arg.startsWith('-')) {
      pluginDir = arg;
    }
  }
  
  if (!pluginDir) {
    log('缺少插件目录参数', 'error');
    printHelp();
    process.exit(1);
  }
  
  if (options.sign && !options.keyFile) {
    log('使用 --sign 时必须提供 --key 私钥文件', 'error');
    process.exit(1);
  }
  
  return { pluginDir, options };
}

function printHelp(): void {
  console.log(`
插件打包 CLI 工具 - 构建 .mxp 插件包

用法:
  npm run build-plugin <plugin-dir> [options]
  ts-node scripts/build-plugin.ts <plugin-dir> [options]

参数:
  <plugin-dir>              插件源代码目录

选项:
  --output, -o <dir>        输出目录 (默认: ./dist)
  --sign, -s                生成数字签名
  --key, -k <file>          私钥文件路径 (与 --sign 配合使用)
  --compress, -c <1-9>      压缩级别 (默认: 6, 1=最快, 9=最小)
  --platform, -p <platform> 平台标识 (默认: all)
                            可选: all, win32-x64, win32-arm64,
                                  darwin-x64, darwin-arm64, linux-x64
  --validate, -v            仅验证不打包
  --help, -h                显示帮助信息

示例:
  # 基本打包
  npm run build-plugin ./plugins/ai-coding-assistant
  
  # 指定输出目录和平台
  npm run build-plugin ./plugins/ar-lab -o ./releases -p win32-x64
  
  # 带签名打包
  npm run build-plugin ./plugins/ml-studio --sign --key ./keys/private.pem
  
  # 仅验证
  npm run build-plugin ./plugins/my-plugin --validate
  
  # 最大压缩
  npm run build-plugin ./plugins/my-plugin -c 9
`);
}

// ==================== 主流程 ====================

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const { pluginDir, options } = parseArgs(args);
  
  console.log('\n========================================');
  console.log('  iMato 插件打包工具 v1.0');
  console.log('========================================\n');
  
  // 1. 检查插件目录
  if (!fs.existsSync(pluginDir)) {
    log(`插件目录不存在: ${pluginDir}`, 'error');
    process.exit(1);
  }
  
  log(`插件目录: ${path.resolve(pluginDir)}`, 'info');
  log(`输出目录: ${path.resolve(options.outputDir)}`, 'info');
  log(`平台标识: ${options.platform}`, 'info');
  
  // 2. 读取 manifest
  log('读取 manifest.json...', 'info');
  const manifest = readManifest(pluginDir);
  if (!manifest) {
    process.exit(1);
  }
  
  log(`插件: ${manifest.name} v${manifest.version} (${manifest.id})`, 'info');
  
  // 3. 验证 manifest
  log('验证 manifest.json...', 'info');
  const manifestResult = validateManifest(manifest);
  
  if (manifestResult.errors.length > 0) {
    log('Manifest 验证失败:', 'error');
    for (const error of manifestResult.errors) {
      console.log(`  ✗ ${error}`);
    }
    process.exit(1);
  }
  
  if (manifestResult.warnings.length > 0) {
    log('Manifest 警告:', 'warn');
    for (const warning of manifestResult.warnings) {
      console.log(`  ⚠ ${warning}`);
    }
  }
  
  log('Manifest 验证通过', 'success');
  
  // 4. 验证文件
  log('验证插件文件...', 'info');
  const fileResult = validatePluginFiles(pluginDir, manifest);
  
  if (fileResult.errors.length > 0) {
    log('文件验证失败:', 'error');
    for (const error of fileResult.errors) {
      console.log(`  ✗ ${error}`);
    }
    process.exit(1);
  }
  
  if (fileResult.warnings.length > 0) {
    log('文件警告:', 'warn');
    for (const warning of fileResult.warnings) {
      console.log(`  ⚠ ${warning}`);
    }
  }
  
  log('文件验证通过', 'success');
  
  // 5. 仅验证模式
  if (options.validateOnly) {
    log('验证模式完成，跳过打包', 'info');
    process.exit(0);
  }
  
  // 6. 打包
  const mxpPath = buildPluginPackage(pluginDir, manifest, options);
  if (!mxpPath) {
    process.exit(1);
  }
  
  // 7. 签名（可选）
  if (options.sign && options.keyFile) {
    const signSuccess = generateSignature(mxpPath, options.keyFile);
    if (!signSuccess) {
      log('签名失败，但插件包已生成', 'warn');
    }
  }
  
  // 8. 完成
  console.log('\n========================================');
  log(`插件包生成成功!`, 'success');
  console.log(`  文件: ${mxpPath}`);
  console.log(`  大小: ${formatBytes(fs.statSync(mxpPath).size)}`);
  console.log('========================================\n');
}

// 执行主流程
if (require.main === module) {
  main().catch(err => {
    log(`未捕获错误: ${err.message}`, 'error');
    console.error(err);
    process.exit(1);
  });
}

export { validateManifest, validatePluginFiles, buildPluginPackage };
