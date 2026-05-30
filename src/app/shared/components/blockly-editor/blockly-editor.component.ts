/**
 * Blockly 可视化编程编辑器
 *
 * 桌面端适配：
 * - 大屏拖拽优化（增大 Blockly 画布尺寸）
 * - Python/JavaScript 代码对照视图（左侧 Blockly / 右侧代码）
 * - 键盘快捷键支持（Ctrl+Enter 运行、Ctrl+Z 撤销）
 * - 实时代码生成
 */
import * as Blockly from 'blockly';
import { pythonGenerator } from 'blockly/python';
import { javascriptGenerator } from 'blockly/javascript';

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  Output,
  ViewChild,
  AfterViewInit,
  OnDestroy,
  ChangeDetectorRef,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

/** 视图模式 */
type ViewMode = 'blockly-only' | 'split' | 'code-only';

/** 生成的代码语言 */
type GeneratedLanguage = 'python' | 'javascript';

/** Blockly 网格配置 */
export interface BlocklyGridOptions {
  spacing: number;
  length: number;
  colour: string;
  snap: boolean;
}

/** Blockly 缩放配置 */
export interface BlocklyZoomOptions {
  controls: boolean;
  wheel: boolean;
  startScale: number;
  maxScale: number;
  minScale: number;
  scaleSpeed: number;
}

/** Blockly 工作区配置 */
export interface BlocklyWorkspaceConfig {
  /** 网格配置，false 则禁用 */
  grid?: BlocklyGridOptions | false;
  /** 是否启用垃圾桶 */
  trashcan?: boolean;
  /** 缩放配置，false 则禁用 */
  zoom?: BlocklyZoomOptions | false;
  /** 是否启用撤销 */
  undo?: boolean;
  /** 主题 */
  theme?: string;
  /** 初始 XML 工作区定义 */
  initialXml?: string;
}

/** 默认工具箱定义（适合编程入门的积木分类） */
const DEFAULT_TOOLBOX: Blockly.utils.toolbox.ToolboxDefinition = {
  kind: 'categoryToolbox',
  contents: [
    {
      kind: 'category',
      name: '逻辑',
      colour: '#5b80a5',
      contents: [
        { kind: 'block', type: 'controls_if' },
        { kind: 'block', type: 'logic_compare' },
        { kind: 'block', type: 'logic_operation' },
        { kind: 'block', type: 'logic_negate' },
        { kind: 'block', type: 'logic_boolean' },
        { kind: 'block', type: 'logic_null' },
        { kind: 'block', type: 'logic_ternary' },
      ],
    },
    {
      kind: 'category',
      name: '循环',
      colour: '#5ba55b',
      contents: [
        { kind: 'block', type: 'controls_repeat_ext' },
        { kind: 'block', type: 'controls_whileUntil' },
        { kind: 'block', type: 'controls_for' },
        { kind: 'block', type: 'controls_forEach' },
        { kind: 'block', type: 'controls_flow_statements' },
      ],
    },
    {
      kind: 'category',
      name: '数学',
      colour: '#5b67a5',
      contents: [
        { kind: 'block', type: 'math_number' },
        { kind: 'block', type: 'math_arithmetic' },
        { kind: 'block', type: 'math_single' },
        { kind: 'block', type: 'math_trig' },
        { kind: 'block', type: 'math_constant' },
        { kind: 'block', type: 'math_number_property' },
        { kind: 'block', type: 'math_round' },
        { kind: 'block', type: 'math_modulo' },
        { kind: 'block', type: 'math_constrain' },
        { kind: 'block', type: 'math_random_int' },
        { kind: 'block', type: 'math_random_float' },
      ],
    },
    {
      kind: 'category',
      name: '文本',
      colour: '#5ba58c',
      contents: [
        { kind: 'block', type: 'text' },
        { kind: 'block', type: 'text_join' },
        { kind: 'block', type: 'text_append' },
        { kind: 'block', type: 'text_length' },
        { kind: 'block', type: 'text_isEmpty' },
        { kind: 'block', type: 'text_indexOf' },
        { kind: 'block', type: 'text_charAt' },
        { kind: 'block', type: 'text_changeCase' },
        { kind: 'block', type: 'text_trim' },
        { kind: 'block', type: 'text_print' },
        { kind: 'block', type: 'text_prompt_ext' },
      ],
    },
    {
      kind: 'category',
      name: '列表',
      colour: '#745ba5',
      contents: [
        { kind: 'block', type: 'lists_create_with' },
        { kind: 'block', type: 'lists_create_with' },
        { kind: 'block', type: 'lists_repeat' },
        { kind: 'block', type: 'lists_length' },
        { kind: 'block', type: 'lists_isEmpty' },
        { kind: 'block', type: 'lists_indexOf' },
        { kind: 'block', type: 'lists_getIndex' },
        { kind: 'block', type: 'lists_setIndex' },
      ],
    },
    {
      kind: 'category',
      name: '颜色',
      colour: '#a5745b',
      contents: [
        { kind: 'block', type: 'colour_picker' },
        { kind: 'block', type: 'colour_random' },
        { kind: 'block', type: 'colour_rgb' },
        { kind: 'block', type: 'colour_blend' },
      ],
    },
    {
      kind: 'category',
      name: '变量',
      colour: '#a55b80',
      custom: 'VARIABLE',
    },
    {
      kind: 'category',
      name: '函数',
      colour: '#995ba5',
      custom: 'PROCEDURE',
    },
  ],
};

