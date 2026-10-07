/**
 * Blockly 工作区组件
 *
 * 提供可视化的 Blockly 积木编程工作区
 * 集成真实 Blockly 库，支持拖拽、代码生成、主题切换
 *
 * 基于 PRD F-05: Blockly 可视化编程
 */

/* eslint-disable no-console */
import { CommonModule } from '@angular/common';
import {
  AfterViewInit,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnDestroy,
  Output,
  ViewChild,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';

import { BlocklyService, TargetLanguage } from '../../../core/services/blockly.service';

@Component({
  selector: 'app-blockly-workspace',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatSelectModule,
    MatTooltipModule,
    MatFormFieldModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './blockly-workspace.component.html',
  styleUrls: ['./blockly-workspace.component.scss'],
})
export class BlocklyWorkspaceComponent implements AfterViewInit, OnDestroy {
  @ViewChild('blocklyContainer') blocklyContainer!: ElementRef<HTMLDivElement>;

  @Input() showCodePreview = true;
  @Input() readOnly = false;
  @Input() initialXml?: string;

  @Output() codeChanged = new EventEmitter<string>();
  @Output() workspaceChanged = new EventEmitter<unknown>();

  // 状态
  isLoading = true;
  error: string | null = null;
  blockCount = 0;
  isEmpty = true;
  currentCode = '# 等待生成代码';

  // 语言选项
  selectedLanguage: TargetLanguage = TargetLanguage.PYTHON;
  languages = [
    { value: TargetLanguage.PYTHON, label: 'Python' },
    { value: TargetLanguage.JAVASCRIPT, label: 'JavaScript' },
  ];

  // 主题选项
  theme = 'classic';
  themes = [
    { value: 'classic', label: '经典' },
    { value: 'dark', label: '深色' },
    { value: 'modern', label: '现代' },
  ];

  // 使用的块类型
  blockTypes: string[] = [];

  // 回调取消订阅函数
  private unsubscribers: (() => void)[] = [];

  constructor(private blocklyService: BlocklyService) {}

  ngAfterViewInit(): void {
    void this.initBlockly();
  }

  ngOnDestroy(): void {
    for (const unsub of this.unsubscribers) unsub();
    this.unsubscribers = [];
    this.blocklyService.dispose();
  }

  /**
   * 初始化 Blockly 工作区
   */
  async initBlockly(): Promise<void> {
    this.isLoading = true;
    this.error = null;

    try {
      if (!this.blocklyContainer?.nativeElement) {
        throw new Error('Blockly 容器未就绪');
      }

      await this.blocklyService.initWorkspace(this.blocklyContainer.nativeElement, {
        language: this.selectedLanguage,
        readOnly: this.readOnly,
      });

      // 加载初始 XML
      if (this.initialXml) {
        this.blocklyService.importXml(this.initialXml);
      }

      // 监听代码变更
      this.unsubscribers.push(
        this.blocklyService.onCodeChange((code, lang) => {
          this.currentCode = code;
          this.selectedLanguage = lang;
          this.codeChanged.emit(code);
          this.updateBlockTypes();
        })
      );

      // 监听积木块计数
      this.unsubscribers.push(
        this.blocklyService.onBlockCountChange((count) => {
          this.blockCount = count;
          this.isEmpty = count === 0;
        })
      );

      // 初始生成代码
      this.currentCode = this.blocklyService.generateCode();
      this.blockCount = this.blocklyService.getBlockCount();
      this.isEmpty = this.blockCount === 0;

      this.isLoading = false;
    } catch (err) {
      this.error = `Blockly 加载失败: ${err instanceof Error ? err.message : String(err)}`;
      this.isLoading = false;
      console.error('[BlocklyWorkspace] 初始化失败:', err);
    }
  }

  // ==================== 工具栏操作 ====================

  undo(): void {
    this.blocklyService.undo();
  }

  redo(): void {
    this.blocklyService.redo();
  }

  clearWorkspace(): void {
    this.blocklyService.clear();
    this.currentCode = '';
    this.blockCount = 0;
    this.isEmpty = true;
    this.blockTypes = [];
  }

  // ==================== 主题/语言切换 ====================

  onThemeChange(value: string): void {
    this.theme = value;
    // Blockly 主题切换需要重新注入（简化处理：仅更新 CSS 变量）
    const container = this.blocklyContainer?.nativeElement;
    if (container) {
      container.classList.remove('theme-classic', 'theme-dark', 'theme-modern');
      container.classList.add(`theme-${value}`);
    }
  }

  onLanguageChange(value: TargetLanguage): void {
    this.selectedLanguage = value;
    this.blocklyService.setLanguage(value);
    this.currentCode = this.blocklyService.generateCode(value);
    this.codeChanged.emit(this.currentCode);
  }

  // ==================== 代码操作 ====================

  copyCode(): void {
    if (!this.currentCode) return;
    navigator.clipboard.writeText(this.currentCode).then(
      () => console.log('[BlocklyWorkspace] 代码已复制到剪贴板'),
      (err) => console.error('[BlocklyWorkspace] 复制失败:', err)
    );
  }

  // ==================== 内部方法 ====================

  trackByValue(_: number, item: { value: string }): string {
    return item.value;
  }

  trackByIndex(index: number): number {
    return index;
  }

  private updateBlockTypes(): void {
    this.blockCount = this.blocklyService.getBlockCount();
    this.isEmpty = this.blockCount === 0;
    // 提取当前工作区中使用的所有块类型
    try {
      const xml = this.blocklyService.exportXml();
      const matches = xml.match(/type="([^"]+)"/g) ?? [];
      const types = new Set<string>();
      for (const m of matches) {
        const match = m.match(/type="([^"]+)"/);
        if (match) types.add(match[1]);
      }
      this.blockTypes = Array.from(types);
    } catch {
      this.blockTypes = [];
    }
  }
}
