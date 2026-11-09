/**
 * AI 编程课页面
 *
 * 集成 Blockly 可视化编程和课程学习
 *
 * 基于 PRD F-05: Blockly 可视化编程
 */

import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ActivatedRoute } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { PublicCourse } from '../../core/services/opensciedu.service';
import { BlocklyWorkspaceComponent } from '../../shared/components/blockly-workspace/blockly-workspace.component';
import { OpenscieduCatalogComponent } from '../../shared/components/opensciedu-catalog/opensciedu-catalog.component';
import { OpenscieduGraphComponent } from '../../shared/components/opensciedu-graph/opensciedu-graph.component';
import {
  EditorTab,
  TabRunResult,
  TabbedEditorComponent,
} from '../../shared/components/tabbed-editor/tabbed-editor.component';

interface CodeExecutionResponse {
  success: boolean;
  output: string;
  error?: string | null;
  execution_time: number;
}

@Component({
  selector: 'app-ai-coding-course',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatTabsModule,
    MatToolbarModule,
    MatTooltipModule,
    BlocklyWorkspaceComponent,
    OpenscieduCatalogComponent,
    OpenscieduGraphComponent,
    TabbedEditorComponent,
  ],
  template: `
    <div class="ai-coding-course">
      <!-- 顶部导航 -->
      <mat-toolbar class="course-toolbar" color="primary">
        <span class="toolbar-title">
          <mat-icon>code</mat-icon>
          AI 编程课
        </span>
        <!-- 【§8.1-5】从课程学习页跳转时展示关联课程 -->
        @if (linkedCourseTitle) {
          <span class="linked-course" [matTooltip]="'从课程页进入：' + linkedCourseTitle">
            <mat-icon>menu_book</mat-icon>
            {{ linkedCourseTitle }}
          </span>
        }
        <span class="toolbar-spacer"></span>
        <button mat-icon-button (click)="refreshData()" matTooltip="刷新">
          <mat-icon>refresh</mat-icon>
        </button>
      </mat-toolbar>

      <!-- 主内容区域 -->
      <div class="course-content">
        <mat-tab-group animationDuration="300ms" class="course-tabs">
          <!-- Tab 1: Blockly 可视化编程 -->
          <mat-tab>
            <ng-template mat-tab-label>
              <mat-icon class="tab-icon">view_module</mat-icon>
              <span>Blockly 可视化编程</span>
            </ng-template>
            <div class="tab-content">
              <app-blockly-workspace
                [showCodePreview]="true"
                (codeChanged)="onCodeChanged($event)"
              ></app-blockly-workspace>
            </div>
          </mat-tab>

          <!-- Tab 2: 课程目录 -->
          <mat-tab>
            <ng-template mat-tab-label>
              <mat-icon class="tab-icon">school</mat-icon>
              <span>课程目录</span>
            </ng-template>
            <div class="tab-content">
              <app-opensciedu-catalog
                (courseSelected)="onCourseSelected($event)"
              ></app-opensciedu-catalog>
            </div>
          </mat-tab>

          <!-- Tab 3: 知识图谱 -->
          <mat-tab>
            <ng-template mat-tab-label>
              <mat-icon class="tab-icon">account_tree</mat-icon>
              <span>知识图谱</span>
            </ng-template>
            <div class="tab-content">
              <app-opensciedu-graph></app-opensciedu-graph>
            </div>
          </mat-tab>

          <!-- Tab 4: 代码编辑器（【P0-C 修复】挂载 Monaco） -->
          <mat-tab>
            <ng-template mat-tab-label>
              <mat-icon class="tab-icon">edit_note</mat-icon>
              <span>代码编辑器</span>
            </ng-template>
            <div class="tab-content editor-tab-content">
              <app-tabbed-editor
                [tabs]="editorTabs"
                [activeTabId]="activeEditorTabId"
                [isRunning]="isEditorRunning"
                [lastRunResult]="editorRunResult"
                (tabChange)="activeEditorTabId = $event"
                (contentChange)="onEditorContentChange($event)"
                (newTabRequest)="addEditorTab()"
                (tabClose)="closeEditorTab($event)"
                (runRequest)="runEditorTab($event)"
              ></app-tabbed-editor>
            </div>
          </mat-tab>
        </mat-tab-group>
      </div>

      <!-- 代码预览面板 -->
      @if (currentCode) {
        <div class="code-panel">
          <mat-card>
            <mat-card-header>
              <mat-card-title>生成的代码</mat-card-title>
              <button mat-icon-button (click)="copyCode()">
                <mat-icon>content_copy</mat-icon>
              </button>
            </mat-card-header>
            <mat-card-content>
              <pre class="code-preview">{{ currentCode }}</pre>
            </mat-card-content>
          </mat-card>
        </div>
      }
    </div>
  `,
  styles: [
    `
      .ai-coding-course {
        display: flex;
        flex-direction: column;
        height: 100vh;
        background: var(--matux-color-background, #f1f5f9);
      }

      .course-toolbar {
        flex-shrink: 0;
      }

      .toolbar-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 18px;
        font-weight: 500;
      }

      .toolbar-spacer {
        flex: 1;
      }

      /* 【§8.1-5】关联课程徒标 */
      .linked-course {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-left: 16px;
        padding: 4px 12px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.18);
        font-size: 13px;
        font-weight: 500;
        max-width: 420px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .linked-course mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }

      .course-content {
        flex: 1;
        overflow: hidden;
        padding: 16px;
      }

      .course-tabs {
        height: 100%;
      }

      .tab-icon {
        margin-right: 8px;
      }

      .tab-content {
        height: calc(100vh - 120px);
        overflow: auto;
      }

      /* 【P0-C 修复】Monaco 编辑器需要固定高度，避免双层滚动条 */
      .editor-tab-content {
        height: calc(100vh - 132px);
        overflow: hidden;

        app-tabbed-editor {
          display: block;
          height: 100%;
        }
      }

      .code-panel {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 400px;
        max-height: 300px;
        z-index: 1000;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }

      .code-preview {
        background: var(--code-editor-bg, #1e1e1e);
        color: var(--code-editor-text, #d4d4d4);
        padding: 12px;
        border-radius: 4px;
        overflow: auto;
        max-height: 200px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        line-height: 1.5;
        margin: 0;
      }

      mat-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
    `,
  ],
})
/* eslint-disable no-console */
export class AICodingCourseComponent implements OnInit {
  currentCode = '';

