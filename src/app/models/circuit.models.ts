/**
 * 电路数据协议类型定义
 *
 * 定义轻量级电路描述协议，用于在虚拟实验室中描述电路结构、
 * 元件连接关系和电气参数
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

// ==================== 基础电路数据结构 ====================

/**
 * 电路描述文件 (JSON 格式)
 *
 * 用途：完整描述一个电路的所有信息，包括元件、连接、参数等
 */
export interface CircuitDescription {
  /** 电路唯一标识符 */
  id: string;

  /** 电路名称 */
  name: string;

  /** 电路描述 */
  description?: string;

  /** 电路版本 */
  version?: string;

  /** 元件列表 */
  components: CircuitComponent[];

  /** 连接关系列表 */
  connections: Connection[];

  /** 网络标签列表 */
  nets?: Net[];

  /** 电气参数 */
  electricalParams?: ElectricalParams;

  /** 元数据 */
  metadata?: CircuitMetadata;
}

/**
 * 电路元件
 *
 * 用途：描述电路中的一个具体元件及其属性
 */
export interface CircuitComponent {
  /** 元件唯一标识符 (如 R1, C2, U3) */
  id: string;

  /** 元件类型 */
  type: ComponentType;

  /** 元件值 (如 "10kΩ", "100μF", "5V") */
  value: string;

  /** 位号 (Designator, 如 R1, C2) */
  designator: string;

  /** 封装类型 (如 axial, dip-8, soic-8) */
  package: string;

  /** 引脚定义 */
  pins: Pin[];

  /** 3D 模型引用 */
  modelRef?: string;

  /** 当前状态 */
  state?: ComponentState;

  /** 物理位置 (在 PCB 上的坐标) */
  footprint?: FootprintPosition;

  /** 额外参数 */
  parameters?: ComponentParameters;
}

/**
 * 元件类型枚举
 */
export type ComponentType =
  | 'resistor' // 电阻
  | 'capacitor' // 电容
  | 'inductor' // 电感
  | 'diode' // 二极管
  | 'led' // 发光二极管
  | 'transistor' // 三极管
  | 'mosfet' // MOSFET
  | 'ic' // 集成电路
  | 'opamp' // 运算放大器
  | 'switch' // 开关
  | 'button' // 按钮
  | 'battery' // 电池/电源
  | 'ground' // 接地
  | 'connector' // 连接器
  | 'potentiometer' // 电位器
  | 'crystal' // 晶振
  | 'fuse' // 保险丝
  | 'custom'; // 自定义元件

/**
 * 引脚定义
 */
export interface Pin {
  /** 引脚编号或名称 (如 "1", "2", "A", "B", "VCC", "GND") */
  id: string;

  /** 引脚名称 (可选，如 "Anode", "Cathode") */
  name?: string;

  /** 引脚类型 */
  pinType: PinType;

  /** 引脚序号 (物理位置) */
  pinNumber?: number;

  /** 当前电气状态 */
  electricalState?: ElectricalState;
}

/**
 * 引脚类型
 */
export type PinType =
  | 'input' // 输入
  | 'output' // 输出
  | 'power' // 电源
  | 'ground' // 接地
  | 'bidirectional' // 双向
  | 'passive'; // 无源

/**
 * 连接关系
 *
 * 用途：描述两个引脚之间的电气连接
 */
export interface Connection {
  /** 连接唯一标识符 */
  id: string;

  /** 起点 */
  from: ConnectionPoint;

  /** 终点 */
  to: ConnectionPoint;

  /** 导线类型 */
  wireType: WireType;

  /** 导线电阻 (欧姆，可选) */
  resistance?: number;

  /** 导线长度 (米，可选) */
  length?: number;

  /** 颜色 (可选) */
  color?: string;
}

/**
 * 连接点
 */
export interface ConnectionPoint {
  /** 元件 ID */
  componentId: string;

  /** 引脚 ID */
  pinId: string;
}

/**
 * 导线类型
 */
export type WireType =
  | 'ideal' // 理想导线 (零电阻)
  | 'resistive' // 有阻导线
  | 'coaxial' // 同轴线
  | 'ribbon'; // 排线

/**
 * 网络 (Net)
 *
 * 用途：表示一组电气连接的集合 (如 VCC 网络、GND 网络)
 */
export interface Net {
  /** 网络名称 (如 "VCC", "GND", "SIGNAL_1") */
  name: string;

  /** 网络描述 */
  description?: string;

  /** 包含的连接点列表 */
  connectionPoints: ConnectionPoint[];

  /** 网络类别 */
  netClass?: NetClass;

  /** 电压等级 (伏特) */
  voltage?: number;
}

/**
 * 网络类别
 */
export type NetClass =
  | 'power' // 电源网络
  | 'ground' // 地网络
  | 'signal' // 信号网络
  | 'analog' // 模拟网络
  | 'digital' // 数字网络
  | 'high_voltage' // 高压网络
  | 'high_current'; // 大电流网络

/**
 * 电气参数
 */
export interface ElectricalParams {
  /** 电源电压 (伏特) */
  supplyVoltage?: number;

  /** 地电位 (伏特，通常为 0) */
  groundPotential?: number;

  /** 工作频率 (赫兹) */
  frequency?: number;

  /** 工作温度范围 (摄氏度) */
  temperatureRange?: {
    min: number;
    max: number;
  };

  /** 最大功率 (瓦特) */
  maxPower?: number;
}

/**
 * 元件状态
 */
export interface ComponentState {
  /** 是否导通/激活 */
  isOn?: boolean;

  /** 亮度 (0-1, LED 用) */
  brightness?: number;

