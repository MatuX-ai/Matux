/**
 * 电路组装服务
 *
 * 实现"拖放 - 吸附"的虚拟焊接/插装功能
 * 检测元件与焊盘的接近度，实现自动对齐吸附
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { HttpClient } from '@angular/common/http';
import { Injectable, Injector } from '@angular/core';
import { lastValueFrom } from 'rxjs';

import { GameObject, Quaternion, Vector3 } from '../../models/vircadia.models';

import { VircadiaSdkService } from './vircadia-sdk.service';

/**
 * 焊盘信息
 *
 * 用途：定义电路板上焊盘的几何和电气属性
 */
export interface SolderPad {
  /** 焊盘 ID */
  id: string;
  /** 焊盘名称 */
  name: string;
  /** 位置 */
  position: Vector3;
  /** 旋转 */
  rotation: Quaternion;
  /** 焊盘类型 */
  padType: 'tht' | 'smd' | 'socket';
  /** 引脚数量 */
  pinCount: number;
  /** 引脚间距 (mm) */
  pitch?: number;
  /** 孔径 (mm, THT 用) */
  holeSize?: number;
  /** 极性 (对于有极性元件) */
  polarity?: 'positive' | 'negative' | 'none';
  /** 网络标签 */
  netLabel?: string;
  /** 丝印层信息 */
  silkscreenInfo?: string;
}

/**
 * 元件封装信息
 */
export interface ComponentFootprint {
  /** 封装名称 */
  name: string;
  /** 焊盘列表 */
  pads: SolderPad[];
  /** 封装边界尺寸 */
  boundingBox: {
    min: Vector3;
    max: Vector3;
  };
  /** 推荐安装面 */
  recommendedSide: 'top' | 'bottom' | 'both';
}

/**
 * 组装步骤记录
 */
export interface AssemblyStep {
  /** 步骤 ID */
  stepId: string;
  /** 用户 ID */
  userId: string;
  /** 元件 ID */
  componentId: string;
  /** 焊盘 ID */
  padId: string;
  /** 时间戳 */
  timestamp: Date;
  /** 是否成功 */
  isSuccess: boolean;
  /** 错误信息 (如果失败) */
  errorMessage?: string;
  /** 尝试次数 */
  attemptNumber: number;
}

/**
 * 组装状态
 */
export enum AssemblyStatus {
  /** 未开始 */
  NOT_STARTED = 'not_started',
  /** 进行中 */
  IN_PROGRESS = 'in_progress',
  /** 已完成 */
  COMPLETED = 'completed',
  /** 错误 */
  ERROR = 'error',
}

@Injectable({
  providedIn: 'root',
})
export class CircuitAssemblyService {
  private http?: HttpClient;

  // 当前装配会话的焊盘映射
  private solderPads: Map<string, SolderPad> = new Map();

  // 已安装的元件
  private installedComponents: Map<string, { component: GameObject; pad: SolderPad }> = new Map();

  // 组装历史记录
  private assemblyHistory: AssemblyStep[] = [];

  // 当前用户 ID (应该从认证服务获取)
  private currentUserId: string = 'user_temp';

  // 配置参数
  private config = {
    // 吸附距离阈值 (米)
    snapThreshold: 0.02, // 2cm

    // 吸附动画持续时间 (毫秒)
    snapAnimationDuration: 300,

    // 验证精度
    validationTolerance: 0.001, // 1mm

    // 最大尝试次数
    maxAttempts: 3,
  };

  constructor(
    private vircadiaSdk: VircadiaSdkService,
    private injector: Injector
  ) {
    setTimeout(() => {
      this.http = this.injector.get(HttpClient);
    }, 0);
  }

  /**
   * 注册焊盘到组装系统
   */
  registerSolderPad(pad: SolderPad): void {
    this.solderPads.set(pad.id, pad);
  }

  /**
   * 批量注册焊盘
   */
  registerSolderPads(pads: SolderPad[]): void {
    pads.forEach((pad) => this.registerSolderPad(pad));
  }

  /**
   * 检测元件与焊盘的接近度
   *
   * @param component 元件对象
   * @param targetPads 目标焊盘列表
   * @returns 最近的焊盘 (如果在阈值内)
   */
  detectProximity(component: GameObject, targetPads: SolderPad[]): SolderPad | null {
    const componentPos = component.position;

    for (const pad of targetPads) {
      const distance = this.calculateDistance(componentPos, pad.position);

      if (distance < this.config.snapThreshold) {
        // 检测到接近的焊盘
        return pad;
      }
    }

    return null;
  }

