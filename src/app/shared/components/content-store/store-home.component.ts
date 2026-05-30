import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';

// 模拟数据模型
interface ContentItem {
  id: string;
  title: string;
  description: string;
  price: number;
  originalPrice?: number;
  rating: number;
  reviewCount: number;
  imageUrl: string;
  contentType: 'course' | 'resource' | 'template';
  category: string;
  isFree: boolean;
  isFeatured: boolean;
  subscriptionLevel: 'free' | 'basic' | 'professional' | 'enterprise';
}

interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  billingCycle: string;
  features: string[];
  isPopular: boolean;
  level: 'basic' | 'professional' | 'enterprise';
}

@Component({
  selector: 'app-store-home',
  template: `
    <div class="store-container">
      <!-- 顶部横幅 -->
      <div class="hero-banner">
        <div class="banner-content">
          <h1>专业内容商店</h1>
          <p>发现高质量的学习资源和专业工具</p>
          <div class="search-box">
            <input
              type="text"
              placeholder="搜索课程、资源或模板..."
              [(ngModel)]="searchQuery"
              (keyup.enter)="searchContent()"
              class="search-input"
            />
            <button mat-raised-button color="primary" (click)="searchContent()">
              <mat-icon>search</mat-icon>
              搜索
            </button>
          </div>
        </div>
      </div>

      <!-- 订阅计划展示 -->
      <section class="subscription-section" *ngIf="subscriptionPlans.length > 0">
        <h2>选择您的订阅计划</h2>
        <div class="plans-grid">
          <div
            *ngFor="let plan of subscriptionPlans"
            class="plan-card"
            [class.popular]="plan.isPopular"
            (click)="selectPlan(plan)"
          >
            <div class="plan-header">
              <h3>{{ plan.name }}</h3>
              <div class="price">
                <span class="amount">¥{{ plan.price }}</span>
                <span class="cycle">/{{ plan.billingCycle }}</span>
              </div>
              <div *ngIf="plan.isPopular" class="popular-badge">推荐</div>
            </div>
            <ul class="features">
              <li *ngFor="let feature of plan.features">{{ feature }}</li>
            </ul>
            <button
              mat-raised-button
              [color]="plan.isPopular ? 'primary' : 'accent'"
              class="subscribe-btn"
            >
              立即订阅
            </button>
          </div>
        </div>
      </section>

      <!-- 特色内容 -->
      <section class="featured-section" *ngIf="featuredContents.length > 0">
        <div class="section-header">
          <h2>精选内容</h2>
          <button mat-button (click)="viewAllFeatured()">查看全部</button>
        </div>
        <div class="content-grid">
          <div
            *ngFor="let content of featuredContents"
            class="content-card"
            (click)="viewContent(content)"
          >
            <div class="card-image">
              <img [src]="content.imageUrl" [alt]="content.title" />
              <div class="content-type-badge">{{ getContentTypeName(content.contentType) }}</div>
              <div *ngIf="content.isFree" class="free-badge">免费</div>
            </div>
            <div class="card-content">
              <h3>{{ content.title }}</h3>
              <p>{{ content.description }}</p>
              <div class="card-footer">
                <div class="rating">
                  <mat-icon
                    *ngFor="let star of getStars(content.rating)"
                    class="star"
                    [class.filled]="star <= content.rating"
                  >
                    star
                  </mat-icon>
                  <span class="review-count">({{ content.reviewCount }})</span>
                </div>
                <div class="price-section">
                  <span
                    *ngIf="content.originalPrice && content.originalPrice > content.price"
                    class="original-price"
                    >¥{{ content.originalPrice }}</span
                  >
                  <span class="price" [class.free]="content.isFree">
                    {{ content.isFree ? '免费' : '¥' + content.price }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 分类浏览 -->
      <section class="categories-section">
        <h2>按分类浏览</h2>
        <div class="categories-grid">
          <div
            *ngFor="let category of categories"
            class="category-card"
            (click)="browseByCategory(category)"
          >
            <mat-icon>{{ category.icon }}</mat-icon>
            <h3>{{ category.name }}</h3>
            <p>{{ category.count }} 个资源</p>
          </div>
        </div>
      </section>

      <!-- 推荐内容 -->
      <section class="recommendations-section" *ngIf="recommendedContents.length > 0">
        <div class="section-header">
          <h2>为您推荐</h2>
          <button mat-button (click)="refreshRecommendations()">换一批</button>
        </div>
        <div class="recommendations-slider">
          <div
            *ngFor="let content of recommendedContents; let i = index"
            class="recommendation-card"
            [style.transform]="'translateX(' + currentIndex * -320 + 'px)'"
            (click)="viewContent(content)"
          >
            <div class="rec-image">
              <img [src]="content.imageUrl" [alt]="content.title" />
            </div>
            <div class="rec-content">
              <h4>{{ content.title }}</h4>
              <div class="rec-meta">
                <span class="level">{{ getSubscriptionLevelName(content.subscriptionLevel) }}</span>
                <span class="rating-small">★ {{ content.rating }}</span>
              </div>
              <div class="rec-price">
                {{ content.isFree ? '免费' : '¥' + content.price }}
              </div>
            </div>
          </div>
        </div>
        <div class="slider-nav">
          <button mat-icon-button (click)="prevRecommendation()" [disabled]="currentIndex <= 0">
            <mat-icon>chevron_left</mat-icon>
          </button>
          <button
            mat-icon-button
            (click)="nextRecommendation()"
            [disabled]="currentIndex >= recommendedContents.length - 3"
          >
            <mat-icon>chevron_right</mat-icon>
          </button>
        </div>
      </section>
    </div>
  `,
  styles: [
    `
      .store-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
      }

      .hero-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 60px 40px;
        border-radius: 12px;
        margin-bottom: 40px;
        text-align: center;
      }

      .banner-content h1 {
        font-size: 2.5rem;
        margin-bottom: 16px;
      }

      .banner-content p {
        font-size: 1.2rem;
        margin-bottom: 32px;
        opacity: 0.9;
      }

      .search-box {
        display: flex;
        gap: 16px;
        max-width: 600px;
        margin: 0 auto;
      }

      .search-input {
        flex: 1;
        padding: 16px;
        border-radius: 8px;
        border: none;
        font-size: 16px;
      }

      .plans-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 24px;
        margin: 32px 0;
      }

      .plan-card {
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 24px;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
      }

      .plan-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
      }

      .plan-card.popular {
        border-color: #667eea;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2);
      }

      .popular-badge {
        position: absolute;
        top: -12px;
        right: 24px;
        background: #667eea;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
      }

      .content-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 24px;
        margin: 32px 0;
      }

      .content-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        overflow: hidden;
        cursor: pointer;
        transition: all 0.3s ease;
      }

      .content-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
      }

      .card-image {
        position: relative;
        height: 180px;
        overflow: hidden;
      }

      .card-image img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .content-type-badge {
        position: absolute;
        top: 12px;
        left: 12px;
        background: rgba(0, 0, 0, 0.7);
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
      }

      .free-badge {
        position: absolute;
        top: 12px;
        right: 12px;
        background: #4caf50;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
      }

      .recommendations-slider {
        display: flex;
        overflow: hidden;
        margin: 32px 0;
        position: relative;
      }

      .recommendation-card {
        min-width: 300px;
        margin-right: 20px;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        overflow: hidden;
        cursor: pointer;
        transition: all 0.3s ease;
      }

      .star {
        color: #ddd;
      }

      .star.filled {
        color: #ffc107;
      }

      .price.free {
        color: #4caf50;
        font-weight: bold;
      }

      .original-price {
        text-decoration: line-through;
        color: #999;
        margin-right: 8px;
      }
    `,
  ],
  imports: [CommonModule, FormsModule, MatIconModule, MatButtonModule],
})
export class StoreHomeComponent implements OnInit {
  searchQuery: string = '';
  featuredContents: ContentItem[] = [];
  recommendedContents: ContentItem[] = [];
  subscriptionPlans: SubscriptionPlan[] = [];
  categories = [
    { name: '编程开发', icon: 'code', count: 128 },
    { name: '数据分析', icon: 'bar_chart', count: 89 },
    { name: '人工智能', icon: 'auto_awesome', count: 156 },
    { name: '设计创意', icon: 'palette', count: 74 },
    { name: '办公效率', icon: 'work', count: 63 },
    { name: '语言学习', icon: 'translate', count: 42 },
  ];
  currentIndex = 0;

