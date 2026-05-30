# 3D 模型库开发者指南

## 📋 文档信息

- **版本**: v1.0
- **创建日期**: 2026-03-03
- **最后更新**: 2026-03-03
- **目标读者**: 前端/后端开发工程师、3D 美术师
- **前置知识**: Angular/TypeScript、Python、Three.js 基础

---

## 🎯 模块概述

虚拟实验室 3D 模型库是 iMatu 项目的核心组件之一，提供从模型获取、转换、优化到加载、交互、仿真的完整解决方案。

### 核心价值

1. **标准化元件库**: 256+ 精选 KiCad 开源模型
2. **高性能渲染**: LOD 三级优化 + 实例化渲染
3. **真实物理**: Ammo.js 刚体模拟 + 碰撞检测
4. **游戏化交互**: 拖放 - 吸附 + 积分奖励
5. **简化仿真**: LED 亮灭 + 开关控制 + ERC 验证

### 技术架构

```
┌─────────────────────────────────────────────────┐
│             应用层 (Angular)                    │
│  Component → Service → Vircadia SDK            │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│           服务层 (TypeScript/Python)            │
│  - Model Loader      - Physics Engine          │
│  - Assembly System   - Simulator               │
│  - Integral Service  - Validation              │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│          引擎层 (Vircadia/Three.js)             │
│  - Scene Graph       - GLTF Loader             │
│  - Ammo.js Physics   - Raycaster               │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│           数据层 (GLB Models + JSON)            │
│  - 256 个 GLB 模型     - 电路协议定义            │
│  - LOD 配置         - 物理预设                 │
└─────────────────────────────────────────────────┘
```

---

## 🛠️ 开发环境搭建

### 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| Python | 3.9+ | 3.11+ |
| Node.js | 18+ | 20+ |
| Blender | 3.6+ | 4.0+ |
| 内存 | 8GB | 16GB |
| 硬盘 | 5GB | 10GB SSD |

### 快速部署

```powershell
# 1. 运行一键部署脚本
cd G:\iMato
.\scripts\quick_setup.ps1

# 2. 验证环境
python --version    # 应显示 Python 3.x
node --version      # 应显示 v22.x
npm --version       # 应显示 10.x

# 3. 安装 Angular CLI (如未安装)
npm install -g @angular/cli
```

### 依赖安装

```bash
# Python 依赖
pip install requests black flake8 mypy pytest

# Angular 依赖
npm install three @types/three
npm install @vircadia/web-sdk  # 如使用 Vircadia
```

---

## 📁 项目结构详解

### 前端文件组织

```
src/app/
├── models/
│   ├── circuit.models.ts          # 电路数据协议定义
│   └── vircadia.models.ts         # Vircadia 实体模型
│
├── core/services/
│   ├── vircadia-model-loader.service.ts    # 模型加载器
│   ├── vircadia-physics.service.ts         # 物理引擎
│   ├── circuit-assembly.service.ts         # 组装交互
│   ├── circuit-simulator.service.ts        # 电路仿真
│   └── circuit-integral.service.ts         # 积分系统
│
├── components/
│   └── vircadia-scene-viewer/     # 3D 场景查看器
│       ├── vircadia-scene-viewer.component.ts
│       ├── vircadia-scene-viewer.component.html
│       └── vircadia-scene-viewer.component.scss
│
└── assets/models/
    └── kicad_model_index.json     # 模型索引表
```

### 后端文件组织

```
backend/
├── services/
│   └── circuit_validation_service.py   # 电路验证服务
│
├── routes/
│   └── circuit_routes.py          # 电路 API 路由
│
└── models/
    └── circuit_models.py          # 后端电路模型
```

### 工具脚本

```
scripts/
├── kicad_model_scraper.py         # 模型爬虫
├── model_converter.py             # 格式转换器
├── lod_generator.py               # LOD 生成器
├── validate_3d_model_implementation.py  # 验证脚本
└── quick_setup.ps1                # 快速部署
```

---

## 🔧 核心服务使用指南

### 1. Vircadia 模型加载器

**功能**: 动态加载 GLB 模型，支持 LOD 切换

**示例代码**:

