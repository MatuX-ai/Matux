/* eslint-disable @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access */
/**
 * 简化电路模拟器服务
 *
 * 实现基础电路状态模拟，用于虚拟实验室中的电路行为仿真
 * 支持 LED 亮灭、开关控制等简单逻辑
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { Injectable } from '@angular/core';
import * as THREE from 'three';

import {
  CircuitComponent,
  CircuitDescription,
  ComponentState,
  Connection,
  ConnectionPoint,
  SimulationResult,
} from '../../models/circuit.models';

/**
 * 电路拓扑分析结果
 */
interface CircuitAnalysis {
  powerNodes: string[];
  groundNodes: string[];
  signalPaths: Map<string, string[]>;
}

/**
 * 组件连接图
 */
interface CircuitGraph {
  nodes: Map<string, ConnectionPoint[]>;
  components: Map<string, CircuitComponent>;
}

/**
 * 场景实体类型
 */
interface SceneEntity {
  material?: {
    setEmissive?: (color: THREE.Color) => void;
    emissiveIntensity?: number;
  };
  metadata?: {
    type?: string;
  };
}

@Injectable({
  providedIn: 'root',
})
export class CircuitSimulatorService {
  // 电源电压 (伏特)
  private defaultSupplyVoltage = 5.0;

  // 地电位 (伏特)
  private groundPotential = 0;

  // LED 导通电压 (伏特)
  private ledForwardVoltage = 2.0;

  // LED 限流电阻最小值 (欧姆)
  private minLedResistor = 100;

  constructor() {}

  /**
   * 模拟电路状态
   *
   * @param circuit 电路描述
   * @returns 仿真结果
   */
  simulateCircuit(circuit: CircuitDescription): SimulationResult {
    const startTime = Date.now();

    // 1. 构建电路连接图
    const circuitGraph = this.buildCircuitGraph(circuit);

    // 2. 分析电路拓扑
    const analysis = this.analyzeCircuitTopology(circuitGraph, circuit);

    // 3. 计算各组件状态
    const componentStates = this.calculateComponentStates(
      circuit.components,
      circuit.connections,
      analysis
    );

    // 4. 检查电路完整性
    const isComplete = this.checkCircuitComplete(circuitGraph);

    // 5. 生成警告信息
    const warnings = this.generateWarnings(circuit, componentStates);

    const simulationTime = Date.now() - startTime;

    return {
      componentStates,
      isComplete,
      warnings,
      simulationTime,
    };
  }

  /**
   * 构建电路连接图
   */
  private buildCircuitGraph(circuit: CircuitDescription): CircuitGraph {
    const graph: CircuitGraph = {
      nodes: new Map(),
      components: new Map(),
    };

    // 添加所有组件
    circuit.components.forEach((comp) => {
      graph.components.set(comp.id, comp);
    });

    // 建立节点映射
    circuit.connections.forEach((conn) => {
      // 为每个连接创建网络节点
      const nodeId =
        `net_${conn.from.componentId}_${conn.from.pinId}_` +
        `${conn.to.componentId}_${conn.to.pinId}`;

      const points = [conn.from, conn.to];
      graph.nodes.set(nodeId, points);
    });

    return graph;
  }

  /**
   * 分析电路拓扑结构
   */
  private analyzeCircuitTopology(
    graph: CircuitGraph,
    circuit: CircuitDescription
  ): {
    powerNodes: string[];
    groundNodes: string[];
    signalPaths: Map<string, string[]>;
  } {
    const powerNodes: string[] = [];
    const groundNodes: string[] = [];
    const signalPaths = new Map<string, string[]>();

    // 查找电源和地网络
    circuit.components.forEach((comp) => {
      if (comp.type === 'battery' || comp.type === 'ground') {
        comp.pins.forEach((pin) => {
          if (pin.pinType === 'power') {
            powerNodes.push(`${comp.id}_${pin.id}`);
          } else if (pin.pinType === 'ground') {
            groundNodes.push(`${comp.id}_${pin.id}`);
          }
        });
      }
    });

    return { powerNodes, groundNodes, signalPaths };
  }

  /**
   * 计算组件状态
   */
  private calculateComponentStates(
    components: CircuitComponent[],
    connections: Connection[],
    _analysis: CircuitAnalysis
  ): Map<string, ComponentState> {
    const states = new Map<string, ComponentState>();

    // 第一步：初始化开关状态
    const switchStates = this.initializeSwitchStates(components);

    // 第二步：检查电路是否形成闭合回路
    const hasPowerPath = this.checkPowerPath(components, connections, switchStates);

    // 第三步：计算各组件状态
    components.forEach((comp) => {
      const state = this.calculateSingleComponentState(
        comp,
        connections,
        components,
        hasPowerPath,
        switchStates
      );
      states.set(comp.id, state);
    });

    return states;
  }

  /**
   * 初始化开关状态
   */
  private initializeSwitchStates(components: CircuitComponent[]): Map<string, boolean> {
    const switchStates = new Map<string, boolean>();
    components.forEach((comp) => {
      if (comp.type === 'switch' || comp.type === 'button') {
        // 默认开关闭合
        switchStates.set(comp.id, comp.state?.isClosed ?? true);
      }
    });
    return switchStates;
  }

