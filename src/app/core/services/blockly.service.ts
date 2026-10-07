/* eslint-disable @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-explicit-any, no-console */
/**
 * Blockly 工作区服务
 *
 * 提供 Blockly 工作区配置和管理功能
 * 使用 blockly npm 包实现真实的可视化编程工作区
 *
 * 基于 PRD F-05: Blockly 可视化编程
 */

import { Injectable, NgZone } from '@angular/core';
import * as Blockly from 'blockly';
import { javascriptGenerator } from 'blockly/javascript';
import { pythonGenerator } from 'blockly/python';

import {
  AI_BLOCK_DEFINITIONS,
  DEFAULT_PYTHON_TOOLBOX,
  TargetLanguage,
  ToolboxConfig,
} from '../models/blockly.models';

// Re-export types for components
export {
  BlocklyOptions,
  BlocklyTheme,
  BlockType,
  TargetLanguage,
  ToolboxConfig,
  WorkspaceState,
} from '../models/blockly.models';

/** 代码变更回调 */
export type CodeChangeCallback = (code: string, language: TargetLanguage) => void;

/** 积木块计数变更回调 */
export type BlockCountCallback = (count: number) => void;

@Injectable({
  providedIn: 'root',
})
export class BlocklyService {
  private workspace: Blockly.WorkspaceSvg | null = null;
  private isInitialized = false;
  private currentLanguage: TargetLanguage = TargetLanguage.PYTHON;
  private codeChangeCallbacks: CodeChangeCallback[] = [];
  private blockCountCallbacks: BlockCountCallback[] = [];
  private changeListenerRef: ((e: Blockly.Events.Abstract) => void) | null = null;

  /** LocalStorage key 前缀 */
  private static readonly STORAGE_PREFIX = 'blockly_project_';

  constructor(private ngZone: NgZone) {
    console.log('[BlocklyService] 服务初始化');
    this.registerCustomBlocks();
  }

  /**
   * 注册自定义 AI 编程积木块
   */
  private registerCustomBlocks(): void {
    try {
      for (const def of AI_BLOCK_DEFINITIONS) {
        if (!Blockly.Blocks[def.type]) {
          Blockly.Blocks[def.type] = {
            init(this: Blockly.Block) {
              this.jsonInit(def);
            },
          };
        }
      }

      // 为自定义块注册代码生成器（生成注释占位）
      // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-explicit-any
      for (const def of AI_BLOCK_DEFINITIONS) {
        const blockType = def.type;
        if (!(pythonGenerator as any)[blockType]) {
          (pythonGenerator as any)[blockType] = function (block: Blockly.Block) {
            const prompt = block.getFieldValue('PROMPT') || block.getFieldValue('ALGORITHM') || '';
            return `# AI: ${prompt}\n`;
          };
        }
        if (!(javascriptGenerator as any)[blockType]) {
          (javascriptGenerator as any)[blockType] = function (block: Blockly.Block) {
            const prompt = block.getFieldValue('PROMPT') || block.getFieldValue('ALGORITHM') || '';
            return `// AI: ${prompt}\n`;
          };
        }
      }
    } catch (err) {
      console.warn('[BlocklyService] 注册自定义块失败:', err);
    }
  }

  /**
   * 构建 Blockly 工具箱 JSON 配置
   */
  private buildToolbox(config?: ToolboxConfig): any {
    const toolbox = config ?? DEFAULT_PYTHON_TOOLBOX;
    const contents: any[] = [];

    for (const category of toolbox.categories) {
      // 跳过自定义 AI 块分类（Blockly 无法识别自定义块定义时会导致工具箱错误）
      if (category.id === 'ai') {
        continue;
      }

      const categoryContents: any[] = [];
      for (const blockType of category.blocks) {
        // 跳过 AI 自定义块（已在上面过滤）
        if (blockType.startsWith('ai_')) continue;
        categoryContents.push({ kind: 'block', type: blockType });
      }

      contents.push({
        kind: 'category',
        name: category.name,
        contents: categoryContents,
        colour: this.getCategoryColour(category.id),
      });
    }

    // 添加变量和函数分类（Blockly 内置动态分类）
    contents.push({
      kind: 'category',
      name: '变量',
      custom: 'VARIABLE',
      colour: '#FF8C00',
    });
    contents.push({
      kind: 'category',
      name: '函数',
      custom: 'PROCEDURE',
      colour: '#995BA5',
    });

    return { kind: 'categoryToolbox', contents };
  }

