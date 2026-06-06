import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface ABTestConfig {
  name: string;
  variants: ABTestVariant[];
  weights: number[];
  startDate?: Date;
  endDate?: Date;
  enabled: boolean;
}

export interface ABTestVariant {
  id: string;
  name: string;
  config: Record<string, unknown>;
}

export interface ABTestExperiment {
  testName: string;
  variantId: string;
  timestamp: number;
  userId: string;
}

@Injectable({
  providedIn: 'root',
})
export class ABTestingService {
  private currentExperiments: Record<string, string> = {};
  private experimentsSubject = new BehaviorSubject<Record<string, string>>({});
  experiments$ = this.experimentsSubject.asObservable();

  private configs: Record<string, ABTestConfig> = {
    'cta-button-test': {
      name: 'CTA按钮颜色测试',
      variants: [
        { id: 'blue', name: '蓝色按钮', config: { color: 'primary' } },
        { id: 'green', name: '绿色按钮', config: { color: 'accent' } },
        { id: 'orange', name: '橙色按钮', config: { color: 'warn' } },
      ],
      weights: [0.4, 0.3, 0.3],
      enabled: true,
    },
    'pricing-page-test': {
      name: '价格页面布局测试',
      variants: [
        { id: '3-cards', name: '3列卡片', config: { columns: 3 } },
        { id: '2-cards', name: '2列卡片', config: { columns: 2 } },
      ],
      weights: [0.5, 0.5],
      enabled: true,
    },
    'hero-text-test': {
      name: '首页文案测试',
      variants: [
        { id: 'original', name: '原始文案', config: { heroTitle: '开启智能学习之旅' } },
        { id: 'variant1', name: '变体1', config: { heroTitle: 'AI+AR，重新定义学习方式' } },
        { id: 'variant2', name: '变体2', config: { heroTitle: '未来教育，触手可及' } },
      ],
      weights: [0.5, 0.25, 0.25],
      enabled: true,
    },
  };

  constructor() {
    this.loadExperiments();
  }

  /**
   * 加载已分配的实验变体
   */
  private loadExperiments(): void {
    const saved = localStorage.getItem('ab-experiments');
    if (saved) {
      try {
        this.currentExperiments = JSON.parse(saved) as Record<string, string>;
        this.experimentsSubject.next(this.currentExperiments);
      } catch (error) {
        console.error('加载A/B测试配置失败:', error);
      }
    }
  }

  /**
   * 保存实验配置
   */
  private saveExperiments(): void {
    localStorage.setItem('ab-experiments', JSON.stringify(this.currentExperiments));
    this.experimentsSubject.next(this.currentExperiments);
  }

  /**
   * 获取用户的唯一ID
   */
  private getUserId(): string {
    let userId = localStorage.getItem('ab-user-id');
    if (!userId) {
      userId = this.generateUserId();
      localStorage.setItem('ab-user-id', userId);
    }
    return userId;
  }

  /**
   * 生成用户ID
   */
  private generateUserId(): string {
    return 'user_' + Math.random().toString(36).substr(2, 9) + Date.now();
  }

  /**
   * 根据权重随机分配变体
   */
  private assignVariant(weights: number[]): number {
    const random = Math.random();
    let cumulative = 0;

    for (let i = 0; i < weights.length; i++) {
      cumulative += weights[i];
      if (random < cumulative) {
        return i;
      }
    }

    return 0;
  }

  /**
   * 获取实验的变体
   */
  getVariant(testName: string): ABTestVariant | null {
    const config = this.configs[testName];

    if (!config?.enabled) {
      return null;
    }

    // 检查是否已分配
    if (!this.currentExperiments[testName]) {
      const userId = this.getUserId();
      const variantIndex = this.assignVariant(config.weights);
      const variant = config.variants[variantIndex];

      this.currentExperiments[testName] = variant.id;
      this.saveExperiments();

      // 发送分配事件（实际项目中应该发送到分析服务）
      this.trackAssignment(testName, variant.id, userId);

      return variant;
    }

    // 返回已分配的变体
    const variantId = this.currentExperiments[testName];
    return config.variants.find((v) => v.id === variantId) ?? null;
  }

  /**
   * 获取变体配置
   */
  getVariantConfig<T = unknown>(testName: string, defaultValue: T): T {
    const variant = this.getVariant(testName);
    return (variant?.config as T) || defaultValue;
  }

  /**
   * 检查是否在特定变体中
   */
  isInVariant(testName: string, variantId: string): boolean {
    return this.getVariant(testName)?.id === variantId;
  }

  /**
   * 强制设置变体（用于测试）
   */
  forceVariant(testName: string, variantId: string): void {
    const config = this.configs[testName];
    if (config?.variants.find((v) => v.id === variantId)) {
      this.currentExperiments[testName] = variantId;
      this.saveExperiments();
    }
  }

  /**
   * 重置实验
   */
  resetExperiment(testName: string): void {
    delete this.currentExperiments[testName];
    this.saveExperiments();
  }

  /**
   * 重置所有实验
   */
  resetAllExperiments(): void {
    this.currentExperiments = {};
    this.saveExperiments();
  }

  /**
   * 追踪分配事件
   */
  private trackAssignment(testName: string, variantId: string, userId: string): void {
    const experiment: ABTestExperiment = {
      testName,
      variantId,
      timestamp: Date.now(),
      userId,
    };

    console.warn('AB Test Assignment:', experiment);

    // 实际项目中应该发送到分析服务
    // this.analyticsService.track('ab_test_assignment', experiment);
  }

  /**
   * 追踪转化事件
   */
  trackConversion(testName: string, conversionType: string, value?: number): void {
    const variantId = this.currentExperiments[testName];
    if (!variantId) {
      return;
    }

    const event = {
      testName,
      variantId,
      conversionType,
      value,
      timestamp: Date.now(),
      userId: this.getUserId(),
    };

    console.warn('AB Test Conversion:', event);

    // 实际项目中应该发送到分析服务
    // this.analyticsService.track('ab_test_conversion', event);
  }

  /**
   * 获取所有实验配置
   */
  getAllConfigs(): Record<string, ABTestConfig> {
    return this.configs;
  }

  /**
   * 添加新实验
   */
  addTest(config: ABTestConfig): void {
    this.configs[config.name] = config;
  }

  /**
   * 启用/禁用实验
   */
  toggleTest(testName: string, enabled: boolean): void {
    if (this.configs[testName]) {
      this.configs[testName].enabled = enabled;
    }
  }

  /**
   * 获取当前用户的实验摘要
   */
  getExperimentSummary(): Array<{ testName: string; variantId: string; variantName: string }> {
    return Object.entries(this.currentExperiments).map(([testName, variantId]) => {
      const config = this.configs[testName];
      const variant = config?.variants.find((v) => v.id === variantId);
      return {
        testName: config?.name || testName,
        variantId,
        variantName: variant?.name ?? variantId,
      };
    });
  }
}
