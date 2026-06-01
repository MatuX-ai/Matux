/**
 * 电路实验快捷键注册器
 *
 * 将 AIEduShortcutService 定义的电路快捷键绑定到 DOM 事件
 * PRD F-07 桌面端适配：大屏拖拽、键盘快捷键（R=旋转、Delete=删除等）
 */

import { Injectable, NgZone } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';

/** 快捷键动作回调 */
export type CircuitShortcutCallback = (action: CircuitAction) => void;

/** 电路操作类型 */
export type CircuitAction =
  | 'rotate'         // R: 旋转选中元件 90 度
  | 'delete'         // Delete: 删除选中元件
  | 'undo'           // Ctrl+Z: 撤销上一步
  | 'cancel'         // Escape: 取消选择
  | 'help'           // F1: 显示帮助
  | 'selectAll'      // Ctrl+A: 全选
  | 'copy'           // Ctrl+C: 复制
  | 'paste';         // Ctrl+V: 粘贴

/** 快捷键定义 */
interface ShortcutDefinition {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  action: CircuitAction;
  description: string;
}

@Injectable({
  providedIn: 'root',
})
export class CircuitShortcutRegistrar {
  /** 快捷键定义列表 */
  private readonly shortcuts: ShortcutDefinition[] = [
    { key: 'r', action: 'rotate', description: '旋转元件 90°' },
    { key: 'R', shift: true, action: 'rotate', description: '旋转元件 90°' },
    { key: 'Delete', action: 'delete', description: '删除选中元件' },
    { key: 'Backspace', action: 'delete', description: '删除选中元件' },
    { key: 'z', ctrl: true, action: 'undo', description: '撤销' },
    { key: 'Escape', action: 'cancel', description: '取消选择' },
    { key: 'F1', action: 'help', description: '显示快捷键帮助' },
    { key: 'a', ctrl: true, action: 'selectAll', description: '全选元件' },
    { key: 'c', ctrl: true, action: 'copy', description: '复制选中元件' },
    { key: 'v', ctrl: true, action: 'paste', description: '粘贴元件' },
  ];

  /** 已注册的回调 */
  private callback: CircuitShortcutCallback | null = null;

  /** 绑定的键盘事件处理器 */
  private keydownHandler: ((event: KeyboardEvent) => void) | null = null;

  constructor(
    private ngZone: NgZone,
    private snackBar: MatSnackBar,
  ) {}

  /**
   * 注册快捷键到指定元素
   * @param element 目标 DOM 元素
   * @param callback 快捷键动作回调
   */
  register(element: HTMLElement, callback: CircuitShortcutCallback): void {
    this.unregister();
    this.callback = callback;

    this.keydownHandler = (event: KeyboardEvent) => {
      const action = this.matchShortcut(event);
      if (action) {
        event.preventDefault();
        event.stopPropagation();
        this.ngZone.run(() => {
          if (this.callback) {
            this.callback(action);
          }
        });
      }
    };

    element.addEventListener('keydown', this.keydownHandler, true);
  }

  /** 注销快捷键 */
  unregister(): void {
    this.callback = null;
    this.keydownHandler = null;
  }

  /** 匹配快捷键 */
  private matchShortcut(event: KeyboardEvent): CircuitAction | null {
    for (const shortcut of this.shortcuts) {
      const keyMatch = event.key === shortcut.key;
      const ctrlMatch = shortcut.ctrl ? (event.ctrlKey || event.metaKey) : !event.ctrlKey;
      const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey;

      if (keyMatch && ctrlMatch && shiftMatch) {
        return shortcut.action;
      }
    }
    return null;
  }

  /** 显示快捷键帮助 */
  showHelp(): void {
    const lines = this.shortcuts.map(
      (s) => `${this.formatKey(s)}: ${s.description}`
    );
    this.snackBar.open(lines.join(' | '), '关闭', { duration: 5000 });
  }

  /** 格式化快捷键显示 */
  private formatKey(shortcut: ShortcutDefinition): string {
    const parts: string[] = [];
    if (shortcut.ctrl) parts.push('Ctrl');
    if (shortcut.shift) parts.push('Shift');
    parts.push(shortcut.key);
    return parts.join('+');
  }

  /** 获取所有快捷键列表 */
  getShortcutsList(): { key: string; action: string; description: string }[] {
    return this.shortcuts.map((s) => ({
      key: this.formatKey(s),
      action: s.action,
      description: s.description,
    }));
  }
}
