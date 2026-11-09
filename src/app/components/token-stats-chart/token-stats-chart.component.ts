/**
 * Token 消费趋势图表组件
 *
 * 使用 ECharts 展示 Token 消费趋势
 *
 * 【P3-B bundle 优化】echarts 通过动态 import 按需加载，
 *   避免 ~1.1 MB 的 echarts 进入 initial chunk
 *   （components 使用 token-stats-chart 时才触发 import）
 *
 * @author MatuX Lab
 * @version 1.1.0
 */

import { CommonModule } from '@angular/common';
import {
  Component,
  ElementRef,
  Input,
  OnChanges,
  OnDestroy,
  OnInit,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { TokenService } from '../../core/services/token.service';
import { TokenTimeStats } from '../../models/token.models';

// ECharts 类型（仅类型导入 - 类型擦除，不参与运行时打包）
// 运行时模块通过动态 import('echarts') 按需加载
type EChartsModule = typeof import('echarts');

// ECharts 颜色令牌: 与设计系统主色保持一致
// 与 _stem-tokens.scss / _css-variables.scss 中令牌值同步
const ECHARTS_PALETTE = {
  consumed: '#ef4444', // 消费 - 对应 --stem-error
  purchased: '#10b981', // 充值 - 对应 --stem-primary-light
} as const;

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

@Component({
  selector: 'app-token-stats-chart',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './token-stats-chart.component.html',
  styleUrls: ['./token-stats-chart.component.scss'],
})
export class TokenStatsChartComponent implements OnInit, OnChanges, OnDestroy {
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

  /**
   * 【P3-B bundle 优化】echarts 模块加载 Promise 缓存。
   * 首次调用触发动态 import('echarts')，后续调用复用同一个 Promise，
   * 既保证按需懒加载，又避免重复触发 import。
   */
  private echartsPromise: Promise<EChartsModule> | null = null;

  /**
   * echarts 是否已经成功初始化（用于 updateChart 防 guard）
   */
  private chartReady = false;

  constructor(private tokenService: TokenService) {}

  /**
   * 异步加载 echarts 模块（按需懒加载）
   */
  private async getECharts(): Promise<EChartsModule> {
    if (!this.echartsPromise) {
      this.echartsPromise = import('echarts');
    }
    return this.echartsPromise;
  }

  ngOnInit(): void {
    // 异步初始化图表，初始化完成后才加载数据（避免 updateChart 时 chartInstance 还未创建）
    this.initChart()
      .then(() => this.loadStats())
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : String(err);
        console.error('初始化图表失败:', err);
        this.error = `图表初始化失败: ${msg}`;
        this.loading = false;
      });
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
   * 初始化图表（异步 - 等待 echarts 模块加载完成）
   */
  async initChart(): Promise<void> {
    const echarts = await this.getECharts();
    const nativeElement = this.chartElement.nativeElement as HTMLElement;
    this.chartInstance = (
      echarts as unknown as { init: (el: HTMLElement) => ChartInstance }
    ).init(nativeElement);
    this.chartReady = true;

    // 响应窗口大小变化
    window.addEventListener('resize', this.handleResize);
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
   * 更新图表（异步 - 等待 echarts 模块加载完成）
   */
  // eslint-disable-next-line max-lines-per-function
  async updateChart(): Promise<void> {
    if (!this.chartInstance || !this.chartReady) {
      // 图表尚未初始化完成，跳过本次更新（通常发生在 initChart 完成前收到 loadStats 数据）
      return;
    }

    const echarts = await this.getECharts();

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
            color: ECHARTS_PALETTE.consumed,
          },
          areaStyle: {
            color: this.createGradient(
              echarts,
              'rgba(239, 68, 68, 0.3)',
              'rgba(239, 68, 68, 0.1)'
            ),
          },
        },
        {
          name: '充值',
          type: this.chartType,
          data: purchasedTokens,
          smooth: true,
          itemStyle: {
            color: ECHARTS_PALETTE.purchased,
          },
          areaStyle: {
            color: this.createGradient(
              echarts,
              'rgba(16, 185, 129, 0.3)',
              'rgba(16, 185, 129, 0.1)'
            ),
          },
        },
      ],
    };

    this.chartInstance.setOption(option);
  }

  /**
   * 创建 echarts 线性渐变对象（通过传入的 echarts 模块，避免模块级静态依赖）
   */
  private createGradient(
    echarts: EChartsModule,
    startColor: string,
    endColor: string
  ): unknown {
    const graphic = (
      echarts as unknown as {
        graphic: Record<string, LinearGradientConstructor>;
      }
    ).graphic;
    const GradientCtor = graphic['LinearGradient'];
    return new GradientCtor(0, 0, 0, 1, [
      { offset: 0, color: startColor },
      { offset: 1, color: endColor },
    ]);
  }

  /**
   * 窗口缩放处理（箭头函数绑定 this，方便 add/removeEventListener）
   */
  private readonly handleResize = (): void => {
    if (this.chartInstance) {
      this.chartInstance.resize();
    }
  };

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
    window.removeEventListener('resize', this.handleResize);
  }
}