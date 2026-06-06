/**
 * 内容商店详情组件
 *
 * PRD F-10 内容商店子路由：内容详情页面
 */

import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-store-content-detail',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatCardModule, MatChipsModule, MatIconModule],
  template: `
    <div class="detail-container">
      <button mat-button (click)="goBack()" class="back-btn">
        <mat-icon>arrow_back</mat-icon> 返回商店
      </button>

      <div class="detail-layout">
        <div class="detail-main">
          <div class="detail-hero" [class]="'hero-' + content?.contentType">
            <span class="hero-emoji">{{
              content?.contentType === 'course'
                ? '📚'
                : content?.contentType === 'resource'
                  ? '📦'
                  : '🔧'
            }}</span>
          </div>

          <mat-card class="detail-card">
            <mat-card-content>
              <h1 class="detail-title">{{ content?.title }}</h1>
              <p class="detail-desc">{{ content?.description }}</p>

              <div class="detail-meta">
                <span class="meta-rating">⭐ {{ content?.rating }}/5.0</span>
                <span class="meta-type">{{ typeLabel }}</span>
              </div>

              <div class="detail-tags">
                <mat-chip-listbox>
                  <mat-chip *ngFor="let tag of content?.tags ?? []">{{ tag }}</mat-chip>
                </mat-chip-listbox>
              </div>

              <div class="detail-actions">
                <button
                  mat-raised-button
                  color="primary"
                  class="action-btn"
                  *ngIf="!content?.isPurchased"
                >
                  {{ content?.isFree ? '免费获取' : '¥' + (content?.price ?? 0) + ' 购买' }}
                </button>
                <button
                  mat-raised-button
                  color="accent"
                  class="action-btn"
                  *ngIf="content?.isPurchased"
                >
                  开始学习
                </button>
              </div>
            </mat-card-content>
          </mat-card>
        </div>

        <div class="detail-sidebar">
          <mat-card>
            <mat-card-header>
              <mat-card-title>内容信息</mat-card-title>
            </mat-card-header>
            <mat-card-content>
              <div class="info-row">
                <span class="info-label">类型</span>
                <span class="info-value">{{ typeLabel }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">分类</span>
                <span class="info-value">{{ content?.category }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">难度</span>
                <span class="info-value">{{ content?.difficulty ?? '中级' }}</span>
              </div>
              <div class="info-row" *ngIf="content?.duration">
                <span class="info-label">时长</span>
                <span class="info-value">{{ content?.duration }}</span>
              </div>
            </mat-card-content>
          </mat-card>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .detail-container {
        padding: 24px;
        max-width: 1200px;
        margin: 0 auto;
      }
      .back-btn {
        margin-bottom: 16px;
      }
      .detail-layout {
        display: grid;
        grid-template-columns: 1fr 300px;
        gap: 24px;
      }
      .detail-hero {
        height: 200px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 16px;
      }
      .hero-course {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
      }
      .hero-resource {
        background: linear-gradient(135deg, #22c55e, #10b981);
      }
      .hero-template {
        background: linear-gradient(135deg, #f59e0b, #ef4444);
      }
      .hero-emoji {
        font-size: 64px;
      }
      .detail-card {
        border-radius: 16px;
      }
      .detail-title {
        font-size: 24px;
        font-weight: 700;
        color: #0f172a;
        margin: 0 0 12px;
      }
      .detail-desc {
        font-size: 15px;
        line-height: 1.6;
        color: #475569;
        margin: 0 0 16px;
      }
      .detail-meta {
        display: flex;
        gap: 16px;
        margin-bottom: 16px;
      }
      .meta-rating {
        color: #f59e0b;
        font-weight: 500;
      }
      .meta-type {
        color: #3b82f6;
      }
      .detail-tags {
        margin-bottom: 20px;
      }
      .action-btn {
        min-width: 200px;
        height: 44px;
        font-size: 16px;
        border-radius: 12px;
      }
      .info-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #f1f5f9;
      }
      .info-label {
        color: #64748b;
        font-size: 13px;
      }
      .info-value {
        color: #0f172a;
        font-size: 14px;
        font-weight: 500;
      }
      @media (max-width: 768px) {
        .detail-layout {
          grid-template-columns: 1fr;
        }
      }
    `,
  ],
})
export class StoreContentDetailComponent implements OnInit {
  content: {
    id: string;
    title: string;
    description: string;
    price: number;
    rating: number;
    contentType: 'course' | 'resource' | 'template';
    category: string;
    isFree: boolean;
    isPurchased: boolean;
    tags: string[];
    difficulty?: string;
    duration?: string;
  } | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    // Mock 数据
    this.content = {
      id: id ?? 'c1',
      title: 'Python 游戏开发入门',
      description:
        '学习使用 Pygame 开发经典小游戏。本课程适合零基础学生，从安装环境到完成第一个游戏项目，循序渐进。',
      price: 0,
      rating: 4.8,
      contentType: 'course',
      category: '编程开发',
      isFree: true,
      isPurchased: false,
      tags: ['Python', '游戏开发', '入门', 'Pygame'],
      difficulty: '初级',
      duration: '12课时',
    };
  }

  get typeLabel(): string {
    const map = { course: '课程', resource: '资源', template: '模板' };
    return this.content ? map[this.content.contentType] : '';
  }

  goBack(): void {
    void this.router.navigate(['/store']);
  }
}
