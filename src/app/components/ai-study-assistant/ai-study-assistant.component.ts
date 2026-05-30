/**
 * AI 学习助手聊天组件
 * 提供悬浮窗式的对话界面，学生可以随时提问
 */

import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

interface ChatResponse {
  reply: string;
  model: string;
  confidence: number;
  inference_time_ms: number;
  knowledge_used: boolean;
  data?: {
    reply: string;
  };
}

@Component({
  selector: 'app-ai-study-assistant',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatIconModule,
    MatButtonModule,
    MatInputModule,
    MatProgressBarModule,
    MatCardModule,
    HttpClientModule,
  ],
  template: `
    <div class="assistant-container">
      <!-- 悬浮按钮 -->
      <button mat-fab color="accent" class="toggle-btn" (click)="toggleChat()" title="AI 学习助手">
        <mat-icon>smart_toy</mat-icon>
      </button>

      <!-- 聊天窗口 -->
      <div class="chat-window" *ngIf="isVisible">
        <!-- 头部 -->
        <div class="chat-header">
          <div class="header-title">
            <mat-icon>school</mat-icon>
            <h3>AI 学习助手</h3>
          </div>
          <div class="header-actions">
            <button mat-icon-button (click)="clearHistory()" title="清除历史">
              <mat-icon>delete</mat-icon>
            </button>
            <button mat-icon-button (click)="toggleChat()" title="关闭">
              <mat-icon>close</mat-icon>
            </button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div class="chat-messages" #messageContainer>
          <div
            *ngFor="let msg of messages"
            [class.user-msg]="msg.role === 'user'"
            [class.ai-msg]="msg.role === 'assistant'"
            class="message-row"
          >
            <div class="avatar">
              {{ msg.role === 'user' ? '👤' : '🤖' }}
            </div>

            <div class="message-content">
              <div class="message-text">{{ msg.content }}</div>
              <div class="message-time" *ngIf="msg.timestamp">
                {{ msg.timestamp | date: 'HH:mm' }}
              </div>
            </div>
          </div>

          <!-- 输入中提示 -->
          <div *ngIf="isTyping" class="typing-indicator">
            <mat-progress-bar mode="indeterminate"></mat-progress-bar>
            <span>AI 正在思考...</span>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input">
          <textarea
            matInput
            [(ngModel)]="userInput"
            (keydown.enter)="handleEnterKey($event)"
            placeholder="问一个 AI 学习问题..."
            rows="2"
          ></textarea>
          <button
            mat-icon-button
            color="primary"
            (click)="sendMessage()"
            [disabled]="!userInput.trim() || isTyping"
          >
            <mat-icon>send</mat-icon>
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .assistant-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
      }

      .toggle-btn {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
      }

      .chat-window {
        position: absolute;
        bottom: 70px;
        right: 0;
        width: 400px;
        height: 600px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }

      .chat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
      }

      .header-title {
        display: flex;
        align-items: center;
        gap: 8px;

        h3 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
        }
      }

      .header-actions {
        display: flex;
        gap: 4px;

        button {
          color: white;
        }
      }

      .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        background: #f5f5f5;
      }

      .message-row {
        display: flex;
        gap: 8px;
        margin-bottom: 16px;

        &.user-msg {
          flex-direction: row-reverse;

          .message-content {
            background: #667eea;
            color: white;

            .message-time {
              color: rgba(255, 255, 255, 0.7);
            }
          }
        }

        &.ai-msg {
          .message-content {
            background: white;
            border: 1px solid #e0e0e0;
          }
        }
      }

      .avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        flex-shrink: 0;
      }

      .message-content {
        max-width: 70%;
        padding: 12px 16px;
        border-radius: 12px;
        word-wrap: break-word;
      }

      .message-text {
        line-height: 1.5;
        white-space: pre-wrap;
      }

      .message-time {
        font-size: 11px;
        margin-top: 4px;
        text-align: right;
      }

      .typing-indicator {
        padding: 12px;
        background: white;
        border-radius: 12px;
        max-width: 200px;

        mat-progress-bar {
          margin-bottom: 8px;
        }

        span {
          font-size: 12px;
          color: #666;
        }
      }

      .chat-input {
        display: flex;
        padding: 12px;
        background: white;
        border-top: 1px solid #e0e0e0;
        gap: 8px;

        textarea {
          flex: 1;
          resize: none;
          font-size: 14px;
        }
      }
    `,
  ],
})
export class AiStudyAssistantComponent implements OnInit, OnDestroy {
  isVisible = false;
  userInput = '';
  isTyping = false;
  messages: Message[] = [];
  currentLessonId?: number; // 当前课程 ID

  @ViewChild('messageContainer') messageContainer!: ElementRef;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    // 加载欢迎消息
    this.messages.push({
      role: 'assistant',
      content: '你好！我是你的 AI 学习助手，有任何学习问题都可以问我哦！😊',
      timestamp: new Date().toISOString(),
    });
  }

  ngOnDestroy(): void {
    // 清理资源
  }

  toggleChat(): void {
    this.isVisible = !this.isVisible;
    if (this.isVisible) {
      setTimeout(() => this.scrollToBottom(), 100);
    }
  }

  handleEnterKey(event: Event): void {
    // 检查是否按下 Shift 键（Shift+Enter 换行）
    if ((event as KeyboardEvent).shiftKey) {
      return;
    }
    event.preventDefault();
    void this.sendMessage();
  }

  async sendMessage(): Promise<void> {
    if (!this.userInput.trim() || this.isTyping) {
      return;
    }

    // 添加用户消息
    const userMessage: Message = {
      role: 'user',
      content: this.userInput.trim(),
      timestamp: new Date().toISOString(),
    };

    this.messages.push(userMessage);
    const question = this.userInput;
    this.userInput = '';
    this.isTyping = true;

    this.scrollToBottom();

    try {
      const reply = await this.callChatApi(question);
      const aiMessage: Message = {
        role: 'assistant',
        content: reply,
        timestamp: new Date().toISOString(),
      };
      this.messages.push(aiMessage);
    } catch (error) {
      this.messages.push({
        role: 'assistant',
        content: '抱歉，我遇到了一些问题，请稍后再试。',
        timestamp: new Date().toISOString(),
      });
    } finally {
      this.isTyping = false;
      this.scrollToBottom();
    }
  }

  private async callChatApi(message: string): Promise<string> {
    const response = await this.http
      .post<ChatResponse>(
        `/api/v1/org/1/ai-edu/assistant/chat`,
        {
          message,
          current_lesson_id: this.currentLessonId,
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      )
      .toPromise();

    if (response?.data) {
      return response.data.reply;
    } else {
      throw new Error('响应格式不正确');
    }
  }

  clearHistory(): void {
    if (confirm('确定要清除对话历史吗？')) {
      this.messages = [
        {
          role: 'assistant',
          content: '对话历史已清除。有什么新的问题吗？',
          timestamp: new Date().toISOString(),
        },
      ];

      // 调用后端 API 清除历史
      this.http
        .delete(`/api/v1/org/1/ai-edu/assistant/history`)
        .toPromise()
        .then(() => {
          // 清除成功
        })
        .catch((_error) => {
          // 忽略错误
        });
    }
  }

  scrollToBottom(): void {
    setTimeout(() => {
      try {
        const element = this.messageContainer.nativeElement as HTMLElement;
        element.scrollTop = element.scrollHeight;
      } catch (err) {
        // 忽略滚动失败错误
      }
    }, 100);
  }
}
