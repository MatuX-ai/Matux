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
  templateUrl: './ai-teacher-settings.component.html',
  styleUrls: ['./ai-teacher-settings.component.scss'],
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