```typescript
import { VircadiaModelLoaderService } from './core/services/vircadia-model-loader.service';

@Component({ /* ... */ })
export class CircuitBoardComponent implements OnInit {
  constructor(private modelLoader: VircadiaModelLoaderService) {}

  async ngOnInit() {
    // 加载电阻模型 (中模)
    const resistor = await this.modelLoader.loadComponentModel(
      'resistor_a1b2c3d4',
      'medium'
    );

    console.log('模型加载完成:', resistor);
    
    // 手动更新 LOD
    this.modelLoader.updateLOD(resistor.id, 10.0); // 10 米距离
  }
}
```

**关键方法**:

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `loadComponentModel(id, lod)` | id: string, lod: 'high'|'medium'|'low' | Promise<GameObject> | 加载指定 LOD 的模型 |
| `updateLOD(entityId, distance)` | entityId: string, distance: number | void | 根据相机距离更新 LOD |
| `preloadModels(category)` | category: string | Promise<void> | 预加载某类元件 |

---

### 2. 物理引擎服务

**功能**: 为元件添加质量、摩擦力、碰撞体积

**示例代码**:

```typescript
import { VircadiaPhysicsService } from './core/services/vircadia-physics.service';

constructor(private physics: VircadiaPhysicsService) {}

async applyResistorPhysics(entity: GameObject) {
  await this.physics.applyComponentPhysics(
    'resistor_axial',  // 元件类型
    entity,            // 游戏对象
    'medium'           // LOD 级别
  );
  
  // 手动添加力
  await this.physics.applyForce(entity.id, { x: 0, y: -9.8, z: 0 });
}
```

**物理预设**:

```typescript
// 内置 8 类元件的物理属性
const PHYSICS_PRESETS = {
  'resistor_axial': {
    mass: 0.01,           // 10 克
    colliderType: 'box',
    friction: 0.7,
    bounciness: 0.1
  },
  'capacitor_radial': {
    mass: 0.015,          // 15 克
    colliderType: 'cylinder',
    friction: 0.6,
    bounciness: 0.15
  },
  'led_5mm': {
    mass: 0.003,          // 3 克
    colliderType: 'capsule',
    friction: 0.6,
    bounciness: 0.2
  }
  // ... 更多预设见 service 源码
};
```

---

### 3. 电路组装交互系统

**功能**: 实现拖放 - 吸附、极性验证、实时反馈

**示例代码**:

```typescript
import { CircuitAssemblyService, SolderPad } from './core/services/circuit-assembly.service';

// 注册焊盘
const solderPad: SolderPad = {
  id: 'pad_r1_1',
  name: 'R1 Pin 1',
  position: { x: 0, y: 0, z: 0 },
  rotation: { x: 0, y: 0, z: 0, w: 1 },
  padType: 'tht',
  pinCount: 1
};

this.assemblyService.registerSolderPad(solderPad);

// 拖动时检测吸附
async onComponentDrag(component: GameObject) {
  const pads = this.assemblyService.getAllPads();
  const nearestPad = this.assemblyService.detectProximity(component, pads);
  
  if (nearestPad && nearestPad.distance < 0.02) { // 2cm 阈值
    const isValid = await this.assemblyService.snapToPad(
      component,
      nearestPad.pad
    );
    
    if (isValid) {
      console.log('✅ 元件放置正确!');
    } else {
      console.log('❌ 极性或连接错误!');
    }
  }
}
```

**吸附流程**:

```
1. 用户拖动元件
       ↓
2. 实时检测与焊盘的距离 (Raycasting)
       ↓
3. 距离 < 2cm → 触发吸附
       ↓
4. 验证连接有效性 (极性/网络)
       ↓
5. 播放吸附动画 (300ms lerp)
       ↓
6. 锁定位置并触发积分奖励
```

---

### 4. 电路仿真引擎

**功能**: 简化逻辑模拟 (LED 亮灭、开关控制)

**示例代码**:

