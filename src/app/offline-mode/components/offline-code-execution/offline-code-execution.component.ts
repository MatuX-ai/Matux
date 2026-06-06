/**
 * 离线代码执行面板组件
 *
 * 提供离线环境下的代码编辑和执行功能
 */

import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';

import {
  CodeExecutionResult,
  CodeLanguage,
  OfflineCodeExecutionService,
} from '../../services/offline-code-execution.service';

@Component({
  selector: 'app-offline-code-execution',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatSelectModule,
    MatChipsModule,
    MatProgressBarModule,
    FormsModule,
  ],
  template: `
    <mat-card class="code-exec-card">
      <mat-card-header>
        <mat-icon mat-card-avatar>code</mat-icon>
        <mat-card-title>离线代码执行</mat-card-title>
        <mat-card-subtitle>{{
          executionService.getExecutionStatusDescription()
        }}</mat-card-subtitle>
      </mat-card-header>

      <mat-card-content>
        <!-- 语言选择 -->
        <div class="language-selector">
          <mat-select [(ngModel)]="selectedLanguage" class="lang-select">
            <mat-select-trigger>
              <mat-icon>{{
                selectedLanguage === 'python' ? 'data_object' : 'javascript'
              }}</mat-icon>
              {{ selectedLanguage === 'python' ? 'Python' : 'JavaScript' }}
            </mat-select-trigger>
            <mat-option value="python" [disabled]="!executionService.canExecute('python')">
              Python {{ executionService.canExecute('python') ? '' : '(需桌面端)' }}
            </mat-option>
            <mat-option value="javascript">JavaScript</mat-option>
          </mat-select>

          <button
            mat-raised-button
            color="primary"
            (click)="runCode()"
            [disabled]="executionService.executing$ | async"
          >
            <mat-icon>play_arrow</mat-icon> 运行
          </button>

          <button mat-icon-button (click)="clearCode()" matTooltip="清空代码">
            <mat-icon>delete_outline</mat-icon>
          </button>
        </div>

        <!-- 代码编辑区 -->
        <div class="code-editor-wrapper">
          <textarea
            [(ngModel)]="code"
            class="code-textarea"
            placeholder="在此输入代码..."
            [attr.data-lang]="selectedLanguage"
            spellcheck="false"
          >
          </textarea>
        </div>

        <!-- 执行进度 -->
        <mat-progress-bar *ngIf="executionService.executing$ | async" mode="indeterminate">
        </mat-progress-bar>

        <!-- 执行结果 -->
        <div
          *ngIf="lastResult"
          class="result-panel"
          [class.result-success]="lastResult.success"
          [class.result-error]="!lastResult.success"
        >
          <div class="result-header">
            <mat-icon>{{ lastResult.success ? 'check_circle' : 'error' }}</mat-icon>
            <span>{{ lastResult.success ? '执行成功' : '执行失败' }}</span>
            <span class="execution-time">{{ lastResult.executionTimeMs }}ms</span>
          </div>
          <pre class="result-output" *ngIf="lastResult.output">{{ lastResult.output }}</pre>
          <pre class="result-error" *ngIf="lastResult.error">{{ lastResult.error }}</pre>
        </div>

        <!-- 执行历史 -->
        <div *ngIf="(executionService.history$ | async)?.length" class="history-section">
          <h4>执行历史</h4>
          <mat-chip-listbox>
            <mat-chip
              *ngFor="let entry of executionService.history$ | async | slice: 0 : 5"
              (click)="loadFromHistory(entry)"
            >
              {{ entry.language }} - {{ entry.result.success ? '成功' : '失败' }}
            </mat-chip>
          </mat-chip-listbox>
        </div>
      </mat-card-content>
    </mat-card>
  `,
  styles: [
    `
      .code-exec-card {
        margin: 16px;
      }
      .language-selector {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
      }
      .lang-select {
        width: 180px;
      }
      .code-editor-wrapper {
        margin-bottom: 12px;
      }
      .code-textarea {
        width: 100%;
        min-height: 200px;
        padding: 12px;
        font-family: 'Geist Mono', 'Consolas', monospace;
        font-size: 14px;
        background: #0f172a;
        color: #22c55e;
        border: 1px solid #334155;
        border-radius: 12px;
        resize: vertical;
        line-height: 1.5;
      }
      .result-panel {
        margin-top: 12px;
        padding: 12px;
        border-radius: 12px;
      }
      .result-success {
        background: #f0fdf4;
        border: 1px solid #86efac;
      }
      .result-error {
        background: #fef2f2;
        border: 1px solid #fca5a5;
      }
      .result-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
      }
      .execution-time {
        margin-left: auto;
        color: #64748b;
        font-size: 12px;
      }
      .result-output,
      .result-error {
        margin: 0;
        padding: 8px;
        font-family: monospace;
        font-size: 13px;
        white-space: pre-wrap;
        word-break: break-word;
      }
      .result-output {
        color: #166534;
      }
      .result-error {
        color: #dc2626;
      }
      .history-section {
        margin-top: 16px;
      }
      .history-section h4 {
        margin-bottom: 8px;
        color: #475569;
      }
    `,
  ],
})
export class OfflineCodeExecutionComponent implements OnInit {
  code = '';
  selectedLanguage: CodeLanguage = 'python';
  lastResult: CodeExecutionResult | null = null;

  constructor(
    public executionService: OfflineCodeExecutionService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    // 设置默认代码
    this.code =
      this.selectedLanguage === 'python'
        ? '# 在此输入 Python 代码\nprint("Hello, MatuX!")\n'
        : '// 在此输入 JavaScript 代码\nconsole.log("Hello, MatuX!");\n';
  }

  async runCode(): Promise<void> {
    if (!this.code.trim()) {
      this.snackBar.open('请输入代码', '关闭', { duration: 2000 });
      return;
    }

    this.lastResult = await this.executionService.executeCode({
      code: this.code,
      language: this.selectedLanguage,
    });
  }

  clearCode(): void {
    this.code = '';
    this.lastResult = null;
  }

  loadFromHistory(entry: { code: string; language: CodeLanguage }): void {
    this.code = entry.code;
    this.selectedLanguage = entry.language;
  }
}
