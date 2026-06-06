/**
 * 设备评估引擎单元测试
 *
 * 测试设备评级算法的准确性和边界情况
 */

const assert = require('assert');
const {
  calculateScores,
  determineDeviceClass,
  generatePluginCompatibility,
  DeviceClass,
} = require('./device-profiler');

// ==================== 测试数据 ====================

const MOCK_HARDWARE_BASIC = {
  cpu: { cores: 2, benchmarkScore: 200 },
  memory: { totalMB: 4096 },
  gpu: { hasDedicatedGPU: false, vramMB: 0, supportsCUDA: false },
  storage: { freeGB: 15, type: 'hdd' },
  peripherals: { hasCamera: false, hasMicrophone: false, hasUSBDevices: false, hasGamepad: false },
};

const MOCK_HARDWARE_STANDARD = {
  cpu: { cores: 4, benchmarkScore: 400 },
  memory: { totalMB: 8192 },
  gpu: { hasDedicatedGPU: false, vramMB: 0, supportsCUDA: false },
  storage: { freeGB: 30, type: 'ssd' },
  peripherals: { hasCamera: true, hasMicrophone: true, hasUSBDevices: false, hasGamepad: false },
};

const MOCK_HARDWARE_ADVANCED = {
  cpu: { cores: 8, benchmarkScore: 700 },
  memory: { totalMB: 16384 },
  gpu: { hasDedicatedGPU: true, vramMB: 4096, supportsCUDA: false },
  storage: { freeGB: 100, type: 'ssd' },
  peripherals: { hasCamera: true, hasMicrophone: true, hasUSBDevices: true, hasGamepad: false },
};

const MOCK_HARDWARE_PROFESSIONAL = {
  cpu: { cores: 12, benchmarkScore: 900 },
  memory: { totalMB: 32768 },
  gpu: { hasDedicatedGPU: true, vramMB: 8192, supportsCUDA: true },
  storage: { freeGB: 200, type: 'ssd' },
  peripherals: { hasCamera: true, hasMicrophone: true, hasUSBDevices: true, hasGamepad: true },
};

const MOCK_SOFTWARE = {
  containers: { dockerInstalled: false, dockerRunning: false },
  hardware_tools: { platformioInstalled: false },
};

// ==================== 测试用例 ====================

function testCalculateScores() {
  console.log('测试:calculateScores');

  // Basic 设备
  const basicScores = calculateScores(MOCK_HARDWARE_BASIC, MOCK_SOFTWARE);
  assert.ok(basicScores.cpuScore > 0, 'CPU 评分应大于 0');
  assert.ok(basicScores.memoryScore >= 20, '4GB 内存评分应 >= 20');
  assert.ok(basicScores.gpuScore < 20, '集成显卡评分应 < 20');
  console.log('  ✓ Basic 设备评分正确');

  // Advanced 设备
  const advancedScores = calculateScores(MOCK_HARDWARE_ADVANCED, MOCK_SOFTWARE);
  assert.ok(advancedScores.gpuScore >= 50, '4GB 独显评分应 >= 50');
  assert.ok(advancedScores.storageScore >= 70, '100GB SSD 评分应 >= 70');
  console.log('  ✓ Advanced 设备评分正确');

  // Professional 设备
  const proScores = calculateScores(MOCK_HARDWARE_PROFESSIONAL, MOCK_SOFTWARE);
  assert.ok(proScores.gpuScore >= 90, '8GB CUDA 显卡评分应 >= 90');
  assert.ok(proScores.memoryScore >= 90, '32GB 内存评分应 >= 90');
  console.log('  ✓ Professional 设备评分正确');
}