```typescript
import { CircuitSimulatorService } from './core/services/circuit-simulator.service';

// 定义简单 LED 电路
const ledCircuit: CircuitDescription = {
  id: 'simple_led_circuit',
  components: [
    {
      id: 'battery_1',
      type: 'battery',
      value: '9V',
      designator: 'B1',
      pins: [{ id: 'p1', net: 'VCC' }, { id: 'p2', net: 'GND' }]
    },
    {
      id: 'led_1',
      type: 'led',
      value: 'RED',
      designator: 'D1',
      pins: [{ id: 'a', net: 'VCC' }, { id: 'k', net: 'R1' }]
    },
    {
      id: 'resistor_1',
      type: 'resistor',
      value: '330Ω',
      designator: 'R1',
      pins: [{ id: 'p1', net: 'LED_K' }, { id: 'p2', net: 'GND' }]
    }
  ],
  connections: [
    { from: 'B1.p1', to: 'D1.a' },
    { from: 'D1.k', to: 'R1.p1' },
    { from: 'R1.p2', to: 'B1.p2' }
  ]
};

// 运行仿真
const result = this.simulator.simulateCircuit(ledCircuit);
console.log('LED 状态:', result.components.find(c => c.type === 'led').state);
// 输出：{ isOn: true, brightness: 1.0 }
```

**仿真规则**:

```typescript
// LED 仿真逻辑
if (hasPowerPath && polarityCorrect) {
  led.isOn = true;
  led.brightness = 1.0;
  led.color = ledColor;
} else {
  led.isOn = false;
  led.brightness = 0.0;
}

// 开关仿真
if (switchClosed) {
  connection.conductivity = 1.0;  // 导通
} else {
  connection.conductivity = 0.0;  // 断开
}
```

---

### 5. 积分系统集成

**功能**: 组装成功奖励、连击加成、特殊成就

**示例代码**:

```typescript
import { CircuitIntegralService } from './core/services/circuit-integral.service';

// 奖励配置
const REWARD_CONFIGS = {
  'circuit_assembly_success': { basePoints: 10 },
  'first_try_success': { basePoints: 20 },
  'circuit_completed': { basePoints: 100, maxComboBonus: 50 }
};

// 触发奖励
async onComponentSnapped(componentId: string, isValid: boolean) {
  if (isValid) {
    const points = await this.integralService.calculateReward(
      'circuit_assembly_success',
      { componentId, attemptCount: 1 }
    );
    
    await this.integralService.awardPoints(points, {
      reason: '成功放置元件',
      componentId,
      timestamp: Date.now()
    });
    
    // 播放奖励动画
    this.integralService.playRewardAnimation(points);
  }
}
```

**奖励计算**:

```typescript
// 基础奖励 + 连击加成
totalPoints = basePoints + (comboCount * comboMultiplier);

// 示例
basePoints = 10;
comboCount = 3;
comboMultiplier = 5;
totalPoints = 10 + (3 * 5) = 15 分
```

---

## 🐍 后端服务使用指南

### 电路验证服务

**功能**: ERC/DRC 检查、极性验证、连通性分析

**示例代码**:

```python
from backend.services.circuit_validation_service import CircuitValidationService

validator = CircuitValidationService()

# 验证电路板组装
validation_result = validator.validate_assembly({
    'board_id': 'pcb_001',
    'components': [
        {
            'designator': 'R1',
            'type': 'resistor',
            'value': '10kΩ',
            'position': {'x': 0, 'y': 0, 'z': 0},
            'rotation': {'x': 0, 'y': 0, 'z': 0, 'w': 1},
            'pins': [
                {'pin': 1, 'net': 'VCC'},
                {'pin': 2, 'net': 'GND'}
            ]
        }
    ],
    'connections': [...]
})

# 检查结果
if validation_result.is_valid:
    print("✅ 组装验证通过")
else:
    print(f"❌ 发现 {len(validation_result.errors)} 个错误:")
    for error in validation_result.errors:
        print(f"  - {error}")
```

**验证规则**:

```python
# 极性检查
if component_type in ['led', 'diode', 'electrolytic_capacitor']:
    if component_polarity != pad_polarity:
        errors.append(f"元件{designator}极性错误!")

# 连通性检查 (ERC)
for net in nets:
    if net.voltage_conflict:
        errors.append(f"网络{net.name}存在电压冲突!")

# 短路检查
if short_circuit_detected:
    errors.append(f"发现短路：{short_description}")
```

---

## 🎨 最佳实践

### 性能优化

#### 1. LOD 策略

