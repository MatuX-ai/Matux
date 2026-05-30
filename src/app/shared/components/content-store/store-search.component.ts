/**
 * 内容商店搜索组件
 *
 * PRD F-10 内容商店子路由：搜索页面
 */

import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';

interface ContentItem {
  id: string;
  title: string;
  description: string;
  price: number;
  rating: number;
  contentType: 'course' | 'resource' | 'template';
  category: string;
  isFree: boolean;
}

@Component({
  selector: 'app-store-search',
  standalone: true,
  imports: [CommonModule, FormsModule, MatButtonModule, MatCardModule, MatIconModule, MatChipsModule],
  template: `
    <div class="search-container">
      <div class="search-header">
        <h2>搜索结果{{ searchQuery ? ': "' + searchQuery + '"' : '' }}</h2>
        <div class="filter-chips">
          <mat-chip-listbox>
            <mat-chip-option [selected]="selectedType === 'all'" (click)="filterByType('all')">全部</mat-chip-option>
            <mat-chip-option [selected]="selectedType === 'course'" (click)="filterByType('course')">课程</mat-chip-option>
            <mat-chip-option [selected]="selectedType === 'resource'" (click)="filterByType('resource')">资源</mat-chip-option>
            <mat-chip-option [selected]="selectedType === 'template'" (click)="filterByType('template')">模板</mat-chip-option>
          </mat-chip-listbox>
        </div>
      </div>

      <div class="results-grid" *ngIf="filteredResults.length">
        <mat-card *ngFor="let item of filteredResults" class="result-card" (click)="navigateToDetail(item.id)">
          <div class="card-type-badge" [class]="'type-' + item.contentType">
            {{ item.contentType === 'course' ? '📚' : item.contentType === 'resource' ? '📦' : '🔧' }}
          </div>
          <mat-card-content>
            <h3 class="card-title">{{ item.title }}</h3>
            <p class="card-desc">{{ item.description }}</p>
            <div class="card-meta">
              <span class="card-rating">⭐ {{ item.rating }}</span>
              <span class="card-price" [class.free]="item.isFree">
                {{ item.isFree ? '免费' : '¥' + item.price }}
              </span>
            </div>
          </mat-card-content>
        </mat-card>
      </div>

      <div *ngIf="!filteredResults.length" class="no-results">
        <mat-icon>search_off</mat-icon>
        <p>未找到相关内容，换个关键词试试？</p>
      </div>
    </div>
  `,
  styles: [`
    .search-container { padding: 24px; max-width: 1200px; margin: 0 auto; }
    .search-header { margin-bottom: 24px; }
    .search-header h2 { margin: 0 0 12px; color: #0f172a; }
    .results-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
    .result-card { cursor: pointer; border-radius: 16px; transition: transform 0.2s, box-shadow 0.2s; position: relative; }
    .result-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .card-type-badge { position: absolute; top: 12px; right: 12px; font-size: 20px; }
    .card-title { font-size: 16px; font-weight: 600; color: #0f172a; margin: 0 0 8px; }
    .card-desc { font-size: 13px; color: #64748b; margin: 0 0 12px; line-height: 1.5; }
    .card-meta { display: flex; justify-content: space-between; align-items: center; }
    .card-rating { font-size: 13px; color: #f59e0b; }
    .card-price { font-size: 14px; font-weight: 600; color: #3b82f6; }
    .card-price.free { color: #22c55e; }
    .no-results { text-align: center; padding: 48px; color: #94a3b8; }
    .no-results mat-icon { font-size: 48px; width: 48px; height: 48px; }
  `],
})
export class StoreSearchComponent implements OnInit {
  searchQuery = '';
  selectedType = 'all';
  results: ContentItem[] = [];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
  ) {}

  ngOnInit(): void {
    this.route.queryParams.subscribe((params) => {
      this.searchQuery = params['q'] ?? '';
      this.loadResults();
    });
  }

  get filteredResults(): ContentItem[] {
    if (this.selectedType === 'all') return this.results;
    return this.results.filter((r) => r.contentType === this.selectedType);
  }

  filterByType(type: string): void {
    this.selectedType = type;
  }

  navigateToDetail(id: string): void {
    this.router.navigate(['/store/content', id]);
  }

  private loadResults(): void {
    // Mock 数据
    this.results = [
      { id: 'c1', title: 'Python 游戏开发入门', description: '学习使用 Pygame 开发经典小游戏', price: 0, rating: 4.8, contentType: 'course', category: '编程开发', isFree: true },
      { id: 'c2', title: 'Arduino 传感器实战', description: '动手搭建10个传感器项目', price: 49.9, rating: 4.6, contentType: 'course', category: '硬件', isFree: false },
      { id: 'r1', title: 'Python 速查表', description: 'Python 常用语法速查手册', price: 0, rating: 4.9, contentType: 'resource', category: '编程开发', isFree: true },
      { id: 't1', title: 'Blockly 项目模板', description: '5个Blockly创意项目模板', price: 9.9, rating: 4.3, contentType: 'template', category: '编程开发', isFree: false },
    ];
  }
}
