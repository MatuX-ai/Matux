/**
 * OpenSciEDU 公共课程页面
 *
 * 展示 OpenSciEDU 公共课程目录和知识图谱
 *
 * 基于 PRD F-18: OpenSciEDU 公共课程自动接入
 */

import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { OpenscieduCatalogComponent } from '../shared/components/opensciedu-catalog/opensciedu-catalog.component';
import { OpenscieduGraphComponent } from '../shared/components/opensciedu-graph/opensciedu-graph.component';
import {
  CourseDetail,
  KnowledgeNode,
  OpenSciEDUService,
  PublicCourse,
} from '../core/services/opensciedu.service';

@Component({
  selector: 'app-opensciedu-page',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatTabsModule,
    MatToolbarModule,
    MatTooltipModule,
    OpenscieduCatalogComponent,
    OpenscieduGraphComponent,
  ],
  template: `
    <div class="opensciedu-page">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-content">
          <div class="header-info">
            <h1 class="page-title">OpenSciEDU 公共课程</h1>
            <p class="page-description">
              探索来自 OpenSciEDU 平台的精选 STEM 课程，涵盖编程、数学、物理等学科
            </p>
          </div>
          <div class="header-actions">
            <button
              mat-stroked-button
              routerLink="/user/courses"
              class="back-btn"
            >
              <mat-icon>arrow_back</mat-icon>
              返回我的课程
            </button>
          </div>
        </div>
      </div>

      <!-- 内容区域 -->
      <div class="page-content">
        <mat-tab-group animationDuration="300ms" class="content-tabs">
          <!-- Tab 1: 课程目录 -->
          <mat-tab>
            <ng-template mat-tab-label>
              <mat-icon>library_books</mat-icon>
              <span>课程目录</span>
            </ng-template>
            <div class="tab-content">
              <app-opensciedu-catalog
                (courseSelected)="onCourseSelected($event)"
              ></app-opensciedu-catalog>
            </div>
          </mat-tab>

          <!-- Tab 2: 知识图谱 -->
          <mat-tab>
            <ng-template mat-tab-label>
              <mat-icon>account_tree</mat-icon>
              <span>知识图谱</span>
            </ng-template>
            <div class="tab-content">
              <app-opensciedu-graph
                height="600px"
                (nodeSelected)="onNodeSelected($event)"
              ></app-opensciedu-graph>
            </div>
          </mat-tab>
        </mat-tab-group>
      </div>

      <!-- 课程详情对话框内容 -->
      <ng-container *ngIf="selectedCourse">
        <div class="course-detail-panel" *ngIf="showCourseDetail">
          <mat-card class="detail-card">
            <mat-card-header>
              <mat-card-title>{{ selectedCourse.title }}</mat-card-title>
              <button mat-icon-button class="close-btn" (click)="closeCourseDetail()">
                <mat-icon>close</mat-icon>
              </button>
            </mat-card-header>
            <mat-card-content>
              <div class="detail-cover" *ngIf="selectedCourse.coverImage">
                <img [src]="selectedCourse.coverImage" [alt]="selectedCourse.title" />
              </div>
              <p class="detail-description">{{ selectedCourse.description }}</p>

              <div class="detail-meta">
                <div class="meta-item">
                  <mat-icon>person</mat-icon>
                  <span>{{ selectedCourse.instructor.name }}</span>
                </div>
                <div class="meta-item">
                  <mat-icon>schedule</mat-icon>
                  <span>{{ openscieduService.formatDuration(selectedCourse.durationMinutes) }}</span>
                </div>
                <div class="meta-item">
                  <mat-icon>people</mat-icon>
                  <span>{{ openscieduService.formatStudentCount(selectedCourse.studentCount) }} 人学习</span>
                </div>
                <div class="meta-item">
                  <mat-icon>star</mat-icon>
                  <span>{{ selectedCourse.rating.toFixed(1) }} 分</span>
                </div>
              </div>

              <div class="detail-chapters" *ngIf="courseDetail && courseDetail.chapters.length">
                <h4>课程章节</h4>
                <div class="chapter-list">
                  <div
                    *ngFor="let chapter of courseDetail.chapters; let i = index"
                    class="chapter-item"
                  >
                    <span class="chapter-number">{{ i + 1 }}</span>
                    <span class="chapter-title">{{ chapter.title }}</span>
                    <span class="chapter-duration" *ngIf="chapter.durationMinutes">
                      {{ chapter.durationMinutes }} 分钟
                    </span>
                  </div>
                </div>
              </div>

              <div class="detail-outcomes" *ngIf="courseDetail && courseDetail.learningOutcomes.length">
                <h4>学习收获</h4>
                <ul class="outcome-list">
                  <li *ngFor="let outcome of courseDetail.learningOutcomes">
                    {{ outcome }}
                  </li>
                </ul>
              </div>
            </mat-card-content>
            <mat-card-actions>
              <button mat-raised-button color="primary" *ngIf="selectedCourse.isFree">
                开始学习
              </button>
              <button mat-stroked-button *ngIf="!selectedCourse.isFree">
                购买课程
              </button>
            </mat-card-actions>
          </mat-card>
        </div>
      </ng-container>

      <!-- 知识节点详情 -->
      <ng-container *ngIf="selectedNode && showNodeDetail">
        <div class="node-detail-panel">
          <mat-card class="detail-card">
            <mat-card-header>
              <mat-card-title>{{ selectedNode.name }}</mat-card-title>
              <button mat-icon-button class="close-btn" (click)="closeNodeDetail()">
                <mat-icon>close</mat-icon>
              </button>
            </mat-card-header>
            <mat-card-content>
              <div class="node-category">
                <span class="category-badge">{{ selectedNode.category }}</span>
                <span class="level-badge">Level {{ selectedNode.level }}</span>
              </div>
              <p class="node-description" *ngIf="selectedNode.description">
                {{ selectedNode.description }}
              </p>
              <div class="node-stats">
                <div class="stat-item">
                  <mat-icon>school</mat-icon>
                  <span>{{ selectedNode.courseCount }} 个相关课程</span>
                </div>
              </div>
            </mat-card-content>
          </mat-card>
        </div>
      </ng-container>
    </div>
  `,
  styles: [
    `
      .opensciedu-page {
        min-height: 100vh;
        background: var(--bg-secondary, #f8fafc);
      }

      .page-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 32px 24px;
      }

      .header-content {
        max-width: 1400px;
        margin: 0 auto;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .page-title {
        font-size: 32px;
        font-weight: 700;
        margin: 0 0 8px;
      }

      .page-description {
        font-size: 16px;
        opacity: 0.9;
        margin: 0;
      }

      .back-btn {
        color: white;
        border-color: rgba(255, 255, 255, 0.5);
      }

      .page-content {
        max-width: 1400px;
        margin: 0 auto;
        padding: 24px;
      }

      .content-tabs {
        background: white;
        border-radius: 16px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      }

      .tab-content {
        padding: 24px;
      }

      .course-detail-panel,
      .node-detail-panel {
        position: fixed;
        top: 0;
        right: 0;
        width: 400px;
        height: 100vh;
        background: white;
        box-shadow: -4px 0 24px rgba(0, 0, 0, 0.15);
        z-index: 1000;
        overflow-y: auto;
        animation: slideIn 0.3s ease;
      }

      @keyframes slideIn {
        from {
          transform: translateX(100%);
        }
        to {
          transform: translateX(0);
        }
      }

      .detail-card {
        border-radius: 0;

        .close-btn {
          margin-left: auto;
        }

        mat-card-content {
          padding: 16px;
        }

        .detail-cover {
          width: 100%;
          height: 200px;
          margin-bottom: 16px;
          border-radius: 8px;
          overflow: hidden;

          img {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }
        }

        .detail-description {
          color: var(--text-secondary, #64748b);
          margin-bottom: 16px;
        }

        .detail-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 16px;
          margin-bottom: 24px;

          .meta-item {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 14px;
            color: var(--text-secondary, #64748b);

            mat-icon {
              font-size: 18px;
              width: 18px;
              height: 18px;
            }
          }
        }

        .detail-chapters,
        .detail-outcomes {
          margin-bottom: 24px;

          h4 {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 12px;
          }

          .chapter-list {
            .chapter-item {
              display: flex;
              align-items: center;
              gap: 12px;
              padding: 8px 0;
              border-bottom: 1px solid var(--border-color, #e5e7eb);

              .chapter-number {
                width: 24px;
                height: 24px;
                border-radius: 50%;
                background: var(--color-primary, #3b82f6);
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: 600;
              }

              .chapter-title {
                flex: 1;
              }

              .chapter-duration {
                font-size: 12px;
                color: var(--text-secondary, #64748b);
              }
            }
          }

          .outcome-list {
            padding-left: 20px;
            margin: 0;

            li {
              margin-bottom: 8px;
              color: var(--text-secondary, #64748b);
            }
          }
        }
      }

      .node-detail-panel {
        .node-category {
          display: flex;
          gap: 8px;
          margin-bottom: 16px;

          .category-badge,
          .level-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
          }

          .category-badge {
            background: var(--color-primary, #3b82f6);
            color: white;
          }

          .level-badge {
            background: var(--bg-secondary, #f1f5f9);
            color: var(--text-secondary, #64748b);
          }
        }

        .node-description {
          color: var(--text-secondary, #64748b);
          margin-bottom: 16px;
        }

        .node-stats {
          .stat-item {
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text-secondary, #64748b);
          }
        }
      }
    `,
  ],
})
export class OpenscieduPageComponent implements OnInit {
  // 选中的课程/节点
  selectedCourse: PublicCourse | null = null;
  selectedNode: KnowledgeNode | null = null;
  courseDetail: CourseDetail | null = null;

  // 显示状态
  showCourseDetail = false;
  showNodeDetail = false;

  constructor(public openscieduService: OpenSciEDUService) {}

  ngOnInit(): void {
    // 初始化逻辑
  }

  // 课程选择
  onCourseSelected(course: PublicCourse): void {
    this.selectedCourse = course;
    this.showCourseDetail = true;
    this.showNodeDetail = false;

    // 加载课程详情
    this.openscieduService.getCourseDetail(course.id).subscribe({
      next: (detail) => {
        if (detail) {
          this.courseDetail = detail;
        }
      },
      error: (err) => {
        console.error('加载课程详情失败:', err);
      },
    });
  }

  closeCourseDetail(): void {
    this.showCourseDetail = false;
    this.selectedCourse = null;
    this.courseDetail = null;
  }

  // 节点选择
  onNodeSelected(node: KnowledgeNode): void {
    this.selectedNode = node;
    this.showNodeDetail = true;
    this.showCourseDetail = false;
  }

  closeNodeDetail(): void {
    this.showNodeDetail = false;
    this.selectedNode = null;
  }
}
