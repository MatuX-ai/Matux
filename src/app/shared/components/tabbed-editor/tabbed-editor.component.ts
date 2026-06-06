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
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnDestroy,
  Output,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MonacoEditorModule } from 'ngx-monaco-editor-v2';

/** Electron API 桥接接口 */
interface ElectronFileResult {
  success: boolean;
  content?: string;
  filePath?: string;
  error?: string;
}

interface ElectronDialogResult {
  success: boolean;
  filePath?: string;
  error?: string;
}

interface ElectronAPI {
  showSaveDialog: (opts?: Record<string, unknown>) => Promise<ElectronDialogResult>;
  showOpenDialog: () => Promise<ElectronDialogResult & { filePaths?: string[] }>;
  readFile: (filePath: string) => Promise<ElectronFileResult>;
  writeFile: (filePath: string, content: string) => Promise<ElectronFileResult>;
  getFileInfo: (filePath: string) => Promise<{ success: boolean; size?: number; error?: string }>;
}

function getElectronAPI(): ElectronAPI | null {
  const api = (window as unknown as { electronAPI?: ElectronAPI }).electronAPI;
  return api ?? null;
}

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

  /** 通过 Electron IPC 打开文件后发出的事件 */
  @Output() fileOpened = new EventEmitter<EditorTab>();

  /** 通过 Electron IPC 保存文件后发出的事件 */
  @Output() fileSaved = new EventEmitter<{ tabId: string; filePath: string }>();

  /** 主题切换事件 */
  @Output() themeChange = new EventEmitter<'vs-dark' | 'vs' | 'hc-black'>();

  /** 是否显示输出面板 */
  showOutput = false;

  /** 当前编辑器主题 */
  @Input() editorTheme: 'vs-dark' | 'vs' | 'hc-black' = 'vs-dark';

  /** 键盘快捷键监听器引用 */
  private keydownHandler: ((e: KeyboardEvent) => void) | null = null;

  /** Electron API 实例（仅在 Electron 环境可用） */
  private readonly electronApi = getElectronAPI();

  /** 是否运行在 Electron 环境 */
  get isElectron(): boolean {
    return this.electronApi !== null;
  }

  constructor(private cdr: ChangeDetectorRef) {
    this.registerKeyboardShortcuts();
  }

  /** 获取 Monaco 编辑器选项 */
  getEditorOptions(language: string): Record<string, unknown> {
    return {
      theme: this.editorTheme,
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
    // 优先通过 Electron IPC 保存文件
    if (this.electronApi && tabId) {
      void this.saveActiveTabToFile(tabId);
      return;
    }
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

  /** 通过 Electron IPC 将当前标签页保存到本地文件 */
  private async saveActiveTabToFile(tabId: string): Promise<void> {
    const api = this.electronApi;
    if (!api) return;

    const tab = this.tabs.find((t) => t.id === tabId);
    if (!tab) return;

    try {
      // 已有文件路径则直接保存，否则弹出保存对话框
      if (tab.filePath) {
        const result = await api.writeFile(tab.filePath, tab.content);
        if (result.success) {
          this.fileSaved.emit({ tabId, filePath: tab.filePath });
        }
      } else {
        const ext = this.getFileExtension(tab.language);
        const dialogResult = await api.showSaveDialog({
          title: '保存文件',
          defaultPath: `${tab.title}${ext}`,
          filters: [
            {
              name: '代码文件',
              extensions: ['py', 'js', 'ts', 'cpp', 'java', 'html', 'css', 'json'],
            },
            { name: '所有文件', extensions: ['*'] },
          ],
        });

        if (dialogResult.success && dialogResult.filePath) {
          await api.writeFile(dialogResult.filePath, tab.content);
          this.fileSaved.emit({ tabId, filePath: dialogResult.filePath });
        }
      }
    } catch (error) {
      console.error('[Editor] 保存文件失败:', error);
    }
  }

  /** 通过 Electron IPC 从本地打开文件 */
  async openFileFromDisk(): Promise<void> {
    const api = this.electronApi;
    if (!api) {
      this.openFileRequest.emit();
      return;
    }

    try {
      const dialogResult = await api.showOpenDialog();
      if (!dialogResult.success || !dialogResult.filePath) return;

      const fileResult = await api.readFile(dialogResult.filePath);
      if (!fileResult.success || fileResult.content === undefined) return;

      const fileName = dialogResult.filePath.split(/[/\\]/).pop() ?? 'untitled';
      const language = this.guessLanguage(fileName);

      const tab: EditorTab = {
        id: `file_${Date.now()}`,
        title: fileName,
        filePath: dialogResult.filePath,
        content: fileResult.content,
        language,
        isDirty: false,
      };

      this.fileOpened.emit(tab);
    } catch (error) {
      console.error('[Editor] 打开文件失败:', error);
    }
  }

  /** 根据文件名猜测编程语言 */
  private guessLanguage(fileName: string): string {
    const extMap: Record<string, string> = {
      py: 'python',
      js: 'javascript',
      ts: 'typescript',
      cpp: 'cpp',
      java: 'java',
      html: 'html',
      css: 'css',
      json: 'json',
      md: 'markdown',
    };
    const ext = fileName.split('.').pop()?.toLowerCase() ?? '';
    return extMap[ext] ?? 'plaintext';
  }

  /** 根据语言获取默认文件扩展名 */
  private getFileExtension(language: string): string {
    const extMap: Record<string, string> = {
      python: '.py',
      javascript: '.js',
      typescript: '.ts',
      cpp: '.cpp',
      java: '.java',
      html: '.html',
      css: '.css',
      json: '.json',
      markdown: '.md',
    };
    return extMap[language] ?? '.txt';
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
    return labels[lang] ?? lang;
  }

  /** 注册桌面端键盘快捷键 */
  // eslint-disable-next-line complexity
  private registerKeyboardShortcuts(): void {
    // eslint-disable-next-line complexity
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

      // Ctrl+O → 打开文件（Electron 优先）
      if (isCtrlOrCmd && event.key === 'o') {
        event.preventDefault();
        void this.openFileFromDisk();
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

  toggleTheme(): void {
    const themes: Array<'vs-dark' | 'vs' | 'hc-black'> = ['vs-dark', 'vs', 'hc-black'];
    const idx = themes.indexOf(this.editorTheme);
    this.editorTheme = themes[(idx + 1) % themes.length];
    this.themeChange.emit(this.editorTheme);
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