  /**
   * 获取分类颜色
   */
  private getCategoryColour(categoryId: string): string {
    const colours: Record<string, string> = {
      logic: '#5C81A6',
      loops: '#5CA65C',
      math: '#5C68A6',
      text: '#5CA68C',
      lists: '#745CA6',
    };
    return colours[categoryId] || '#4C97FF';
  }

  /**
   * 初始化工作区
   */
  // eslint-disable-next-line @typescript-eslint/require-await, max-lines-per-function
  async initWorkspace(
    container: HTMLElement,
    options?: { language?: TargetLanguage; readOnly?: boolean; toolbox?: ToolboxConfig }
  ): Promise<Blockly.WorkspaceSvg> {
    if (this.workspace) {
      this.dispose();
    }

    this.currentLanguage = options?.language ?? TargetLanguage.PYTHON;

    const toolbox = this.buildToolbox(options?.toolbox);

    const blocklyOptions: Blockly.BlocklyOptions = {
      toolbox,
      trashcan: true,
      collapse: true,
      comments: true,
      disable: true,
      sounds: true,
      grid: {
        spacing: 20,
        length: 3,
        colour: '#ccc',
        snap: true,
      },
      zoom: {
        controls: true,
        wheel: true,
        startScale: 1.0,
        maxScale: 3,
        minScale: 0.3,
        scaleSpeed: 1.2,
      },
      move: {
        scrollbars: true,
        drag: true,
        wheel: true,
      },
      readOnly: options?.readOnly ?? false,
    };

    this.workspace = Blockly.inject(container, blocklyOptions);
    this.isInitialized = true;

    // 监听工作区变更
    this.changeListenerRef = this.workspace.addChangeListener((event: Blockly.Events.Abstract) => {
      if (
        // eslint-disable-next-line @typescript-eslint/no-unsafe-enum-comparison
        event.type === Blockly.Events.BLOCK_CREATE ||
        // eslint-disable-next-line @typescript-eslint/no-unsafe-enum-comparison
        event.type === Blockly.Events.BLOCK_DELETE ||
        // eslint-disable-next-line @typescript-eslint/no-unsafe-enum-comparison
        event.type === Blockly.Events.BLOCK_CHANGE ||
        // eslint-disable-next-line @typescript-eslint/no-unsafe-enum-comparison
        event.type === Blockly.Events.BLOCK_MOVE
      ) {
        this.ngZone.run(() => {
          this.notifyCodeChange();
          this.notifyBlockCountChange();
        });
      }
    });

    console.log('[BlocklyService] 工作区初始化完成');
    return this.workspace;
  }

  /**
   * 通知代码变更
   */
  private notifyCodeChange(): void {
    const code = this.generateCode();
    for (const cb of this.codeChangeCallbacks) {
      cb(code, this.currentLanguage);
    }
  }

  /**
   * 通知积木块计数变更
   */
  private notifyBlockCountChange(): void {
    const count = this.getBlockCount();
    for (const cb of this.blockCountCallbacks) {
      cb(count);
    }
  }

  /**
   * 监听代码变更
   * @returns 取消监听函数
   */
  onCodeChange(callback: CodeChangeCallback): () => void {
    this.codeChangeCallbacks.push(callback);
    return () => {
      const idx = this.codeChangeCallbacks.indexOf(callback);
      if (idx >= 0) this.codeChangeCallbacks.splice(idx, 1);
    };
  }

  /**
   * 监听积木块计数变更
   * @returns 取消监听函数
   */
  onBlockCountChange(callback: BlockCountCallback): () => void {
    this.blockCountCallbacks.push(callback);
    return () => {
      const idx = this.blockCountCallbacks.indexOf(callback);
      if (idx >= 0) this.blockCountCallbacks.splice(idx, 1);
    };
  }

  /**
   * 生成代码
   */
  generateCode(language?: TargetLanguage): string {
    if (!this.workspace) {
      return '# 工作区未初始化';
    }

    const lang = language ?? this.currentLanguage;

    try {
      switch (lang) {
        case TargetLanguage.PYTHON:
          return pythonGenerator.workspaceToCode(this.workspace);
        case TargetLanguage.JAVASCRIPT:
          return javascriptGenerator.workspaceToCode(this.workspace);
        default:
          return pythonGenerator.workspaceToCode(this.workspace);
      }
    } catch (err) {
      console.error('[BlocklyService] 代码生成失败:', err);
      return `# 代码生成失败: ${String(err)}`;
    }
  }

