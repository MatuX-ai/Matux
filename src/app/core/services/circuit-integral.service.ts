/**
 * 电路组装与积分系统集成服务
 *
 * 在用户完成电路组装操作时触发积分奖励
 * 实现游戏化激励机制
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { Injectable } from '@angular/core';

import { AssemblyStep, CircuitAssemblyService } from './circuit-assembly.service';
import { VircadiaSdkService } from './vircadia-sdk.service';

/**
 * 奖励动作类型
 */
export type RewardActionType =
  | 'circuit_assembly_success' // 成功安装元件
  | 'circuit_completed' // 完成整个电路
  | 'first_try_success' // 一次尝试成功
  | 'speed_bonus' // 快速完成奖励
  | 'perfect_installation' // 完美安装 (无错误)
  | 'correct_polarity' // 正确识别极性
  | 'creative_design' // 创意设计奖励
  | 'help_peer' // 帮助同学
  | 'daily_challenge'; // 每日挑战

/**
 * 奖励配置
 */
export interface RewardConfig {
  /** 奖励动作类型 */
  action: RewardActionType;

  /** 基础积分 */
  basePoints: number;

  /** 最大连击加成 */
  maxComboBonus?: number;

  /** 时间奖励系数 (每秒加分) */
  timeBonusCoefficient?: number;

  /** 描述模板 */
  descriptionTemplate: string;

  /** 图标 URL */
  iconUrl?: string;

  /** 是否播放特效动画 */
  playAnimation: boolean;
}

/**
 * 奖励事件
 */
export interface RewardEvent {
  /** 事件 ID */
  eventId: string;

  /** 用户 ID */
  userId: string;

  /** 奖励动作类型 */
  action: RewardActionType;

  /** 获得积分 */
  pointsAwarded: number;

  /** 描述 */
  description: string;

  /** 时间戳 */
  timestamp: Date;

  /** 额外数据 */
  metadata?: {
    componentId?: string;
    componentName?: string;
    circuitId?: string;
    assemblyTime?: number;
    attemptCount?: number;
    comboCount?: number;
  };
}

/**
 * 积分服务接口 (应该对接现有积分系统)
 */
export interface IntegralServiceInterface {
  rewardUser(event: RewardEvent): Promise<void>;
  getUserPoints(userId: string): Promise<number>;
  getRewardHistory(userId: string): Promise<RewardEvent[]>;
}

@Injectable({
  providedIn: 'root',
})
export class CircuitIntegralService implements IntegralServiceInterface {
  // 奖励配置表
  private readonly REWARD_CONFIGS: Record<RewardActionType, RewardConfig> = {
    circuit_assembly_success: {
      action: 'circuit_assembly_success',
      basePoints: 10,
      descriptionTemplate: '成功安装 {componentName}',
      playAnimation: true,
    },

    circuit_completed: {
      action: 'circuit_completed',
      basePoints: 100,
      maxComboBonus: 50,
      descriptionTemplate: '完成电路：{circuitName}',
      playAnimation: true,
    },

    first_try_success: {
      action: 'first_try_success',
      basePoints: 20,
      descriptionTemplate: '一次尝试成功！太棒了!',
      playAnimation: true,
    },

    speed_bonus: {
      action: 'speed_bonus',
      basePoints: 5,
      timeBonusCoefficient: 0.5,
      descriptionTemplate: '快速完成奖励 (+{bonus}分)',
      playAnimation: false,
    },

    perfect_installation: {
      action: 'perfect_installation',
      basePoints: 30,
      descriptionTemplate: '完美安装 - 零失误',
      playAnimation: true,
    },

    correct_polarity: {
      action: 'correct_polarity',
      basePoints: 15,
      descriptionTemplate: '正确识别极性',
      playAnimation: true,
    },

    creative_design: {
      action: 'creative_design',
      basePoints: 50,
      descriptionTemplate: '创意设计奖',
      playAnimation: true,
    },

    help_peer: {
      action: 'help_peer',
      basePoints: 25,
      descriptionTemplate: '帮助同学',
      playAnimation: false,
    },

    daily_challenge: {
      action: 'daily_challenge',
      basePoints: 100,
      descriptionTemplate: '完成每日挑战',
      playAnimation: true,
    },
  };

