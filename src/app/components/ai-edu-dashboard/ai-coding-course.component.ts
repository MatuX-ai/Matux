/**
 * AI 编程课页面
 *
 * 集成 Blockly 可视化编程和课程学习
 *
 * 基于 PRD F-05: Blockly 可视化编程
 */

import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { FormsModule } from '@angular/forms';

import { BlocklyWorkspaceComponent } from '../../shared/components/blockly-workspace/blockly-workspace.component';
import { OpenscieduCatalogComponent } from '../../shared/components/opensciedu-catalog/opensciedu-catalog.component';
import { OpenscieduGraphComponent } from '../../shared/components/opensciedu-graph/opensciedu-graph.component';
import { PublicCourse } from '../../core/services/opensciedu.service';

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
  ],
  template: `
    <div class="ai-coding-course">
      <!-- 顶部导航 -->
      <mat-toolbar class="course-toolbar" color="primary">
        <span class="toolbar-title">
          <mat-icon>code</mat-icon>
          AI 编程课
        </span>
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
  styles: [`
    .ai-coding-course {
      display: flex;
      flex-direction: column;
      height: 100vh;
      background: #f5f5f5;
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
      background: #1e1e1e;
      color: #d4d4d4;
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
  `],
})
export class AICodingCourseComponent implements OnInit {
  currentCode = '';

  ngOnInit(): void {
    console.log('[AICodingCourse] 组件初始化');
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
      navigator.clipboard.writeText(this.currentCode).then(() => {
        console.log('[AICodingCourse] 代码已复制');
      });
    }
  }
}
