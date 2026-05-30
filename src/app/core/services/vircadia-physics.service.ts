/**
 * Vircadia 物理引擎服务
 *
 * 为 3D 模型添加刚体物理属性和碰撞检测功能
 * 基于 Vircadia 内置物理引擎实现
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { Injectable } from '@angular/core';

import { GameObject, Vector3, VirtualWorldEvent } from '../../models/vircadia.models';

import { VircadiaSdkService } from './vircadia-sdk.service';

/**
 * 元件物理属性预设
 *
 * 用途：定义常用电子元件的标准物理参数，确保真实的物理模拟效果
 */
export interface PhysicsProperties {
  /** 质量（千克） */
  mass: number;
  /** 碰撞体类型 */
  colliderType: 'box' | 'sphere' | 'capsule' | 'cylinder' | 'mesh';
  /** 碰撞体尺寸 */
  colliderSize?: Vector3;
  /** 摩擦系数 (0-1) */
  friction: number;
  /** 弹性系数 (0-1) */
  bounciness: number;
  /** 是否为触发器（不产生物理碰撞，仅检测） */
  isTrigger: boolean;
  /** 是否受重力影响 */
  affectedByGravity: boolean;
}

/**
 * 刚体配置
 */
export interface RigidBodyConfig {
  /** 刚体类型 */
  type: 'static' | 'dynamic' | 'kinematic';
  /** 物理属性 */
  properties: PhysicsProperties;
  /** 约束条件 */
  constraints?: {
    freezeRotation?: boolean;
    freezePosition?: boolean;
    axisLock?: 'x' | 'y' | 'z' | Array<'x' | 'y' | 'z'>;
  };
}

/**
 * 碰撞事件数据
 */
export interface CollisionEvent {
  /** 碰撞 ID */
  collisionId: string;
  /** 物体 A ID */
  entityA: GameObject;
  /** 物体 B ID */
  entityB: GameObject;
  /** 接触点坐标 */
  contactPoint: Vector3;
  /** 碰撞冲量 */
  impulse: number;
  /** 相对速度 */
  relativeVelocity: number;
  /** 碰撞时间戳 */
  timestamp: Date;
}

/**
 * 元件物理属性预设
 *
 * 用途：定义常用电子元件的标准物理参数，确保真实的物理模拟效果
 */
export const PHYSICS_PRESETS: Record<string, PhysicsProperties> = {
  // 电阻类 - 小质量，有摩擦
  resistor_axial: {
    mass: 0.01, // 10 克，典型轴向电阻质量
    colliderType: 'box', // 长方体碰撞盒
    colliderSize: { x: 0.012, y: 0.006, z: 0.006 }, // 12mm x 6mm x 6mm
    friction: 0.7, // 较高摩擦，防止滑动
    bounciness: 0.1, // 低弹性
    isTrigger: false, // 实体碰撞
    affectedByGravity: true, // 受重力影响
  },

  // 电容类 - 圆柱形
  capacitor_radial: {
    mass: 0.005, // 5 克
    colliderType: 'capsule', // 胶囊体 (近似圆柱)
    colliderSize: { x: 0.005, y: 0.011, z: 0.005 }, // 直径 5mm, 高 11mm
    friction: 0.6,
    bounciness: 0.15,
    isTrigger: false,
    affectedByGravity: true,
  },

  // IC 芯片 - DIP 封装
  ic_dip: {
    mass: 0.002, // 2 克
    colliderType: 'box',
    colliderSize: { x: 0.019, y: 0.008, z: 0.006 }, // DIP-8 标准尺寸
    friction: 0.5,
    bounciness: 0.1,
    isTrigger: false,
    affectedByGravity: true,
  },

  // IC 芯片 - SOP 表面贴装
  ic_soic: {
    mass: 0.001, // 1 克
    colliderType: 'box',
    colliderSize: { x: 0.005, y: 0.004, z: 0.002 }, // SOIC-8 尺寸
    friction: 0.5,
    bounciness: 0.1,
    isTrigger: false,
    affectedByGravity: true,
  },

  // LED - 圆柱形带引脚
  led_5mm: {
    mass: 0.003, // 3 克
    colliderType: 'capsule',
    colliderSize: { x: 0.005, y: 0.009, z: 0.005 }, // 5mm 直径，9mm 高
    friction: 0.6,
    bounciness: 0.2,
    isTrigger: false,
    affectedByGravity: true,
  },

  // 开关 - 按钮型
  switch_pushbutton: {
    mass: 0.008, // 8 克
    colliderType: 'box',
    colliderSize: { x: 0.006, y: 0.006, z: 0.006 }, // 6x6mm 按钮开关
    friction: 0.7,
    bounciness: 0.15,
    isTrigger: false,
    affectedByGravity: true,
  },

  // 晶振 - HC49 封装
  crystal_hc49: {
    mass: 0.004, // 4 克
    colliderType: 'box',
    colliderSize: { x: 0.011, y: 0.003, z: 0.003 }, // HC49-U 尺寸
    friction: 0.5,
    bounciness: 0.1,
    isTrigger: false,
    affectedByGravity: true,
  },

  // 连接器 - 排针
  connector_pin_header: {
    mass: 0.01, // 10 克
    colliderType: 'box',
    colliderSize: { x: 0.025, y: 0.008, z: 0.003 }, // 单排 20P 尺寸
    friction: 0.6,
    bounciness: 0.1,
    isTrigger: false,
    affectedByGravity: true,
  },
};

