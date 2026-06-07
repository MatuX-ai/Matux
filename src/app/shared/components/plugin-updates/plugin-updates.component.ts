/**
 * 插件更新通知组件
 * 
 * 功能:
 * 1. 显示待处理更新
 * 2. 严重程度标识
 * 3. 一键更新/关闭
 * 4. 更新历史
 */

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatBadgeModule } from '@angular/material/badge';

interface UpdateNotification {
  id: string;
  pluginId: string;
  pluginName: string;
  currentVersion: string;
  newVersion: string;
  releaseNotes: string;
  severity: 'info' | 'warning' | 'critical';
  notifiedAt: string;
  dismissed: boolean;
  installed: boolean;
}

@Component({
  selector: 'app-plugin-updates',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatBadgeModule,
  ],
  templateUrl: './plugin-updates.component.html',
  styleUrls: ['./plugin-updates.component.scss'],
})
export class PluginUpdatesComponent implements OnInit {
  notifications: UpdateNotification[] = [];
  loading = true;
  error: string | null = null;
  updating = new Set<string>();
  
  constructor(private snackBar: MatSnackBar) {}
  
  ngOnInit(): void {
    this.loadNotifications();
  }
  
  async loadNotifications(): Promise<void> {
    this.loading = true;
    this.error = null;
    
    try {
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用');
      }
      
      const result = (await window.pluginAPI.getPendingNotifications()) as { success: boolean; data: UpdateNotification[] };
      if (result.success && result.data) {
        this.notifications = result.data;
      }
    } catch (err) {
      this.error = (err as Error).message;
      console.error('加载更新通知失败:', err);
    } finally {
      this.loading = false;
    }
  }
  
  async updatePlugin(notification: UpdateNotification): Promise<void> {
    this.updating.add(notification.id);
    
    try {
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用');
      }
      
      await window.pluginAPI.updatePlugin(notification.pluginId);
      await window.pluginAPI.markNotificationInstalled(notification.id);
      
      this.snackBar.open(`${notification.pluginName} 更新成功`, '关闭', {
        duration: 3000,
      });
      
      // 从列表中移除
      this.notifications = this.notifications.filter(n => n.id !== notification.id);
    } catch (err) {
      this.snackBar.open(`更新失败: ${(err as Error).message}`, '关闭', {
        duration: 5000,
      });
    } finally {
      this.updating.delete(notification.id);
    }
  }
  
  async dismissNotification(notification: UpdateNotification): Promise<void> {
    try {
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用');
      }
      
      await window.pluginAPI.dismissNotification(notification.id);
      
      // 从列表中移除
      this.notifications = this.notifications.filter(n => n.id !== notification.id);
      
      this.snackBar.open('通知已关闭', '关闭', { duration: 2000 });
    } catch (err) {
      this.snackBar.open(`操作失败: ${(err as Error).message}`, '关闭', {
        duration: 3000,
      });
    }
  }
  
  async dismissAll(): Promise<void> {
    try {
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用');
      }
      
      await window.pluginAPI.dismissNotification('all');
      this.notifications = [];
      
      this.snackBar.open('所有通知已关闭', '关闭', { duration: 2000 });
    } catch (err) {
      this.snackBar.open(`操作失败: ${(err as Error).message}`, '关闭', {
        duration: 3000,
      });
    }
  }
  
  async checkForUpdates(): Promise<void> {
    try {
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用');
      }
      
      this.snackBar.open('正在检查更新...', '关闭', { duration: 2000 });
      
      // 这里需要获取已安装插件列表
      const installedResult = (await window.pluginAPI.getInstalledPlugins()) as { success: boolean; data: unknown };
      if (installedResult.success && installedResult.data) {
        await window.pluginAPI.checkForUpdates(installedResult.data);
        await this.loadNotifications();
        
        if (this.notifications.length === 0) {
          this.snackBar.open('所有插件已是最新版本', '关闭', { duration: 3000 });
        } else {
          this.snackBar.open(`发现 ${this.notifications.length} 个更新`, '关闭', {
            duration: 3000,
          });
        }
      }
    } catch (err) {
      this.snackBar.open(`检查更新失败: ${(err as Error).message}`, '关闭', {
        duration: 5000,
      });
    }
  }
  
  getSeverityIcon(severity: string): string {
    switch (severity) {
      case 'critical': return 'error';
      case 'warning': return 'warning';
      default: return 'info';
    }
  }
  
  getSeverityColor(severity: string): string {
    switch (severity) {
      case 'critical': return '#f44336';
      case 'warning': return '#ff9800';
      default: return '#2196f3';
    }
  }
  
  getSeverityLabel(severity: string): string {
    switch (severity) {
      case 'critical': return '重要更新';
      case 'warning': return '建议更新';
      default: return '普通更新';
    }
  }
  
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return '今天';
    if (days === 1) return '昨天';
    if (days < 7) return `${days} 天前`;
    return date.toLocaleDateString('zh-CN');
  }
}
