/**
 * AI 教师人格设置组件
 *
 * PRD 6.6 关键页面线框 - "AI 教师设置"
 * 允许学生调整AI教师的称呼方式、语言风格、提示程度等
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, Input, Output, EventEmitter } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatRadioModule } from '@angular/material/radio';

import {
  TeacherPersona,
  AddressMode,
  LanguageStyle,
  HintLevel,
  EncouragementFrequency,
  EmojiUsage,
} from '../../../core/models/ai-teacher.models';

@Component({
  selector: 'app-teacher-persona-settings',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatRadioModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="settings-container">
      <!-- 称呼方式 -->
      <mat-card class="setting-card">
        <mat-card-header>
          <mat-icon mat-card-avatar>badge</mat-icon>
          <mat-card-title>称呼方式</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <mat-radio-group [(ngModel)]="persona.addressMode" (change)="onSettingChange()">
            <mat-radio-button value="name">叫我"{{ studentName }}"</mat-radio-button>
            <mat-radio-button value="nickname">叫我"{{ persona.nickname || '小明明' }}"（昵称）</mat-radio-button>
            <mat-radio-button value="classmate">叫我"同学"</mat-radio-button>
          </mat-radio-group>
          <div *ngIf="persona.addressMode === 'nickname'" class="nickname-input">
            <input type="text" [(ngModel)]="persona.nickname"
              placeholder="输入昵称" class="nickname-field"
              (input)="onSettingChange()">
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 语言风格 -->
      <mat-card class="setting-card">
        <mat-card-header>
          <mat-icon mat-card-avatar>chat</mat-icon>
          <mat-card-title>语言风格</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <mat-radio-group [(ngModel)]="persona.languageStyle" (change)="onSettingChange()">
            <mat-radio-button value="lively">活泼开朗</mat-radio-button>
            <mat-radio-button value="formal">严谨专业</mat-radio-button>
            <mat-radio-button value="concise">简洁高效</mat-radio-button>
            <mat-radio-button value="humorous">幽默风趣</mat-radio-button>
          </mat-radio-group>
        </mat-card-content>
      </mat-card>

      <!-- 提示程度 -->
      <mat-card class="setting-card">
        <mat-card-header>
          <mat-icon mat-card-avatar>lightbulb</mat-icon>
          <mat-card-title>提示程度</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <mat-radio-group [(ngModel)]="persona.hintLevel" (change)="onSettingChange()">
            <mat-radio-button value="direct_answer">直接给答案</mat-radio-button>
            <mat-radio-button value="guided_thinking">引导我思考</mat-radio-button>
            <mat-radio-button value="direction_only">只给方向，让我自己探索</mat-radio-button>
          </mat-radio-group>
        </mat-card-content>
      </mat-card>

      <!-- 鼓励频率 -->
      <mat-card class="setting-card">
        <mat-card-header>
          <mat-icon mat-card-avatar>favorite</mat-icon>
          <mat-card-title>鼓励频率</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <mat-radio-group [(ngModel)]="persona.encouragementFrequency" (change)="onSettingChange()">
            <mat-radio-button value="high">高（经常夸我）</mat-radio-button>
            <mat-radio-button value="moderate">适中</mat-radio-button>
            <mat-radio-button value="milestone_only">低（只在里程碑时）</mat-radio-button>
          </mat-radio-group>
        </mat-card-content>
      </mat-card>

      <!-- Emoji 使用 -->
      <mat-card class="setting-card">
        <mat-card-header>
          <mat-icon mat-card-avatar>emoji_emotions</mat-icon>
          <mat-card-title>Emoji 使用</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <mat-radio-group [(ngModel)]="persona.emojiUsage" (change)="onSettingChange()">
            <mat-radio-button value="heavy">多用 emoji，我喜欢！</mat-radio-button>
            <mat-radio-button value="moderate">适量</mat-radio-button>
            <mat-radio-button value="none">不用</mat-radio-button>
          </mat-radio-group>
        </mat-card-content>
      </mat-card>

      <!-- 重置记忆 -->
      <mat-card class="setting-card danger-card">
        <mat-card-header>
          <mat-icon mat-card-avatar class="danger-icon">restart_alt</mat-icon>
          <mat-card-title>重置 AI 教师记忆</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <p class="danger-text">清除 AI 教师关于你的所有记忆，从头开始</p>
          <button mat-raised-button color="warn" (click)="resetMemory()">
            重置记忆
          </button>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .settings-container {
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding: 16px;
      max-width: 600px;
    }
    .setting-card {
      border-radius: 16px;
    }
    .setting-card [mat-card-avatar] {
      font-size: 24px;
      color: #3b82f6;
    }
    mat-radio-group {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 8px 0;
    }
    .nickname-input {
      margin-top: 12px;
    }
    .nickname-field {
      padding: 8px 12px;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      font-size: 14px;
      outline: none;
      transition: border-color 0.2s;
    }
    .nickname-field:focus {
      border-color: #3b82f6;
    }
    .danger-card {
      border: 1px solid #fecaca;
    }
    .danger-icon {
      color: #ef4444 !important;
    }
    .danger-text {
      font-size: 13px;
      color: #64748b;
      margin-bottom: 12px;
    }
  `],
})
export class TeacherPersonaSettingsComponent {
  @Input() persona: TeacherPersona = {
    userId: '',
    addressMode: 'name',
    nickname: '',
    languageStyle: 'lively',
    hintLevel: 'guided_thinking',
    encouragementFrequency: 'moderate',
    strictness: 'standard',
    emojiUsage: 'moderate',
  };
  @Input() studentName = '小明';

  @Output() personaChange = new EventEmitter<TeacherPersona>();
  @Output() resetMemoryRequest = new EventEmitter<void>();

  onSettingChange(): void {
    this.personaChange.emit({ ...this.persona });
  }

  resetMemory(): void {
    if (confirm('确定要重置 AI 教师的所有记忆吗？此操作不可撤销。')) {
      this.resetMemoryRequest.emit();
    }
  }
}
