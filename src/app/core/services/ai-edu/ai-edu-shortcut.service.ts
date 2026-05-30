/**
 * AI-Edu 快捷键服务
 * 提供全局和组件级的快捷键支持
 */

import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface ShortcutConfig {
  key: string; // 按键组合，如 'Ctrl+ArrowRight'
  description: string; // 快捷键描述
  action: () => void; // 执行的动作
  context?: string; // 适用上下文（player/quiz/global）
}

@Injectable({
  providedIn: 'root',
})
export class AIEduShortcutService {
  private shortcuts: Map<string, ShortcutConfig> = new Map();
  private enabled = true;

  // 快捷键状态流
  private shortcutTriggered$ = new BehaviorSubject<string>('');

  constructor() {}

  /**
   * 注册快捷键
   */
  register(config: ShortcutConfig): void {
    this.shortcuts.set(config.key, config);
  }

  /**
   * 批量注册快捷键
   */
  registerAll(configs: ShortcutConfig[]): void {
    configs.forEach((config) => this.register(config));
  }

  /**
   * 移除快捷键
   */
  unregister(key: string): void {
    this.shortcuts.delete(key);
  }

  /**
   * 启用/禁用快捷键
   */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  /**
   * 获取所有注册的快捷键
   */
  getAllShortcuts(): ShortcutConfig[] {
    return Array.from(this.shortcuts.values());
  }

  /**
   * 获取快捷键状态流
   */
  getShortcutTriggered(): Observable<string> {
    return this.shortcutTriggered$.asObservable();
  }

  /**
   * 监听键盘事件（需要在组件中调用）
   */
  handleKeydown(event: KeyboardEvent): void {
    if (!this.enabled) {
      return;
    }

    const keyCombo = this.buildKeyCombo(event);
    const shortcut = this.shortcuts.get(keyCombo);

    if (shortcut) {
      event.preventDefault();
      event.stopPropagation();
      shortcut.action();
      this.shortcutTriggered$.next(shortcut.key);
    }
  }

  /**
   * 构建按键组合字符串
   */
  private buildKeyCombo(event: KeyboardEvent): string {
    const parts: string[] = [];

    if (event.ctrlKey) {
      parts.push('Ctrl');
    }
    if (event.altKey) {
      parts.push('Alt');
    }
    if (event.shiftKey) {
      parts.push('Shift');
    }

    // 特殊键位映射
    const keyMap: Record<string, string> = {
      ArrowLeft: 'ArrowLeft',
      ArrowRight: 'ArrowRight',
      ArrowUp: 'ArrowUp',
      ArrowDown: 'ArrowDown',
      ' ': 'Space',
      Enter: 'Enter',
      Escape: 'Escape',
      Tab: 'Tab',
    };

    const keyName = keyMap[event.code] || event.key.toUpperCase();
    parts.push(keyName);

    return parts.join('+');
  }

  /**
   * 获取课程播放器的默认快捷键配置
   */
  getPlayerShortcuts(actions: {
    nextResource: () => void;
    prevResource: () => void;
    togglePlayPause: () => void;
    runCode: () => void;
    showHelp: () => void;
  }): ShortcutConfig[] {
    return [
      {
        key: 'ArrowRight',
        description: '下一个资源',
        action: actions.nextResource,
        context: 'player',
      },
      {
        key: 'ArrowLeft',
        description: '上一个资源',
        action: actions.prevResource,
        context: 'player',
      },
      {
        key: 'Space',
        description: '播放/暂停',
        action: actions.togglePlayPause,
        context: 'player',
      },
      {
        key: 'Ctrl+Enter',
        description: '运行代码',
        action: actions.runCode,
        context: 'player',
      },
      {
        key: 'F1',
        description: '显示帮助',
        action: actions.showHelp,
        context: 'player',
      },
    ];
  }

  /**
   * 获取测验的默认快捷键配置
   */
  getQuizShortcuts(actions: {
    nextQuestion: () => void;
    prevQuestion: () => void;
    submitAnswer: () => void;
    submitQuiz: () => void;
    showHelp: () => void;
  }): ShortcutConfig[] {
    return [
      {
        key: 'ArrowRight',
        description: '下一题',
        action: actions.nextQuestion,
        context: 'quiz',
      },
      {
        key: 'ArrowLeft',
        description: '上一题',
        action: actions.prevQuestion,
        context: 'quiz',
      },
      {
        key: 'Enter',
        description: '提交答案',
        action: actions.submitAnswer,
        context: 'quiz',
      },
      {
        key: 'Ctrl+Enter',
        description: '交卷',
        action: actions.submitQuiz,
        context: 'quiz',
      },
      {
        key: 'F1',
        description: '显示帮助',
        action: actions.showHelp,
        context: 'quiz',
      },
    ];
  }

  /**
   * 获取电路虚拟实验的默认快捷键配置
   * 桌面端适配：R=旋转元件、Delete=删除元件、Escape=取消选择
   */
  getCircuitShortcuts(actions: {
    rotateComponent: () => void;
    deleteComponent: () => void;
    deselectAll: () => void;
    undo: () => void;
    showHelp: () => void;
  }): ShortcutConfig[] {
    return [
      {
        key: 'R',
        description: '旋转选中元件 90°',
        action: actions.rotateComponent,
        context: 'circuit',
      },
      {
        key: 'DELETE',
        description: '删除选中元件',
        action: actions.deleteComponent,
        context: 'circuit',
      },
      {
        key: 'Escape',
        description: '取消选择',
        action: actions.deselectAll,
        context: 'circuit',
      },
      {
        key: 'Ctrl+Z',
        description: '撤销操作',
        action: actions.undo,
        context: 'circuit',
      },
      {
        key: 'F1',
        description: '显示帮助',
        action: actions.showHelp,
        context: 'circuit',
      },
    ];
  }
}
