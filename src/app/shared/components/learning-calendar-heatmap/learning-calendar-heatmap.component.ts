/**
 * 学习日历热力图组件
 *
 * 基于 ECharts 展示学习活跃度的日历热力图
 * 桌面端适配：支持大屏渲染、键盘导航
 */
import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';

/** 每日学习记录 */
export interface DailyLearningRecord {
  date: string; // YYYY-MM-DD
  minutes: number; // 学习时长（分钟）
  courses: number; // 参与课程数
  quizzes: number; // 完成测验数
  score?: number; // 平均得分
}

/** 日历热力图配置 */
export interface CalendarHeatmapConfig {
  year: number;
  data: DailyLearningRecord[];
  loading?: boolean;
  emptyMessage?: string;
  maxValue?: number; // 色阶最大值（分钟），默认 240
}

@Component({
  selector: 'app-learning-calendar-heatmap',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
  ],
  template: `
    <mat-card class="heatmap-card">
      <mat-card-header>
        <mat-card-title>
          <mat-icon>calendar_month</mat-icon>
          学习日历
        </mat-card-title>
        <div class="year-nav">
          <button mat-icon-button (click)="prevYear()" matTooltip="上一年">
            <mat-icon>chevron_left</mat-icon>
          </button>
          <span class="year-display">{{ config?.year }}</span>
          <button mat-icon-button (click)="nextYear()" matTooltip="下一年">
            <mat-icon>chevron_right</mat-icon>
          </button>
        </div>
      </mat-card-header>
      <mat-card-content>
        <!-- 加载状态 -->
        <div class="loading-state" *ngIf="config?.loading">
          <mat-progress-spinner diameter="32" mode="indeterminate"></mat-progress-spinner>
          <span>加载中...</span>
        </div>

        <!-- 空状态 -->
        <div class="empty-state" *ngIf="!config?.loading && isEmpty">
          <mat-icon>event_busy</mat-icon>
          <p>{{ config?.emptyMessage || '暂无学习记录' }}</p>
        </div>

        <!-- 选中日期的详情面板 -->
        <div class="selected-day-panel" *ngIf="selectedRecord && !config?.loading && !isEmpty">
          <div class="selected-date">
            <strong>{{ selectedRecord.date }}</strong>
          </div>
          <div class="selected-stats">
            <span class="sel-stat">
              <mat-icon>timer</mat-icon> {{ selectedRecord.minutes }}分钟
            </span>
            <span class="sel-stat" *ngIf="selectedRecord.courses > 0">
              <mat-icon>school</mat-icon> {{ selectedRecord.courses }}门课
            </span>
            <span class="sel-stat" *ngIf="selectedRecord.quizzes > 0">
              <mat-icon>quiz</mat-icon> {{ selectedRecord.quizzes }}次测验
            </span>
            <span class="sel-stat" *ngIf="selectedRecord.score != null">
              <mat-icon>score</mat-icon> {{ selectedRecord.score }}分
            </span>
          </div>
          <button mat-icon-button class="close-sel" (click)="clearSelection()">
            <mat-icon>close</mat-icon>
          </button>
        </div>

        <!-- 月度统计条 -->
        <div class="monthly-bars" *ngIf="!config?.loading && !isEmpty">
          <div
            *ngFor="let m of monthlyStats"
            class="month-bar-item"
            [matTooltip]="m.label + ': ' + m.minutes + '分钟'"
          >
            <div class="month-bar" [style.height.px]="getMonthlyBarHeight(m)"></div>
            <span class="month-bar-label">{{ m.shortLabel }}</span>
          </div>
        </div>

        <!-- 图例 -->
        <div class="heatmap-legend" *ngIf="!config?.loading && !isEmpty">
          <span class="legend-label">学习时长（分钟）</span>
          <div class="legend-colors">
            <span
              class="legend-item"
              *ngFor="let level of legendLevels; let i = index"
              [style.background]="getColorForMinutes(level.value)"
            >
            </span>
          </div>
          <span class="legend-label"
            >{{ legendLevels[0].value || 0 }} -
            {{ legendLevels[legendLevels.length - 1].value || 240 }}分</span
          >
          <span class="legend-spacer"></span>
          <span class="legend-summary"
            >年均 <strong>{{ yearlyAvgMinutes }}</strong> 分钟/日</span
          >
        </div>

        <!-- 热力图网格 -->
        <div class="heatmap-grid" *ngIf="!config?.loading && !isEmpty">
          <!-- 月份标签 -->
          <div class="month-labels">
            <span *ngFor="let month of months" class="month-label">{{ month }}</span>
          </div>
          <!-- 周标签 + 方格 -->
          <div class="heatmap-body">
            <div class="week-labels">
              <span class="week-label">一</span>
              <span class="week-label">三</span>
              <span class="week-label">五</span>
            </div>
            <div class="heatmap-cells" #cellsContainer>
              <div
                *ngFor="let cell of calendarCells; trackBy: trackByIndex"
                class="heatmap-cell"
                [style.background]="getCellColor(cell)"
                [matTooltip]="getCellTooltip(cell)"
                [class.has-data]="cell.value > 0"
                [class.selected]="isSelectedCell(cell)"
                [attr.data-date]="cell.date"
                (click)="onCellClick(cell)"
                (keydown.enter)="onCellClick(cell)"
                tabindex="0"
                role="gridcell"
                [attr.aria-label]="getCellTooltip(cell)"
              ></div>
            </div>
          </div>
        </div>
      </mat-card-content>
    </mat-card>
  `,
  styles: [
    `
      :host {
        display: block;
      }

      .heatmap-card {
        mat-card-header {
          margin-bottom: 16px;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        mat-card-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 18px;
        }
      }

      /* 年份导航 */
      .year-nav {
        display: flex;
        align-items: center;
        gap: 4px;
      }
      .year-display {
        font-size: 16px;
        font-weight: 600;
        min-width: 48px;
        text-align: center;
        color: #334155;
      }

      /* 选中日详情面板 */
      .selected-day-panel {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 12px;
        margin-bottom: 12px;
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        border-radius: 8px;
        font-size: 13px;
        position: relative;
      }
      .selected-date {
        color: #0369a1;
        font-size: 14px;
      }
      .selected-stats {
        display: flex;
        gap: 12px;
        flex: 1;
        flex-wrap: wrap;
      }
      .sel-stat {
        display: flex;
        align-items: center;
        gap: 4px;
        color: #475569;
      }
      .sel-stat mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }
      .close-sel {
        position: absolute;
        top: 4px;
        right: 4px;
        --mat-icon-button-touch-target: 24px;
      }
      .close-sel mat-icon {
        font-size: 16px;
      }

      /* 月度统计条 */
      .monthly-bars {
        display: flex;
        gap: 6px;
        margin-bottom: 12px;
        padding: 0 32px;
        height: 50px;
        align-items: flex-end;
      }
      .month-bar-item {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
      }
      .month-bar {
        width: 100%;
        min-height: 2px;
        background: linear-gradient(180deg, #3b82f6, #2563eb);
        border-radius: 3px 3px 0 0;
        transition: height 0.3s ease;
      }
      .month-bar-label {
        font-size: 9px;
        color: #94a3b8;
      }

      /* 加载状态 */
      .loading-state {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        padding: 32px;
        color: #666;
      }

      /* 空状态 */
      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 32px;
        color: #999;

        mat-icon {
          font-size: 48px;
          width: 48px;
          height: 48px;
          margin-bottom: 8px;
          opacity: 0.5;
        }
      }

      /* 图例 */
      .heatmap-legend {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
        font-size: 12px;
        color: #666;
      }
      .legend-spacer {
        flex: 1;
      }
      .legend-summary {
        font-size: 12px;
        color: #64748b;
      }

      .legend-colors {
        display: flex;
        gap: 2px;
      }

      .legend-item {
        width: 16px;
        height: 12px;
        border-radius: 2px;
      }

      /* 月份标签 */
      .month-labels {
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        gap: 2px;
        margin-bottom: 4px;
        padding-left: 32px;
      }

      .month-label {
        font-size: 11px;
        color: #999;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
      }

      /* 热力图主体 */
      .heatmap-body {
        display: flex;
        gap: 4px;
      }

      .week-labels {
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        width: 28px;
        font-size: 10px;
        color: #999;
        text-align: center;
      }

      .week-label {
        line-height: 16px;
      }

      /* 热力图方格容器 */
      .heatmap-cells {
        display: grid;
        grid-template-columns: repeat(53, 1fr);
        grid-template-rows: repeat(7, 1fr);
        gap: 2px;
        flex: 1;
      }

      .heatmap-cell {
        aspect-ratio: 1;
        border-radius: 3px;
        background: #ebedf0;
        transition:
          background 0.2s,
          transform 0.15s;
        cursor: pointer;

        &.has-data {
          &:hover {
            outline: 2px solid #2563eb;
            outline-offset: -2px;
            z-index: 1;
            transform: scale(1.15);
          }
          &:focus-visible {
            outline: 2px solid #2563eb;
            outline-offset: 0;
            z-index: 2;
          }
        }

        &.selected {
          outline: 2px solid #2563eb;
          outline-offset: -2px;
          z-index: 1;
        }
      }

      /* 响应式：移动端缩小 */
      @media (max-width: 768px) {
        .heatmap-cells {
          gap: 1px;
        }

        .heatmap-cell {
          border-radius: 2px;
        }

        .month-labels {
          gap: 1px;
          padding-left: 24px;
        }

        .week-labels {
          width: 22px;
          font-size: 9px;
        }

        .monthly-bars {
          padding: 0 24px;
        }
        .selected-day-panel {
          flex-wrap: wrap;
        }
      }

      /* 桌面大屏：增大方格 */
      @media (min-width: 1600px) {
        .heatmap-cell {
          border-radius: 4px;
        }

        .heatmap-cells {
          gap: 3px;
        }
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LearningCalendarHeatmapComponent implements OnChanges {
  /** 热力图配置 */
  @Input() config: CalendarHeatmapConfig | null = null;

  /** 年份变更事件 */
  @Output() yearChange = new EventEmitter<number>();

  /** 日期点击事件（返回选中日的学习记录） */
  @Output() daySelect = new EventEmitter<DailyLearningRecord | null>();

  /** 月份标签 */
  months: string[] = [
    '1月',
    '2月',
    '3月',
    '4月',
    '5月',
    '6月',
    '7月',
    '8月',
    '9月',
    '10月',
    '11月',
    '12月',
  ];

  /** 图例等级 */
  legendLevels = [
    { value: 0, label: '0' },
    { value: 60, label: '60' },
    { value: 120, label: '120' },
    { value: 180, label: '180' },
    { value: 240, label: '240+' },
  ];

  /** 所有日历方格 */
  calendarCells: Array<{ date: string; value: number; dayOfWeek: number; weekIndex: number }> = [];

  /** 选中的学习记录 */
  selectedRecord: DailyLearningRecord | null = null;

  /** 日期→学习记录映射 */
  private dataMap: Map<string, DailyLearningRecord> = new Map();

  /** 年平均每日学习分钟 */
  get yearlyAvgMinutes(): number {
    const withData = this.calendarCells.filter((c) => c.value > 0);
    if (withData.length === 0) return 0;
    const sum = withData.reduce((s, c) => s + c.value, 0);
    return Math.round(sum / withData.length);
  }

  /** 月度统计数据 */
  get monthlyStats(): { index: number; label: string; shortLabel: string; minutes: number }[] {
    if (!this.config) return [];
    const minutesByMonth = Array.from({ length: 12 }, () => 0);
    for (const record of this.config.data) {
      const month = parseInt(record.date.split('-')[1], 10) - 1;
      minutesByMonth[month] += record.minutes;
    }
    const monthNames = [
      '1月',
      '2月',
      '3月',
      '4月',
      '5月',
      '6月',
      '7月',
      '8月',
      '9月',
      '10月',
      '11月',
      '12月',
    ];
    const shortNames = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'];
    const _max = Math.max(...minutesByMonth, 1);
    return minutesByMonth.map((m, i) => ({
      index: i,
      label: monthNames[i],
      shortLabel: shortNames[i],
      minutes: m,
    }));
  }

  get isEmpty(): boolean {
    return this.calendarCells.length === 0 || this.calendarCells.every((c) => c.value === 0);
  }

  constructor(private cdr: ChangeDetectorRef) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['config'] && this.config) {
      this.buildCalendar();
    }
  }

  /** 上一年 */
  prevYear(): void {
    if (!this.config) return;
    const newYear = this.config.year - 1;
    this.yearChange.emit(newYear);
  }

  /** 下一年 */
  nextYear(): void {
    if (!this.config) return;
    const newYear = this.config.year + 1;
    this.yearChange.emit(newYear);
  }

  /** 点击日历方格 */
  onCellClick(cell: { date: string; value: number }): void {
    if (cell.value <= 0) {
      this.clearSelection();
      return;
    }
    const record = this.dataMap.get(cell.date) ?? null;
    this.selectedRecord = record;
    this.daySelect.emit(record);
  }

  /** 清除选择 */
  clearSelection(): void {
    this.selectedRecord = null;
    this.daySelect.emit(null);
  }

  /** 判断方格是否被选中 */
  isSelectedCell(cell: { date: string }): boolean {
    return this.selectedRecord?.date === cell.date;
  }

  /** 获取月度条高度 */
  getMonthlyBarHeight(m: { minutes: number }): number {
    const max = Math.max(...this.monthlyStats.map((s) => s.minutes), 1);
    return Math.max(2, (m.minutes / max) * 40);
  }

  /** 构建日历网格 */
  private buildCalendar(): void {
    if (!this.config) return;

    // 建立日期映射
    this.dataMap.clear();
    for (const record of this.config.data) {
      this.dataMap.set(record.date, record);
    }

    const year = this.config.year;
    const startDate = new Date(year, 0, 1);
    const endDate = new Date(year, 11, 31);

    // 找到第一个周一作为起始点
    const firstMonday = new Date(startDate);
    const startDay = firstMonday.getDay();
    const daysToMonday = startDay === 0 ? -6 : 1 - startDay;
    firstMonday.setDate(firstMonday.getDate() + daysToMonday);

    this.calendarCells = [];

    const currentDate = new Date(firstMonday);
    let weekIndex = 0;
    let dayOfWeek = 0;

    while (currentDate <= endDate || dayOfWeek < 7) {
      const dateStr = this.formatDate(currentDate);
      const record = this.dataMap.get(dateStr);
      const isInYear = currentDate.getFullYear() === year;

      this.calendarCells.push({
        date: dateStr,
        value: isInYear && record ? record.minutes : 0,
        dayOfWeek,
        weekIndex,
      });

      currentDate.setDate(currentDate.getDate() + 1);
      dayOfWeek++;
      if (dayOfWeek >= 7) {
        dayOfWeek = 0;
        weekIndex++;
      }
    }

    // 清除过期选择
    this.clearSelection();
  }

  /** 获取方格颜色 */
  getCellColor(cell: { value: number }): string {
    return this.getColorForMinutes(cell.value);
  }

  /** 根据分钟数获取颜色 */
  getColorForMinutes(minutes: number): string {
    if (minutes <= 0) return '#ebedf0';
    const max = this.config?.maxValue ?? 240;
    const ratio = Math.min(minutes / max, 1);

    // 绿色渐变：从浅绿到深绿
    if (ratio <= 0.25) return '#c6e48b';
    if (ratio <= 0.5) return '#7bc96f';
    if (ratio <= 0.75) return '#239a3b';
    return '#196127';
  }

  /** 获取 tooltip 文本 */
  getCellTooltip(cell: { date: string; value: number }): string {
    if (cell.value <= 0) return cell.date;
    const record = this.dataMap.get(cell.date);
    if (!record) return `${cell.date}：${cell.value}分钟`;

    const parts: string[] = [`${cell.date}`];
    parts.push(`学习时长：${record.minutes}分钟`);
    if (record.courses > 0) parts.push(`课程：${record.courses}门`);
    if (record.quizzes > 0) parts.push(`测验：${record.quizzes}次`);
    if (record.score != null) parts.push(`均分：${record.score}分`);
    return parts.join('\n');
  }

  /** trackBy 函数 */
  trackByIndex(index: number): number {
    return index;
  }

  /** 格式化日期 */
  private formatDate(date: Date): string {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }
}
