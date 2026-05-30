/* eslint-disable @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-explicit-any */
import { AfterViewInit, Component, ElementRef, Input, OnInit, ViewChild } from '@angular/core';
// 注意：需要安装 echarts: npm install echarts
import * as echarts from 'echarts';

export interface EChartsOption {
  title?: Record<string, unknown>;
  tooltip?: Record<string, unknown>;
  legend?: Record<string, unknown>;
  xAxis?: Record<string, unknown> | Array<Record<string, unknown>>;
  yAxis?: Record<string, unknown> | Array<Record<string, unknown>>;
  series?: Array<Record<string, unknown>>;
  grid?: Record<string, unknown>;
  dataZoom?: Array<Record<string, unknown>>;
  visualMap?: Record<string, unknown>;
}

@Component({
  selector: 'app-echarts-visualization',
  standalone: false,
  template: ` <div #chartContainer class="echart-container"></div> `,
  styles: [
    `
      .echart-container {
        width: 100%;
        height: 100%;
        min-height: 300px;
      }
    `,
  ],
})
export class EChartsVisualizationComponent implements OnInit, AfterViewInit {
  @Input() option: EChartsOption = {};
  @Input() style: Record<string, string> = { height: '400px' };
  @Input() theme: string = '';

  @ViewChild('chartContainer', { static: true }) chartContainer!: ElementRef;

  private chartInstance: any = null;

  ngOnInit(): void {
    // 初始化时设置容器样式
    if (this.chartContainer) {
      Object.entries(this.style).forEach(([key, value]) => {
        (this.chartContainer.nativeElement as HTMLElement).style.setProperty(key, value);
      });
    }
  }

  ngAfterViewInit(): void {
    this.initChart();
  }

  private initChart(): void {
    if (this.chartContainer) {
      this.chartInstance = echarts.init(
        this.chartContainer.nativeElement as HTMLElement,
        this.theme || undefined
      );

      if (this.option) {
        this.chartInstance.setOption(this.option as any);
      }

      // 响应窗口大小变化
      window.addEventListener('resize', this.onResize.bind(this));
    }
  }

  private onResize(): void {
    if (this.chartInstance) {
      this.chartInstance.resize();
    }
  }

  // 更新图表配置
  updateOption(option: EChartsOption): void {
    this.option = { ...this.option, ...option };
    if (this.chartInstance) {
      this.chartInstance.setOption(this.option, true);
    }
  }

  // 获取图表实例
  // eslint-disable-next-line @typescript-eslint/no-redundant-type-constituents
  getChartInstance(): any | null {
    return this.chartInstance;
  }

  ngOnDestroy(): void {
    if (this.chartInstance) {
      this.chartInstance.dispose();
      window.removeEventListener('resize', this.onResize.bind(this));
    }
  }
}

@Component({
  selector: 'app-sponsorship-analytics-dashboard',
  standalone: false,
  template: `
    <div class="analytics-dashboard">
      <!-- 实时数据监控 -->
      <div class="realtime-monitor">
        <h3>实时数据监控</h3>
        <div class="monitor-grid">
          <app-echarts-visualization [option]="realtimeOption" [style]="{ height: '300px' }">
          </app-echarts-visualization>
        </div>
      </div>

      <!-- 综合分析面板 -->
      <div class="analysis-panel">
        <h3>综合分析</h3>
        <div class="panel-grid">
          <app-echarts-visualization [option]="performanceOption" [style]="{ height: '400px' }">
          </app-echarts-visualization>

          <app-echarts-visualization [option]="conversionOption" [style]="{ height: '400px' }">
          </app-echarts-visualization>
        </div>
      </div>

      <!-- 趋势预测 -->
      <div class="prediction-section">
        <h3>趋势预测</h3>
        <div class="prediction-grid">
          <app-echarts-visualization [option]="forecastOption" [style]="{ height: '350px' }">
          </app-echarts-visualization>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .analytics-dashboard {
        padding: 20px;
      }

      .realtime-monitor,
      .analysis-panel,
      .prediction-section {
        margin-bottom: 30px;
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }

      .monitor-grid,
      .panel-grid,
      .prediction-grid {
        display: grid;
        gap: 20px;
        margin-top: 15px;
      }

      .monitor-grid {
        grid-template-columns: 1fr;
      }

      .panel-grid {
        grid-template-columns: 1fr 1fr;
      }

      .prediction-grid {
        grid-template-columns: 1fr;
      }

      @media (max-width: 768px) {
        .panel-grid {
          grid-template-columns: 1fr;
        }
      }
    `,
  ],
})
export class SponsorshipAnalyticsDashboardComponent implements OnInit {
  realtimeOption: EChartsOption = {};
  performanceOption: EChartsOption = {};
  conversionOption: EChartsOption = {};
  forecastOption: EChartsOption = {};

  ngOnInit(): void {
    this.initRealtimeChart();
    this.initPerformanceChart();
    this.initConversionChart();
    this.initForecastChart();
  }

