/**
 * Token 消费趋势图表组件
 *
 * 使用 ECharts 展示 Token 消费趋势
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { CommonModule } from '@angular/common';
import {
  Component,
  ElementRef,
  Input,
  OnChanges,
  OnInit,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import * as echarts from 'echarts';

import { TokenService } from '../../core/services/token.service';
import { TokenTimeStats } from '../../models/token.models';

// ECharts 类型定义（原生库无完整类型声明）
interface ChartInstance {
  setOption(option: unknown): void;
  resize(): void;
  dispose(): void;
}

interface GradientStop {
  offset: number;
  color: string;
}

type LinearGradientConstructor = new (
  x: number,
  y: number,
  x2: number,
  y2: number,
  colorStops: GradientStop[]
) => unknown;

function createGradient(startColor: string, endColor: string): unknown {
  const graphic = echarts as { graphic?: Record<string, unknown> }['graphic'];
  const GradientCtor = (graphic as Record<string, unknown>)[
    'LinearGradient'
  ] as LinearGradientConstructor;
  return new GradientCtor(0, 0, 0, 1, [
    { offset: 0, color: startColor },
    { offset: 1, color: endColor },
  ]);
}

function initChartInstance(element: HTMLElement): ChartInstance {
  return (echarts as { init: (el: HTMLElement) => ChartInstance }).init(element);
}

@Component({
  selector: 'app-token-stats-chart',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './token-stats-chart.component.html',
  styleUrls: ['./token-stats-chart.component.scss'],
})
export class TokenStatsChartComponent implements OnInit, OnChanges {
  @ViewChild('chart', { static: true }) chartElement!: ElementRef;

  /**
   * 开始日期
   */
  @Input() startDate?: string;

  /**
   * 结束日期
   */
  @Input() endDate?: string;

  /**
   * 图表类型
   */
  @Input() chartType: 'line' | 'bar' = 'line';

  chartInstance: ChartInstance | null = null;
  loading = false;
  error: string | null = null;
  statsData: TokenTimeStats[] = [];

  constructor(private tokenService: TokenService) {}

  ngOnInit(): void {
    this.initChart();
    this.loadStats();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (
      (changes['startDate'] || changes['endDate'] || changes['chartType']) &&
      !changes['startDate'].firstChange
    ) {
      this.loadStats();
    }
  }

  /**
   * 初始化图表
   */
  initChart(): void {
    this.chartInstance = initChartInstance(this.chartElement.nativeElement as HTMLElement);

    // 响应窗口大小变化
    window.addEventListener('resize', () => {
      if (this.chartInstance) {
        this.chartInstance.resize();
      }
    });
  }

  /**
   * 加载统计数据
   */
  loadStats(): void {
    this.loading = true;
    this.error = null;

    const start = this.startDate ?? this.getDaysAgo(7);
    const end = this.endDate ?? new Date().toISOString().split('T')[0];

    this.tokenService.getTimeStats(start, end).subscribe({
      next: (data) => {
        this.statsData = data;
        this.updateChart();
        this.loading = false;
      },
      error: (error: Error) => {
        console.error('加载统计数据失败:', error);
        this.error = error.message || '加载数据失败';
        this.loading = false;
      },
    });
  }

  /**
   * 更新图表
   */
  // eslint-disable-next-line max-lines-per-function
  updateChart(): void {
    if (!this.chartInstance) return;

    const dates = this.statsData.map((item) => item.date);
    const consumedTokens = this.statsData.map((item) => item.consumed);
    const purchasedTokens = this.statsData.map((item) => item.purchased);

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      legend: {
        data: ['消费', '充值'],
        top: 10,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLabel: {
          rotate: 45,
          interval: 'auto',
        },
      },
      yAxis: {
        type: 'value',
        name: 'Token 数量',
        axisLabel: {
          formatter: '{value}',
        },
      },
      series: [
        {
          name: '消费',
          type: this.chartType,
          data: consumedTokens,
          smooth: true,
          itemStyle: {
            color: '#ef4444',
          },
          areaStyle: {
            color: createGradient('rgba(239, 68, 68, 0.3)', 'rgba(239, 68, 68, 0.1)'),
          },
        },
        {
          name: '充值',
          type: this.chartType,
          data: purchasedTokens,
          smooth: true,
          itemStyle: {
            color: '#10b981',
          },
          areaStyle: {
            color: createGradient('rgba(16, 185, 129, 0.3)', 'rgba(16, 185, 129, 0.1)'),
          },
        },
      ],
    };

    this.chartInstance.setOption(option);
  }

  /**
   * 获取 N 天前的日期
   */
  private getDaysAgo(days: number): string {
    const date = new Date();
    date.setDate(date.getDate() - days);
    return date.toISOString().split('T')[0];
  }

  /**
   * 刷新图表
   */
  refresh(): void {
    this.loadStats();
  }

  /**
   * 切换图表类型
   */
  toggleChartType(): void {
    this.chartType = this.chartType === 'line' ? 'bar' : 'line';
    this.updateChart();
  }

  ngOnDestroy(): void {
    if (this.chartInstance) {
      this.chartInstance.dispose();
    }
    window.removeEventListener('resize', () => {});
  }
}
