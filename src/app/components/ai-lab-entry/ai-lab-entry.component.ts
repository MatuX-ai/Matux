import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { interval, Observable, Subscription } from 'rxjs';
import { catchError, startWith, switchMap, tap } from 'rxjs/operators';

import { ContainerStatusResponse, OpenHydraService } from '../../core/services/openhydra.service';

@Component({
  selector: 'app-ai-lab-entry',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
  ],
  template: `
    <div class="ai-lab-container">
      <!-- 进入实验室按钮 -->
      <button
        mat-raised-button
        color="primary"
        [disabled]="isLoading || !isServiceHealthy"
        (click)="enterLab()"
        class="enter-lab-btn"
      >
        <mat-icon *ngIf="!isLoading">science</mat-icon>
        <mat-spinner *ngIf="isLoading" diameter="20"></mat-spinner>
        {{ getButtonText() }}
      </button>

      <!-- 状态指示器 -->
      <div class="status-indicator" *ngIf="containerStatus">
        <div class="status-item">
          <mat-icon [color]="getStatusColor()">{{ getStatusIcon() }}</mat-icon>
          <span>{{ getStatusText() }}</span>
        </div>

        <div class="status-item" *ngIf="containerStatus.is_running">
          <mat-icon>memory</mat-icon>
          <span>CPU: {{ containerStatus.resource_usage.cpu || 0 }}%</span>
        </div>

        <div class="status-actions">
          <button
            mat-icon-button
            color="accent"
            (click)="openJupyter()"
            [disabled]="!canOpenJupyter()"
            matTooltip="打开 Jupyter 环境"
          >
            <mat-icon>open_in_new</mat-icon>
          </button>

          <button
            mat-icon-button
            color="warn"
            (click)="stopContainer()"
            [disabled]="!containerStatus.is_running"
            matTooltip="停止容器"
          >
            <mat-icon>stop</mat-icon>
          </button>

          <button mat-icon-button (click)="refreshStatus()" matTooltip="刷新状态">
            <mat-icon>refresh</mat-icon>
          </button>
        </div>
      </div>

      <!-- 服务健康状态 -->
      <div class="health-status" *ngIf="!isServiceHealthy">
        <mat-icon color="warn">warning</mat-icon>
        <span>AI 实验室服务暂时不可用</span>
      </div>
    </div>
  `,
  styles: [
    `
      .ai-lab-container {
        padding: 16px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }

      .enter-lab-btn {
        width: 100%;
        padding: 12px 24px;
        font-size: 16px;
        font-weight: 500;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        margin-bottom: 16px;
      }

      .status-indicator {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px;
        background: #f5f5f5;
        border-radius: 6px;
        gap: 16px;
      }

      .status-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
      }

      .status-actions {
        display: flex;
        gap: 8px;
      }

      .health-status {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px;
        background: #fff3cd;
        border-radius: 6px;
        color: #856404;
        margin-top: 12px;
      }

      :host ::ng-deep .mat-mdc-raised-button.mat-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
      }

      :host ::ng-deep .mat-mdc-raised-button:disabled {
        background: #e0e0e0;
        color: #9e9e9e;
      }
    `,
  ],
})
export class AiLabEntryComponent implements OnInit, OnDestroy {
  containerStatus: ContainerStatusResponse | null = null;
  isLoading = false;
  isServiceHealthy = true;
  private statusRefreshSub?: Subscription;

  constructor(
    private openHydraService: OpenHydraService,
    private snackBar: MatSnackBar,
    private dialog: MatDialog
  ) {}

  ngOnInit(): void {
    // 启动定时刷新状态
    this.statusRefreshSub = interval(30000) // 每 30 秒刷新一次
      .pipe(
        startWith(0),
        switchMap(() => this.checkContainerStatus())
      )
      .subscribe();

    // 检查服务健康状态
    void this.checkHealth();
  }

  ngOnDestroy(): void {
    this.statusRefreshSub?.unsubscribe();
  }