  /**
   * 获取积木块数量
   */
  getBlockCount(): number {
    if (!this.workspace) return 0;
    return this.workspace.getAllBlocks(false).length;
  }

  /**
   * 撤销
   */
  undo(): void {
    this.workspace?.undo(false);
  }

  /**
   * 重做
   */
  redo(): void {
    this.workspace?.undo(true);
  }

  /**
   * 清空工作区
   */
  clear(): void {
    this.workspace?.clear();
  }

  /**
   * 设置目标语言
   */
  setLanguage(language: TargetLanguage): void {
    this.currentLanguage = language;
    this.notifyCodeChange();
  }

  /**
   * 获取当前语言
   */
  getLanguage(): TargetLanguage {
    return this.currentLanguage;
  }

  // ==================== XML 导入/导出 ====================

  /**
   * 导出工作区为 XML 字符串
   */
  exportXml(): string {
    if (!this.workspace) return '<xml></xml>';
    try {
      const dom = Blockly.Xml.workspaceToDom(this.workspace);
      return Blockly.Xml.domToText(dom);
    } catch (err) {
      console.error('[BlocklyService] 导出 XML 失败:', err);
      return '<xml></xml>';
    }
  }

  /**
   * 从 XML 导入工作区
   */
  importXml(xml: string): boolean {
    if (!this.workspace) return false;
    try {
      this.workspace.clear();
      const dom = Blockly.utils.xml.textToDom(xml);
      Blockly.Xml.domToWorkspace(dom, this.workspace);
      return true;
    } catch (err) {
      console.error('[BlocklyService] 导入 XML 失败:', err);
      return false;
    }
  }

  // ==================== 项目保存/加载 ====================

  /**
   * 保存项目到 LocalStorage
   */
  saveProject(name: string): boolean {
    if (!this.workspace) return false;
    try {
      const project = {
        name,
        xml: this.exportXml(),
        language: this.currentLanguage,
        savedAt: new Date().toISOString(),
        blockCount: this.getBlockCount(),
      };
      localStorage.setItem(`${BlocklyService.STORAGE_PREFIX}${name}`, JSON.stringify(project));
      console.log('[BlocklyService] 项目已保存:', name);
      return true;
    } catch (err) {
      console.error('[BlocklyService] 保存项目失败:', err);
      return false;
    }
  }

  /**
   * 从 LocalStorage 加载项目
   */
  loadProject(name: string): boolean {
    try {
      const data = localStorage.getItem(`${BlocklyService.STORAGE_PREFIX}${name}`);
      if (!data) {
        console.warn('[BlocklyService] 项目不存在:', name);
        return false;
      }
      const project = JSON.parse(data);
      if (project.xml) {
        const success = this.importXml(project.xml);
        if (project.language) {
          this.currentLanguage = project.language;
        }
        return success;
      }
      return false;
    } catch (err) {
      console.error('[BlocklyService] 加载项目失败:', err);
      return false;
    }
  }

  /**
   * 列出所有已保存的项目
   */
  listProjects(): { name: string; savedAt: string; blockCount: number }[] {
    const projects: { name: string; savedAt: string; blockCount: number }[] = [];
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key?.startsWith(BlocklyService.STORAGE_PREFIX)) {
          const data = JSON.parse(localStorage.getItem(key) ?? '{}');
          projects.push({
            name: (data.name as string) ?? key.replace(BlocklyService.STORAGE_PREFIX, ''),
            savedAt: (data.savedAt as string) ?? '',
            blockCount: (data.blockCount as number) ?? 0,
          });
        }
      }
    } catch (err) {
      console.error('[BlocklyService] 列出项目失败:', err);
    }
    return projects;
  }

  /**
   * 删除项目
   */
  deleteProject(name: string): void {
    localStorage.removeItem(`${BlocklyService.STORAGE_PREFIX}${name}`);
  }

  /**
   * 销毁工作区
   */
  dispose(): void {
    if (this.changeListenerRef && this.workspace) {
      this.workspace.removeChangeListener(this.changeListenerRef);
      this.changeListenerRef = null;
    }
    if (this.workspace) {
      this.workspace.dispose();
      this.workspace = null;
    }
    this.isInitialized = false;
    this.codeChangeCallbacks = [];
    this.blockCountCallbacks = [];
  }
}
