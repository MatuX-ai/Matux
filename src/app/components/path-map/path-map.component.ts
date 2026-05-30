import { HttpClient } from '@angular/common/http';
import { AfterViewInit, Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

// ECharts类型定义
interface EChartsTooltipParams {
  dataType?: string;
  data?: unknown;
  name?: string;
}

interface EChartsTitle {
  text?: string;
  left?: string | number;
  top?: number;
}

interface EChartsTooltip {
  trigger?: string;
  formatter?: (params: EChartsTooltipParams) => string;
}

interface EChartsLegend {
  data?: string[];
  bottom?: number;
}

interface EChartsLabel {
  show?: boolean;
  position?: string;
  fontSize?: number;
}

interface EChartsForce {
  repulsion?: number;
  gravity?: number;
  edgeLength?: number;
}

interface EChartsCategory {
  name: string;
  itemStyle: {
    color: string;
  };
}

interface EChartsLineStyle {
  color?: string;
  curveness?: number;
}

interface EChartsGraphNode {
  id?: string;
  name?: string;
  category?: number;
  value?: number;
  difficulty?: number;
  description?: string;
  symbolSize?: number;
  x?: number;
  y?: number;
}

interface EChartsGraphLink {
  source: string;
  target: string;
  label?: {
    show?: boolean;
    formatter?: string;
  };
}

interface EChartsSeries {
  type?: string;
  layout?: string;
  symbolSize?: number;
  roam?: boolean;
  label?: EChartsLabel;
  edgeSymbol?: string[];
  edgeSymbolSize?: number[];
  force?: EChartsForce;
  categories?: EChartsCategory[];
  data?: EChartsGraphNode[];
  links?: EChartsGraphLink[];
  lineStyle?: EChartsLineStyle;
}

interface EChartsOption {
  title?: EChartsTitle;
  tooltip?: EChartsTooltip;
  legend?: EChartsLegend;
  series?: EChartsSeries[];
}

interface EChartsInstance {
  setOption(option: EChartsOption): void;
  resize(): void;
  dispose(): void;
}

declare let echarts: {
  init(dom: HTMLElement): EChartsInstance;
};

interface PathNode {
  node_type: string;
  node_id: string;
  title: string;
  difficulty: number;
  estimated_hours: number;
  description?: string;
}

interface PathSummary {
  total_nodes: number;
  total_hours: number;
  avg_difficulty: number;
  type_distribution: Record<string, number>;
  estimated_completion_days: number;
}

interface LearningPath {
  user_id: string;
  path_nodes: PathNode[];
  summary: PathSummary;
  generated_at: string;
}

@Component({
  selector: 'app-path-map',
  templateUrl: './path-map.component.html',
  styleUrls: ['./path-map.component.scss'],
  standalone: false,
})
export class PathMapComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('chartContainer') chartContainer!: ElementRef;

  private destroy$ = new Subject<void>();
  private chart: EChartsInstance | null = null;

  // 用户信息
  userId: string = 'test_user_001';
  age: number = 13;
  gradeLevel: string = '初中';

  // 学习路径数据
  learningPath: LearningPath | null = null;
  isLoading: boolean = false;
  errorMessage: string = '';

  // API端点
  private apiBaseUrl = 'http://localhost:8001/api/v1/path';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    // 初始化
  }

  ngAfterViewInit(): void {
    // 初始化ECharts图表
    this.initChart();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();

    if (this.chart) {
      this.chart.dispose();
    }
  }

  /**
   * 初始化ECharts图表
   */
  initChart(): void {
    if (!this.chartContainer) return;

    this.chart = echarts.init(this.chartContainer.nativeElement as HTMLElement);

    // 设置初始空图表
    const option = this.getInitialChartOption();
    this.chart.setOption(option);

    // 响应式调整
    window.addEventListener('resize', () => {
      this.chart?.resize();
    });
  }

  /**
   * 获取初始图表配置
   */
  private getInitialChartOption(): EChartsOption {
    return {
      title: this.getChartTitle(),
      tooltip: this.getChartTooltip(),
      legend: this.getChartLegend(),
      series: [this.getGraphSeries()],
    };
  }

  /**
   * 获取图表标题配置
   */
  private getChartTitle(): EChartsTitle {
    return {
      text: 'STEM学习路径地图',
      left: 'center',
      top: 20,
    };
  }

  /**
   * 获取图表提示框配置
   */
  private getChartTooltip(): EChartsTooltip {
    return {
      trigger: 'item',
      formatter: (params: EChartsTooltipParams) => {
        if (params.dataType === 'node') {
          const data = params.data as {
            name: string;
            category: number;
            difficulty: number;
            value: number;
            description?: string;
          };
          return `
              <div style="padding: 10px;">
                <strong>${data.name}</strong><br/>
                类型: ${this.getNodeTypeLabel(this.getCategoryKey(data.category))}<br/>
                难度: ${'★'.repeat(data.difficulty)}${'☆'.repeat(5 - data.difficulty)}<br/>
                时长: ${data.value}小时
                ${data.description ? `<br/>说明: ${data.description}` : ''}
              </div>
            `;
        }
        return params.name ?? '';
      },
    };
  }

  /**
   * 获取图例配置
   */
  private getChartLegend(): EChartsLegend {
    return {
      data: ['课程单元', '过渡项目', '教材章节', '硬件项目'],
      bottom: 20,
    };
  }

  /**
   * 获取图谱系列配置
   */
  private getGraphSeries(): EChartsSeries {
    return {
      type: 'graph',
      layout: 'force',
      symbolSize: 60,
      roam: true,
      label: {
        show: true,
        position: 'bottom',
        fontSize: 12,
      },
      edgeSymbol: ['circle', 'arrow'],
      edgeSymbolSize: [4, 10],
      force: {
        repulsion: 200,
        gravity: 0.1,
        edgeLength: 150,
      },
      categories: [
        { name: '课程单元', itemStyle: { color: '#5470c6' } },
        { name: '过渡项目', itemStyle: { color: '#91cc75' } },
        { name: '教材章节', itemStyle: { color: '#fac858' } },
        { name: '硬件项目', itemStyle: { color: '#ee6666' } },
      ],
      data: [],
      links: [],
      lineStyle: {
        color: 'source',
        curveness: 0.3,
      },
    };
  }

  /**
   * 根据类别索引获取类别键
   */
  getCategoryKey(categoryIndex: number): string {
    const categoryKeys = [
      'course_unit',
      'transition_project',
      'textbook_chapter',
      'hardware_project',
    ];
    return categoryKeys[categoryIndex] || 'course_unit';
  }

  /**
   * 生成学习路径
   */
  generatePath(): void {
    this.isLoading = true;
    this.errorMessage = '';

    const requestData = {
      user_id: this.userId,
      age: this.age,
      grade_level: this.gradeLevel,
      max_nodes: 20,
    };

    this.http
      .post<LearningPath>(`${this.apiBaseUrl}/generate`, requestData)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.learningPath = response;
          this.updateChart(response);
          this.isLoading = false;
        },
        error: (error) => {
          console.error('生成路径失败:', error);
          this.errorMessage = '生成路径失败,请检查后端服务是否启动';
          this.isLoading = false;
        },
      });
  }

  /**
   * 更新图表数据
   */
  updateChart(path: LearningPath): void {
    if (!this.chart) return;

    const nodes = path.path_nodes.map((node, index) => ({
      id: node.node_id,
      name: node.title.length > 10 ? node.title.substring(0, 10) + '...' : node.title,
      category: this.getNodeCategory(node.node_type),
      value: node.estimated_hours,
      difficulty: node.difficulty,
      description: node.description,
      symbolSize: 50 + node.difficulty * 10,
      x: index * 200,
      y: 100 + Math.sin(index) * 50,
    }));

    const links = [];
    for (let i = 0; i < nodes.length - 1; i++) {
      links.push({
        source: nodes[i].id,
        target: nodes[i + 1].id,
        label: {
          show: true,
          formatter: '→',
        },
      });
    }

    const option = {
      series: [
        {
          data: nodes,
          links,
        },
      ],
    };

    this.chart.setOption(option);
  }

  /**
   * 获取节点类别索引
   */
  getNodeCategory(nodeType: string): number {
    const categoryMap: Record<string, number> = {
      course_unit: 0,
      transition_project: 1,
      textbook_chapter: 2,
      hardware_project: 3,
    };
    return categoryMap[nodeType] || 0;
  }

  /**
   * 获取节点类型标签
   */
  getNodeTypeLabel(nodeType: string): string {
    const labels: Record<string, string> = {
      course_unit: '课程单元',
      transition_project: '过渡项目',
      textbook_chapter: '教材章节',
      hardware_project: '硬件项目',
    };
    return labels[nodeType] || '未知';
  }

  /**
   * 获取节点类别标签(用于分布图)
   */
  getNodeCategoryLabel(categoryKey: string): string {
    return this.getNodeTypeLabel(categoryKey);
  }

  /**
   * Math.round包装器(用于模板)
   */
  round(value: number): number {
    return Math.round(value);
  }

  /**
   * 获取示例路径(用于测试)
   */
  loadSamplePath(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.http
      .get<LearningPath>(`${this.apiBaseUrl}/sample/${this.userId}`)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.learningPath = response;
          this.updateChart(response);
          this.isLoading = false;
        },
        error: (error) => {
          console.error('加载示例路径失败:', error);
          this.errorMessage = '加载示例路径失败';
          this.isLoading = false;
        },
      });
  }

  /**
   * 清空图表
   */
  clearChart(): void {
    this.learningPath = null;

    if (this.chart) {
      this.chart.setOption({
        series: [
          {
            data: [],
            links: [],
          },
        ],
      });
    }
  }
}