  /**
   * 进入 AI 实验室
   */
  async enterLab(): Promise<void> {
    this.isLoading = true;

    try {
      const response = await this.openHydraService.enterLab().toPromise();

      if (response?.success) {
        this.snackBar.open(`✅ ${response.message}`, '关闭', {
          duration: 3000,
          panelClass: ['success-snackbar'],
        });

        // 自动打开 Jupyter 环境
        setTimeout(() => {
          if (response) {
            this.openHydraService.openJupyterEnvironment(
              response.access_token,
              response.jupyter_url
            );
          }
        }, 500);

        // 刷新状态
        this.checkContainerStatus().subscribe();
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '请稍后重试';
      this.snackBar.open(`❌ 进入实验室失败：${errorMessage}`, '关闭', {
        duration: 5000,
        panelClass: ['error-snackbar'],
      });
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * 打开 Jupyter 环境
   */
  openJupyter(): void {
    const token = this.openHydraService.getStoredToken();
    const containerId = this.openHydraService.getStoredContainerId();

    if (!token || !this.containerStatus) {
      this.snackBar.open('❌ 未找到有效的 Jupyter 会话', '关闭', {
        duration: 3000,
      });
      return;
    }

    // 从容器状态构建 URL（实际应该从 API 获取完整的 jupyter_url）
    const jupyterUrl = this.containerStatus?.jupyter_accessible
      ? `http://localhost:8000/user/${containerId}`
      : 'http://localhost:8000';

    if (token) {
      this.openHydraService.openJupyterEnvironment(token, jupyterUrl);
    }
  }

  /**
   * 停止容器
   */
  async stopContainer(): Promise<void> {
    if (!confirm('确定要停止当前容器吗？未保存的工作可能会丢失。')) {
      return;
    }

    try {
      const response = await this.openHydraService.stopContainer().toPromise();

      if (response) {
        this.snackBar.open(`✅ ${response.message}`, '关闭', {
          duration: 3000,
        });
      }

      this.containerStatus = null;
      this.openHydraService.clearStoredToken();

      // 刷新状态
      this.checkContainerStatus().subscribe();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '请稍后重试';
      this.snackBar.open(`❌ 停止容器失败：${errorMessage}`, '关闭', {
        duration: 5000,
      });
    }
  }

  /**
   * 检查容器状态
   */
  checkContainerStatus(): Observable<ContainerStatusResponse> {
    return this.openHydraService.getContainerStatus().pipe(
      tap((status) => {
        this.containerStatus = status;

        if (status.container_id && status.is_running) {
          // 容器正在运行，可以执行相关操作
        }
      }),
      catchError((error: unknown) => {
        console.error('检查容器状态失败:', error);
        throw error;
      })
    );
  }

  /**
   * 检查服务健康状态
   */
  async checkHealth(): Promise<void> {
    try {
      const health = await this.openHydraService.healthCheck().toPromise();
      this.isServiceHealthy = health?.status === 'healthy';
    } catch (error) {
      this.isServiceHealthy = false;
    }
  }

  /**
   * 刷新状态
   */
  refreshStatus(): void {
    void this.checkContainerStatus().subscribe();
    void this.checkHealth();
  }

  /**
   * 获取按钮文本
   */
  getButtonText(): string {
    if (this.isLoading) {
      return '正在加载...';
    }

    if (this.containerStatus?.is_running) {
      return '继续实验';
    }

    return '开始实验';
  }

  /**
   * 获取状态文本
   */
  getStatusText(): string {
    if (!this.containerStatus) {
      return '未运行';
    }

    if (this.containerStatus.is_running) {
      return '运行中';
    }

    return '已停止';
  }

  /**
   * 获取状态图标
   */
  getStatusIcon(): string {
    if (!this.containerStatus) {
      return 'circle';
    }

    if (this.containerStatus.is_running) {
      return 'play_circle';
    }

    return 'pause_circle';
  }

  /**
   * 获取状态颜色
   */
  getStatusColor(): 'primary' | 'accent' | 'warn' {
    if (!this.containerStatus) {
      return 'primary';
    }

    if (this.containerStatus.is_running) {
      return 'accent';
    }

    return 'warn';
  }

  /**
   * 是否可以打开 Jupyter
   */
  canOpenJupyter(): boolean {
    return !!this.containerStatus?.is_running && this.containerStatus.jupyter_accessible;
  }
}
