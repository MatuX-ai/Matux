/**
 * Blockly 积木→Python 代码生成 & 电路欧姆定律仿真 逻辑验证
 * 运行: node scripts/test-logic.mjs
 *
 * 从 BlocklyPage.tsx / CircuitLabPage.tsx 提取的核心纯函数，
 * 用模拟数据验证各种边界场景。
 */

// ============================================================
// Part 1: Blockly 积木→Python 代码生成
// ============================================================

// 积木定义（与 BlocklyPage.tsx categories 一致）
const blockDefs = {
  'on-start':   { pyCode: '# 程序入口' },
  'on-click':   { pyCode: '@on_click' },
  'on-key':     { pyCode: '@on_key("space")' },
  'repeat':     { pyCode: 'for _ in range(4):' },
  'forever':    { pyCode: 'while True:' },
  'wait':       { pyCode: 'time.sleep(1)' },
  'if':         { pyCode: 'if condition:' },
  'move-steps': { pyCode: 'character.move(10)' },
  'turn-right': { pyCode: 'character.turn(15)' },
  'turn-left':  { pyCode: 'character.turn(-15)' },
  'go-to':      { pyCode: 'character.goto(0, 0)' },
  'say':        { pyCode: 'character.say("你好", 2)' },
};

// 缩进触发积木：放在这些积木后面的块应缩进 4 空格
const INDENT_TRIGGERS = new Set(['repeat', 'forever', 'if']);

/**
 * 模拟 addBlock：添加一个积木到画布，自动计算缩进
 */
function addBlock(placed, blockId) {
  const def = blockDefs[blockId];
  if (!def) throw new Error(`未知积木: ${blockId}`);
  const lastBlock = placed[placed.length - 1];
  let indent = '';
  if (lastBlock && INDENT_TRIGGERS.has(lastBlock.blockId)) {
    indent = '    ';
  }
  return [...placed, {
    uid: `b${placed.length}`,
    blockId,
    pyCode: indent + def.pyCode,
  }];
}

/**
 * 模拟 removeBlock：从画布删除指定积木
 */
function removeBlock(placed, uid) {
  return placed.filter((b) => b.uid !== uid);
}

/**
 * 生成 Python 代码（与 useMemo 逻辑一致）
 */
function generateCode(placed) {
  return placed.map((b) => b.pyCode).join('\n');
}

