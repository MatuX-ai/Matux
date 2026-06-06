/**
 * 插件使用统计组件
 * 
 * 功能:
 * 1. 显示使用时间统计
 * 2. 使用频率分析
 * 3. 趋势展示
 * 4. 功能使用分布
 */

import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

interface UsageStats {
  totalUsageTime: number;
  usageCount: number;
  lastUsedAt: string | null;
  averageSessionTime: number;
  userRating: number;
  trend: string;
}

@Component({
  selector: 'app-plugin-usage-stats',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatButtonModule,
    MatCardModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './plugin-usage-stats.component.html',
  styleUrls: ['./plugin-usage-stats.component.scss'],
})
export class PluginUsageStatsComponent implements OnInit {
  @Input() pluginId = '';
  
  stats: UsageStats | null = null;
  loading = true;
  error: string | null = null;
  
  ngOnInit(): void {
    if (this.pluginId) {
      this.loadStats();
    }
  }
  
  async loadStats(): Promise<void> {
    this.loading = true;
    this.error = null;
    
    try {
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用');
      }
      
      const result = await window.pluginAPI.getPluginUsageStats(this.pluginId);
      if (result.success && result.data) {
        this.stats = result.data;
      }
    } catch (err) {
      this.error = (err as Error).message;
      console.error('加载使用统计失败:', err);
    } finally {
      this.loading = false;
    }
  }
  
  formatTime(seconds: number): string {
    if (seconds < 60) return `${seconds} 秒`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时`;
    return `${Math.floor(seconds / 86400)} 天`;
  }
  
  getTrendIcon(trend: string): string {
    switch (trend) {
      case 'active': return 'trending_up';
      case 'stable': return 'trending_flat';
      case 'declining': return 'trending_down';
      default: return 'remove_circle';
    }
  }
  
  getTrendColor(trend: string): string {
    switch (trend) {
      case 'active': return '#4caf50';
      case 'stable': return '#ff9800';
      case 'declining': return '#f44336';
      default: return '#999';
    }
  }
  
  getTrendLabel(trend: string): string {
    switch (trend) {
      case 'active': return '活跃使用';
      case 'stable': return '使用稳定';
      case 'declining': return '使用下降';
      case 'inactive': return '未使用';
      default: return trend;
    }
  }
}
