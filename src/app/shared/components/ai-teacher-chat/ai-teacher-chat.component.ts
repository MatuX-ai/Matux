/**
 * AI 个性化教师聊天面板
 *
 * PRD 6.6 关键页面线框 - "AI 教师聊天面板"
 * 特性：
 * - 上下文感知（注入学生画像）
 * - 长期记忆引用
 * - 个性化教学建议
 * - 情感感知
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { Subscription } from 'rxjs';

import { AITeacherService } from '../../../core/services/ai-teacher.service';
import {
  ChatMessage,
  StudentLearningProfile,
  TeacherPersona,
} from '../../../core/models/ai-teacher.models';

@Component({
  selector: 'app-ai-teacher-chat',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatIconModule,
    MatButtonModule,
    MatInputModule,
    MatProgressBarModule,
    MatCardModule,
    MatChipsModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <!-- 悬浮按钮 -->
    <button mat-fab class="toggle-btn" (click)="toggleChat()" title="AI 个性化教师">
      <mat-icon>smart_toy</mat-icon>
    </button>

    <!-- 聊天窗口 -->
    <div class="chat-window" *ngIf="isVisible">
      <!-- 头部 - 渐变背景 -->
      <div class="chat-header">
        <div class="header-info">
          <div class="header-title">
            <mat-icon>school</mat-icon>
            <h3>AI 老师 · {{ profile?.displayName ?? '同学' }}的学习伙伴</h3>
          </div>
          <div class="profile-chips" *ngIf="profile">
            <span class="profile-chip">📊 画像：{{ profile.gradeLevel }} · {{ learningStyleLabel }} · Python {{ skillLevelLabel }}</span>
          </div>
        </div>
        <div class="header-actions">
          <button mat-icon-button (click)="clearHistory()" title="清除历史" class="header-btn">
            <mat-icon>delete_outline</mat-icon>
          </button>
          <button mat-icon-button (click)="toggleChat()" title="关闭" class="header-btn">
            <mat-icon>close</mat-icon>
          </button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div class="chat-messages" #messageContainer>
        <div *ngFor="let msg of messages"
          [class.user-msg]="msg.role === 'user'"
          [class.ai-msg]="msg.role === 'assistant'"
          class="message-row">
          <div class="avatar">
            {{ msg.role === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="message-bubble">
            <p class="message-text">{{ msg.content }}</p>
            <div *ngIf="msg.metadata" class="message-meta">
              <span *ngIf="msg.metadata.knowledgeUsed" class="meta-tag knowledge">📚 知识库</span>
              <span *ngIf="msg.metadata.referencedMemories?.length" class="meta-tag memory">📌 记忆引用</span>
              <span *ngIf="msg.metadata.emotionDetected && msg.metadata.emotionDetected !== 'neutral'"
                class="meta-tag emotion">{{ emotionEmoji[msg.metadata.emotionDetected] }}</span>
            </div>
            <span class="message-time">{{ msg.timestamp | date:'HH:mm' }}</span>
          </div>
        </div>

        <!-- 加载中 -->
        <div *ngIf="isLoading" class="message-row ai-msg">
          <div class="avatar">🤖</div>
          <div class="message-bubble thinking">
            <span class="thinking-dots">
              <span>.</span><span>.</span><span>.</span>
            </span>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input">
        <input
          type="text"
          placeholder="输入问题..."
          [(ngModel)]="userInput"
          (keyup.enter)="sendMessage()"
          class="chat-input-field"
          [disabled]="isLoading">
        <button mat-icon-button (click)="sendMessage()" [disabled]="isLoading || !userInput.trim()"
          color="primary" class="send-btn">
          <mat-icon>send</mat-icon>
        </button>
      </div>
    </div>
  `,
  styles: [`
    .toggle-btn {
      position: fixed;
      bottom: 96px;
      right: 24px;
      z-index: 1000;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      color: white;
      width: 56px; height: 56px;
      box-shadow: 0 4px 20px rgba(99,102,241,0.4);
      transition: transform 0.2s;
    }
    .toggle-btn:hover { transform: scale(1.1); }

    .chat-window {
      position: fixed;
      bottom: 168px;
      right: 24px;
      width: 420px;
      max-height: 560px;
      background: white;
      border-radius: 24px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.15);
      display: flex;
      flex-direction: column;
      z-index: 1001;
      overflow: hidden;
    }

    .chat-header {
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      color: white;
      padding: 12px 16px;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
    }
    .header-info { flex: 1; }
    .header-title {
      display: flex; align-items: center; gap: 8px;
    }
    .header-title h3 { margin: 0; font-size: 14px; font-weight: 600; }
    .header-title mat-icon { font-size: 20px; }
    .profile-chips { margin-top: 6px; }
    .profile-chip {
      font-size: 11px; background: rgba(255,255,255,0.2);
      padding: 2px 8px; border-radius: 12px;
    }
    .header-actions { display: flex; gap: 4px; }
    .header-btn { color: white; }

    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 12px;
      max-height: 380px;
    }

    .message-row {
      display: flex;
      gap: 8px;
      margin-bottom: 12px;
      align-items: flex-start;
    }
    .user-msg { flex-direction: row-reverse; }

    .avatar {
      font-size: 20px;
      min-width: 32px;
      text-align: center;
    }

    .message-bubble {
      max-width: 300px;
      padding: 10px 14px;
      border-radius: 16px;
      font-size: 13px;
      line-height: 1.5;
      position: relative;
    }
    .ai-msg .message-bubble {
      background: #f1f5f9;
      color: #1e293b;
      border-bottom-left-radius: 4px;
    }
    .user-msg .message-bubble {
      background: #3b82f6;
      color: white;
      border-bottom-right-radius: 4px;
    }

    .message-text { margin: 0; white-space: pre-wrap; }
    .message-meta {
      display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap;
    }
    .meta-tag {
      font-size: 10px; padding: 1px 6px; border-radius: 8px;
    }
    .meta-tag.knowledge { background: #dbeafe; color: #2563eb; }
    .meta-tag.memory { background: #fef3c7; color: #92400e; }
    .meta-tag.emotion { background: #fce7f3; color: #9d174d; }
    .message-time {
      font-size: 10px; color: #94a3b8;
      display: block; text-align: right; margin-top: 4px;
    }
    .user-msg .message-time { color: rgba(255,255,255,0.7); }

    .thinking { padding: 14px; }
    .thinking-dots span {
      animation: blink 1.4s infinite both;
      font-size: 18px;
    }
    .thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
    .thinking-dots span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes blink { 0%, 80%, 100% { opacity: 0; } 40% { opacity: 1; } }

    .chat-input {
      display: flex;
      align-items: center;
      padding: 8px 12px;
      border-top: 1px solid #f1f5f9;
      gap: 8px;
    }
    .chat-input-field {
      flex: 1;
      border: none;
      outline: none;
      font-size: 14px;
      padding: 8px;
      border-radius: 12px;
      background: #f8fafc;
    }
    .chat-input-field:focus { background: #f1f5f9; }
    .send-btn { flex-shrink: 0; }

    @media (max-width: 768px) {
      .chat-window {
        width: calc(100vw - 16px);
        right: 8px;
        bottom: 80px;
        max-height: 70vh;
      }
      .toggle-btn { bottom: 24px; right: 16px; }
    }
  `],
})
export class AITeacherChatComponent implements OnInit, OnDestroy {
  isVisible = false;
  isLoading = false;
  userInput = '';
  messages: ChatMessage[] = [];

  profile: StudentLearningProfile | null = null;
  persona: TeacherPersona | null = null;

  emotionEmoji: Record<string, string> = {
    frustrated: '😫', confused: '😕', excited: '🎉',
    anxious: '😰', bored: '😐', confident: '💪', neutral: '',
  };

  @ViewChild('messageContainer') messageContainer!: ElementRef;

  private subs: Subscription[] = [];

  constructor(private aiTeacherService: AITeacherService) {}

  ngOnInit(): void {
    this.subs.push(
      this.aiTeacherService.profile$.subscribe((p) => { this.profile = p; }),
      this.aiTeacherService.persona$.subscribe((p) => { this.persona = p; }),
      this.aiTeacherService.session$.subscribe((s) => {
        if (s) { this.messages = s.recentMessages; }
      }),
    );
  }

  ngOnDestroy(): void {
    this.subs.forEach((s) => s.unsubscribe());
  }

  get learningStyleLabel(): string {
    const map: Record<string, string> = { visual: '视觉型', auditory: '听觉型', reading: '读写型', kinesthetic: '动觉型' };
    return map[this.profile?.learningStyle ?? 'visual'] ?? '视觉型';
  }

  get skillLevelLabel(): string {
    const score = this.profile?.abilityDimensions?.programmingThinking ?? 0;
    if (score >= 80) return '高阶';
    if (score >= 50) return '中阶';
    return '入门';
  }

  toggleChat(): void {
    this.isVisible = !this.isVisible;
    if (this.isVisible && !this.messages.length) {
      // 显示欢迎消息
      this.messages = [{
        role: 'assistant',
        content: `${this.profile?.displayName ?? '同学'}，你好！☀️\n我是你的 AI 学习伙伴。我记得你最近在学循环，上次测验正确率不错哦！\n\n💡 有什么问题都可以问我～`,
        timestamp: new Date().toISOString(),
      }];
    }
  }

  sendMessage(): void {
    const msg = this.userInput.trim();
    if (!msg || this.isLoading) return;

    this.userInput = '';
    this.isLoading = true;

    // 添加用户消息
    const userMsg: ChatMessage = {
      role: 'user',
      content: msg,
      timestamp: new Date().toISOString(),
    };
    this.messages = [...this.messages, userMsg];
    this.scrollToBottom();

    // 调用AI教师服务
    this.aiTeacherService.chat({
      userId: this.profile?.userId ?? '',
      message: msg,
      sessionId: this.aiTeacherService.currentSession?.sessionId ?? `session_${Date.now()}`,
    }).subscribe({
      next: (response) => {
        const aiMsg: ChatMessage = {
          role: 'assistant',
          content: response.reply,
          timestamp: new Date().toISOString(),
          metadata: {
            knowledgeUsed: response.knowledgeUsed,
            confidence: response.confidence,
            referencedMemories: response.memoriesReferenced,
            emotionDetected: response.emotionDetected,
          },
        };
        this.messages = [...this.messages, aiMsg];
        this.isLoading = false;
        this.scrollToBottom();
      },
      error: () => {
        this.messages = [...this.messages, {
          role: 'assistant',
          content: '抱歉，我暂时无法回复。请稍后再试～',
          timestamp: new Date().toISOString(),
        }];
        this.isLoading = false;
        this.scrollToBottom();
      },
    });
  }

  clearHistory(): void {
    this.messages = [];
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      if (this.messageContainer?.nativeElement) {
        this.messageContainer.nativeElement.scrollTop = this.messageContainer.nativeElement.scrollHeight;
      }
    }, 50);
  }
}