  /**
   * 计算单个组件的状态
   */
  private calculateSingleComponentState(
    comp: CircuitComponent,
    connections: Connection[],
    components: CircuitComponent[],
    hasPowerPath: boolean,
    switchStates: Map<string, boolean>
  ): ComponentState {
    switch (comp.type) {
      case 'led':
        return this.calculateLEDState(comp, connections, components, hasPowerPath);

      case 'resistor':
        return this.calculateResistorState(comp, connections, components, hasPowerPath);

      case 'switch':
      case 'button':
        return this.calculateSwitchState(comp, switchStates);

      case 'battery':
        return this.calculateBatteryState(comp);

      default:
        return this.calculateDefaultState(hasPowerPath);
    }
  }

  /**
   * 检查电源路径是否存在
   */
  private checkPowerPath(
    components: CircuitComponent[],
    connections: Connection[],
    switchStates: Map<string, boolean>
  ): boolean {
    // 简化的检查逻辑：
    // 1. 必须有电源
    // 2. 必须有完整回路
    // 3. 所有开关必须闭合

    const hasBattery = components.some((c) => c.type === 'battery');
    if (!hasBattery) {
      return false;
    }

    // 检查所有开关
    for (const [, isClosed] of switchStates.entries()) {
      if (!isClosed) {
        return false;
      }
    }

    // TODO: 实现完整的回路检测算法 (使用 DFS/BFS)
    // 这里简化处理：假设有电池且开关闭合就有回路
    return true;
  }

  /**
   * 计算 LED 状态
   */
  private calculateLEDState(
    led: CircuitComponent,
    connections: Connection[],
    components: CircuitComponent[],
    hasPowerPath: boolean
  ): ComponentState {
    const state: ComponentState = {};
    state.isOn = hasPowerPath && this.checkLEDPolarity(led, connections);
    state.brightness = state.isOn ? 1.0 : 0.0;

    if (state.isOn) {
      state.voltageAcross = this.ledForwardVoltage;
      // 估算电流 (I = V/R)
      const resistorValue = this.findSeriesResistor(led, connections, components);
      if (resistorValue > 0) {
        state.currentThrough = (this.defaultSupplyVoltage - this.ledForwardVoltage) / resistorValue;
      }
    }
    return state;
  }

  /**
   * 计算电阻状态
   */
  private calculateResistorState(
    resistor: CircuitComponent,
    connections: Connection[],
    components: CircuitComponent[],
    hasPowerPath: boolean
  ): ComponentState {
    const state: ComponentState = {};
    state.voltageAcross = hasPowerPath
      ? this.calculateResistorVoltage(resistor, connections, components)
      : 0;
    if (state.voltageAcross > 0) {
      const resistance = this.parseResistanceValue(resistor.value);
      state.currentThrough = state.voltageAcross / resistance;
      state.power = state.voltageAcross * state.currentThrough;
    }
    return state;
  }

  /**
   * 计算开关状态
   */
  private calculateSwitchState(
    switchComp: CircuitComponent,
    switchStates: Map<string, boolean>
  ): ComponentState {
    const state: ComponentState = {};
    state.isClosed = switchStates.get(switchComp.id) ?? false;
    state.voltageAcross = state.isClosed ? 0 : this.defaultSupplyVoltage;
    return state;
  }

  /**
   * 计算电池状态
   */
  private calculateBatteryState(battery: CircuitComponent): ComponentState {
    const state: ComponentState = {};
    state.voltageAcross = this.parseVoltageValue(battery.value);
    return state;
  }

  /**
   * 计算默认状态
   */
  private calculateDefaultState(hasPowerPath: boolean): ComponentState {
    const state: ComponentState = {};
    state.isOn = hasPowerPath;
    return state;
  }

  /**
   * 检查 LED 极性是否正确
   */
  private checkLEDPolarity(led: CircuitComponent, connections: Connection[]): boolean {
    // 查找 LED 的阳极连接
    const anodeConnection = connections.find(
      (conn) =>
        (conn.from.componentId === led.id && conn.from.pinId === 'anode') ||
        (conn.to.componentId === led.id && conn.to.pinId === 'anode')
    );

    if (!anodeConnection) {
      return false;
    }

    // TODO: 追踪到电源正极
    // 简化：假设连接了就正确
    return true;
  }

  /**
   * 查找与 LED 串联的电阻
   */
  private findSeriesResistor(
    led: CircuitComponent,
    connections: Connection[],
    components: CircuitComponent[]
  ): number {
    // 查找与 LED 直接连接的组件
    const connectedComponentIds = new Set<string>();

    connections.forEach((conn) => {
      if (conn.from.componentId === led.id || conn.to.componentId === led.id) {
        connectedComponentIds.add(conn.from.componentId);
        connectedComponentIds.add(conn.to.componentId);
      }
    });

    // 查找其中的电阻
    for (const compId of connectedComponentIds) {
      const comp = components.find((c) => c.id === compId);
      if (comp && comp.type === 'resistor') {
        return this.parseResistanceValue(comp.value);
      }
    }

    return 0;
  }

