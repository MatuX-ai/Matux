/**
 * 插件卡片组件
 * 
 * 功能:
 * 1. 插件信息展示
 * 2. 兼容性标识
 * 3. 安装/卸载操作
 * 4. 状态显示
 * 5. 导航到详情页
 */

import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { PluginStoreService, PluginListItem, InstallProgress } from '../../../core/services/plugin-store.service';

@Component({
  selector: 'app-plugin-card',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatIconModule,
    MatButtonModule,
    MatChipsModule,
    MatTooltipModule,
    MatProgressBarModule,
    MatSnackBarModule,
  ],
  templateUrl: './plugin-card.component.html',
  styleUrls: ['./plugin-card.component.scss'],
})
export class PluginCardComponent implements OnInit {
  @Input() plugin!: PluginListItem;
  
  installing = false;
  installProgress: InstallProgress | null = null;
  
  constructor(
    private pluginService: PluginStoreService,
    private snackBar: MatSnackBar,
  ) {}
  
  ngOnInit(): void {
    // 监听安装进度
    if (this.plugin) {
      this.pluginService.getInstallProgress(this.plugin.id).subscribe((progress: any) => {
        this.installProgress = progress;
        
        if (progress?.status === 'completed') {
          this.installing = false;
          this.snackBar.open(`${this.plugin.name} 安装完成`, '关闭', { duration: 3000 });
        } else if (progress?.status === 'failed') {
          this.installing = false;
          this.snackBar.open(`安装失败: ${progress.error}`, '关闭', { duration: 5000 });
        }
      });
    }
  }
  
  /**
   * 安装插件
   */
  async installPlugin(): Promise<void> {
    if (this.installing) return;
    
    this.installing = true;
    
    try {
      await this.pluginService.installPlugin(this.plugin.id, this.plugin.version);
      this.snackBar.open(`开始安装 ${this.plugin.name}`, '关闭', { duration: 2000 });
    } catch (err) {
      this.installing = false;
      this.snackBar.open(`安装失败: ${(err as Error).message}`, '关闭', { duration: 5000 });
    }
  }
  
  /**
   * 获取兼容性图标
   */
  getCompatibilityIcon(): string {
    if (this.plugin.compatible === true) return 'check_circle';
    if (this.plugin.compatible === false) return 'cancel';
    return 'help_outline';
  }
  
  /**
   * 获取兼容性颜色
   */
  getCompatibilityColor(): string {
    if (this.plugin.compatible === true) return '#4CAF50';
    if (this.plugin.compatible === false) return '#F44336';
    return '#9E9E9E';
  }
  
  /**
   * 获取状态标签
   */
  getStateLabel(): string {
    return this.pluginService.getStateLabel(this.plugin.state);
  }
  
  /**
   * 获取状态颜色
   */
  getStateColor(): string {
    return this.pluginService.getStateColor(this.plugin.state);
  }
  
  /**
   * 获取分类标签
   */
  getCategoryLabels(): string[] {
    return this.plugin.categories.map((cat: string) => this.pluginService.getCategoryLabel(cat));
  }
  
  /**
   * 是否已安装
   */
  isInstalled(): boolean {
    return ['installed', 'loaded', 'enabled', 'disabled'].includes(this.plugin.state);
  }
  
  /**
   * 是否兼容
   */
  isCompatible(): boolean {
    return this.plugin.compatible === true;
  }
}