  constructor(
    private router: Router,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadSubscriptionPlans();
    this.loadFeaturedContents();
    this.loadRecommendations();
  }

  loadSubscriptionPlans(): void {
    // 模拟加载订阅计划
    this.subscriptionPlans = [
      {
        id: 'basic',
        name: '基础版',
        price: 29.9,
        billingCycle: '月',
        features: ['访问基础课程', '下载学习资料', '社区讨论'],
        isPopular: false,
        level: 'basic',
      },
      {
        id: 'professional',
        name: '专业版',
        price: 99.9,
        billingCycle: '月',
        features: ['所有基础功能', '高级课程', '一对一指导', '项目实战'],
        isPopular: true,
        level: 'professional',
      },
      {
        id: 'enterprise',
        name: '企业版',
        price: 299.9,
        billingCycle: '月',
        features: ['所有专业功能', '团队管理', '定制培训', 'API访问'],
        isPopular: false,
        level: 'enterprise',
      },
    ];
  }

  loadFeaturedContents(): void {
    // 模拟加载特色内容
    this.featuredContents = [
      {
        id: '1',
        title: 'Python全栈开发实战',
        description: '从零开始学习Python全栈开发，涵盖Web、数据分析、AI等多个领域',
        price: 199,
        originalPrice: 299,
        rating: 4.8,
        reviewCount: 1234,
        imageUrl: 'assets/images/python-course.jpg',
        contentType: 'course',
        category: '编程开发',
        isFree: false,
        isFeatured: true,
        subscriptionLevel: 'professional',
      },
      {
        id: '2',
        title: '数据可视化模板包',
        description: '包含50+专业的数据可视化模板，适用于各类商业场景',
        price: 0,
        rating: 4.6,
        reviewCount: 856,
        imageUrl: 'assets/images/data-viz.jpg',
        contentType: 'template',
        category: '数据分析',
        isFree: true,
        isFeatured: true,
        subscriptionLevel: 'free',
      },
    ];
  }