@Injectable({
  providedIn: 'root',
})
export class VircadiaPhysicsService {
  // 碰撞事件监听器
  private collisionListeners: Set<(event: CollisionEvent) => void> = new Set();

  // 已注册的刚体列表
  private rigidBodies: Map<string, RigidBodyConfig> = new Map();

  constructor(private vircadiaSdk: VircadiaSdkService) {
    this.setupCollisionDetection();
  }

  /**
   * 设置碰撞检测系统
   */
  private setupCollisionDetection(): void {
    // 监听 Vircadia 物理碰撞事件
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    this.vircadiaSdk.on('physics.collision', (event: VirtualWorldEvent) => {
      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
      const collisionEvent: CollisionEvent = {
        collisionId: String(event.data?.['eventId'] ?? `collision_${Date.now()}`),
        entityA: event.data?.['entityA'] as GameObject,
        entityB: event.data?.['entityB'] as GameObject,
        contactPoint: event.data?.['contactPoint'] as Vector3,
        impulse: Number(event.data?.['impulse'] ?? 0),
        relativeVelocity: Number(event.data?.['relativeVelocity'] ?? 0),
        timestamp: new Date(),
      };

      // 通知所有监听器
      this.collisionListeners.forEach((listener) => {
        try {
          listener(collisionEvent);
        } catch (error) {
          console.error('Collision listener error:', error);
        }
      });

      // 自动处理电路连接检测
      this.handleCircuitCollision(collisionEvent);
    });
  }