  /** 开关状态 (开关用) */
  isClosed?: boolean;

  /** 两端电压 (伏特) */
  voltageAcross?: number;

  /** 流过电流 (安培) */
  currentThrough?: number;

  /** 功率 (瓦特) */
  power?: number;

  /** 温度 (摄氏度) */
  temperature?: number;
}

/**
 * 电气状态
 */
export interface ElectricalState {
  /** 电压 (伏特) */
  voltage?: number;

  /** 电流 (安培) */
  current?: number;

  /** 电位 (伏特) */
  potential?: number;

  /** 最后更新时间 */
  lastUpdate?: Date;
}

/**
 * 物理位置
 */
export interface FootprintPosition {
  /** X 坐标 (米) */
  x: number;

  /** Y 坐标 (米) */
  y: number;

  /** 旋转角度 (弧度) */
  rotation: number;

  /** 安装面 */
  side?: 'top' | 'bottom';
}

/**
 * 元件参数 (键值对)
 */
export interface ComponentParameters {
  [key: string]: any;
}

/**
 * 电路元数据
 */
export interface CircuitMetadata {
  /** 作者 */
  author?: string;

  /** 创建日期 */
  createdAt?: Date;

  /** 最后修改日期 */
  modifiedAt?: Date;

  /** 许可证 */
  license?: string;

  /** 标签 */
  tags?: string[];

  /** 难度等级 */
  difficultyLevel?: 'beginner' | 'intermediate' | 'advanced';

  /** 预计完成时间 (分钟) */
  estimatedTimeMinutes?: number;

  /** 学习目辬 */
  learningObjectives?: string[];
}

// ==================== 电路示例 ====================

/**
 * 简单 LED 电路示例
 *
 * 用途：演示电路描述文件的实际使用
 */
export const EXAMPLE_LED_CIRCUIT: CircuitDescription = {
  id: 'led-blinker-demo',
  name: 'LED 闪烁电路',
  description: '一个简单的 LED 闪烁电路，包含电阻、LED 和开关',
  version: '1.0',

  components: [
    {
      id: 'r1',
      type: 'resistor',
      value: '330Ω',
      designator: 'R1',
      package: 'axial',
      pins: [
        { id: 'pin1', name: 'Pin 1', pinType: 'passive' },
        { id: 'pin2', name: 'Pin 2', pinType: 'passive' },
      ],
      modelRef: 'resistor_axial_330',
      footprint: { x: 0.05, y: 0.02, rotation: 0 },
    },
    {
      id: 'led1',
      type: 'led',
      value: 'Red LED',
      designator: 'LED1',
      package: '5mm',
      pins: [
        { id: 'anode', name: 'Anode', pinType: 'input' },
        { id: 'cathode', name: 'Cathode', pinType: 'output' },
      ],
      modelRef: 'led_5mm_red',
      footprint: { x: 0.1, y: 0.02, rotation: 0 },
    },
    {
      id: 'sw1',
      type: 'switch',
      value: 'SPST',
      designator: 'SW1',
      package: 'pushbutton',
      pins: [
        { id: 'terminal1', name: 'Terminal 1', pinType: 'passive' },
        { id: 'terminal2', name: 'Terminal 2', pinType: 'passive' },
      ],
      modelRef: 'switch_pushbutton',
      footprint: { x: 0.02, y: 0.05, rotation: Math.PI / 2 },
    },
    {
      id: 'bat1',
      type: 'battery',
      value: '9V',
      designator: 'BAT1',
      package: '9v_battery',
      pins: [
        { id: 'positive', name: 'Positive (+)', pinType: 'power' },
        { id: 'negative', name: 'Negative (-)', pinType: 'ground' },
      ],
      footprint: { x: 0.02, y: 0.02, rotation: 0 },
    },
  ],

  connections: [
    {
      id: 'conn1',
      from: { componentId: 'bat1', pinId: 'positive' },
      to: { componentId: 'sw1', pinId: 'terminal1' },
      wireType: 'ideal',
    },
    {
      id: 'conn2',
      from: { componentId: 'sw1', pinId: 'terminal2' },
      to: { componentId: 'r1', pinId: 'pin1' },
      wireType: 'ideal',
    },
    {
      id: 'conn3',
      from: { componentId: 'r1', pinId: 'pin2' },
      to: { componentId: 'led1', pinId: 'anode' },
      wireType: 'ideal',
    },
    {
      id: 'conn4',
      from: { componentId: 'led1', pinId: 'cathode' },
      to: { componentId: 'bat1', pinId: 'negative' },
      wireType: 'ideal',
    },
  ],

  electricalParams: {
    supplyVoltage: 9,
    groundPotential: 0,
  },

  metadata: {
    author: 'iMatu Team',
    createdAt: new Date('2026-03-03'),
    difficultyLevel: 'beginner',
    estimatedTimeMinutes: 10,
    learningObjectives: ['理解串联电路原理', '掌握 LED 极性识别', '学习开关的使用方法'],
  },
};

// ==================== 辅助函数类型 ====================

/**
 * 电路验证结果
 */
export interface CircuitValidationResult {
  /** 是否有效 */
  isValid: boolean;

  /** 错误列表 */
  errors: string[];

  /** 警告列表 */
  warnings: string[];

  /** 验证时间戳 */
  timestamp: Date;
}

/**
 * 电路仿真结果
 */
export interface SimulationResult {
  /** 组件状态映射表 */
  componentStates: Map<string, ComponentState>;

  /** 电路是否完整/闭合 */
  isComplete: boolean;

  /** 警告信息 */
  warnings: string[];

  /** 仿真时间 */
  simulationTime: number;
}