  loadRecommendations(): void {
    // 模拟加载推荐内容
    this.recommendedContents = [
      // 更多推荐内容...
    ];
  }

  searchContent(): void {
    if (this.searchQuery.trim()) {
      void this.router.navigate(['/store/search'], {
        queryParams: { q: this.searchQuery },
      });
    }
  }

  selectPlan(plan: SubscriptionPlan): void {
    void this.router.navigate(['/subscription/plans', plan.id]);
  }

  viewContent(content: ContentItem): void {
    void this.router.navigate(['/store/content', content.id]);
  }

  viewAllFeatured(): void {
    void this.router.navigate(['/store/featured']);
  }

  browseByCategory(category: { name: string }): void {
    void this.router.navigate(['/store/category', category.name]);
  }

  refreshRecommendations(): void {
    this.loadRecommendations();
    this.snackBar.open('已刷新推荐内容', '', { duration: 2000 });
  }

  prevRecommendation(): void {
    if (this.currentIndex > 0) {
      this.currentIndex--;
    }
  }

  nextRecommendation(): void {
    if (this.currentIndex < this.recommendedContents.length - 3) {
      this.currentIndex++;
    }
  }

  getContentTypeName(type: string): string {
    const typeMap: Record<string, string> = {
      course: '课程',
      resource: '资源',
      template: '模板',
    };
    return typeMap[type] || type;
  }

  getSubscriptionLevelName(level: string): string {
    const levelMap: Record<string, string> = {
      free: '免费',
      basic: '基础版',
      professional: '专业版',
      enterprise: '企业版',
    };
    return levelMap[level] || level;
  }

  getStars(_rating: number): number[] {
    return Array(5)
      .fill(0)
      .map((_, i) => i + 1);
  }
}