  // 当前用户的连击数
  private comboCount: Map<string, number> = new Map();

  // 奖励历史记录
  private rewardHistory: RewardEvent[] = [];

  // 当前用户 ID (应从认证服务获取)
  private currentUserId: string = 'user_temp';

  constructor(
    private assemblyService: CircuitAssemblyService,
    private vircadiaSdk: VircadiaSdkService
  ) {
    this.setupAssemblyListener();
  }

  /**
   * 设置组装事件监听
   */
  private setupAssemblyListener(): void {
    // 监听每次组装步骤
    const history = this.assemblyService.getHistory();

    // 使用轮询检测新步骤 (实际应该用事件订阅)
    let lastHistoryLength = history.length;

    setInterval(() => {
      const currentHistory = this.assemblyService.getHistory();

      if (currentHistory.length > lastHistoryLength) {
        // 有新的组装步骤
        const newSteps = currentHistory.slice(lastHistoryLength);
        newSteps.forEach((step) => this.handleAssemblyStep(step));

        lastHistoryLength = currentHistory.length;
      }
    }, 500); // 每 500ms 检查一次
  }

  /**
   * 处理组装步骤
   */
  private handleAssemblyStep(step: AssemblyStep): void {
    if (!step.isSuccess) {
      // 失败时重置连击
      this.comboCount.set(this.currentUserId, 0);
      return;
    }

    // 1. 基础成功奖励
    this.rewardUser({
      eventId: `reward_${step.stepId}`,
      userId: step.userId,
      action: 'circuit_assembly_success',
      pointsAwarded: this.REWARD_CONFIGS['circuit_assembly_success'].basePoints,
      description: `成功安装元件 (位号：${step.padId})`,
      timestamp: step.timestamp,
      metadata: {
        componentId: step.componentId,
        attemptCount: step.attemptNumber,
      },
    });

    // 2. 检查是否为首次尝试成功
    if (step.attemptNumber === 1) {
      const config = this.REWARD_CONFIGS['first_try_success'];
      this.rewardUser({
        eventId: `reward_first_${step.stepId}`,
        userId: step.userId,
        action: 'first_try_success',
        pointsAwarded: config.basePoints,
        description: config.descriptionTemplate,
        timestamp: step.timestamp,
        metadata: {
          componentId: step.componentId,
        },
      });
    }

    // 3. 更新连击数
    const currentCombo = (this.comboCount.get(this.currentUserId) || 0) + 1;
    this.comboCount.set(this.currentUserId, currentCombo);

    // 4. 检查是否完成整个电路
    const progress = this.assemblyService.getAssemblyProgress();
    if (progress.status === 'completed') {
      this.handleCircuitCompleted(progress.installed);
    }
  }

  /**
   * 处理电路完成事件
   */
  private async handleCircuitCompleted(installedCount: number): Promise<void> {
    const config = this.REWARD_CONFIGS['circuit_completed'];

    // 计算连击加成
    const combo = this.comboCount.get(this.currentUserId) || 0;
    const comboBonus = Math.min(combo * 5, config.maxComboBonus || 0);

    const totalPoints = config.basePoints + comboBonus;

    await this.rewardUser({
      eventId: `reward_circuit_complete_${Date.now()}`,
      userId: this.currentUserId,
      action: 'circuit_completed',
      pointsAwarded: totalPoints,
      description: config.descriptionTemplate.replace('{circuitName}', '未知电路'),
      timestamp: new Date(),
      metadata: {
        assemblyTime: installedCount, // 这里应该是实际用时
        comboCount: combo,
      },
    });

    // 重置连击
    this.comboCount.set(this.currentUserId, 0);
  }