  /**
   * 计算两点间距离
   */
  private calculateDistance(a: Vector3, b: Vector3): number {
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    const dz = a.z - b.z;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }

  /**
   * 自动对齐并吸附到焊盘
   *
   * @param component 元件对象
   * @param pad 目标焊盘
   */
  async snapToPad(component: GameObject, pad: SolderPad): Promise<boolean> {
    try {
      // 1. 验证连接是否有效
      const isValid = this.validateConnection(component, pad);

      if (!isValid) {
        const error = '元件与焊盘不匹配';

        this.recordAssemblyStep(component.id, pad.id, false, error);
        return false;
      }

      // 2. 播放吸附动画
      await this.animateSnap(component, pad.position, pad.rotation);

      // 3. 锁定位置
      await this.vircadiaSdk.updateObjectState(component.id, {
        position: pad.position,
        rotation: pad.rotation,
        metadata: {
          ...component.metadata,
          isSnapped: true,
          snappedToPadId: pad.id,
          snapTimestamp: Date.now(),
        },
      });

      // 4. 记录安装
      this.installedComponents.set(component.id, {
        component,
        pad,
      });

      // 5. 记录成功步骤
      this.recordAssemblyStep(component.id, pad.id, true);

      // 6. 触发连接事件
      this.emitConnectionEvent(component, pad);

      return true;
    } catch (error) {
      this.recordAssemblyStep(component.id, pad.id, false, String(error));
      return false;
    }
  }

  /**
   * 验证元件与焊盘的连接
   */
  validateConnection(component: GameObject, pad: SolderPad): boolean {
    const metadata = component.metadata;

    if (!metadata) {
      return false;
    }

    // 1. 检查引脚数量匹配
    if (!this.validatePinCount(metadata, pad)) {
      return false;
    }

    // 2. 检查封装类型兼容性
    if (!this.validatePackageType(metadata, pad)) {
      return false;
    }

    // 3. 检查极性 (如果有)
    if (!this.validatePolarity(metadata, pad)) {
      return false;
    }

    // 4. 检查焊盘是否已被占用
    if (this.isPadOccupied(pad)) {
      return false;
    }

    return true;
  }

  /**
   * 验证引脚数量匹配
   */
  private validatePinCount(metadata: Record<string, unknown>, pad: SolderPad): boolean {
    const componentPinCount = (metadata['pinCount'] as number) || 2; // 默认 2 引脚
    return componentPinCount === pad.pinCount;
  }

  /**
   * 验证封装类型兼容性
   */
  private validatePackageType(metadata: Record<string, unknown>, pad: SolderPad): boolean {
    const packageType = metadata['packageType'] as string;
    const padType = pad.padType;

    const compatibilityMap: Record<string, string[]> = {
      axial: ['tht'],
      radial: ['tht'],
      dip: ['tht'],
      soic: ['smd'],
      '5mm': ['tht'],
      '3mm': ['tht'],
      smd: ['smd'],
    };

    const compatiblePadTypes = compatibilityMap[packageType] || [];
    return compatiblePadTypes.length > 0 && compatiblePadTypes.includes(padType);
  }

  /**
   * 验证极性匹配
   */
  private validatePolarity(metadata: Record<string, unknown>, pad: SolderPad): boolean {
    const polarity = metadata['polarity'] as string | undefined;
    if (polarity && pad.polarity && pad.polarity !== 'none') {
      return polarity === pad.polarity;
    }
    return true;
  }

  /**
   * 检查焊盘是否已被占用
   */
  private isPadOccupied(pad: SolderPad): boolean {
    return Array.from(this.installedComponents.values()).some(
      (installed) => installed.pad.id === pad.id
    );
  }

