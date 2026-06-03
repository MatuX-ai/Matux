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
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { AITeacherService } from '../../../core/services/ai-teacher.service';
import {
  ChatMessage,
  StudentLearningProfile,
  TeacherPersona,
  TeachingSuggestion,
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
            <span class="profile-chip">📊 {{ profile.gradeLevel }} · {{ learningStyleLabel }} · {{ skillLevelLabel }}</span>
            <span class="profile-chip persona-chip" *ngIf="persona">{{ personaLabel }}</span>
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
        <!-- 空状态：快捷操作区 -->
        <div class="welcome-section" *ngIf="messages.length === 0 && !isLoading">
          <div class="welcome-avatar">🤖</div>
          <h4 class="welcome-title">嗨，{{ profile?.displayName ?? '同学' }}！👋</h4>
          <p class="welcome-desc">我是你的 AI 学习伙伴，有什么需要帮助的吗？</p>
          <div class="quick-actions">
            <button
              *ngFor="let action of quickActions"
              mat-stroked-button
              class="quick-action-btn"
              (click)="sendQuickAction(action.query)">
              <mat-icon>{{ action.icon }}</mat-icon>
              {{ action.label }}
            </button>
          </div>
        </div>

        <div *ngFor="let msg of messages"
          [class.user-msg]="msg.role === 'user'"
          [class.ai-msg]="msg.role === 'assistant'"
          class="message-row">
          <div class="avatar">
            {{ msg.role === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="message-bubble">
            <div class="message-text" [innerHTML]="formatMessage(msg.content)"></div>
            <div *ngIf="msg.metadata" class="message-meta">
              <span *ngIf="msg.metadata.knowledgeUsed" class="meta-tag knowledge">📚 知识库</span>
              <span *ngIf="msg.metadata.referencedMemories?.length" class="meta-tag memory">📌 记忆引用·{{ msg.metadata.referencedMemories?.length ?? 0 }}</span>
              <span *ngIf="msg.metadata.emotionDetected && msg.metadata.emotionDetected !== 'neutral'"
                class="meta-tag emotion">{{ emotionEmoji[msg.metadata.emotionDetected] }} {{ emotionLabel(msg.metadata.emotionDetected) }}</span>
            </div>
            <span class="message-time">{{ msg.timestamp | date:'HH:mm' }}</span>
          </div>
        </div>

        <!-- 教学建议标签 -->
        <div class="suggestion-section" *ngIf="suggestions.length > 0">
          <span class="suggestion-label">💡 试试问这些：</span>
          <div class="suggestion-chips">
            <button
              *ngFor="let item of suggestions"
              mat-chip
              class="suggestion-chip"
              (click)="sendQuickAction(item.title)">
              {{ item.title }}
            </button>
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
      max-height: 600px;
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
    .profile-chips { margin-top: 6px; display: flex; gap: 4px; flex-wrap: wrap; }
    .profile-chip {
      font-size: 11px; background: rgba(255,255,255,0.2);
      padding: 2px 8px; border-radius: 12px;
    }
    .persona-chip {
      background: rgba(253, 224, 71, 0.25);
    }
    .header-actions { display: flex; gap: 4px; }
    .header-btn { color: white; }

    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 12px;
      max-height: 400px;
    }

    /* 欢迎区 / 快捷操作 */
    .welcome-section {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 24px 16px 16px;
      text-align: center;
    }
    .welcome-avatar { font-size: 48px; margin-bottom: 8px; }
    .welcome-title {
      font-size: 18px; font-weight: 700; color: #0f172a; margin: 0 0 4px 0;
    }
    .welcome-desc {
      font-size: 13px; color: #64748b; margin: 0 0 20px 0;
    }
    .quick-actions {
      display: flex;
      flex-direction: column;
      gap: 8px;
      width: 100%;
    }
    .quick-action-btn {
      width: 100%;
      display: flex;
      align-items: center;
      gap: 8px;
      justify-content: center;
      padding: 8px;
    }
    .quick-action-btn mat-icon {
      font-size: 18px;
    }

    /* 教学建议标签 */
    .suggestion-section {
      padding: 4px 12px 12px;
    }
    .suggestion-label {
      font-size: 12px;
      color: #94a3b8;
      margin-bottom: 6px;
      display: block;
    }
    .suggestion-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .suggestion-chip {
      font-size: 12px !important;
      padding: 4px 10px !important;
      background: #f1f5f9 !important;
      cursor: pointer;
      transition: background 0.2s;
      border: none;
    }
    .suggestion-chip:hover {
      background: #dbeafe !important;
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

    .message-text { margin: 0; white-space: pre-wrap; word-break: break-word; }
    .message-text :deep(code) {
      background: #e2e8f0;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 12px;
      font-family: 'Fira Code', 'Consolas', monospace;
    }
    .message-text :deep(pre) {
      background: #1e293b;
      color: #e2e8f0;
      padding: 12px;
      border-radius: 8px;
      overflow-x: auto;
      font-size: 12px;
      font-family: 'Fira Code', 'Consolas', monospace;
      margin: 8px 0;
      line-height: 1.6;
    }
    .user-msg .message-text :deep(code) {
      background: rgba(255,255,255,0.2);
    }
    .user-msg .message-text :deep(pre) {
      background: rgba(0,0,0,0.15);
      color: white;
    }
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

  suggestions: TeachingSuggestion[] = [];
  quickActions = [
    { icon: 'trending_up', label: '我的学习进度', query: '我最近学习进展如何？' },
    { icon: 'psychology', label: '推荐学什么', query: '根据我的情况，推荐我学习什么？' },
    { icon: 'emoji_events', label: '今天挑战', query: '给我一个今天的编程挑战' },
    { icon: 'help', label: '解答问题', query: '我有个问题想问你' },
  ];

  private destroy$ = new Subject<void>();

  constructor(private aiTeacherService: AITeacherService) {}

  ngOnInit(): void {
    this.aiTeacherService.profile$.pipe(takeUntil(this.destroy$)).subscribe((p) => { this.profile = p; });
    this.aiTeacherService.persona$.pipe(takeUntil(this.destroy$)).subscribe((p) => {
      this.persona = p;
    });
    this.aiTeacherService.session$.pipe(takeUntil(this.destroy$)).subscribe((s) => {
      if (s) { this.messages = s.recentMessages; }
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
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

  /** 根据AI教师人格显示风格标签 */
  get personaLabel(): string {
    const styleMap: Record<string, string> = {
      lively: '🗣️ 活泼', formal: '🎓 专业',
      concise: '⚡ 简洁', humorous: '😄 幽默',
    };
    return styleMap[this.persona?.languageStyle ?? ''] ?? '🎯 标准';
  }

  /** 格式化消息内容：支持代码块、粗体 */
  formatMessage(content: string): string {
    let html = this.escapeHtml(content);
    // 代码块 ```code```
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
      const langLabel = lang ? `<span class="code-lang">${lang}</span>` : '';
      return `<pre>${langLabel}${this.escapeHtml(code.trim())}</pre>`;
    });
    // 行内代码 `code`
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    // 粗体 **text**
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // 换行
    html = html.replace(/\n/g, '<br>');
    return html;
  }

  /** 发送快捷操作 */
  sendQuickAction(query: string): void {
    this.userInput = query;
    this.sendMessage();
  }

  /** 情感标签中文名 */
  emotionLabel(emotion: string): string {
    const map: Record<string, string> = {
      frustrated: '沮丧', confused: '困惑', excited: '兴奋',
      anxious: '焦虑', bored: '无聊', confident: '自信',
    };
    return map[emotion] ?? '';
  }

  private escapeHtml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
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
    this.suggestions = []; // 清除旧建议

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
        // 显示AI建议（最多3条）
        if (response.suggestions?.length) {
          this.suggestions = response.suggestions.slice(0, 3);
        }
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