// ---- Blockly 测试用例 ----
function testBlockly() {
  console.log('\n========== Part 1: Blockly 积木→代码生成 ==========\n');
  let passed = 0, failed = 0;
  const assert = (name, actual, expected) => {
    if (actual === expected) {
      console.log(`  ✅ ${name}`);
      passed++;
    } else {
      console.log(`  ❌ ${name}`);
      console.log(`     期望: ${JSON.stringify(expected)}`);
      console.log(`     实际: ${JSON.stringify(actual)}`);
      failed++;
    }
  };

  // T1: 空画布 → 空代码
  assert('T1 空画布生成空代码', generateCode([]), '');

  // T2: 单个积木
  let blocks = addBlock([], 'on-start');
  assert('T2 单个积木 on-start', generateCode(blocks), '# 程序入口');

  // T3: repeat 后的积木自动缩进
  blocks = addBlock([], 'on-start');
  blocks = addBlock(blocks, 'repeat');
  blocks = addBlock(blocks, 'move-steps');
  assert('T3 repeat 后 move-steps 自动缩进', generateCode(blocks),
    '# 程序入口\nfor _ in range(4):\n    character.move(10)');

  // T4: repeat 后多个积木只有第一个缩进（当前实现：仅看上一个块是否是触发器）
  blocks = addBlock([], 'repeat');
  blocks = addBlock(blocks, 'move-steps');  // 缩进（上一个 repeat）
  blocks = addBlock(blocks, 'turn-right');  // 不缩进（上一个 move-steps 不是触发器）
  assert('T4 repeat 后第二个块不缩进（当前逻辑）', generateCode(blocks),
    'for _ in range(4):\n    character.move(10)\ncharacter.turn(15)');

  // T5: forever 循环后缩进
  blocks = addBlock([], 'forever');
  blocks = addBlock(blocks, 'say');
  assert('T5 forever 后 say 缩进', generateCode(blocks),
    'while True:\n    character.say("你好", 2)');

  // T6: if 条件后缩进
  blocks = addBlock([], 'if');
  blocks = addBlock(blocks, 'move-steps');
  assert('T6 if 后 move-steps 缩进', generateCode(blocks),
    'if condition:\n    character.move(10)');

  // T7: wait 积木不触发缩进
  blocks = addBlock([], 'wait');
  blocks = addBlock(blocks, 'move-steps');
  assert('T7 wait 后 move-steps 不缩进', generateCode(blocks),
    'time.sleep(1)\ncharacter.move(10)');

  // T8: 删除积木后代码更新
  blocks = addBlock([], 'on-start');
  blocks = addBlock(blocks, 'move-steps');
  blocks = addBlock(blocks, 'turn-right');
  blocks = removeBlock(blocks, 'b1'); // 删除 move-steps
  assert('T8 删除中间积木后代码更新', generateCode(blocks),
    '# 程序入口\ncharacter.turn(15)');

  // T9: 复杂嵌套场景
  blocks = addBlock([], 'on-start');
  blocks = addBlock(blocks, 'repeat');
  blocks = addBlock(blocks, 'move-steps');  // 缩进
  blocks = addBlock(blocks, 'turn-right');  // 不缩进
  blocks = addBlock(blocks, 'say');          // 不缩进
  assert('T9 复杂场景', generateCode(blocks),
    '# 程序入口\nfor _ in range(4):\n    character.move(10)\ncharacter.turn(15)\ncharacter.say("你好", 2)');

  // T10: 预置示例电路积木（与 BlocklyPage initial state 一致）
  blocks = addBlock([], 'on-start');
  blocks = addBlock(blocks, 'repeat');
  blocks = addBlock(blocks, 'move-steps');  // 缩进
  blocks = addBlock(blocks, 'turn-right');  // 不缩进
  blocks = addBlock(blocks, 'say');          // 不缩进
  const expectedInit = '# 程序入口\nfor _ in range(4):\n    character.move(10)\ncharacter.turn(15)\ncharacter.say("你好", 2)';
  assert('T10 预置示例（与页面 initial 一致）', generateCode(blocks), expectedInit);

  console.log(`\n  Blockly: ${passed} passed, ${failed} failed`);
  return { passed, failed };
}

// ============================================================
// Part 2: 电路欧姆定律仿真
// ============================================================

/**
 * 仿真计算（与 CircuitLabPage.tsx useMemo 逻辑完全一致）
 * @param {Array} components - 元件列表
 * @returns {Object} 仿真结果 { voltage, current, resistance, power, status, ledOn, ok }
 */
function simulate(components) {
  const hasBattery = components.some((c) => c.type === 'battery');
  const hasLED = components.some((c) => c.type === 'led');
  const hasSwitch = components.some((c) => c.type === 'switch');
  const switchOn = !hasSwitch || components.find((c) => c.type === 'switch')?.value === 'ON';
  const resistors = components.filter((c) => c.type === 'resistor');
  const totalResistance = resistors.reduce((sum, r) => {
    const m = r.value.match(/(\d+)/);
    return sum + (m ? parseInt(m[1]) : 0);
  }, 0);
  const battery = components.find((c) => c.type === 'battery');
  const voltage = battery ? parseInt(battery.value) || 5 : 0;
  const ledDrop = hasLED ? 2 : 0;

  if (!hasBattery) return { voltage: 0, current: 0, resistance: totalResistance, power: 0, status: '⚠ 缺少电池', ledOn: false, ok: false };
  if (!hasLED && !resistors.length) return { voltage, current: 0, resistance: 0, power: 0, status: '⚠ 请添加元件', ledOn: false, ok: false };
  if (!switchOn) return { voltage, current: 0, resistance: totalResistance, power: 0, status: '⚪ 开关已断开', ledOn: false, ok: true };

  const effectiveR = totalResistance || 220;
  const current = ((voltage - ledDrop) / effectiveR * 1000); // mA
  const power = voltage * current / 1000;
  const ledOn = hasLED && current > 5 && current < 30;
  let status = '✓ 电路正常运行';
  if (current > 30) status = '⚠ 电流过大！LED 可能烧毁';
  if (current < 5 && hasLED) status = '⚠ 电流过小，LED 不亮';
  return {
    voltage,
    current: Math.round(current * 10) / 10,
    resistance: effectiveR,
    power: Math.round(power * 1000) / 1000,
    status, ledOn, ok: true,
  };
}