  private initRealtimeChart(): void {
    this.realtimeOption = {
      title: {
        text: '实时品牌曝光监控',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any[]) => {
          const data = params[0];
          return `${data.name}<br/>当前曝光：${data.value.toLocaleString()} 次`;
        },
      },
      xAxis: {
        type: 'category',
        data: this.generateTimeLabels(24),
        axisLabel: {
          rotate: 45,
        },
      },
      yAxis: {
        type: 'value',
        name: '曝光次数',
      },
      series: [
        {
          data: this.generateRandomData(24, 1000, 5000),
          type: 'line',
          smooth: true,
          areaStyle: {
            opacity: 0.3,
          },
          itemStyle: {
            color: '#2196F3',
          },
        },
      ],
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true,
      },
    };
  }

  private initPerformanceChart(): void {
    this.performanceOption = {
      title: {
        text: '赞助活动绩效分析',
        left: 'center',
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)',
      },
      legend: {
        orient: 'vertical',
        left: 'left',
      },
      series: [
        {
          name: '活动类型',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: false,
            position: 'center',
          },
          emphasis: {
            label: {
              show: true,
              fontSize: '16',
              fontWeight: 'bold',
            },
          },
          labelLine: {
            show: false,
          },
          data: [
            { value: 45, name: '教育赞助' },
            { value: 30, name: '科技赞助' },
            { value: 15, name: '公益赞助' },
            { value: 10, name: '其他赞助' },
          ],
        },
      ],
    };
  }

  // eslint-disable-next-line max-lines-per-function
  private initConversionChart(): void {
    const categories = ['横幅广告', '侧边栏', '弹窗', '邮件推广', '社交媒体', '内容植入'];
    const conversionRates = [3.2, 2.8, 4.1, 1.9, 3.5, 5.2];
    const exposureCounts = [50000, 30000, 15000, 25000, 35000, 40000];

    this.conversionOption = {
      title: {
        text: '曝光渠道转化效果',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      legend: {
        data: ['曝光次数', '转化率(%)'],
        top: '10%',
      },
      xAxis: [
        {
          type: 'category',
          data: categories,
          axisTick: {
            alignWithLabel: true,
          },
        },
      ],
      yAxis: [
        {
          type: 'value',
          name: '曝光次数',
          position: 'left',
        },
        {
          type: 'value',
          name: '转化率(%)',
          position: 'right',
        },
      ],
      series: [
        {
          name: '曝光次数',
          type: 'bar',
          barWidth: '60%',
          data: exposureCounts,
          itemStyle: {
            color: '#2196F3',
          },
        },
        {
          name: '转化率(%)',
          type: 'line',
          yAxisIndex: 1,
          data: conversionRates,
          itemStyle: {
            color: '#4CAF50',
          },
          smooth: true,
        },
      ],
    };
  }

  // eslint-disable-next-line max-lines-per-function
  private initForecastChart(): void {
    const dates = this.generateDateLabels(30);
    const actualData = this.generateRandomData(30, 2000, 8000);
    const trendData = this.generateTrendData(actualData);
    const confidenceUpper = trendData.map((val) => val + 1000);
    const confidenceLower = trendData.map((val) => Math.max(0, val - 1000));

    this.forecastOption = {
      title: {
        text: '品牌曝光趋势预测',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any[]) => {
          let result = `${params[0].name}<br/>`;
          params.forEach((param: any) => {
            if (param.seriesName === '实际数据') {
              result += `${param.marker} ${param.seriesName}: ${param.value.toLocaleString()}<br/>`;
            } else if (param.seriesName === '预测趋势') {
              result += `${param.marker} ${param.seriesName}: ${param.value.toLocaleString()}<br/>`;
            }
          });
          return result;
        },
      },
      legend: {
        data: ['实际数据', '预测趋势', '置信区间'],
        top: '10%',
      },
      xAxis: {
        type: 'category',
        data: dates,
      },
      yAxis: {
        type: 'value',
        name: '曝光次数',
      },
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100,
        },
        {
          start: 0,
          end: 100,
        },
      ],
      series: [
        {
          name: '实际数据',
          type: 'line',
          data: actualData,
          itemStyle: {
            color: '#2196F3',
          },
          smooth: true,
        },
        {
          name: '预测趋势',
          type: 'line',
          data: [...actualData.slice(0, 20), ...trendData.slice(20)],
          itemStyle: {
            color: '#FF9800',
          },
          lineStyle: {
            type: 'dashed',
          },
          smooth: true,
        },
        {
          name: '置信区间',
          type: 'line',
          data: confidenceUpper,
          lineStyle: {
            opacity: 0,
          },
          stack: 'confidence',
          symbol: 'none',
        },
        {
          name: '置信区间',
          type: 'line',
          data: confidenceLower,
          areaStyle: {
            color: 'rgba(255, 152, 0, 0.2)',
          },
          lineStyle: {
            opacity: 0,
          },
          stack: 'confidence',
          symbol: 'none',
        },
      ],
    };
  }

  // 辅助方法
  private generateTimeLabels(hours: number): string[] {
    const now = new Date();
    const labels = [];
    for (let i = hours - 1; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      labels.push(`${time.getHours().toString().padStart(2, '0')}:00`);
    }
    return labels;
  }

  private generateDateLabels(days: number): string[] {
    const now = new Date();
    const labels = [];
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
      labels.push(`${date.getMonth() + 1}/${date.getDate()}`);
    }
    return labels;
  }

  private generateRandomData(count: number, min: number, max: number): number[] {
    return Array.from({ length: count }, () => Math.floor(Math.random() * (max - min + 1)) + min);
  }

  private generateTrendData(baseData: number[]): number[] {
    return baseData.map((val, index) => {
      const trend = index * 50; // 简单的线性趋势
      const noise = (Math.random() - 0.5) * 1000;
      return Math.max(0, val + trend + noise);
    });
  }
}