@Component({
  selector: 'app-blockly-editor',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatButtonToggleModule,
    MatIconModule,
    MatSnackBarModule,
    MatTooltipModule,
  ],
  template: `
    <div class="blockly-editor" [class.split-view]="viewMode === 'split'">
      <!-- 工具栏 -->
      <div class="blockly-toolbar">
        <div class="toolbar-left">
          <span class="toolbar-title">
            <mat-icon>extension</mat-icon>
            Blockly 可视化编程
          </span>
        </div>
        <div class="toolbar-center">
          <mat-button-toggle-group
            [value]="viewMode"
            (change)="onViewModeChange($event.value)"
            [hideSingleSelectionIndicator]="true"
          >
            <mat-button-toggle value="blockly-only" matTooltip="仅积木视图">
              <mat-icon>view_module</mat-icon>
            </mat-button-toggle>
            <mat-button-toggle value="split" matTooltip="积木+代码对照">
              <mat-icon>vertical_split</mat-icon>
            </mat-button-toggle>
            <mat-button-toggle value="code-only" matTooltip="仅代码视图">
              <mat-icon>code</mat-icon>
            </mat-button-toggle>
          </mat-button-toggle-group>
        </div>
        <div class="toolbar-right">
          <button mat-icon-button matTooltip="撤销 (Ctrl+Z)" (click)="undo()">
            <mat-icon>undo</mat-icon>
          </button>
          <button mat-icon-button matTooltip="重做 (Ctrl+Y)" (click)="redo()">
            <mat-icon>redo</mat-icon>
          </button>
          <button mat-icon-button matTooltip="运行程序 (Ctrl+Enter)" (click)="onRun()" color="primary">
            <mat-icon>play_arrow</mat-icon>
          </button>
          <button mat-icon-button matTooltip="放大" (click)="zoomIn()">
            <mat-icon>zoom_in</mat-icon>
          </button>
          <button mat-icon-button matTooltip="缩小" (click)="zoomOut()">
            <mat-icon>zoom_out</mat-icon>
          </button>
          <button mat-icon-button matTooltip="还原缩放" (click)="zoomReset()">
            <mat-icon>fit_screen</mat-icon>
          </button>
        </div>
      </div>

      <!-- 主体区域 -->
      <div class="blockly-body">
        <!-- Blockly 积木区 -->
        <div
          class="blockly-workspace"
          [class.hidden]="viewMode === 'code-only'"
          #blocklyContainer
        >
          <div class="blockly-placeholder" *ngIf="!blocklyReady">
            <mat-icon>hourglass_empty</mat-icon>
            <p>正在加载 Blockly 编辑器...</p>
          </div>
        </div>

        <!-- 代码对照区 -->
        <div
          class="code-panel"
          [class.hidden]="viewMode === 'blockly-only'"
          *ngIf="viewMode !== 'blockly-only'"
        >
          <div class="code-header">
            <span class="code-language">{{ generatedLanguage }}</span>
            <button mat-icon-button matTooltip="复制代码" (click)="copyGeneratedCode()">
              <mat-icon>content_copy</mat-icon>
            </button>
          </div>
          <pre class="generated-code"><code>{{ generatedCode || '// 拖拽积木块后，此处将显示生成的代码' }}</code></pre>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      height: 100%;
    }

    .blockly-editor {
      display: flex;
      flex-direction: column;
      height: 100%;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      overflow: hidden;
      background: #fff;
    }

    .blockly-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 6px 12px;
      background: #f5f5f5;
      border-bottom: 1px solid #e0e0e0;
      min-height: 44px;
      flex-wrap: wrap;
      gap: 8px;
    }

    .toolbar-left { display: flex; align-items: center; }

    .toolbar-title {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 14px;
      font-weight: 600;
      color: #333;
      mat-icon { color: #ff9800; }
    }

    .toolbar-center {
      display: flex;
      align-items: center;
      mat-button-toggle-group { --mat-standard-button-toggle-height: 32px; }
    }

    .toolbar-right { display: flex; align-items: center; gap: 4px; }

    .blockly-body { flex: 1; display: flex; min-height: 0; }

    .blockly-workspace {
      flex: 1;
      min-width: 0;
      position: relative;
      overflow: hidden;
      &.hidden { display: none; }
    }

    .blockly-placeholder {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: #999;
      mat-icon { font-size: 48px; width: 48px; height: 48px; margin-bottom: 8px; opacity: 0.5; }
    }

    .code-panel {
      width: 40%;
      min-width: 300px;
      display: flex;
      flex-direction: column;
      border-left: 1px solid #e0e0e0;
      background: #1e1e1e;
      &.hidden { display: none; }
    }

    .code-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 6px 12px;
      background: #2d2d2d;
      border-bottom: 1px solid #404040;
      button { color: #888; }
    }

    .code-language {
      font-size: 12px;
      color: #ccc;
      text-transform: uppercase;
      font-weight: 600;
    }

    .generated-code {
      flex: 1;
      margin: 0;
      padding: 16px;
      font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
      font-size: 13px;
      color: #d4d4d4;
      white-space: pre-wrap;
      overflow: auto;
      line-height: 1.6;
      background: #1e1e1e;
    }

    @media (max-width: 768px) {
      .blockly-toolbar { padding: 4px 8px; gap: 4px; }
      .code-panel { width: 100%; min-width: 0; max-height: 40%; }
      .blockly-body { flex-direction: column; }
    }

    @media (min-width: 1600px) {
      .code-panel { width: 35%; }
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BlocklyEditorComponent implements AfterViewInit, OnDestroy {
  @ViewChild('blocklyContainer', { static: true })
  blocklyContainer!: ElementRef<HTMLDivElement>;

  /** 目标生成语言 */
  @Input() generatedLanguage: GeneratedLanguage = 'python';

  /** Blockly 工作区配置 */
  @Input() workspaceConfig: BlocklyWorkspaceConfig = {};

  /** 自定义工具箱定义（覆盖默认） */
  @Input() toolbox: Blockly.utils.toolbox.ToolboxDefinition | null = null;

  /** 运行代码事件 */
  @Output() runCode = new EventEmitter<{ code: string; language: string }>();

  /** 代码变更事件 */
  @Output() codeChange = new EventEmitter<string>();

  /** Blockly 工作区实例是否就绪事件 */
  @Output() workspaceReady = new EventEmitter<Blockly.WorkspaceSvg>();

  /** 当前视图模式 */
  viewMode: ViewMode = 'split';

  /** Blockly 是否就绪 */
  blocklyReady = false;

  /** 当前生成的代码 */
  generatedCode = '';

  /** Blockly 工作区 */
  private workspace: Blockly.WorkspaceSvg | null = null;

  /** 键盘事件监听器引用 */
  private keydownHandler: ((e: KeyboardEvent) => void) | null = null;

  constructor(
    private cdr: ChangeDetectorRef,
    private snackBar: MatSnackBar,
  ) {}

  ngAfterViewInit(): void {
    this.initBlockly();
  }

  /** 初始化 Blockly 工作区 */
  private initBlockly(): void {
    if (!this.blocklyContainer?.nativeElement) return;

    const config = this.workspaceConfig;
    const toolboxDef = this.toolbox ?? DEFAULT_TOOLBOX;

    const gridOpts: BlocklyGridOptions = config.grid === false
      ? { spacing: 0, length: 0, colour: '', snap: false }
      : (config.grid ?? { spacing: 25, length: 3, colour: '#ccc', snap: true });

    const zoomOpts: BlocklyZoomOptions = config.zoom === false
      ? { controls: false, wheel: false, startScale: 1.0, maxScale: 3, minScale: 0.3, scaleSpeed: 1.2 }
      : (config.zoom ?? { controls: false, wheel: true, startScale: 1.0, maxScale: 3, minScale: 0.3, scaleSpeed: 1.2 });

    this.workspace = Blockly.inject(this.blocklyContainer.nativeElement, {
      toolbox: toolboxDef,
      grid: gridOpts,
      trashcan: config.trashcan ?? true,
      zoom: zoomOpts,
      move: {
        scrollbars: true,
        drag: true,
        wheel: true,
      },
      sounds: false,
      renderer: 'zelos',
    });

    // 监听工作区变化，实时生成代码
    this.workspace.addChangeListener((event: Blockly.Events.Abstract) => {
      // 过滤不需要触发代码生成的事件
      if (event.isUiEvent) return;

      // 防止移动事件频繁触发
      if (
        event.type === Blockly.Events.VIEWPORT_CHANGE ||
        event.type === Blockly.Events.TOOLBOX_ITEM_SELECT
      ) {
        return;
      }

      this.updateGeneratedCode();
    });

    // 如果有初始 XML，加载到工作区
    if (config.initialXml) {
      try {
        Blockly.Xml.domToWorkspace(
          Blockly.utils.xml.textToDom(config.initialXml),
          this.workspace,
        );
      } catch (e) {
        console.warn('[Blockly] 加载初始工作区 XML 失败:', e);
      }
    }

    this.blocklyReady = true;
    this.cdr.markForCheck();

    // 注册桌面端快捷键
    this.registerKeyboardShortcuts();

    // 通知外部工作区已就绪
    this.workspaceReady.emit(this.workspace);

    // 首次生成代码
    this.updateGeneratedCode();
  }

  /** 更新生成的代码 */
  private updateGeneratedCode(): void {
    if (!this.workspace) return;

    try {
      let code = '';
      if (this.generatedLanguage === 'python') {
        code = pythonGenerator.workspaceToCode(this.workspace);
      } else {
        code = javascriptGenerator.workspaceToCode(this.workspace);
      }
      this.generatedCode = code;
      this.codeChange.emit(code);
      this.cdr.markForCheck();
    } catch (e) {
      console.warn('[Blockly] 代码生成失败:', e);
    }
  }

  /** 注册桌面端键盘快捷键 */
  private registerKeyboardShortcuts(): void {
    this.keydownHandler = (event: KeyboardEvent) => {
      const isCtrlOrCmd = event.ctrlKey || event.metaKey;

      // Ctrl+Enter → 运行代码
      if (isCtrlOrCmd && event.key === 'Enter') {
        event.preventDefault();
        this.onRun();
        return;
      }

      // F5 → 运行代码
      if (event.key === 'F5') {
        event.preventDefault();
        this.onRun();
      }
    };

    document.addEventListener('keydown', this.keydownHandler);
  }

  /** 切换视图模式 */
  onViewModeChange(mode: ViewMode): void {
    this.viewMode = mode;
    this.cdr.markForCheck();

    // Blockly 在隐藏后显示需要重新调整尺寸
    if (mode !== 'code-only' && this.workspace) {
      setTimeout(() => {
        Blockly.svgResize(this.workspace!);
      }, 0);
    }
  }

  /** 运行代码 */
  onRun(): void {
    this.updateGeneratedCode();
    this.runCode.emit({
      code: this.generatedCode,
      language: this.generatedLanguage,
    });
  }

  /** 撤销 */
  undo(): void {
    this.workspace?.undo(false);
  }

  /** 重做 */
  redo(): void {
    this.workspace?.undo(true);
  }

  /** 放大 */
  zoomIn(): void {
    if (!this.workspace) return;
    const current = this.workspace.getScale();
    this.workspace.setScale(Math.min(current * 1.2, 3));
  }

  /** 缩小 */
  zoomOut(): void {
    if (!this.workspace) return;
    const current = this.workspace.getScale();
    this.workspace.setScale(Math.max(current / 1.2, 0.3));
  }

  /** 还原缩放 */
  zoomReset(): void {
    this.workspace?.setScale(1);
  }

  /** 复制生成的代码 */
  copyGeneratedCode(): void {
    if (!this.generatedCode) return;
    void navigator.clipboard.writeText(this.generatedCode).then(() => {
      this.snackBar.open('代码已复制到剪贴板', '关闭', { duration: 2000 });
    });
  }

  /** 获取当前工作区 XML */
  getWorkspaceXml(): string {
    if (!this.workspace) return '';
    const dom = Blockly.Xml.workspaceToDom(this.workspace);
    return Blockly.Xml.domToText(dom);
  }

  /** 加载工作区 XML */
  loadWorkspaceXml(xml: string): void {
    if (!this.workspace) return;
    try {
      Blockly.Xml.domToWorkspace(Blockly.utils.xml.textToDom(xml), this.workspace);
    } catch (e) {
      console.warn('[Blockly] 加载工作区 XML 失败:', e);
    }
  }

  /** 清空工作区 */
  clearWorkspace(): void {
    this.workspace?.clear();
  }

  /** 获取 Blockly 工作区实例 */
  getWorkspace(): Blockly.WorkspaceSvg | null {
    return this.workspace;
  }

  ngOnDestroy(): void {
    if (this.keydownHandler) {
      document.removeEventListener('keydown', this.keydownHandler);
      this.keydownHandler = null;
    }
    if (this.workspace) {
      this.workspace.dispose();
      this.workspace = null;
    }
  }
}
