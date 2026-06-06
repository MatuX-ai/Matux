/**
 * 仪表盘自定义布局服务
 *
 * 管理仪表盘各区块的可见性、顺序，支持持久化到 localStorage
 */
import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface DashboardWidget {
  id: string;
  label: string;
  icon: string;
  visible: boolean;
  order: number;
}

const DEFAULT_WIDGETS: DashboardWidget[] = [
  { id: 'stats', label: '统计卡片', icon: 'bar_chart', visible: true, order: 0 },
  { id: 'learning_sources', label: '学习来源', icon: 'hub', visible: true, order: 1 },
  {
    id: 'source_details',
    label: '学习来源详情',
    icon: 'account_balance',
    visible: false,
    order: 2,
  },
  { id: 'heatmap', label: '学习日历热力图', icon: 'calendar_month', visible: true, order: 3 },
  { id: 'achievements', label: '成就墙', icon: 'emoji_events', visible: true, order: 4 },
  { id: 'enrolled_courses', label: '正在学习', icon: 'menu_book', visible: true, order: 5 },
  { id: 'recommended_courses', label: '推荐课程', icon: 'explore', visible: true, order: 6 },
  { id: 'materials', label: '课件库', icon: 'folder', visible: true, order: 7 },
];

const STORAGE_KEY = 'imato_dashboard_layout';

@Injectable({ providedIn: 'root' })
export class DashboardLayoutService {
  private widgetsSubject = new BehaviorSubject<DashboardWidget[]>(this.loadWidgets());
  public widgets$ = this.widgetsSubject.asObservable();

  /** 获取所有组件 */
  getWidgets(): DashboardWidget[] {
    return this.widgetsSubject.value;
  }

  /** 获取可见组件（按 order 排序） */
  getVisibleWidgets(): DashboardWidget[] {
    return this.widgetsSubject.value.filter((w) => w.visible).sort((a, b) => a.order - b.order);
  }

  /** 判断组件是否可见 */
  isVisible(widgetId: string): boolean {
    return this.widgetsSubject.value.find((w) => w.id === widgetId)?.visible ?? true;
  }

  /** 更新组件列表（拖拽排序后调用） */
  updateWidgets(widgets: DashboardWidget[]): void {
    this.widgetsSubject.next(widgets);
    this.saveWidgets(widgets);
  }

  /** 切换可见性 */
  toggleWidget(widgetId: string): void {
    const widgets = this.getWidgets().map((w) =>
      w.id === widgetId ? { ...w, visible: !w.visible } : w
    );
    this.updateWidgets(widgets);
  }

  /** 重置为默认布局 */
  resetToDefault(): void {
    this.updateWidgets(DEFAULT_WIDGETS.map((w) => ({ ...w })));
  }

  private loadWidgets(): DashboardWidget[] {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved) as DashboardWidget[];
        // 补全新增的 widget（当默认列表中有新条目时）
        const merged = DEFAULT_WIDGETS.map((def) => {
          const existing = parsed.find((p) => p.id === def.id);
          return existing ?? def;
        });
        return merged;
      }
    } catch {
      /* ignore */
    }
    return DEFAULT_WIDGETS.map((w) => ({ ...w }));
  }

  private saveWidgets(widgets: DashboardWidget[]): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(widgets));
    } catch {
      /* ignore */
    }
  }
}