  // 【P0-C 修复】Monaco 多标签编辑器状态
  editorTabs: EditorTab[] = [
    {
      id: 'main',
      title: 'main.py',
      content:
        '# MatuX 代码编辑器（Monaco）\n# Ctrl+Enter 运行，Ctrl+S 保存，Ctrl+N 新建标签页\nprint("Hello, MatuX!")\n',
      language: 'python',
      isDirty: false,
    },
  ];
  activeEditorTabId: string | null = 'main';
  isEditorRunning = false;
  editorRunResult: TabRunResult | null = null;

  /** 【§8.1-5】从课程学习页带入的关联课程 */
  linkedCourseId: number | null = null;
  linkedCourseTitle = '';

  constructor(
    private http: HttpClient,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    const params = this.route.snapshot.queryParamMap;
    const courseId = Number(params.get('courseId'));
    if (courseId && !Number.isNaN(courseId)) {
      this.linkedCourseId = courseId;
      this.linkedCourseTitle = params.get('courseTitle') || `课程 #${courseId}`;
    }
    console.log('[AICodingCourse] 组件初始化', { linkedCourseId: this.linkedCourseId });
  }

  /** 【P0-C 修复】编辑器内容变更 */
  onEditorContentChange(event: { tabId: string; content: string }): void {
    const tab = this.editorTabs.find((t) => t.id === event.tabId);
    if (tab) {
      tab.content = event.content;
      tab.isDirty = true;
    }
    this.currentCode = event.content;
  }