function testDetermineDeviceClass() {
  console.log('测试：determineDeviceClass');

  // Basic
  const basicScores = calculateScores(MOCK_HARDWARE_BASIC, MOCK_SOFTWARE);
  const basicResult = determineDeviceClass(basicScores, MOCK_HARDWARE_BASIC, MOCK_SOFTWARE);
  assert.strictEqual(basicResult.deviceClass, DeviceClass.BASIC, '2 核/4GB 应为 Basic');
  console.log(`  ✓ Basic: ${basicResult.deviceClass} (${basicResult.score}分)`);

  // Standard
  const stdScores = calculateScores(MOCK_HARDWARE_STANDARD, MOCK_SOFTWARE);
  const stdResult = determineDeviceClass(stdScores, MOCK_HARDWARE_STANDARD, MOCK_SOFTWARE);
  assert.strictEqual(stdResult.deviceClass, DeviceClass.STANDARD, '4 核/8GB 应为 Standard');
  console.log(`  ✓ Standard: ${stdResult.deviceClass} (${stdResult.score}分)`);

  // Advanced
  const advScores = calculateScores(MOCK_HARDWARE_ADVANCED, MOCK_SOFTWARE);
  const advResult = determineDeviceClass(advScores, MOCK_HARDWARE_ADVANCED, MOCK_SOFTWARE);
  assert.strictEqual(advResult.deviceClass, DeviceClass.ADVANCED, '8 核/16GB/独显 应为 Advanced');
  console.log(`  ✓ Advanced: ${advResult.deviceClass} (${advResult.score}分)`);

  // Professional
  const proScores = calculateScores(MOCK_HARDWARE_PROFESSIONAL, MOCK_SOFTWARE);
  const proResult = determineDeviceClass(proScores, MOCK_HARDWARE_PROFESSIONAL, MOCK_SOFTWARE);
  assert.strictEqual(proResult.deviceClass, DeviceClass.PROFESSIONAL, '12 核/32GB/CUDA 应为 Professional');
  console.log(`  ✓ Professional: ${proResult.deviceClass} (${proResult.score}分)`);
}

function testGeneratePluginCompatibility() {
  console.log('测试：generatePluginCompatibility');

  // Basic 设备
  const basicCompat = generatePluginCompatibility(
    DeviceClass.BASIC,
    MOCK_HARDWARE_BASIC,
    MOCK_SOFTWARE
  );
  assert.ok(basicCompat.compatiblePluginTiers.includes('tier-a'), 'Basic 应兼容 Tier A');
  assert.ok(!basicCompat.compatiblePluginTiers.includes('tier-c'), 'Basic 不应兼容 Tier C');
  assert.ok(basicCompat.recommendedPlugins.includes('ai-tutor'), '应推荐 AI 教师');
  console.log('  ✓ Basic 兼容性正确');

  // Advanced 设备
  const advCompat = generatePluginCompatibility(
    DeviceClass.ADVANCED,
    MOCK_HARDWARE_ADVANCED,
    MOCK_SOFTWARE
  );
  assert.ok(advCompat.compatiblePluginTiers.includes('tier-c'), 'Advanced 应兼容 Tier C');
  assert.ok(!advCompat.compatiblePluginTiers.includes('tier-d'), 'Advanced 不应兼容 Tier D');
  assert.ok(advCompat.recommendedPlugins.includes('creativity-engine'), '应推荐创意引擎');
  console.log('  ✓ Advanced 兼容性正确');

  // Professional 设备
  const proCompat = generatePluginCompatibility(
    DeviceClass.PROFESSIONAL,
    MOCK_HARDWARE_PROFESSIONAL,
    { ...MOCK_SOFTWARE, containers: { dockerInstalled: true, dockerRunning: true }, hardware_tools: { platformioInstalled: true } }
  );
  assert.ok(proCompat.compatiblePluginTiers.includes('tier-d'), 'Professional 应兼容 Tier D');
  assert.ok(proCompat.recommendedPlugins.includes('federated-learning'), '应推荐联邦学习');
  assert.ok(proCompat.recommendedPlugins.includes('hardware-cert'), '应推荐硬件认证');
  console.log('  ✓ Professional 兼容性正确');
}

// ==================== 运行测试 ====================

console.log('\n========== 设备评估引擎单元测试 ==========\n');

try {
  testCalculateScores();
  testDetermineDeviceClass();
  testGeneratePluginCompatibility();

  console.log('\n✅ 所有测试通过！\n');
} catch (err) {
  console.error('\n❌ 测试失败:', err.message);
  console.error(err.stack);
  process.exit(1);
}
