/**
 * 推荐插件展示组件
 * 
 * 功能:
 * 1. 显示个性化推荐插件
 * 2. 显示推荐捆绑包
 * 3. 推荐理由展示
 * 4. 一键安装推荐
 */

import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface Recommendation {
  pluginId: string;
  score: number;
  reason: string;
  sources: string[];
}

interface Bundle {
  id: string;
  name: string;
  description: string;
  plugins: string[];
  discount: number;
  category: string;
  targetDeviceClass: string;
  priority: number;
}

interface RecommendationResult {
  recommendations: Recommendation[];
  bundles: Bundle[];
  reason: string;
  confidence: number;
  generatedAt: string;
}

@Component({
  selector: 'app-plugin-recommendations',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
  ],
  templateUrl: './plugin-recommendations.component.html',
  styleUrls: ['./plugin-recommendations.component.scss'],
})
export class PluginRecommendationsComponent implements OnInit, OnDestroy {
  // 数据
  recommendations: Recommendation[] = [];
  bundles: Bundle[] = [];
  recommendationReason = '';
  confidence = 0;
  loading = true;
  error: string | null = null;
  
  private destroy$ = new Subject<void>();
  
  constructor(private snackBar: MatSnackBar) {}
  
  ngOnInit(): void {
    this.loadRecommendations();
  }
  
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
  
  /**
   * 加载推荐数据
   */
  async loadRecommendations(): Promise<void> {
    this.loading = true;
    this.error = null;
    
    try {
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用（非 Electron 环境）');
      }
      
      const result = await window.pluginAPI.getRecommendations({
        maxRecommendations: 10,
        includeBundles: true,
        excludeInstalled: true,
      });
      
      if (result.success && result.data) {
        const data: RecommendationResult = result.data;
        this.recommendations = data.recommendations;
        this.bundles = data.bundles;
        this.recommendationReason = data.reason;
        this.confidence = data.confidence;
      }
    } catch (err) {
      this.error = (err as Error).message;
      console.error('加载推荐失败:', err);
    } finally {
      this.loading = false;
    }
  }
  
  /**
   * 安装推荐插件
   */
  async installPlugin(pluginId: string): Promise<void> {
    try {
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用');
      }
      
      await window.pluginAPI.installPlugin(pluginId);
      this.snackBar.open('开始安装插件', '关闭', { duration: 2000 });
      
      // 从推荐列表中移除
      this.recommendations = this.recommendations.filter(
        rec => rec.pluginId !== pluginId
      );
    } catch (err) {
      this.snackBar.open(`安装失败: ${(err as Error).message}`, '关闭', {
        duration: 5000,
      });
    }
  }
  
  /**
   * 安装捆绑包
   */
  async installBundle(bundle: Bundle): Promise<void> {
    try {
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用');
      }
      
      let installedCount = 0;
      
      for (const pluginId of bundle.plugins) {
        try {
          await window.pluginAPI.installPlugin(pluginId);
          installedCount++;
        } catch (err) {
          console.warn(`插件 ${pluginId} 安装失败:`, err);
        }
      }
      
      this.snackBar.open(
        `已安装 ${installedCount}/${bundle.plugins.length} 个插件`,
        '关闭',
        { duration: 3000 }
      );
      
      // 从推荐列表中移除已安装的插件
      this.recommendations = this.recommendations.filter(
        rec => !bundle.plugins.includes(rec.pluginId)
      );
      
      // 从捆绑包列表中移除
      this.bundles = this.bundles.filter(b => b.id !== bundle.id);
    } catch (err) {
      this.snackBar.open(`安装失败: ${(err as Error).message}`, '关闭', {
        duration: 5000,
      });
    }
  }
  
  /**
   * 获取置信度标签
   */
  getConfidenceLabel(confidence: number): string {
    if (confidence >= 0.9) return '非常高';
    if (confidence >= 0.8) return '高';
    if (confidence >= 0.7) return '中等';
    return '较低';
  }
  
  /**
   * 获取置信度颜色
   */
  getConfidenceColor(confidence: number): string {
    if (confidence >= 0.9) return '#4CAF50';
    if (confidence >= 0.8) return '#8BC34A';
    if (confidence >= 0.7) return '#FFC107';
    return '#FF9800';
  }
  
  /**
   * 获取折扣文本
   */
  getDiscountText(discount: number): string {
    return `${Math.round(discount * 100)}% 折扣`;
  }
  
  /**
   * 刷新推荐
   */
  async refresh(): Promise<void> {
    await this.loadRecommendations();
    this.snackBar.open('推荐已刷新', '关闭', { duration: 2000 });
  }
}
