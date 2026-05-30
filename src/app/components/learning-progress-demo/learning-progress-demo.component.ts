/**
 * AI-Edu 学习进度实时同步演示组件
 * 展示如何使用 WebSocket 服务实现多设备同步
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';

import { AiEduWebSocketService } from '../../core/services/ai-edu-websocket.service';

interface LearningState {
  lesson_id: number;
  progress: number;
  status: string;
  time_spent_seconds: number;
  last_update?: string;
}

@Component({
  selector: 'app-learning-progress-demo',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="progress-demo-container">
      <h2>📡 学习进度实时同步演示</h2>

      <!-- 连接状态 -->
      <div
        class="connection-status"
        [class.connected]="isConnected"
        [class.disconnected]="!isConnected"
      >
        <span class="status-indicator"></span>
        {{ connectionStatus }}
      </div>

      <!-- 控制面板 -->
      <div class="control-panel">
        <button (click)="connect()" [disabled]="isConnected">🔌 连接 WebSocket</button>
        <button (click)="disconnect()" [disabled]="!isConnected">❌ 断开连接</button>
        <button (click)="getCurrentState()" [disabled]="!isConnected">📊 获取当前状态</button>
      </div>

      <!-- 进度更新表单 -->
      <div class="progress-form" *ngIf="isConnected">
        <h3>更新学习进度</h3>
        <div class="form-group">
          <label>课程 ID:</label>
          <input type="number" [(ngModel)]="lessonId" placeholder="输入课程 ID" />
        </div>
        <div class="form-group">
          <label>进度百分比:</label>
          <input type="range" [(ngModel)]="progressPercentage" min="0" max="100" step="5" />
          <span>{{ progressPercentage }}%</span>
        </div>
        <div class="form-group">
          <label>学习时长 (秒):</label>
          <input type="number" [(ngModel)]="timeSpentSeconds" min="0" />
        </div>
        <div class="form-group">
          <label>测验分数:</label>
          <input type="number" [(ngModel)]="quizScore" min="0" max="100" />
        </div>
        <button (click)="updateProgress()">🚀 发送进度更新</button>
      </div>

      <!-- 实时消息日志 -->
      <div class="message-log">
        <h3>📨 实时消息日志</h3>
        <div class="log-container">
          <div *ngFor="let msg of messageLog" class="log-entry" [class]="'type-' + msg.type">
            <span class="timestamp">{{ msg.timestamp }}</span>
            <span class="type">{{ msg.type }}</span>
            <pre>{{ msg.data | json }}</pre>
          </div>
          <div *ngIf="messageLog.length === 0" class="no-messages">暂无消息</div>
        </div>
        <button (click)="clearLog()" class="clear-btn">🗑️ 清空日志</button>
      </div>

      <!-- 当前学习状态 -->
      <div class="current-state" *ngIf="currentState">
        <h3>📈 当前学习状态</h3>
        <div class="state-info">
          <div class="info-item"><strong>课程 ID:</strong> {{ currentState.lesson_id }}</div>
          <div class="info-item"><strong>进度:</strong> {{ currentState.progress }}%</div>
          <div class="info-item"><strong>状态:</strong> {{ currentState.status }}</div>
          <div class="info-item">
            <strong>学习时长:</strong> {{ formatTime(currentState.time_spent_seconds || 0) }}
          </div>
          <div class="info-item">
            <strong>最后更新:</strong> {{ currentState.last_update || 'N/A' }}
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .progress-demo-container {
        padding: 20px;
        max-width: 800px;
        margin: 0 auto;
      }

      h2 {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
      }

      .connection-status {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px;
        border-radius: 5px;
        margin: 20px 0;
        font-weight: bold;
      }

      .connection-status.connected {
        background-color: #d4edda;
        color: #155724;
      }

      .connection-status.disconnected {
        background-color: #f8d7da;
        color: #721c24;
      }

      .status-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: currentColor;
        animation: pulse 2s infinite;
      }

      @keyframes pulse {
        0%,
        100% {
          opacity: 1;
        }
        50% {
          opacity: 0.5;
        }
      }

      .control-panel {
        display: flex;
        gap: 10px;
        margin: 20px 0;
      }

      button {
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        background-color: #3498db;
        color: white;
        cursor: pointer;
        transition: all 0.3s;
      }

      button:hover:not(:disabled) {
        background-color: #2980b9;
      }

      button:disabled {
        background-color: #bdc3c7;
        cursor: not-allowed;
      }

      .progress-form {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 5px;
        margin: 20px 0;
      }

      .form-group {
        margin: 15px 0;
      }

      .form-group label {
        display: block;
        margin-bottom: 5px;
        font-weight: bold;
      }

      .form-group input[type='range'] {
        width: 100%;
      }

      .message-log {
        margin-top: 30px;
      }

      .log-container {
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        background-color: #f8f9fa;
      }

      .log-entry {
        padding: 10px;
        margin: 10px 0;
        border-left: 3px solid #3498db;
        background-color: white;
        border-radius: 3px;
      }

      .type-progress_update {
        border-left-color: #2ecc71;
        background-color: #e8f8f5;
      }

      .type-error {
        border-left-color: #e74c3c;
        background-color: #fdedec;
      }

      .timestamp {
        color: #95a5a6;
        font-size: 12px;
      }

      .type {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 3px;
        background-color: #3498db;
        color: white;
        font-size: 12px;
        margin-left: 10px;
      }

      pre {
        margin: 5px 0 0 0;
        padding: 10px;
        background-color: #2c3e50;
        color: #ecf0f1;
        border-radius: 3px;
        overflow-x: auto;
        font-size: 12px;
      }

      .clear-btn {
        margin-top: 10px;
        background-color: #e74c3c;
      }

      .current-state {
        margin-top: 30px;
        padding: 20px;
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 5px;
      }

      .state-info {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin-top: 15px;
      }

      .info-item {
        padding: 10px;
        background-color: white;
        border-radius: 3px;
      }

      .no-messages {
        text-align: center;
        color: #95a5a6;
        padding: 20px;
      }
    `,
  ],
})
export class LearningProgressDemoComponent implements OnInit, OnDestroy {
  isConnected = false;
  connectionStatus = '未连接';
  messageLog: Array<{ type: string; data: unknown; timestamp: string }> = [];
  currentState: LearningState | null = null;

  // 表单数据
  lessonId = 1;
  progressPercentage = 50;
  timeSpentSeconds = 300;
  quizScore = 85;

  private subscriptions: Subscription[] = [];

  constructor(private wsService: AiEduWebSocketService) {}

  ngOnInit(): void {
    // 监听连接状态
    const statusSub = this.wsService.connectionStatus$.subscribe((status) => {
      this.isConnected = status === 'connected';
      this.connectionStatus = this.getStatusText(status);
    });
    this.subscriptions.push(statusSub);

    // 监听进度更新
    const progressSub = this.wsService.onProgressUpdate().subscribe((data) => {
      this.addLog('progress_update', data);
      this.currentState = {
        lesson_id: data.lesson_id,
        progress: data.progress_percentage,
        status: data.status,
        time_spent_seconds: data.time_spent_seconds,
        last_update: data.timestamp,
      };
    });
    this.subscriptions.push(progressSub);

    // 监听错误
    const errorSub = this.wsService.onErrors().subscribe((error) => {
      this.addLog('error', { code: error.code, message: error.error });
    });
    this.subscriptions.push(errorSub);
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach((sub) => sub.unsubscribe());
  }

  connect(): void {
    // 使用测试用户 ID 和组织 ID
    this.wsService.connect(1, 1, 'http://localhost:8000');
  }

  disconnect(): void {
    this.wsService.disconnect();
  }

  getCurrentState(): void {
    this.wsService.getCurrentState();
  }

  updateProgress(): void {
    this.wsService.updateProgress({
      lesson_id: this.lessonId,
      progress: {
        progress_percentage: this.progressPercentage,
        time_spent_seconds: this.timeSpentSeconds,
        quiz_score: this.quizScore,
        status: this.progressPercentage >= 100 ? 'completed' : 'in_progress',
      },
    });
  }

  private addLog(type: string, data: unknown): void {
    this.messageLog.unshift({
      type,
      data,
      timestamp: new Date().toLocaleTimeString(),
    });

    // 限制日志数量
    if (this.messageLog.length > 50) {
      this.messageLog.pop();
    }
  }

  clearLog(): void {
    this.messageLog = [];
  }

  private getStatusText(status: string): string {
    switch (status) {
      case 'connecting':
        return '连接中...';
      case 'connected':
        return '已连接 ✅';
      case 'disconnected':
        return '已断开 ❌';
      case 'error':
        return '错误 ⚠️';
      default:
        return '未知状态';
    }
  }

  formatTime(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}分${secs}秒`;
  }
}
