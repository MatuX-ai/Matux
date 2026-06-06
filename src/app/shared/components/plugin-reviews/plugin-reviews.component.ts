/**
 * 插件评分和评论组件
 * 
 * 功能:
 * 1. 显示平均评分和评分分布
 * 2. 评论列表展示（排序、分页）
 * 3. 添加新评论
 * 4. 标记评论为有帮助
 */

import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatChipsModule } from '@angular/material/chips';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface Review {
  id: string;
  pluginId: string;
  userId: string;
  userName: string;
  rating: number;
  title: string;
  content: string;
  pros: string[];
  cons: string[];
  createdAt: string;
  helpfulCount: number;
  verified: boolean;
}

interface RatingStats {
  average: number;
  count: number;
  distribution: { [key: number]: number };
}

@Component({
  selector: 'app-plugin-reviews',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatIconModule,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatChipsModule,
  ],
  templateUrl: './plugin-reviews.component.html',
  styleUrls: ['./plugin-reviews.component.scss'],
})
export class PluginReviewsComponent implements OnInit, OnDestroy {
  @Input() pluginId = '';
  
  // 数据
  reviews: Review[] = [];
  ratingStats: RatingStats | null = null;
  loading = true;
  error: string | null = null;
  
  // 排序和分页
  sortBy = 'createdAt';
  sortOrder: 'asc' | 'desc' = 'desc';
  currentPage = 0;
  pageSize = 10;
  
  // 添加评论
  showAddForm = false;
  newRating = 5;
  newTitle = '';
  newContent = '';
  newPros: string[] = [];
  newCons: string[] = [];
  newProInput = '';
  newConInput = '';
  
  private destroy$ = new Subject<void>();
  
  constructor(private snackBar: MatSnackBar) {}
  
  ngOnInit(): void {
    if (this.pluginId) {
      this.loadReviews();
      this.loadRatingStats();
    }
  }
  
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
  
  /**
   * 加载评论列表
   */
  async loadReviews(): Promise<void> {
    this.loading = true;
    this.error = null;
    
    try {
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用');
      }
      
      const result = await window.pluginAPI.getPluginReviews(this.pluginId, {
        sortBy: this.sortBy,
        sortOrder: this.sortOrder,
        limit: this.pageSize,
        offset: this.currentPage * this.pageSize,
      });
      
      if (result.success && result.data) {
        this.reviews = result.data;
      }
    } catch (err) {
      this.error = (err as Error).message;
      console.error('加载评论失败:', err);
    } finally {
      this.loading = false;
    }
  }
  
  /**
   * 加载评分统计
   */
  async loadRatingStats(): Promise<void> {
    try {
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用');
      }
      
      const result = await window.pluginAPI.getPluginAverageRating(this.pluginId);
      if (result.success && result.data) {
        this.ratingStats = result.data;
      }
    } catch (err) {
      console.error('加载评分统计失败:', err);
    }
  }
  
  /**
   * 提交新评论
   */
  async submitReview(): Promise<void> {
    try {
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用');
      }
      
      if (!this.newTitle.trim() || !this.newContent.trim()) {
        this.snackBar.open('请填写标题和内容', '关闭', { duration: 2000 });
        return;
      }
      
      const result = await window.pluginAPI.addPluginReview({
        pluginId: this.pluginId,
        userId: 'current_user', // 从认证服务获取
        userName: '当前用户',
        rating: this.newRating,
        title: this.newTitle,
        content: this.newContent,
        pros: this.newPros,
        cons: this.newCons,
      });
      
      if (result.success) {
        this.snackBar.open('评论已提交', '关闭', { duration: 2000 });
        this.closeAddForm();
        await this.loadReviews();
        await this.loadRatingStats();
      }
    } catch (err) {
      this.snackBar.open(`提交失败: ${(err as Error).message}`, '关闭', {
        duration: 5000,
      });
    }
  }
  
  /**
   * 标记评论为有帮助
   */
  async markHelpful(reviewId: string): Promise<void> {
    try {
      if (!window.pluginAPI) {
        throw new Error('Plugin API 不可用');
      }
      
      const result = await window.pluginAPI.markReviewHelpful(reviewId, this.pluginId);
      if (result.success) {
        // 更新本地数据
        const review = this.reviews.find(r => r.id === reviewId);
        if (review) {
          review.helpfulCount++;
        }
        this.snackBar.open('已标记为有帮助', '关闭', { duration: 2000 });
      }
    } catch (err) {
      this.snackBar.open(`操作失败: ${(err as Error).message}`, '关闭', {
        duration: 3000,
      });
    }
  }
  
  /**
   * 排序变化
   */
  onSortChange(): void {
    this.currentPage = 0;
    this.loadReviews();
  }
  
  /**
   * 上一页
   */
  prevPage(): void {
    if (this.currentPage > 0) {
      this.currentPage--;
      this.loadReviews();
    }
  }
  
  /**
   * 下一页
   */
  nextPage(): void {
    if (this.reviews.length === this.pageSize) {
      this.currentPage++;
      this.loadReviews();
    }
  }
  
  /**
   * 显示添加表单
   */
  openAddForm(): void {
    this.showAddForm = true;
    this.newRating = 5;
    this.newTitle = '';
    this.newContent = '';
    this.newPros = [];
    this.newCons = [];
  }
  
  /**
   * 关闭添加表单
   */
  closeAddForm(): void {
    this.showAddForm = false;
    this.newRating = 5;
    this.newTitle = '';
    this.newContent = '';
    this.newPros = [];
    this.newCons = [];
    this.newProInput = '';
    this.newConInput = '';
  }
  
  /**
   * 添加优点
   */
  addPro(): void {
    if (this.newProInput.trim()) {
      this.newPros.push(this.newProInput.trim());
      this.newProInput = '';
    }
  }
  
  /**
   * 添加缺点
   */
  addCon(): void {
    if (this.newConInput.trim()) {
      this.newCons.push(this.newConInput.trim());
      this.newConInput = '';
    }
  }
  
  /**
   * 移除优点
   */
  removePro(index: number): void {
    this.newPros.splice(index, 1);
  }
  
  /**
   * 移除缺点
   */
  removeCon(index: number): void {
    this.newCons.splice(index, 1);
  }
  
  /**
   * 获取评分百分比
   */
  getRatingPercentage(star: number): number {
    if (!this.ratingStats || this.ratingStats.count === 0) return 0;
    return (this.ratingStats.distribution[star] || 0) / this.ratingStats.count * 100;
  }
  
  /**
   * 获取星级图标
   */
  getStarIcon(rating: number): string {
    if (rating >= 4.5) return 'star';
    if (rating >= 3.5) return 'star_half';
    return 'star_border';
  }
  
  /**
   * 格式化日期
   */
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return '今天';
    if (days === 1) return '昨天';
    if (days < 7) return `${days} 天前`;
    if (days < 30) return `${Math.floor(days / 7)} 周前`;
    if (days < 365) return `${Math.floor(days / 30)} 个月前`;
    return `${Math.floor(days / 365)} 年前`;
  }
}