```typescript
// 根据距离动态切换 LOD
updateLOD(entityId: string, cameraDistance: number): void {
  let targetLOD: string;
  
  if (cameraDistance < 5.0) {
    targetLOD = 'high';     // < 5m 使用高模 (5000 tris)
  } else if (cameraDistance > 15.0) {
    targetLOD = 'low';      // > 15m 使用低模 (500 tris)
  } else {
    targetLOD = 'medium';   // 5-15m 使用中模 (1500 tris)
  }
  
  // 平滑过渡
  this.smoothLODTransition(entityId, targetLOD, 0.3);
}
```

#### 2. 实例化渲染

```typescript
// 批量渲染相同元件
const instances = [
  { position: {x:0, y:0, z:0}, rotation: {...} },
  { position: {x:1, y:0, z:0}, rotation: {...} },
  // ... 100 个实例
];

this.renderer.renderInstanced(
  'resistor_axial.glb',
  instances
);
// 单次 draw call 渲染所有实例
```

#### 3. 对象池管理

```typescript
// 预分配元件对象池
class ComponentPool {
  private pool: GameObject[] = [];
  
  constructor(private size: number = 50) {
    for (let i = 0; i < size; i++) {
      this.pool.push(this.createEmptyComponent());
    }
  }
  
  acquire(): GameObject {
    return this.pool.pop() || this.createEmptyComponent();
  }
  
  release(obj: GameObject): void {
    this.pool.push(obj);
  }
}
```

### 内存管理

```typescript
// 及时释放不再使用的模型
disposeUnusedModels(): void {
  Object.keys(this.loadedModels).forEach(id => {
    if (!this.isInScene(id)) {
      this.modelLoader.unloadModel(id);
      delete this.loadedModels[id];
    }
  });
}

// Three.js 资源清理
cleanupThreeResources(geometry: THREE.BufferGeometry): void {
  geometry.dispose();
  
  if (geometry.material) {
    geometry.material.dispose();
    geometry.material.map?.dispose();
  }
}
```

---

## 🧪 测试指南

### 单元测试示例

```typescript
// circuit-simulator.service.spec.ts
describe('CircuitSimulatorService', () => {
  let service: CircuitSimulatorService;
  
  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(CircuitSimulatorService);
  });
  
  it('should detect LED polarity correctly', () => {
    const circuit: CircuitDescription = {
      // ... 定义测试电路
    };
    
    const result = service.simulateCircuit(circuit);
    
    expect(result.components[0].state.isOn).toBe(true);
    expect(result.components[0].state.brightness).toBe(1.0);
  });
  
  it('should detect short circuit', () => {
    const shortCircuit: CircuitDescription = {
      // ... 定义短路电路
    };
    
    const result = service.simulateCircuit(shortCircuit);
    
    expect(result.warnings).toContain('Short circuit detected');
  });
});
```

### 集成测试

```python
# test_circuit_validation.py
def test_complete_assembly_flow():
    """测试完整的组装验证流程"""
    
    # 1. 注册 PCB
    board_id = validator.register_pcb_board(pcb_design)
    
    # 2. 添加元件
    validator.add_component(board_id, resistor_data)
    validator.add_component(board_id, led_data)
    
    # 3. 验证组装
    result = validator.validate_assembly(board_id)
    
    # 4. 断言
    assert result.is_valid == True
    assert len(result.errors) == 0
    assert len(result.warnings) <= 2
```

---

## 📚 API 参考

### 前端服务 API

#### VircadiaModelLoaderService

```typescript
interface VircadiaModelLoaderService {
  loadComponentModel(
    id: string,
    lod: 'high' | 'medium' | 'low'
  ): Promise<GameObject>;
  
  unloadModel(entityId: string): Promise<void>;
  
  updateLOD(entityId: string, cameraDistance: number): void;
  
  preloadModels(category: string): Promise<void>;
  
  getModelStats(): ModelStats;
}
```

#### VircadiaPhysicsService

```typescript
interface VircadiaPhysicsService {
  applyComponentPhysics(
    componentType: string,
    entity: GameObject,
    lod: string
  ): Promise<void>;
  
  removePhysics(entity: GameObject): void;
  
  applyForce(entityId: string, force: Vector3): Promise<void>;
  
  setMass(entityId: string, mass: number): Promise<void>;
}
```

