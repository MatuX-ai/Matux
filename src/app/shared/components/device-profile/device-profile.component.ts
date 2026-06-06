/**
 * 设备评估报告组件
 *
 * 显示当前设备的硬件/软件能力评估结果，
 * 包括设备等级、核心指标、插件兼容性信息。
 *
 * 用法：
 * <app-device-profile></app-device-profile>
 * <app-device-profile [compact]="true"></app-device-profile>
 */

import { CommonModule } from '@angular/common';
import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { Subject, takeUntil } from 'rxjs';

import type {
  DeviceProfile,
  DeviceClass,
  DeviceAssessment,
  HardwareProfile,
  SoftwareProfile,
  PluginAPI,
} from '../../../core/models/electron-api.model';

/** 设备等级显示配置 */
const DEVICE_CLASS_LABELS: Record<DeviceClass, { label: string; icon: string; color: string }> = {
  basic: { label: '基础级', icon: 'memory', color: '#94a3b8' },
  standard: { label: '标准级', icon: 'computer', color: '#3b82f6' },
  advanced: { label: '进阶级', icon: 'videogame_asset', color: '#10b981' },
  professional: { label: '专业级', icon: 'precision_manufacturing', color: '#f59e0b' },
};

const TIER_LABELS: Record<string, { label: string; color: string }> = {
  'tier-a': { label: 'Tier A 通用', color: '#10b981' },
  'tier-b': { label: 'Tier B 标准', color: '#3b82f6' },
  'tier-c': { label: 'Tier C 高级', color: '#f59e0b' },
  'tier-d': { label: 'Tier D 专业', color: '#ef4444' },
};

@Component({
  selector: 'app-device-profile',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatTooltipModule, MatButtonModule, MatProgressBarModule],
  templateUrl: './device-profile.component.html',
  styleUrls: ['./device-profile.component.scss'],
})
export class DeviceProfileComponent implements OnInit, OnDestroy {
  @Input() compact = false;

  private destroy$ = new Subject<void>();
  private pluginAPI: PluginAPI | undefined;

  profile: DeviceProfile | null = null;
  loading = true;
  error: string | null = null;
  reassessing = false;

  // 便捷访问器
  get deviceClass(): DeviceClass {
    return this.profile?.assessment?.deviceClass || 'basic';
  }

  get deviceClassConfig() {
    return DEVICE_CLASS_LABELS[this.deviceClass];
  }

  get score(): number {
    return this.profile?.assessment?.score || 0;
  }

  get hardware(): HardwareProfile | null {
    return this.profile?.hardware || null;
  }

  get software(): SoftwareProfile | null {
    return this.profile?.software || null;
  }

  get assessment(): DeviceAssessment | null {
    return this.profile?.assessment || null;
  }

  get assessedAtLabel(): string {
    if (!this.profile?.assessedAt) return '';
    const date = new Date(this.profile.assessedAt);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
  }

  get memoryGB(): string {
    if (!this.hardware) return '-';
    return (this.hardware.memory.totalMB / 1024).toFixed(0);
  }

  get vramLabel(): string {
    if (!this.hardware?.gpu) return '-';
    if (!this.hardware.gpu.hasDedicatedGPU) return '集成显卡';
    const vramGB = this.hardware.gpu.vramMB / 1024;
    return vramGB >= 1 ? `${vramGB.toFixed(0)}GB` : `${this.hardware.gpu.vramMB}MB`;
  }

  ngOnInit(): void {
    this.pluginAPI = window.pluginAPI;
    if (this.pluginAPI) {
      this.loadProfile();
    } else {
      // 非 Electron 环境
      this.loading = false;
      this.error = '插件系统仅在桌面客户端可用';
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  async loadProfile(): Promise<void> {
    if (!this.pluginAPI) return;
    this.loading = true;
    this.error = null;

    try {
      const result = await this.pluginAPI.getDeviceProfile();
      if (result.success && result.profile) {
        this.profile = result.profile;
      } else {
        this.error = result.error || '获取设备评估报告失败';
      }
    } catch (err) {
      this.error = `加载失败: ${(err as Error).message}`;
    } finally {
      this.loading = false;
    }
  }

  async reassess(): Promise<void> {
    if (!this.pluginAPI || this.reassessing) return;
    this.reassessing = true;
    this.error = null;

    try {
      const result = await this.pluginAPI.reassessDevice();
      if (result.success && result.profile) {
        this.profile = result.profile;
      } else {
        this.error = result.error || '重新评估失败';
      }
    } catch (err) {
      this.error = `评估失败: ${(err as Error).message}`;
    } finally {
      this.reassessing = false;
    }
  }

  getTierConfig(tier: string) {
    return TIER_LABELS[tier] || { label: tier, color: '#64748b' };
  }

  getIncompatibleTiers(): string[] {
    if (!this.assessment) return [];
    const allTiers = ['tier-a', 'tier-b', 'tier-c', 'tier-d'];
    const compatible = this.assessment.compatiblePluginTiers || [];
    return allTiers.filter((t) => !compatible.includes(t));
  }

  getScoreColor(score: number): string {
    if (score >= 80) return '#10b981';
    if (score >= 50) return '#3b82f6';
    if (score >= 30) return '#f59e0b';
    return '#ef4444';
  }
}
