/**
 * AI 教师设置页面
 *
 * PRD 3.3-AI.6 情感陪伴 - AI教师人格设定
 * 提供：称呼方式、语言风格、提示程度、鼓励频率、Emoji使用、重置记忆
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
} from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatRadioModule } from '@angular/material/radio';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { TeacherPersona } from '../../../core/models/ai-teacher.models';
import { AITeacherService } from '../../../core/services/ai-teacher.service';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-ai-teacher-settings',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatRadioModule,
    MatFormFieldModule,
    MatDividerModule,
    MatSnackBarModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="settings-container">
      <div class="page-header">
        <h1 class="page-title">AI 教师设置</h1>
      </div>

      <form [formGroup]="settingsForm" (ngSubmit)="saveSettings()">
        <!-- 称呼方式 -->
        <mat-card class="settings-section">
          <mat-card-content>
            <h3 class="settings-label">称呼方式</h3>
            <mat-radio-group formControlName="addressMode" class="radio-group">
              <mat-radio-button value="name"
                >叫我的名字{{ userName ? '"' + userName + '"' : '' }}</mat-radio-button
              >
              <mat-radio-button value="nickname"
                >叫我的昵称{{ userNickname ? '"' + userNickname + '"' : '' }}</mat-radio-button
              >
              <mat-radio-button value="classmate">叫我"同学"</mat-radio-button>
            </mat-radio-group>
          </mat-card-content>
        </mat-card>

        <!-- 语言风格 -->
        <mat-card class="settings-section">
          <mat-card-content>
            <h3 class="settings-label">语言风格</h3>
            <mat-radio-group formControlName="languageStyle" class="radio-group">
              <mat-radio-button value="lively">🗣️ 活泼开朗</mat-radio-button>
              <mat-radio-button value="formal">🎓 严谨专业</mat-radio-button>
              <mat-radio-button value="concise">⚡ 简洁高效</mat-radio-button>
              <mat-radio-button value="humorous">😄 幽默风趣</mat-radio-button>
            </mat-radio-group>
          </mat-card-content>
        </mat-card>

        <!-- 提示程度 -->
        <mat-card class="settings-section">
          <mat-card-content>
            <h3 class="settings-label">提示程度</h3>
            <mat-radio-group formControlName="hintLevel" class="radio-group">
              <mat-radio-button value="direct_answer">💡 直接给答案</mat-radio-button>
              <mat-radio-button value="guided_thinking">🧭 引导我思考</mat-radio-button>
              <mat-radio-button value="direction_only">🗺️ 只给方向，让我自己探索</mat-radio-button>
            </mat-radio-group>
          </mat-card-content>
        </mat-card>

        <!-- 鼓励频率 -->
        <mat-card class="settings-section">
          <mat-card-content>
            <h3 class="settings-label">鼓励频率</h3>
            <mat-radio-group formControlName="encouragementFrequency" class="radio-group">
              <mat-radio-button value="high">🌟 高（经常夸我）</mat-radio-button>
              <mat-radio-button value="moderate">👍 适中</mat-radio-button>
              <mat-radio-button value="milestone_only">🏆 低（只在里程碑时）</mat-radio-button>
            </mat-radio-group>
          </mat-card-content>
        </mat-card>

        <!-- Emoji 使用 -->
        <mat-card class="settings-section">
          <mat-card-content>
            <h3 class="settings-label">Emoji 使用</h3>
            <mat-radio-group formControlName="emojiUsage" class="radio-group">
              <mat-radio-button value="heavy">😊🎉 多用 emoji，我喜欢！</mat-radio-button>
              <mat-radio-button value="moderate">🙂 适量</mat-radio-button>
              <mat-radio-button value="none">🗣️ 不用</mat-radio-button>
            </mat-radio-group>
          </mat-card-content>
        </mat-card>

        <!-- 严格程度 -->
        <mat-card class="settings-section">
          <mat-card-content>
            <h3 class="settings-label">严格程度</h3>
            <mat-radio-group formControlName="strictness" class="radio-group">
              <mat-radio-button value="lenient">😊 宽松（鼓励为主）</mat-radio-button>
              <mat-radio-button value="standard">🎯 标准</mat-radio-button>
              <mat-radio-button value="strict">📏 严格（高标准要求）</mat-radio-button>
            </mat-radio-group>
          </mat-card-content>
        </mat-card>

        <!-- 保存按钮 -->
        <div class="action-row">
          <button
            mat-raised-button
            color="primary"
            type="submit"
            [disabled]="!settingsForm.dirty || saving"
            class="save-btn"
          >
            {{ saving ? '保存中...' : '保存设置' }}
          </button>
        </div>
      </form>

      <!-- 重置记忆 -->
      <mat-card class="reset-section">
        <mat-card-content>
          <div class="reset-content">
            <div class="reset-text">
              <h3>🔄 重置 AI 教师记忆</h3>
              <p>清除 AI 教师关于你的所有记忆，从头开始</p>
            </div>
            <button
              mat-stroked-button
              color="warn"
              (click)="confirmResetMemory()"
              [disabled]="resetting"
            >
              {{ resetting ? '重置中...' : '重置记忆' }}
            </button>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [
    `
      .settings-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 24px;
      }

      .page-header {
        margin-bottom: 24px;
      }
      .page-title {
        font-size: 28px;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
      }

      .settings-section {
        margin-bottom: 16px;
      }
      .settings-label {
        font-size: 16px;
        font-weight: 600;
        color: #0f172a;
        margin: 0 0 16px 0;
        padding-bottom: 12px;
        border-bottom: 1px solid #f1f5f9;
      }

      .radio-group {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .radio-group mat-radio-button {
        padding: 8px 12px;
        border-radius: 8px;
        transition: background 0.2s;
      }

      .radio-group mat-radio-button:hover {
        background: #f8fafc;
      }

      .action-row {
        display: flex;
        justify-content: center;
        margin: 24px 0;
      }

      .save-btn {
        min-width: 160px;
        padding: 8px 32px;
        font-size: 15px;
      }

      .reset-section {
        border: 1px solid #fecaca;
        background: #fef2f2;
      }
      .reset-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 24px;
      }
      .reset-text h3 {
        font-size: 16px;
        font-weight: 600;
        color: #dc2626;
        margin: 0 0 4px 0;
      }
      .reset-text p {
        font-size: 14px;
        color: #64748b;
        margin: 0;
      }
    `,
  ],
})
export class AITeacherSettingsComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  settingsForm: FormGroup;
  saving = false;
  resetting = false;

  userName = '';
  userNickname = '';
  userId = '';

  constructor(
    private fb: FormBuilder,
    private aiTeacherService: AITeacherService,
    private authService: AuthService,
    private snackBar: MatSnackBar,
    private cdr: ChangeDetectorRef
  ) {
    this.settingsForm = this.fb.group({
      addressMode: ['name', Validators.required.bind(undefined)],
      languageStyle: ['lively', Validators.required.bind(undefined)],
      hintLevel: ['guided_thinking', Validators.required.bind(undefined)],
      encouragementFrequency: ['moderate', Validators.required.bind(undefined)],
      emojiUsage: ['moderate', Validators.required.bind(undefined)],
      strictness: ['standard', Validators.required.bind(undefined)],
    });
  }

  ngOnInit(): void {
    this.authService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe((user) => {
      if (user?.id) {
        this.userId = String(user.id);
        this.userName = user.username ?? '';
        this.userNickname = (user as { nickname?: string }).nickname ?? this.userName;
        this.loadPersona();
      }
    });
  }

  private loadPersona(): void {
    this.aiTeacherService
      .getPersona(this.userId)
      .pipe(takeUntil(this.destroy$))
      .subscribe((persona) => {
        this.settingsForm.patchValue(
          {
            addressMode: persona.addressMode,
            languageStyle: persona.languageStyle,
            hintLevel: persona.hintLevel,
            encouragementFrequency: persona.encouragementFrequency,
            emojiUsage: persona.emojiUsage,
            strictness: persona.strictness,
          },
          { emitEvent: false }
        );
        this.settingsForm.markAsPristine();
        this.cdr.markForCheck();
      });
  }

  saveSettings(): void {
    if (this.settingsForm.invalid) return;

    this.saving = true;
    this.aiTeacherService
      .updatePersona(this.userId, this.settingsForm.value as Partial<TeacherPersona>)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.saving = false;
          this.settingsForm.markAsPristine();
          this.snackBar.open('✅ AI 教师设置已保存！', '关闭', { duration: 3000 });
          this.cdr.markForCheck();
        },
        error: () => {
          this.saving = false;
          this.snackBar.open('❌ 保存失败，请稍后重试', '关闭', { duration: 3000 });
          this.cdr.markForCheck();
        },
      });
  }

  confirmResetMemory(): void {
    const confirmed = window.confirm(
      '⚠️ 确定要重置 AI 教师记忆吗？\n\n此操作将清除 AI 教师关于你的所有记忆，包括学习记录、对话历史和个性化推荐。\n\n此操作不可恢复！'
    );

    if (confirmed) {
      this.resetMemory();
    }
  }

  private resetMemory(): void {
    this.resetting = true;
    this.aiTeacherService
      .resetMemory(this.userId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.resetting = false;
          this.snackBar.open('🔄 AI 教师记忆已重置', '关闭', { duration: 3000 });
          this.cdr.markForCheck();
        },
        error: () => {
          this.resetting = false;
          this.snackBar.open('❌ 重置失败，请稍后重试', '关闭', { duration: 3000 });
          this.cdr.markForCheck();
        },
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