  /**
   * 播放吸附动画
   */
  private async animateSnap(
    component: GameObject,
    targetPosition: Vector3,
    targetRotation: Quaternion
  ): Promise<void> {
    const startTime = Date.now();
    const duration = this.config.snapAnimationDuration;

    const startPos = component.position;
    const startRot = component.rotation;

    return new Promise((resolve) => {
      const animate = (): void => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1.0);

        // 缓动函数 (ease-out-cubic)
        const eased = 1 - Math.pow(1 - progress, 3);

        // 插值位置
        const currentPosition: Vector3 = {
          x: startPos.x + (targetPosition.x - startPos.x) * eased,
          y: startPos.y + (targetPosition.y - startPos.y) * eased,
          z: startPos.z + (targetPosition.z - startPos.z) * eased,
        };

        // 插值旋转 (简化处理)
        const currentRotation: Quaternion = {
          x: startRot.x + (targetRotation.x - startRot.x) * eased,
          y: startRot.y + (targetRotation.y - startRot.y) * eased,
          z: startRot.z + (targetRotation.z - startRot.z) * eased,
          w: startRot.w + (targetRotation.w - startRot.w) * eased,
        };

        // 更新对象位置
        this.vircadiaSdk
          .updateObjectState(component.id, {
            position: currentPosition,
            rotation: currentRotation,
          })
          .catch((err) => console.error('[Assembly] 动画更新失败:', err));

        if (progress < 1.0) {
          requestAnimationFrame(animate);
        } else {
          resolve();
        }
      };

      animate();
    });
  }

  /**
   * 记录组装步骤
   */
  private recordAssemblyStep(
    componentId: string,
    padId: string,
    isSuccess: boolean,
    errorMessage?: string
  ): void {
    const step: AssemblyStep = {
      stepId: `step_${Date.now()}`,
      userId: this.currentUserId,
      componentId,
      padId,
      timestamp: new Date(),
      isSuccess,
      errorMessage,
      attemptNumber: this.getAttemptCount(componentId) + 1,
    };

    this.assemblyHistory.push(step);

    // 同步到后端
    this.syncToBackend(step).catch((err) => console.error('[Assembly] 同步失败:', err));
  }

  /**
   * 获取某元件的尝试次数
   */
  private getAttemptCount(componentId: string): number {
    return this.assemblyHistory.filter((step) => step.componentId === componentId).length;
  }

  /**
   * 同步组装记录到后端
   */
  private async syncToBackend(step: AssemblyStep): Promise<void> {
    if (!this.http) return;

    try {
      await lastValueFrom(
        this.http.post('/api/v1/circuit/assembly/record', {
          session_id: step.stepId,
          component_id: step.componentId,
          pad_id: step.padId,
          user_id: step.userId,
          attempt_number: step.attemptNumber,
          is_success: step.isSuccess,
          timestamp: step.timestamp.toISOString(),
        })
      );
    } catch (error) {
      console.error('[CircuitAssembly] 同步组装记录失败:', error);
    }
  }

  /**
   * 触发连接事件 (用于积分系统等)
   */
  private emitConnectionEvent(component: GameObject, pad: SolderPad): void {
    const event = {
      type: 'circuit.component_connected',
      data: {
        componentId: component.id,
        componentName: component.name,
        padId: pad.id,
        padName: pad.name,
        timestamp: Date.now(),
        userId: this.currentUserId,
      },
    };

    // 发送到 Vircadia 事件系统
    this.vircadiaSdk
      .interact({
        objectId: 'circuit_board',
        interactionType: 'use',
        data: event.data,
      })
      .catch((err) => console.error('[Assembly] 发送事件失败:', err));
  }

  /**
   * 检查电路完整性
   */
  checkCircuitIntegrity(): { isValid: boolean; missingComponents: string[] } {
    const missingComponents: string[] = [];

    // 遍历所有焊盘，检查是否有未安装的
    this.solderPads.forEach((pad, padId) => {
      const isInstalled = Array.from(this.installedComponents.values()).some(
        (installed) => installed.pad.id === padId
      );

      if (!isInstalled) {
        missingComponents.push(pad.name);
      }
    });

    const isValid = missingComponents.length === 0;

    return { isValid, missingComponents };
  }

  /**
   * 获取组装进度
   */
  getAssemblyProgress(): {
    total: number;
    installed: number;
    percentage: number;
    status: AssemblyStatus;
  } {
    const total = this.solderPads.size;
    const installed = this.installedComponents.size;
    const percentage = total > 0 ? (installed / total) * 100 : 0;

    let status: AssemblyStatus;
    if (installed === 0) {
      status = AssemblyStatus.NOT_STARTED;
    } else if (installed === total) {
      status = AssemblyStatus.COMPLETED;
    } else {
      status = AssemblyStatus.IN_PROGRESS;
    }

    return { total, installed, percentage, status };
  }

  /**
   * 重置组装状态
   */
  reset(): void {
    this.installedComponents.clear();
    this.assemblyHistory = [];
  }

  /**
   * 获取组装历史
   */
  getHistory(): AssemblyStep[] {
    return [...this.assemblyHistory];
  }

  /**
   * 获取已安装的元件
   */
  getInstalledComponents(): Map<string, { component: GameObject; pad: SolderPad }> {
    return new Map(this.installedComponents);
  }
}
