/**
 * 插件商店主页面组件
 * 
 * 功能:
 * 1. 插件列表展示
 * 2. 搜索和过滤
 * 3. 分类导航
 * 4. 兼容性过滤
 * 5. 插件卡片网格
 */

import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatChipsModule } from '@angular/material/chips';
import { MatTabsModule } from '@angular/material/tabs';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, takeUntil } from 'rxjs/operators';

import { PluginStoreService, PluginListItem, PluginStats } from '../../core/services/plugin-store.service';
import { PluginCardComponent } from '../../shared/components/plugin-card/plugin-card.component';

// Phase 5 新组件
import { PluginRecommendationsComponent } from '../../shared/components/plugin-recommendations/plugin-recommendations.component';
import { FirstRunGuideComponent } from '../../shared/components/first-run-guide/first-run-guide.component';
import { PluginReviewsComponent } from '../../shared/components/plugin-reviews/plugin-reviews.component';
import { PluginUsageStatsComponent } from '../../shared/components/plugin-usage-stats/plugin-usage-stats.component';
import { PluginUpdatesComponent } from '../../shared/components/plugin-updates/plugin-updates.component';

@Component({
  selector: 'app-plugin-store',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    MatIconModule,
    MatButtonModule,
    MatInputModule,
    MatFormFieldModule,
    MatChipsModule,
    MatTabsModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    MatSnackBarModule,
    PluginCardComponent,
    // Phase 5 新组件
    PluginRecommendationsComponent,
    FirstRunGuideComponent,
    PluginReviewsComponent,
    PluginUsageStatsComponent,
    PluginUpdatesComponent,
  ],
  templateUrl: './plugin-store.component.html',
  styleUrls: ['./plugin-store.component.scss'],
})
export class PluginStoreComponent implements OnInit, OnDestroy {
  // 数据
  plugins: PluginListItem[] = [];
  filteredPlugins: PluginListItem[] = [];
  stats: PluginStats | null = null;
  loading = true;
  error: string | null = null;
  
  // 搜索和过滤
  searchQuery = '';
  selectedCategory: string | null = null;
  compatibleOnly = false;
  selectedTab = 'all'; // all, installed, compatible
  
  // Phase 5: 首次运行引导
  showFirstRunGuide = false;
  
  // Phase 5: 选中的插件（用于显示评论和统计）
  selectedPluginId: string | null = null;
  showPluginDetails = false;
  
  // 分类列表
  categories = [
    { id: 'ai-assistant', name: 'AI 助手', icon: 'smart_toy' },
    { id: 'ar-vr-lab', name: 'AR/VR 实验室', icon: 'view_in_ar' },
    { id: 'coding-tools', name: '编程工具', icon: 'code' },
    { id: 'data-analysis', name: '数据分析', icon: 'analytics' },
    { id: 'education', name: '教育', icon: 'school' },
    { id: 'gamification', name: '游戏化', icon: 'casino' },
    { id: 'hardware', name: '硬件', icon: 'memory' },
    { id: 'ml-training', name: '机器学习', icon: 'model_training' },
    { id: 'visualization', name: '可视化', icon: 'bar_chart' },
    { id: 'productivity', name: '效率工具', icon: 'bolt' },
  ];
  
  private searchSubject = new Subject<string>();
  private destroy$ = new Subject<void>();
  
  constructor(
    private pluginService: PluginStoreService,
    private snackBar: MatSnackBar,
  ) {}
  
  ngOnInit(): void {
    this.loadPlugins();
    this.loadStats();
    this.setupSearch();
    this.checkFirstRun(); // Phase 5: 检查首次运行
  }
  
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
  
  /**
   * 加载插件列表
   */
  async loadPlugins(): Promise<void> {
    this.loading = true;
    this.error = null;
    
    try {
      const options: any = {};
      
      if (this.selectedTab === 'installed') {
        options.state = 'enabled';
      } else if (this.selectedTab === 'compatible') {
        options.compatibleOnly = true;
      }
      
      if (this.selectedCategory) {
        options.category = this.selectedCategory;
      }
      
      this.plugins = await this.pluginService.getPlugins(options).toPromise();
      this.applyFilters();
    } catch (err) {
      this.error = `加载插件列表失败: ${(err as Error).message}`;
      this.snackBar.open(this.error, '关闭', { duration: 5000 });
    } finally {
      this.loading = false;
    }
  }
  