### 后端服务 API

#### CircuitValidationService

```python
class CircuitValidationService:
    def register_pcb_board(self, design: PCBDesign) -> str:
        """注册 PCB 设计"""
        
    def add_component(self, board_id: str, data: dict) -> bool:
        """添加元件到电路板"""
        
    def validate_assembly(self, board_id: str) -> ValidationResult:
        """验证电路板组装"""
        
    def check_erc(self, netlist: Netlist) -> list[str]:
        """执行电气规则检查"""
```

---

## 🔍 调试技巧

### 常见问题排查

#### 问题 1: 模型加载失败

**症状**: 控制台报错 `Failed to load GLTF`

**解决方案**:
```typescript
// 1. 检查模型路径
console.log('Loading from:', modelPath);

// 2. 验证文件存在
fetch(modelPath, { method: 'HEAD' })
  .then(response => {
    if (!response.ok) {
      console.error('Model file not found!');
    }
  });

// 3. 使用 GLTFLoader 的 onError 回调
this.loader.load(
  modelPath,
  (gltf) => { /* success */ },
  undefined,
  (error) => {
    console.error('GLTF loading error:', error);
  }
);
```

#### 问题 2: 物理碰撞不生效

**症状**: 元件可以穿模

**解决方案**:
```typescript
// 1. 确认已添加碰撞盒
await this.physics.applyComponentPhysics(type, entity, lod);

// 2. 检查碰撞盒大小
const collider = entity.collider;
console.log('Collider size:', collider.size);

// 3. 确保刚体启用
entity.rigidbody.enabled = true;
entity.rigidbody.useGravity = true;
```

#### 问题 3: 吸附精度不够

**症状**: 元件无法准确对齐焊盘

**解决方案**:
```typescript
// 调整吸附阈值
const SNAP_THRESHOLD = 0.02; // 2cm

// 使用更精确的射线检测
const hit = this.raycaster.intersectObject(padMesh);
if (hit.distance < SNAP_THRESHOLD) {
  // 执行吸附
}

// 添加可视化辅助
this.debugHelper.showSnapZone(pad.position, SNAP_THRESHOLD);
```

---

## 🚀 进阶主题

### 自定义元件类别

```typescript
// 扩展 ComponentType 枚举
type CustomComponentType = 
  | 'transistor' 
  | 'mosfet' 
  | 'ic_555_timer'
  | 'operational_amplifier';

// 添加物理预设
PHYSICS_PRESETS['transistor'] = {
  mass: 0.005,
  colliderType: 'box',
  friction: 0.65,
  bounciness: 0.15
};
```

### SPICE 仿真集成 (未来)

```typescript
// 预留 SPICE 接口
interface SpiceSimulator {
  runTransientAnalysis(circuit: Circuit): Promise<Waveform[]>;
  runACAnalysis(circuit: Circuit): Promise<FrequencyResponse>;
  runDCSweep(circuit: Circuit): Promise<VICurve>;
}

// 当前使用简化仿真，未来可集成 ngspice.js
```

---

## 📞 获取帮助

### 文档资源

- [`LOCAL_DEPLOYMENT_GUIDE.md`](./docs/LOCAL_DEPLOYMENT_GUIDE.md) - 部署指南
- [`QUICK_START_3D_MODEL_LIBRARY.md`](./docs/QUICK_START_3D_MODEL_LIBRARY.md) - 快速开始
- [`KICAD_MODEL_SELECTION_GUIDE.md`](./docs/KICAD_MODEL_SELECTION_GUIDE.md) - 模型选择
- [`GLOBAL_TECHNICAL_ARCHITECTURE.md`](./docs/GLOBAL_TECHNICAL_ARCHITECTURE.md) - 全局架构

### 诊断工具

```powershell
# 运行完整验证
python scripts\validate_3d_model_implementation.py

# 查看详细日志
Get-Content logs\*.log -Tail 100
```

### 社区支持

- GitHub Issues: 提交 bug 报告和功能请求
- 项目文档：https://github.com/iMatu/docs
- 技术讨论：加入 iMatu 开发者 Discord

---

**最后更新**: 2026-03-03  
**文档版本**: v1.0  
**维护者**: iMatu Development Team

*祝开发愉快!* 🚀
