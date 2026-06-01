/**
 * 多标签页编辑器组件
 *
 * 桌面端特性：支持多个文件标签页同时编辑
 * - 基于 Monaco Editor 的多标签页编辑
 * - 标签页切换 (Ctrl+Tab / Ctrl+Shift+Tab)
 * - 标签页关闭 (Ctrl+W)
 * - 新建标签页 (Ctrl+N)
 * - 文件保存 (Ctrl+S / Ctrl+Shift+S)
 * - 运行代码 (Ctrl+Enter / F5)
 */
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnDestroy,
  Output,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MonacoEditorModule } from 'ngx-monaco-editor-v2';

/** 编辑器标签页 */
export interface EditorTab {
  /** 唯一标识 */
  id: string;
  /** 显示名称 */
  title: string;
  /** 文件路径（本地文件才有） */
  filePath?: string;
  /** 文件内容 */
  content: string;
  /** 编程语言 */
  language: string;
  /** 是否已修改（未保存） */
  isDirty: boolean;
  /** 图标名称 */
  icon?: string;
}

/** 代码运行结果 */
export interface TabRunResult {
  tabId: string;
  success: boolean;
  output: string;
  error?: string;
  executionTime?: number;
}

@Component({
  selector: 'app-tabbed-editor',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatIconModule,
    MatMenuModule,
    MatTooltipModule,
    MonacoEditorModule,
  ],
  templateUrl: './tabbed-editor.component.html',
  styleUrls: ['./tabbed-editor.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TabbedEditorComponent implements OnDestroy {
  /** 标签页列表 */
  @Input() tabs: EditorTab[] = [];

  /** 当前激活的标签页 ID */
  @Input() activeTabId: string | null = null;

  /** 是否正在运行代码 */
  @Input() isRunning = false;

  /** 运行结果 */
  @Input() lastRunResult: TabRunResult | null = null;

  /** 标签页切换事件 */
  @Output() tabChange = new EventEmitter<string>();

  /** 标签页关闭事件 */
  @Output() tabClose = new EventEmitter<string>();

  /** 内容变更事件 */
  @Output() contentChange = new EventEmitter<{ tabId: string; content: string }>();

  /** 保存请求事件 */
  @Output() saveRequest = new EventEmitter<string>();

  /** 运行代码事件 */
  @Output() runRequest = new EventEmitter<string>();

  /** 新建标签页请求事件 */
  @Output() newTabRequest = new EventEmitter<void>();

  /** 打开文件请求事件 */
  @Output() openFileRequest = new EventEmitter<void>();

  /** 是否显示输出面板 */
  showOutput = false;

  /** 键盘快捷键监听器引用 */
  private keydownHandler: ((e: KeyboardEvent) => void) | null = null;

  constructor(private cdr: ChangeDetectorRef) {
    this.registerKeyboardShortcuts();
  }

  /** 获取 Monaco 编辑器选项 */
  getEditorOptions(language: string): Record<string, unknown> {
    return {
      theme: 'vs-dark',
      language,
      fontSize: 14,
      minimap: { enabled: false },
      automaticLayout: true,
      scrollBeyondLastLine: false,
      tabSize: 4,
      insertSpaces: true,
      bracketPairColorization: { enabled: true },
      padding: { top: 8 },
      smoothScrolling: true,
      cursorBlinking: 'smooth',
      renderWhitespace: 'selection',
      suggest: { showWords: true, showSnippets: true },
      quickSuggestions: true,
    };
  }

  /** 切换到指定标签页 */
  selectTab(tabId: string): void {
    if (tabId !== this.activeTabId) {
      this.activeTabId = tabId;
      this.tabChange.emit(tabId);
    }
  }

  /** 关闭标签页 */
  closeTab(tabId: string, event: MouseEvent): void {
    event.stopPropagation();
    this.tabClose.emit(tabId);
  }

  /** 处理编辑器内容变更 */
  onContentChange(tabId: string, content: string): void {
    this.contentChange.emit({ tabId, content });
  }

  /** 请求保存当前标签页 */
  requestSave(tabId: string): void {
    this.saveRequest.emit(tabId);
  }

  /** 运行当前标签页的代码 */
  runActiveTab(): void {
    if (this.activeTabId) {
      this.showOutput = true;
      this.runRequest.emit(this.activeTabId);
    }
  }

  /** 获取当前激活的标签页 */
  getActiveTab(): EditorTab | undefined {
    return this.tabs.find((t) => t.id === this.activeTabId);
  }

  /** 获取语言标签映射 */
  getLanguageLabel(lang: string): string {
    const labels: Record<string, string> = {
      python: 'Python',
      javascript: 'JavaScript',
      typescript: 'TypeScript',
      cpp: 'C++',
      java: 'Java',
      html: 'HTML',
      css: 'CSS',
      json: 'JSON',
      markdown: 'Markdown',
    };
    return labels[lang] || lang;
  }

  /** 注册桌面端键盘快捷键 */
  private registerKeyboardShortcuts(): void {
    this.keydownHandler = (event: KeyboardEvent) => {
      const isCtrlOrCmd = event.ctrlKey || event.metaKey;

      // Ctrl+S / Ctrl+Shift+S → 保存
      if (isCtrlOrCmd && event.key === 's') {
        event.preventDefault();
        if (this.activeTabId) {
          this.requestSave(this.activeTabId);
        }
        return;
      }

      // Ctrl+W → 关闭当前标签页
      if (isCtrlOrCmd && event.key === 'w') {
        event.preventDefault();
        if (this.activeTabId) {
          this.tabClose.emit(this.activeTabId);
        }
        return;
      }

      // Ctrl+N → 新建标签页
      if (isCtrlOrCmd && event.key === 'n') {
        event.preventDefault();
        this.newTabRequest.emit();
        return;
      }

      // Ctrl+O → 打开文件
      if (isCtrlOrCmd && event.key === 'o') {
        event.preventDefault();
        this.openFileRequest.emit();
        return;
      }

      // Ctrl+Enter → 运行代码
      if (isCtrlOrCmd && event.key === 'Enter') {
        event.preventDefault();
        this.runActiveTab();
        return;
      }

      // F5 → 运行代码
      if (event.key === 'F5') {
        event.preventDefault();
        this.runActiveTab();
        return;
      }

      // Ctrl+Tab → 下一个标签页
      if (isCtrlOrCmd && event.key === 'Tab' && !event.shiftKey) {
        event.preventDefault();
        this.switchToNextTab();
        return;
      }

      // Ctrl+Shift+Tab → 上一个标签页
      if (isCtrlOrCmd && event.key === 'Tab' && event.shiftKey) {
        event.preventDefault();
        this.switchToPrevTab();
        return;
      }
    };

    document.addEventListener('keydown', this.keydownHandler);
  }

  /** 切换到下一个标签页 */
  private switchToNextTab(): void {
    if (this.tabs.length <= 1) return;
    const idx = this.tabs.findIndex((t) => t.id === this.activeTabId);
    const nextIdx = (idx + 1) % this.tabs.length;
    this.selectTab(this.tabs[nextIdx].id);
    this.cdr.markForCheck();
  }

  /** 切换到上一个标签页 */
  private switchToPrevTab(): void {
    if (this.tabs.length <= 1) return;
    const idx = this.tabs.findIndex((t) => t.id === this.activeTabId);
    const prevIdx = (idx - 1 + this.tabs.length) % this.tabs.length;
    this.selectTab(this.tabs[prevIdx].id);
    this.cdr.markForCheck();
  }

  ngOnDestroy(): void {
    if (this.keydownHandler) {
      document.removeEventListener('keydown', this.keydownHandler);
      this.keydownHandler = null;
    }
  }
}