  /**
   * 加载统计信息
   */
  async loadStats(): Promise<void> {
    try {
      this.stats = await this.pluginService.getPluginStats().toPromise();
    } catch (err) {
      console.warn('加载统计信息失败:', err);
    }
  }
  
  /**
   * 设置搜索
   */
  setupSearch(): void {
    this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      takeUntil(this.destroy$),
    ).subscribe(query => {
      this.searchQuery = query;
      this.applyFilters();
    });
  }
  
  /**
   * 搜索输入
   */
  onSearchInput(value: string): void {
    this.searchSubject.next(value);
  }
  
  /**
   * 应用过滤
   */
  applyFilters(): void {
    let result = [...this.plugins];
    
    // 搜索过滤
    if (this.searchQuery.trim()) {
      const query = this.searchQuery.toLowerCase();
      result = result.filter(plugin =>
        plugin.name.toLowerCase().includes(query) ||
        plugin.description.toLowerCase().includes(query) ||
        plugin.author.toLowerCase().includes(query)
      );
    }
    
    // 分类过滤
    if (this.selectedCategory) {
      result = result.filter(plugin =>
        plugin.categories.includes(this.selectedCategory!)
      );
    }
    
    // 兼容性过滤
    if (this.compatibleOnly) {
      result = result.filter(plugin => plugin.compatible === true);
    }
    
    this.filteredPlugins = result;
  }
  
  /**
   * 切换分类
   */
  selectCategory(categoryId: string | null): void {
    this.selectedCategory = categoryId;
    this.loadPlugins();
  }
  
  /**
   * 切换标签页
   */
  onTabChange(event: any): void {
    const tabs = ['all', 'installed', 'compatible'];
    this.selectedTab = tabs[event.index] || 'all';
    this.loadPlugins();
  }
  
  /**
   * 切换兼容性过滤
   */
  toggleCompatibleOnly(): void {
    this.compatibleOnly = !this.compatibleOnly;
    this.loadPlugins();
  }
  
  /**
   * 清除搜索
   */
  clearSearch(): void {
    this.searchQuery = '';
    this.applyFilters();
  }
  
  /**
   * 刷新列表
   */
  async refresh(): Promise<void> {
    await this.loadPlugins();
    await this.loadStats();
    this.snackBar.open('插件列表已刷新', '关闭', { duration: 2000 });
  }
  
  /**
   * 获取插件数量
   */
  getPluginCount(): number {
    return this.filteredPlugins.length;
  }
  
  /**
   * 获取已安装数量
   */
  getInstalledCount(): number {
    return this.stats?.total_installed || 0;
  }
  
  /**
   * 获取已启用数量
   */
  getEnabledCount(): number {
    return this.stats?.total_enabled || 0;
  }
  
  // ==================== Phase 5 方法 ====================
  
  /**
   * 检查是否首次运行
   */
  async checkFirstRun(): Promise<void> {
    try {
      if (!window.pluginAPI) {
        console.warn('Plugin API 不可用');
        return;
      }
      
      const result = await (window.pluginAPI as any).isFirstRunCompleted();
      if (result.success && !result.data) {
        this.showFirstRunGuide = true;
      }
    } catch (err) {
      console.error('检查首次运行失败:', err);
    }
  }
  
  /**
   * 首次引导完成
   */
  onFirstRunComplete(): void {
    this.showFirstRunGuide = false;
    this.snackBar.open('欢迎使用 iMato！', '关闭', { duration: 3000 });
    // 刷新插件列表
    this.loadPlugins();
    this.loadStats();
  }
  
  /**
   * 选中插件（显示详情）
   */
  selectPlugin(pluginId: string): void {
    this.selectedPluginId = pluginId;
    this.showPluginDetails = true;
  }
  
  /**
   * 关闭插件详情
   */
  closePluginDetails(): void {
    this.showPluginDetails = false;
    this.selectedPluginId = null;
  }
}