  /**
   * 为实体添加刚体组件
   *
   * @param entityId 实体 ID
   * @param config 刚体配置
   */
  async addRigidBody(entityId: string, config: RigidBodyConfig): Promise<boolean> {
    try {
      // 更新对象状态
      await this.vircadiaSdk.updateObjectState(entityId, {
        rigidbody: {
          type: config.type,
          mass: config.properties.mass,
          collider: {
            type: config.properties.colliderType,
            size: config.properties.colliderSize,
            isTrigger: config.properties.isTrigger,
          },
          physicsMaterial: {
            friction: config.properties.friction,
            bounciness: config.properties.bounciness,
          },
          constraints: config.constraints,
          affectedByGravity: config.properties.affectedByGravity,
        },
      });

      // 记录配置
      this.rigidBodies.set(entityId, config);

      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * 应用预设的物理属性到元件
   *
   * @param componentId 元件 ID
   * @param entity 实体对象
   * @param lodLevel LOD 级别 (用于调整碰撞盒精度)
   */
  async applyComponentPhysics(
    componentId: string,
    entity: GameObject,
    lodLevel: 'high' | 'medium' | 'low' = 'medium'
  ): Promise<boolean> {
    // 查找匹配的预设
    const preset = this.findMatchingPreset(componentId);

    if (!preset) {
      return false;
    }

    // 根据 LOD 级别调整碰撞盒精度
    const colliderSize = this.adjustColliderForLOD(preset.colliderSize, lodLevel);

    const config: RigidBodyConfig = {
      type: 'dynamic', // 动态刚体
      properties: {
        ...preset,
        colliderSize,
      },
      constraints: {
        freezeRotation: false, // 允许旋转
        freezePosition: false, // 允许移动
        axisLock: undefined, // 不锁定轴向
      },
    };

    await this.addRigidBody(entity.id, config);
    return true;
  }

  /**
   * 查找匹配的物理预设
   */
  private findMatchingPreset(componentId: string): PhysicsProperties | null {
    // 尝试精确匹配
    if (PHYSICS_PRESETS[componentId]) {
      return PHYSICS_PRESETS[componentId];
    }

    // 尝试模糊匹配 (通过类别)
    const categoryMap: Record<string, string> = {
      resistor: 'resistor_axial',
      capacitor: 'capacitor_radial',
      ic_dip: 'ic_dip',
      ic_soic: 'ic_soic',
      led: 'led_5mm',
      switch: 'switch_pushbutton',
      crystal: 'crystal_hc49',
      connector: 'connector_pin_header',
    };

    for (const [key, presetKey] of Object.entries(categoryMap)) {
      if (componentId.toLowerCase().includes(key)) {
        return PHYSICS_PRESETS[presetKey];
      }
    }

    return null;
  }

  /**
   * 根据 LOD 级别调整碰撞盒尺寸
   */
  private adjustColliderForLOD(
    originalSize: Vector3 | undefined,
    lodLevel: 'high' | 'medium' | 'low'
  ): Vector3 | undefined {
    if (!originalSize) {
      return undefined;
    }

    // LOD 越低，碰撞盒越简化
    const simplificationFactor = {
      high: 1.0, // 100% 精度
      medium: 0.8, // 80% 精度
      low: 0.6, // 60% 精度
    };

    const factor = simplificationFactor[lodLevel];

    return {
      x: originalSize.x * factor,
      y: originalSize.y * factor,
      z: originalSize.z * factor,
    };
  }

  /**
   * 注册碰撞事件监听器
   */
  onCollision(listener: (event: CollisionEvent) => void): void {
    this.collisionListeners.add(listener);
  }

  /**
   * 移除碰撞事件监听器
   */
  offCollision(listener: (event: CollisionEvent) => void): void {
    this.collisionListeners.delete(listener);
  }

  /**
   * 处理电路相关的碰撞 (用于检测元件是否正确放置)
   */
  private handleCircuitCollision(event: CollisionEvent): void {
    const entityA = event.entityA;
    const entityB = event.entityB;

    // 检查是否是元件与焊盘的碰撞
    const isComponentToPad =
      (this.isComponent(entityA) && this.isSolderPad(entityB)) ||
      (this.isComponent(entityB) && this.isSolderPad(entityA));

    if (isComponentToPad) {
      // 触发吸附逻辑
      this.triggerSnapLogic(event);
    }
  }

  /**
   * 判断是否为电子元件
   */
  private isComponent(entity: GameObject): boolean {
    const metadata = entity.metadata;
    if (!metadata) {
      return false;
    }
    return (
      metadata['category'] === 'resistor' ||
      metadata['category'] === 'capacitor' ||
      metadata['category'] === 'ic' ||
      metadata['category'] === 'led' ||
      metadata['category'] === 'switch' ||
      metadata['category'] === 'crystal'
    );
  }

  /**
   * 判断是否为焊盘
   */
  private isSolderPad(entity: GameObject): boolean {
    const metadata = entity.metadata;
    if (!metadata) {
      return false;
    }
    return metadata['type'] === 'solder_pad';
  }

  /**
   * 触发吸附逻辑
   */
  private triggerSnapLogic(collisionEvent: CollisionEvent): void {
    // 如果碰撞速度很小，说明元件接近静止，可以执行吸附
    if (collisionEvent.relativeVelocity < 0.1) {
      // TODO: 调用组装服务的吸附方法
      // this.circuitAssemblyService.snapToPad(component, pad);
    }
  }

  /**
   * 移除刚体
   */
  async removeRigidBody(entityId: string): Promise<boolean> {
    try {
      await this.vircadiaSdk.updateObjectState(entityId, {
        rigidbody: null,
      });

      this.rigidBodies.delete(entityId);

      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * 获取刚体配置
   */
  getRigidBodyConfig(entityId: string): RigidBodyConfig | null {
    return this.rigidBodies.get(entityId) ?? null;
  }

  /**
   * 设置重力
   */
  async setGravity(gravity: Vector3): Promise<void> {
    try {
      await this.vircadiaSdk.updateObjectState('world', {
        physics: {
          gravity,
        },
      });
    } catch (error) {
      // 忽略错误
    }
  }

  /**
   * 清除所有物理配置
   */
  clearAll(): void {
    this.rigidBodies.clear();
    this.collisionListeners.clear();
  }
}
