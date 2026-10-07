/**
 * 学生课件库仪表板组件
 *
 * 在首页 widget 中展示最近 4-6 个课件，提供缩略图、文件类型和快速入口。
 * 完整课件库管理功能由独立路由页面承载（待规划）。
 */

import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

interface MaterialItem {
  id: string;
  title: string;
  type: 'pdf' | 'video' | 'doc' | 'slides';
  size: string;
  course: string;
  updatedAt: string;
  icon: string;
  color: string;
}

const MOCK_MATERIALS: MaterialItem[] = [
  {
    id: 'm1',
    title: '机器人基础 - 第1章 概述',
    type: 'pdf',
    size: '2.4 MB',
    course: '机器人基础入门',
    updatedAt: '2 天前',
    icon: 'picture_as_pdf',
    color: '#ef4444',
  },
  {
    id: 'm2',
    title: 'AI 编程实战视频',
    type: 'video',
    size: '156 MB',
    course: 'AI 编程与机器学习',
    updatedAt: '5 天前',
    icon: 'play_circle',
    color: '#0ea5e9',
  },
  {
    id: 'm3',
    title: 'Python 语法速查表',
    type: 'doc',
    size: '320 KB',
    course: 'Python 机器人控制',
    updatedAt: '1 周前',
    icon: 'description',
    color: '#2563eb',
  },
  {
    id: 'm4',
    title: '电路实验 PPT',
    type: 'slides',
    size: '8.7 MB',
    course: '电子电路基础',
    updatedAt: '2 周前',
    icon: 'slideshow',
    color: '#f59e0b',
  },
  {
    id: 'm5',
    title: '传感器原理手册',
    type: 'pdf',
    size: '4.1 MB',
    course: '传感器与控制',
    updatedAt: '3 周前',
    icon: 'picture_as_pdf',
    color: '#ef4444',
  },
  {
    id: 'm6',
    title: '项目答辩模板',
    type: 'slides',
    size: '1.2 MB',
    course: '通用',
    updatedAt: '1 个月前',
    icon: 'slideshow',
    color: '#f59e0b',
  },
];

const TYPE_LABEL_MAP: Record<MaterialItem['type'], string> = {
  pdf: 'PDF',
  video: '视频',
  doc: '文档',
  slides: '幻灯片',
};

@Component({
  selector: 'app-student-material-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatChipsModule,
    MatTooltipModule,
  ],
  template: `
    <div class="material-dashboard">
      <div class="material-grid">
        <mat-card *ngFor="let item of materials" class="material-card">
          <div
            class="material-cover"
            [style.background]="item.color + '15'"
            [style.color]="item.color"
          >
            <mat-icon>{{ item.icon }}</mat-icon>
          </div>
          <div class="material-info">
            <h4 class="material-title" [matTooltip]="item.title">{{ item.title }}</h4>
            <div class="material-meta">
              <mat-chip
                class="material-type-chip"
                [style.background]="item.color + '15'"
                [style.color]="item.color"
              >
                {{ getTypeLabel(item.type) }}
              </mat-chip>
              <span class="material-size">{{ item.size }}</span>
            </div>
            <div class="material-footer">
              <span class="material-course">{{ item.course }}</span>
              <span class="material-date">{{ item.updatedAt }}</span>
            </div>
          </div>
          <button mat-icon-button matTooltip="查看课件" class="material-action">
            <mat-icon>arrow_forward</mat-icon>
          </button>
        </mat-card>
      </div>
    </div>
  `,
  styles: [
    `
      :host {
        display: block;
      }

      .material-dashboard {
        display: block;
        width: 100%;
      }

      .material-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
      }

      .material-card {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px !important;
        border: 1px solid var(--matux-color-divider, #e2e8f0) !important;
        border-radius: 14px !important;
        background: var(--matux-color-surface, #fff) !important;
        box-shadow: 0 1px 3px rgb(0 0 0 / 4%);
        transition:
          transform 0.2s ease,
          box-shadow 0.2s ease;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgb(0 0 0 / 8%);
        }
      }

      .material-cover {
        display: flex;
        flex-shrink: 0;
        justify-content: center;
        align-items: center;
        width: 48px;
        height: 48px;
        border-radius: 12px;

        mat-icon {
          width: 28px;
          height: 28px;
          font-size: 28px;
        }
      }

      .material-info {
        flex: 1;
        min-width: 0;
      }

      .material-title {
        margin: 0 0 6px;
        overflow: hidden;
        color: var(--matux-color-text-primary, #0f172a);
        font-size: 14px;
        font-weight: 600;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .material-meta {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
      }

      .material-type-chip {
        display: inline-flex !important;
        align-items: center !important;
        min-height: 20px !important;
        padding: 0 8px !important;
        border-radius: 10px !important;
        font-size: 11px !important;
        font-weight: 600 !important;
      }

      .material-size {
        color: var(--matux-color-text-secondary, #64748b);
        font-size: 11px;
      }

      .material-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: var(--matux-color-text-disabled, #94a3b8);
        font-size: 11px;
      }

      .material-course {
        overflow: hidden;
        max-width: 60%;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .material-action {
        flex-shrink: 0;
      }

      @media (max-width: 1024px) {
        .material-grid {
          grid-template-columns: repeat(2, 1fr);
        }
      }

      @media (max-width: 768px) {
        .material-grid {
          grid-template-columns: 1fr;
        }
      }
    `,
  ],
})
export class StudentMaterialDashboardComponent {
  readonly materials = MOCK_MATERIALS;

  getTypeLabel(type: MaterialItem['type']): string {
    return TYPE_LABEL_MAP[type] ?? type;
  }
}