  /**
   * 奖励用户
   */
  async rewardUser(event: RewardEvent): Promise<void> {
    // 1. 记录到历史
    this.rewardHistory.push(event);

    // 2. 播放奖励动画 (如果配置了)
    const config = this.REWARD_CONFIGS[event.action];
    if (config?.playAnimation) {
      this.playRewardAnimation(event.pointsAwarded);
    }

    // 3. 发送到后端积分服务
    try {
      await this.syncToBackend(event);
    } catch (error) {}

    // 4. 触发 Vircadia 事件
    this.emitVircadiaEvent(event);
  }

  /**
   * 播放奖励动画
   */
  private playRewardAnimation(points: number): void {
    console.log('[Integral] 🎉 播放奖励动画：+{} 分'.replace('{}', String(points)));

    // TODO: 实现 UI 动画效果
    // 可以使用 Angular CDK Toast 或自定义动画组件

    // 示例：发送消息到 Vircadia 聊天系统
    this.vircadiaSdk
      .interact({
        objectId: 'ui_system',
        interactionType: 'activate',
        data: {
          type: 'reward_popup',
          points,
          message: `+${points} 积分!`,
        },
      })
      .catch((err) => console.error('[Integral] 发送动画事件失败:', err));
  }

  /**
   * 同步到后端
   */
  private async syncToBackend(event: RewardEvent): Promise<void> {
    // TODO: 调用后端 API
    // 示例 API 调用:
    // await this.httpClient.post('/api/integral/reward', event).toPromise();
  }

  /**
   * 发送到 Vircadia 事件系统
   */
  private emitVircadiaEvent(event: RewardEvent): void {
    const vircadiaEvent = {
      type: 'gamification.reward',
      data: {
        eventId: event.eventId,
        action: event.action,
        points: event.pointsAwarded,
        timestamp: event.timestamp.getTime(),
      },
    };

    // 广播到虚拟世界
    this.vircadiaSdk
      .interact({
        objectId: 'gamification_system',
        interactionType: 'use',
        data: vircadiaEvent.data,
      })
      .catch((err) => console.error('[Integral] 发送事件失败:', err));
  }

  /**
   * 获取用户积分
   */
  async getUserPoints(userId: string): Promise<number> {
    // TODO: 从后端获取
    // 临时返回缓存的总和
    return this.rewardHistory
      .filter((e) => e.userId === userId)
      .reduce((sum, e) => sum + e.pointsAwarded, 0);
  }

  /**
   * 获取奖励历史
   */
  async getRewardHistory(userId: string): Promise<RewardEvent[]> {
    return this.rewardHistory.filter((e) => e.userId === userId);
  }

  /**
   * 手动触发奖励 (用于特殊成就等)
   */
  async triggerManualReward(action: RewardActionType, metadata?: any): Promise<void> {
    const config = this.REWARD_CONFIGS[action];

    if (!config) {
      return;
    }

    await this.rewardUser({
      eventId: `manual_${action}_${Date.now()}`,
      userId: this.currentUserId,
      action,
      pointsAwarded: config.basePoints,
      description: config.descriptionTemplate,
      timestamp: new Date(),
      metadata,
    });
  }

  /**
   * 清除所有数据
   */
  clear(): void {
    this.rewardHistory = [];
    this.comboCount.clear();
  }

  /**
   * 获取统计数据
   */
  getStatistics(): {
    totalRewards: number;
    totalPoints: number;
    averagePoints: number;
    byActionType: Record<string, number>;
  } {
    const stats = {
      totalRewards: this.rewardHistory.length,
      totalPoints: this.rewardHistory.reduce((sum, e) => sum + e.pointsAwarded, 0),
      averagePoints: 0,
      byActionType: {} as Record<string, number>,
    };

    if (stats.totalRewards > 0) {
      stats.averagePoints = stats.totalPoints / stats.totalRewards;
    }

    // 按类型统计
    this.rewardHistory.forEach((event) => {
      const key = event.action;
      stats.byActionType[key] = (stats.byActionType[key] || 0) + 1;
    });

    return stats;
  }
}
