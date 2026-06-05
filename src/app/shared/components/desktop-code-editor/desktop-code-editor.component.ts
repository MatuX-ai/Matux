/**
 * 桌面端代码编辑器组件
 *
 * 基于 Monaco Editor 封装，支持：
 * - Ctrl+S / Ctrl+Shift+S 保存文件
 * - Ctrl+Enter / F5 运行代码
 * - 运行结果面板
 * - 多语言语法高亮
 * - 桌面端全屏适配
 */
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MonacoEditorModule } from 'ngx-monaco-editor-v2';

/** 代码运行结果 */
export interface CodeRunResult {
  success: boolean;
  output: string;
  error?: string;
  executionTime?: number;
}

/** 编辑器语言 */
export type EditorLanguage = 'python' | 'javascript' | 'typescript' | 'cpp' | 'java' | 'go' | 'rust' | 'html' | 'css' | 'json' | 'markdown';

/** 编辑器配置 */
export interface DesktopEditorConfig {
  code?: string;
  language: EditorLanguage;
  readOnly?: boolean;
  theme?: 'vs' | 'vs-dark' | 'hc-black';
  fontSize?: number;
  minimap?: boolean;
  wordWrap?: 'on' | 'off';
  lineNumbers?: 'on' | 'off' | 'relative';
  showRunButton?: boolean;
  showSaveButton?: boolean;
  placeholder?: string;
}