// 辅助：构造元件
function comp(type, value = '') {
  const defaults = {
    battery: '5V', resistor: '220Ω', led: '2V/20mA', switch: 'ON', wire: '—',
  };
  return { uid: type, type, value: value || defaults[type] };
}

function testCircuit() {
  console.log('\n========== Part 2: 电路欧姆定律仿真 ==========\n');
  let passed = 0, failed = 0;
  const assert = (name, actual, expected) => {
    const actualStr = JSON.stringify(actual);
    const expectedStr = JSON.stringify(expected);
    if (actualStr === expectedStr) {
      console.log(`  ✅ ${name}`);
      passed++;
    } else {
      console.log(`  ❌ ${name}`);
      console.log(`     期望: ${expectedStr}`);
      console.log(`     实际: ${actualStr}`);
      failed++;
    }
  };

  // T1: 标准电路 5V + 开关ON + 220Ω + LED
  // I = (5-2)/220 * 1000 = 13.636... mA → 13.6
  // P = 5 * 13.636 / 1000 = 0.068 → 0.068
  // LED 亮: 5 < 13.6 < 30 ✓
  assert('T1 标准电路 5V+220Ω+LED',
    simulate([comp('battery'), comp('switch', 'ON'), comp('resistor'), comp('led')]),
    { voltage: 5, current: 13.6, resistance: 220, power: 0.068, status: '✓ 电路正常运行', ledOn: true, ok: true });

  // T2: 无电池 → 缺少电池
  assert('T2 无电池',
    simulate([comp('resistor'), comp('led')]),
    { voltage: 0, current: 0, resistance: 220, power: 0, status: '⚠ 缺少电池', ledOn: false, ok: false });

  // T3: 开关断开 → 开关已断开
  assert('T3 开关断开',
    simulate([comp('battery'), comp('switch', 'OFF'), comp('resistor'), comp('led')]),
    { voltage: 5, current: 0, resistance: 220, power: 0, status: '⚪ 开关已断开', ledOn: false, ok: true });

  // T4: 电流过大 5V + 10Ω + LED
  // I = (5-2)/10 * 1000 = 300 mA → >30 → 电流过大
  // P = 5 * 300 / 1000 = 1.5
  // LED 不亮: 300 > 30
  assert('T4 电流过大 5V+10Ω+LED',
    simulate([comp('battery'), comp('resistor', '10Ω'), comp('led')]),
    { voltage: 5, current: 300, resistance: 10, power: 1.5, status: '⚠ 电流过大！LED 可能烧毁', ledOn: false, ok: true });

  // T5: 电流过小 5V + 10000Ω + LED
  // I = (5-2)/10000 * 1000 = 0.3 mA → <5 → 电流过小
  // P = 5 * 0.3 / 1000 = 0.0015 → 0.002 (rounded)
  // LED 不亮: 0.3 < 5
  assert('T5 电流过小 5V+10000Ω+LED',
    simulate([comp('battery'), comp('resistor', '10000Ω'), comp('led')]),
    { voltage: 5, current: 0.3, resistance: 10000, power: 0.002, status: '⚠ 电流过小，LED 不亮', ledOn: false, ok: true });

  // T6: 只有电池无其他元件 → 请添加元件
  assert('T6 只有电池',
    simulate([comp('battery')]),
    { voltage: 5, current: 0, resistance: 0, power: 0, status: '⚠ 请添加元件', ledOn: false, ok: false });

  // T7: 无电阻默认 220Ω（5V + LED，无电阻）
  // I = (5-2)/220 * 1000 = 13.6 mA
  // resistance = 220 (default)
  assert('T7 无电阻默认220Ω',
    simulate([comp('battery'), comp('led')]),
    { voltage: 5, current: 13.6, resistance: 220, power: 0.068, status: '✓ 电路正常运行', ledOn: true, ok: true });

  // T8: 无 LED（5V + 220Ω 电阻）
  // ledDrop = 0, I = (5-0)/220 * 1000 = 22.7 mA
  // ledOn = false (hasLED = false)
  assert('T8 无LED 5V+220Ω',
    simulate([comp('battery'), comp('resistor')]),
    { voltage: 5, current: 22.7, resistance: 220, power: 0.114, status: '✓ 电路正常运行', ledOn: false, ok: true });

  // T9: 多电阻串联 5V + 100Ω + 200Ω + LED
  // totalR = 300, I = (5-2)/300 * 1000 = 10 mA
  // P = 5 * 10 / 1000 = 0.05
  // LED 亮: 5 < 10 < 30 ✓
  assert('T9 多电阻串联 100Ω+200Ω',
    simulate([comp('battery'), comp('resistor', '100Ω'), comp('resistor', '200Ω'), comp('led')]),
    { voltage: 5, current: 10, resistance: 300, power: 0.05, status: '✓ 电路正常运行', ledOn: true, ok: true });

  // T10: 9V 电池 + 330Ω + LED（常见 Arduino 电路）
  // I = (9-2)/330 * 1000 = 21.2 mA
  // P = 9 * 21.2 / 1000 = 0.191
  // LED 亮: 5 < 21.2 < 30 ✓
  assert('T10 9V+330Ω Arduino 经典电路',
    simulate([comp('battery', '9V'), comp('resistor', '330Ω'), comp('led')]),
    { voltage: 9, current: 21.2, resistance: 330, power: 0.191, status: '✓ 电路正常运行', ledOn: true, ok: true });

  // T11: 3V 电池 + 220Ω + LED（低电压场景）
  // I = (3-2)/220 * 1000 = 4.5 mA → <5 → 电流过小
  assert('T11 3V低电压 电流过小',
    simulate([comp('battery', '3V'), comp('resistor', '220Ω'), comp('led')]),
    { voltage: 3, current: 4.5, resistance: 220, power: 0.014, status: '⚠ 电流过小，LED 不亮', ledOn: false, ok: true });

  // T12: 预置示例电路（与 CircuitLabPage initialCircuit 一致）
  // 电池5V + 开关ON + 电阻220Ω + LED
  // I = (5-2)/220 * 1000 = 13.6 mA
  assert('T12 预置示例电路（页面 initial）',
    simulate([comp('battery'), comp('switch', 'ON'), comp('resistor'), comp('led')]),
    { voltage: 5, current: 13.6, resistance: 220, power: 0.068, status: '✓ 电路正常运行', ledOn: true, ok: true });

  console.log(`\n  电路: ${passed} passed, ${failed} failed`);
  return { passed, failed };
}

// ============================================================
// 运行
// ============================================================
const r1 = testBlockly();
const r2 = testCircuit();
const totalPassed = r1.passed + r2.passed;
const totalFailed = r1.failed + r2.failed;
console.log(`\n========== 总计: ${totalPassed} passed, ${totalFailed} failed ==========`);
process.exit(totalFailed > 0 ? 1 : 0);