  /**
   * 计算电阻两端电压
   */
  private calculateResistorVoltage(
    _resistor: CircuitComponent,
    _connections: Connection[],
    _components: CircuitComponent[]
  ): number {
    // 简化计算：假设电阻直接接在电源两端
    return this.defaultSupplyVoltage;
  }

  /**
   * 检查电路完整性
   */
  private checkCircuitComplete(graph: CircuitGraph): boolean {
    // 检查是否有孤立节点
    let isolatedNodes = 0;

    graph.nodes.forEach((points, _nodeId) => {
      if (points.length === 0) {
        isolatedNodes++;
      }
    });

    return isolatedNodes === 0;
  }

  /**
   * 生成警告信息
   */
  private generateWarnings(
    circuit: CircuitDescription,
    states: Map<string, ComponentState>
  ): string[] {
    const warnings: string[] = [];

    // 检查 LED 是否有限流电阻
    const leds = circuit.components.filter((c) => c.type === 'led');
    leds.forEach((led) => {
      const state = states.get(led.id);
      if (state?.isOn) {
        const hasResistor = this.hasCurrentLimitingResistor(led, circuit);
        if (!hasResistor) {
          warnings.push(`LED "${led.designator}" 缺少限流电阻!`);
        }
      }
    });

    // 检查电源短路
    if (this.checkShortCircuit(circuit)) {
      warnings.push('检测到电源短路风险!');
    }

    return warnings;
  }

  /**
   * 检查是否有限流电阻
   */
  private hasCurrentLimitingResistor(led: CircuitComponent, circuit: CircuitDescription): boolean {
    // 查找与 LED 串联的电阻
    const resistors = circuit.components.filter((c) => c.type === 'resistor');

    for (const resistor of resistors) {
      if (this.isInSeries(led, resistor, circuit.connections)) {
        return true;
      }
    }

    return false;
  }

  /**
   * 判断两个元件是否串联
   */
  private isInSeries(
    comp1: CircuitComponent,
    comp2: CircuitComponent,
    connections: Connection[]
  ): boolean {
    // 简化判断：如果有直接连接，则认为串联
    return connections.some(
      (conn) =>
        (conn.from.componentId === comp1.id && conn.to.componentId === comp2.id) ||
        (conn.from.componentId === comp2.id && conn.to.componentId === comp1.id)
    );
  }

  /**
   * 检查短路
   */
  private checkShortCircuit(circuit: CircuitDescription): boolean {
    // 简化检查：如果电源两端直接用导线连接，认为短路
    const battery = circuit.components.find((c) => c.type === 'battery');
    if (!battery) {
      return false;
    }

    // TODO: 实现完整的短路检测
    return false;
  }

  /**
   * 解析电阻值
   */
  private parseResistanceValue(value: string): number {
    // 解析 "330Ω", "10k", "1M" 等格式
    const match = value.match(/([\d.]+)\s*([kKMΩ])?/);
    if (!match) {
      return 0;
    }

    const num = parseFloat(match[1]);
    const unit = match[2];

    if (unit === 'k' || unit === 'K') {
      return num * 1000;
    } else if (unit === 'M') {
      return num * 1000000;
    }

    return num;
  }

  /**
   * 解析电压值
   */
  private parseVoltageValue(value: string): number {
    const match = value.match(/([\d.]+)\s*[Vv]?/);
    return match ? parseFloat(match[1]) : 0;
  }

  /**
   * 更新可视化状态
   *
   * 根据仿真结果更新 3D 场景中的元件状态
   */
  updateVisualization(result: SimulationResult, sceneObjects: Map<string, SceneEntity>): void {
    result.componentStates.forEach((state, componentId) => {
      const entity = sceneObjects.get(componentId);

      if (!entity || typeof entity !== 'object' || entity === null) {
        return;
      }

      // 更新 LED 亮度
      if (state.isOn !== undefined && entity.metadata?.type === 'led') {
        this.setLEDBrightness(entity, state.brightness ?? 0);
      }

      // 更新开关状态 - TODO: 实现开关状态更新
      // if (
      //   state.isClosed !== undefined &&
      //   entity.metadata?.type === 'switch'
      // ) {
      //   this.setSwitchState(entity, state.isClosed);
      // }
    });
  }

  /**
   * 设置 LED 亮度
   */
  private setLEDBrightness(entity: SceneEntity, brightness: number): void {
    // TODO: 调用渲染引擎设置 LED 自发光材质

    // 示例：设置 emissive color
    if (brightness > 0) {
      entity.material?.setEmissive?.(new THREE.Color(0xff0000));
      if (entity.material) {
        entity.material.emissiveIntensity = brightness;
      }
    } else {
      entity.material?.setEmissive?.(new THREE.Color(0x000000));
      if (entity.material) {
        entity.material.emissiveIntensity = 0;
      }
    }
  }

  /**
   * 重置仿真器
   */
  reset(): void {}
}
