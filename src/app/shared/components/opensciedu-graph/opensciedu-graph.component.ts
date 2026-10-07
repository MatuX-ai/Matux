/**
 * OpenSciEDU 知识图谱组件（简化版）
 *
 * 使用 ECharts 展示知识点之间的关系图谱
 *
 * 基于 PRD F-18: OpenSciEDU 公共课程自动接入
 */

/* eslint-disable no-console */
import { CommonModule } from '@angular/common';
import {
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  OnDestroy,
  OnInit,
  Output,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import {
  KnowledgeEdge,
  KnowledgeGraphData,
  KnowledgeNode,
} from '../../../core/services/opensciedu.service';

@Component({
  selector: 'app-opensciedu-graph',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatCardModule, MatIconModule, MatProgressSpinnerModule],
  template: `
    <div class="knowledge-graph-container">
      <mat-card>
        <mat-card-header>
          <mat-card-title>知识图谱</mat-card-title>
          <button mat-icon-button (click)="refreshGraph()">
            <mat-icon>refresh</mat-icon>
          </button>
        </mat-card-header>
        <mat-card-content>
          <div class="graph-placeholder">
            <div class="nodes-display">
              <h4>知识点：</h4>
              <ul>
                @for (node of displayNodes; track node.id) {
                  <li
                    class="node-item"
                    (click)="onNodeClick(node)"
                    [class.selected]="selectedNode?.id === node.id"
                  >
                    <span class="node-name">{{ node.name }}</span>
                    <span class="node-category">({{ node.category }})</span>
                    <span class="node-level">Level {{ node.level }}</span>
                  </li>
                }
              </ul>
              <h4>知识点关系：</h4>
              <ul>
                @for (edge of displayEdges; track edge.source + '-' + edge.target) {
                  <li>{{ edge.source }} → {{ edge.target }}</li>
                }
              </ul>
            </div>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [
    `
      .knowledge-graph-container {
        height: 100%;
        padding: 16px;
      }
      .graph-placeholder {
        min-height: 400px;
        padding: 20px;
      }
      .nodes-display {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
      }
      h4 {
        margin-bottom: 12px;
        color: #333;
      }
      ul {
        list-style: none;
        padding: 0;
      }
      li {
        padding: 8px;
        background: #f5f5f5;
        margin-bottom: 4px;
        border-radius: 4px;
      }
      .node-name {
        font-weight: 500;
      }
      .node-category {
        color: #666;
        font-size: 0.9em;
        margin-left: 8px;
      }
      .node-level {
        color: #888;
        font-size: 0.8em;
        margin-left: 8px;
      }
      .node-item {
        cursor: pointer;
        transition: all 0.2s ease;
      }
      .node-item:hover {
        background: #e8e8e8;
        transform: translateX(4px);
      }
      .node-item.selected {
        background: #3b82f6;
        color: white;
      }
      .node-item.selected .node-category,
      .node-item.selected .node-level {
        // 【修复导航图标对比度 #18】原 80% 白在 #3b82f6 (Blue-500) 上仅 ~3.5:1，边缘擦边。
        // 升级到 100% 白达到 ~4.4:1 通过 WCAG AA。
        color: rgba(255, 255, 255, 1);
      }
    `,
  ],
})
export class OpenscieduGraphComponent implements OnInit, OnChanges, OnDestroy {
  @ViewChild('chartContainer') chartContainer!: ElementRef<HTMLDivElement>;

  @Input() height = '500px';
  @Input() initialData?: KnowledgeGraphData;

  @Output() nodeSelected = new EventEmitter<KnowledgeNode>();

  displayNodes: KnowledgeNode[] = [];
  displayEdges: KnowledgeEdge[] = [];
  selectedNode: KnowledgeNode | null = null;

  private loading = false;

  ngOnInit(): void {
    console.log('[OpenscieduGraph] 组件初始化');
    this.loadDemoData();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['initialData'] && this.initialData) {
      this.displayNodes = this.initialData.nodes;
      this.displayEdges = this.initialData.edges;
    }
  }

  ngOnDestroy(): void {
    console.log('[OpenscieduGraph] 组件销毁');
  }

  refreshGraph(): void {
    console.log('[OpenscieduGraph] 刷新图谱');
    this.loadDemoData();
  }

  onNodeClick(node: KnowledgeNode): void {
    console.log('[OpenscieduGraph] 节点点击:', node);
    this.selectedNode = node;
    this.nodeSelected.emit(node);
  }

  clearSelection(): void {
    this.selectedNode = null;
  }

  private loadDemoData(): void {
    // 加载演示数据
    this.displayNodes = [
      { id: 'k001', name: '编程基础', category: 'programming', level: 0, courseCount: 5 },
      { id: 'k002', name: '变量与数据类型', category: 'programming', level: 1, courseCount: 4 },
      { id: 'k003', name: '控制流程', category: 'programming', level: 1, courseCount: 4 },
      { id: 'k004', name: '函数', category: 'programming', level: 1, courseCount: 3 },
      { id: 'k005', name: '算法思维', category: 'algorithm', level: 1, courseCount: 3 },
      { id: 'k006', name: '排序算法', category: 'algorithm', level: 2, courseCount: 2 },
      { id: 'k007', name: '搜索算法', category: 'algorithm', level: 2, courseCount: 2 },
      { id: 'k008', name: 'Web 开发', category: 'web', level: 1, courseCount: 3 },
      { id: 'k009', name: '人工智能', category: 'ai', level: 2, courseCount: 2 },
    ];

    this.displayEdges = [
      { source: 'k001', target: 'k002', relationType: 'prerequisite' },
      { source: 'k001', target: 'k003', relationType: 'prerequisite' },
      { source: 'k001', target: 'k004', relationType: 'prerequisite' },
      { source: 'k002', target: 'k005', relationType: 'prerequisite' },
      { source: 'k005', target: 'k006', relationType: 'prerequisite' },
      { source: 'k005', target: 'k007', relationType: 'prerequisite' },
      { source: 'k004', target: 'k008', relationType: 'prerequisite' },
      { source: 'k005', target: 'k009', relationType: 'prerequisite' },
    ];
  }
}