@Component({
  selector: 'app-desktop-code-editor',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatTooltipModule,
    MonacoEditorModule,
  ],
  template: `
    <div class="desktop-editor" [class.fullscreen]="isFullscreen">
      <!-- 工具栏 -->
      <div class="editor-toolbar" *ngIf="config.showSaveButton || config.showRunButton">
        <div class="toolbar-left">
          <span class="language-badge">{{ languageLabel }}</span>
        </div>
        <div class="toolbar-right">
          <button
            mat-icon-button
            matTooltip="保存 (Ctrl+S)"
            *ngIf="config.showSaveButton"
            [disabled]="isRunning"
            (click)="onSave()"
          >
            <mat-icon>save</mat-icon>
          </button>
          <button
            mat-icon-button
            matTooltip="运行 (Ctrl+Enter)"
            *ngIf="config.showRunButton"
            color="primary"
            [disabled]="isRunning"
            (click)="onRun()"
          >
            <mat-icon *ngIf="!isRunning">play_arrow</mat-icon>
            <mat-progress-spinner *ngIf="isRunning" diameter="20" mode="indeterminate">
            </mat-progress-spinner>
          </button>
          <button
            mat-icon-button
            matTooltip="全屏"
            (click)="toggleFullscreen()"
          >
            <mat-icon>{{ isFullscreen ? 'fullscreen_exit' : 'fullscreen' }}</mat-icon>
          </button>
        </div>
      </div>

      <!-- Monaco 编辑器 -->
      <div class="editor-container">
        <ngx-monaco-editor
          class="monaco-editor"
          [options]="editorOptions"
          [(ngModel)]="code"
          (onInit)="onEditorInit()"
        >
        </ngx-monaco-editor>
      </div>

      <!-- 运行结果面板 -->
      <div class="output-panel" *ngIf="showOutput">
        <div class="output-header">
          <span class="output-title">
            <mat-icon [class.success]="lastResult?.success" [class.error]="!lastResult?.success">
              {{ lastResult?.success ? 'check_circle' : 'error' }}
            </mat-icon>
            运行结果
            <span class="exec-time" *ngIf="lastResult?.executionTime != null">
              ({{ lastResult?.executionTime }}ms)
            </span>
          </span>
          <button mat-icon-button matTooltip="关闭" (click)="showOutput = false">
            <mat-icon>close</mat-icon>
          </button>
        </div>
        <pre class="output-content" [class.error-output]="!lastResult?.success">{{
          lastResult?.output || ''
        }}</pre>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      height: 100%;
    }

    .desktop-editor {
      display: flex;
      flex-direction: column;
      height: 100%;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      overflow: hidden;
      background: #1e1e1e;

      &.fullscreen {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 9999;
        border-radius: 0;
      }
    }

    /* 工具栏 */
    .editor-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 4px 12px;
      background: #2d2d2d;
      border-bottom: 1px solid #404040;
      min-height: 40px;
    }

    .toolbar-left {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .language-badge {
      font-size: 12px;
      color: #ccc;
      background: #404040;
      padding: 2px 10px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .toolbar-right {
      display: flex;
      align-items: center;
      gap: 4px;

      button {
        color: #ccc;

        &:hover {
          color: #fff;
        }

        &[color="primary"] {
          color: #10b981;
        }
      }
    }

    /* 编辑器容器 */
    .editor-container {
      flex: 1;
      min-height: 0;
    }

    .monaco-editor {
      height: 100%;
      width: 100%;
    }

    /* 输出面板 */
    .output-panel {
      border-top: 1px solid #404040;
      background: #1a1a1a;
      max-height: 40%;
      display: flex;
      flex-direction: column;
    }

    .output-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 6px 12px;
      background: #252525;
      border-bottom: 1px solid #333;

      button {
        color: #888;
      }
    }

    .output-title {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      color: #ccc;

      mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;

        &.success { color: #10b981; }
        &.error { color: #ef4444; }
      }

      .exec-time {
        font-size: 11px;
        color: #888;
      }
    }

    .output-content {
      flex: 1;
      margin: 0;
      padding: 12px;
      font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
      font-size: 13px;
      color: #d4d4d4;
      white-space: pre-wrap;
      overflow: auto;
      line-height: 1.5;

      &.error-output {
        color: #f48771;
      }
    }

    /* 响应式 */
    @media (max-width: 768px) {
      .editor-toolbar {
        padding: 4px 8px;
      }

      .output-panel {
        max-height: 50%;
      }
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DesktopCodeEditorComponent {
  /** 编辑器配置 */
  @Input() config: DesktopEditorConfig = {
    language: 'python',
    theme: 'vs-dark',
    fontSize: 14,
    minimap: false,
    showRunButton: true,
    showSaveButton: true,
  };

  /** 代码内容（双向绑定） */
  @Input() code = '';

  /** 保存事件 */
  @Output() save = new EventEmitter<{ code: string; language: EditorLanguage }>();

  /** 运行事件 */
  @Output() run = new EventEmitter<{ code: string; language: EditorLanguage }>();

  /** 当前运行结果 */
  @Input() lastResult: CodeRunResult | null = null;

  /** 是否显示输出面板 */
  @Input() showOutput = false;

  /** 是否正在运行 */
  @Input() isRunning = false;

  /** 是否全屏 */
  isFullscreen = false;

  /** Monaco 编辑器选项 */
  get editorOptions(): Record<string, unknown> {
    return {
      theme: this.config.theme || 'vs-dark',
      language: this.config.language,
      fontSize: this.config.fontSize ?? 14,
      minimap: { enabled: this.config.minimap ?? false },
      automaticLayout: true,
      readOnly: this.config.readOnly ?? false,
      wordWrap: this.config.wordWrap || 'off',
      lineNumbers: this.config.lineNumbers || 'on',
      scrollBeyondLastLine: false,
      tabSize: 4,
      insertSpaces: true,
      bracketPairColorization: { enabled: true },
      padding: { top: 8 },
      smoothScrolling: true,
      cursorBlinking: 'smooth',
      cursorSmoothCaretAnimation: 'on',
      renderWhitespace: 'selection',
      suggest: { showWords: true, showSnippets: true },
      quickSuggestions: true,
      placeholder: this.config.placeholder || '',
    };
  }

  /** 语言标签映射 */
  private languageLabels: Record<string, string> = {
    python: 'Python',
    javascript: 'JavaScript',
    typescript: 'TypeScript',
    cpp: 'C++',
    java: 'Java',
    go: 'Go',
    rust: 'Rust',
    html: 'HTML',
    css: 'CSS',
    json: 'JSON',
    markdown: 'Markdown',
  };

  get languageLabel(): string {
    return this.languageLabels[this.config.language] || this.config.language;
  }

  constructor(private snackBar: MatSnackBar) {}

  /** 编辑器初始化完成 */
  onEditorInit(): void {
    // 注册全局快捷键（Monaco 内部处理）
    this.registerKeyboardShortcuts();
  }

  /** 注册键盘快捷键 */
  private registerKeyboardShortcuts(): void {
    document.addEventListener('keydown', this.handleGlobalKeydown);
  }

  /** 全局键盘事件处理 */
  private handleGlobalKeydown = (event: KeyboardEvent): void => {
    const isCtrlOrCmd = event.ctrlKey || event.metaKey;

    // Ctrl+S / Ctrl+Shift+S → 保存
    if (isCtrlOrCmd && event.key === 's') {
      event.preventDefault();
      this.onSave();
      return;
    }

    // Ctrl+Enter → 运行
    if (isCtrlOrCmd && event.key === 'Enter') {
      event.preventDefault();
      this.onRun();
      return;
    }

    // F5 → 运行（桌面端习惯）
    if (event.key === 'F5') {
      event.preventDefault();
      this.onRun();
      return;
    }

    // F11 → 全屏切换
    if (event.key === 'F11') {
      event.preventDefault();
      this.toggleFullscreen();
      return;
    }
  };

  /** 保存 */
  onSave(): void {
    this.save.emit({ code: this.code, language: this.config.language });
    this.snackBar.open('已保存', '关闭', { duration: 2000 });
  }

  /** 运行代码 */
  onRun(): void {
    if (this.isRunning) return;
    this.showOutput = true;
    this.run.emit({ code: this.code, language: this.config.language });
  }

  /** 切换全屏 */
  toggleFullscreen(): void {
    this.isFullscreen = !this.isFullscreen;
  }

  /** 清理快捷键监听 */
  ngOnDestroy(): void {
    document.removeEventListener('keydown', this.handleGlobalKeydown);
  }
}