  /** 新建编辑器标签页 */
  addEditorTab(): void {
    const index = this.editorTabs.length + 1;
    const tab: EditorTab = {
      id: `tab_${Date.now()}`,
      title: `untitled_${index}.py`,
      content: '',
      language: 'python',
      isDirty: false,
    };
    this.editorTabs = [...this.editorTabs, tab];
    this.activeEditorTabId = tab.id;
  }

  /** 关闭编辑器标签页 */
  closeEditorTab(tabId: string): void {
    this.editorTabs = this.editorTabs.filter((t) => t.id !== tabId);
    if (this.activeEditorTabId === tabId) {
      this.activeEditorTabId = this.editorTabs[0]?.id ?? null;
    }
  }

  /** 【P0-C 修复】运行编辑器标签页代码 */
  async runEditorTab(tabId: string): Promise<void> {
    const tab = this.editorTabs.find((t) => t.id === tabId);
    if (!tab || this.isEditorRunning) return;

    this.isEditorRunning = true;
    const startTime = performance.now();

    try {
      if (tab.language === 'javascript') {
        const output = this.executeLocalJavaScript(tab.content);
        this.editorRunResult = {
          tabId,
          success: !output.startsWith('运行错误'),
          output,
          executionTime: Math.round(performance.now() - startTime),
        };
        return;
      }

      // Python 等语言走后端沙箱（桌面端未部署 Docker 时给出明确提示）
      const orgId = Number(localStorage.getItem('org_id')) || 1;
      const response = await firstValueFrom(
        this.http.post<CodeExecutionResponse>(
          `/api/v1/org/${orgId}/ai-edu/execute-code`,
          { code: tab.content, language: tab.language, timeout: 5 }
        )
      );
      this.editorRunResult = {
        tabId,
        success: response.success,
        output: response.output || '(无输出)',
        error: response.error ?? undefined,
        executionTime: Math.round(performance.now() - startTime),
      };
    } catch (err) {
      this.editorRunResult = {
        tabId,
        success: false,
        output: '',
        error:
          '在线执行服务不可用（桌面端未启用代码沙箱时属正常现象）。可切换到 JavaScript 标签页在前端运行。' +
          (err instanceof Error ? ` 详情：${err.message}` : ''),
        executionTime: Math.round(performance.now() - startTime),
      };
    } finally {
      this.isEditorRunning = false;
    }
  }

  /** 前端 JavaScript 沙箱执行 */
  private executeLocalJavaScript(code: string): string {
    const logs: string[] = [];
    const capture = (...args: unknown[]): void => {
      logs.push(args.map((a) => (typeof a === 'string' ? a : JSON.stringify(a))).join(' '));
    };
    const sandboxConsole = {
      log: capture,
      info: capture,
      warn: capture,
      error: capture,
      debug: capture,
    };

    try {
      // eslint-disable-next-line no-new-func
      const runner = new Function('console', `"use strict";\n${code}`);
      runner(sandboxConsole);
      return logs.length > 0 ? logs.join('\n') : '（程序执行完成，没有输出）';
    } catch (err) {
      return `运行错误: ${err instanceof Error ? err.message : String(err)}`;
    }
  }

  /**
   * 处理代码变更
   */
  onCodeChanged(code: string): void {
    this.currentCode = code;
    console.log('[AICodingCourse] 代码变更:', code.substring(0, 100));
  }

  /**
   * 处理课程选择
   */
  onCourseSelected(course: PublicCourse): void {
    console.log('[AICodingCourse] 选择课程:', course.title);
    // 可以加载课程到 Blockly 工作区
  }

  /**
   * 刷新数据
   */
  refreshData(): void {
    console.log('[AICodingCourse] 刷新数据');
    this.currentCode = '';
  }

  /**
   * 复制代码
   */
  copyCode(): void {
    if (this.currentCode) {
      void navigator.clipboard.writeText(this.currentCode).then(() => {
        console.log('[AICodingCourse] 代码已复制');
      });
    }
  }
}
