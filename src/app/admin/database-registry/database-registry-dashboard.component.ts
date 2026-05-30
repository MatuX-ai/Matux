import { Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';

// Services
import {
  DatabaseRegistryService,
  RegistryHealth,
  RegistryStats,
} from './services/database-registry.service';

@Component({
  selector: 'app-database-registry-dashboard',
  standalone: false,
  templateUrl: './database-registry-dashboard.component.html',
  styleUrls: ['./database-registry-dashboard.component.scss'],
})
export class DatabaseRegistryDashboardComponent implements OnInit, OnDestroy {
  stats: RegistryStats | null = null;
  health: RegistryHealth | null = null;
  loading = true;
  error: string | null = null;

  private subscriptions = new Subscription();

  constructor(
    private registryService: DatabaseRegistryService,
    private router: Router,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.loadDashboardData();

    // 定期刷新数据
    const refreshSub = this.registryService.refreshInterval().subscribe(() => {
      this.loadDashboardData();
    });
    this.subscriptions.add(refreshSub);
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  private loadDashboardData(): void {
    this.loading = true;
    this.error = null;

    // 并行加载统计信息和健康状态
    Promise.all([
      this.registryService.getRegistryStats().toPromise(),
      this.registryService.getRegistryHealth().toPromise(),
    ])
      .then(([stats, health]) => {
        this.stats = stats ?? null;
        this.health = health ?? null;
        this.loading = false;
      })
      .catch((error) => {
        console.error('Failed to load dashboard data:', error);
        this.error = '加载数据失败，请稍后重试';
        this.loading = false;
      });
  }

  navigateToModules(): void {
    void this.router.navigate(['modules'], { relativeTo: this.route });
  }

  navigateToStats(): void {
    void this.router.navigate(['stats'], { relativeTo: this.route });
  }

  refreshData(): void {
    this.loadDashboardData();
  }

  getStatusColor(health: RegistryHealth | null): string {
    if (!health) return 'warn';
    switch (health.registry_status) {
      case 'healthy':
        return 'primary';
      case 'degraded':
        return 'warn';
      case 'uninitialized':
        return 'warn';
      default:
        return 'warn';
    }
  }

  getCategoryCount(category: string): number {
    if (!this.stats?.modules_by_category) return 0;
    return this.stats.modules_by_category[category]?.length || 0;
  }

  // 添加缺失的 getter 方法 - 直接访问 registry_stats 嵌套对象
  get total_modules(): number {
    return this.stats?.registry_stats?.total_modules ?? 0;
  }

  get active_modules(): number {
    return this.stats?.registry_stats?.active_modules ?? 0;
  }

  get inactive_modules(): number {
    return this.stats?.registry_stats?.inactive_modules ?? 0;
  }

  getTopCategories(): Array<{ name: string; count: number }> {
    if (!this.stats?.modules_by_category) return [];
    return Object.entries(this.stats.modules_by_category)
      .map(([name, modules]) => ({ name, count: modules.length }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  }

  getInitializedCount(): number {
    if (!this.health?.modules_status) return 0;
    return this.health.modules_status.filter((m) => m.initialized).length;
  }

  getActiveCount(): number {
    if (!this.health?.modules_status) return 0;
    return this.health.modules_status.filter((m) => m.active).length;
  }
}
