import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';

/**
 * Admin 营销数据展示组件
 * 展示营销页面的统计数据、联系表单、订阅用户等数据
 */
@Component({
  selector: 'app-marketing-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="marketing-dashboard">
      <div class="dashboard-header">
        <h1>📊 营销数据看板</h1>
        <div class="date-range">
          <select [(ngModel)]="dateRange" (change)="loadData()">
            <option value="7">最近 7 天</option>
            <option value="30">最近 30 天</option>
            <option value="90">最近 90 天</option>
          </select>
        </div>
      </div>

      <!-- 核心指标卡片 -->
      <div class="metrics-grid">
        <div class="metric-card primary">
          <div class="metric-icon">👁️</div>
          <div class="metric-content">
            <div class="metric-label">页面访问量</div>
            <div class="metric-value">{{ metrics.pageViews | number }}</div>
            <div
              class="metric-trend"
              [class.up]="metrics.pageViewsTrend > 0"
              [class.down]="metrics.pageViewsTrend < 0"
            >
              {{ metrics.pageViewsTrend > 0 ? '+' : '' }}{{ metrics.pageViewsTrend }}%
            </div>
          </div>
        </div>

        <div class="metric-card success">
          <div class="metric-icon">✉️</div>
          <div class="metric-content">
            <div class="metric-label">联系表单</div>
            <div class="metric-value">{{ metrics.contactForms | number }}</div>
            <div
              class="metric-trend"
              [class.up]="metrics.contactFormsTrend > 0"
              [class.down]="metrics.contactFormsTrend < 0"
            >
              {{ metrics.contactFormsTrend > 0 ? '+' : '' }}{{ metrics.contactFormsTrend }}%
            </div>
          </div>
        </div>

        <div class="metric-card warning">
          <div class="metric-icon">📧</div>
          <div class="metric-content">
            <div class="metric-label">新增订阅</div>
            <div class="metric-value">{{ metrics.newSubscribers | number }}</div>
            <div
              class="metric-trend"
              [class.up]="metrics.newSubscribersTrend > 0"
              [class.down]="metrics.newSubscribersTrend < 0"
            >
              {{ metrics.newSubscribersTrend > 0 ? '+' : '' }}{{ metrics.newSubscribersTrend }}%
            </div>
          </div>
        </div>

        <div class="metric-card info">
          <div class="metric-icon">⏱️</div>
          <div class="metric-content">
            <div class="metric-label">平均停留时间</div>
            <div class="metric-value">{{ metrics.avgTimeOnPage }}s</div>
            <div
              class="metric-trend"
              [class.up]="metrics.avgTimeOnPageTrend > 0"
              [class.down]="metrics.avgTimeOnPageTrend < 0"
            >
              {{ metrics.avgTimeOnPageTrend > 0 ? '+' : '' }}{{ metrics.avgTimeOnPageTrend }}%
            </div>
          </div>
        </div>
      </div>

      <!-- 页面访问统计 -->
      <div class="dashboard-section">
        <h2>📄 页面访问统计</h2>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>页面</th>
                <th>访问量</th>
                <th>独立访客</th>
                <th>跳出率</th>
                <th>平均停留</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let page of pageStats">
                <td>{{ page.name }}</td>
                <td>{{ page.views | number }}</td>
                <td>{{ page.uniqueVisitors | number }}</td>
                <td>{{ page.bounceRate }}%</td>
                <td>{{ page.avgDuration }}s</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 联系表单数据 -->
      <div class="dashboard-section">
        <h2>📝 联系表单</h2>
        <div class="toolbar">
          <select [(ngModel)]="filterType" (change)="filterContacts()">
            <option value="">全部类型</option>
            <option value="business">商务合作</option>
            <option value="school">学校采购</option>
            <option value="personal">个人学习</option>
            <option value="technical">技术支持</option>
          </select>
          <input
            type="text"
            [(ngModel)]="searchQuery"
            placeholder="搜索..."
            (input)="filterContacts()"
          />
        </div>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>姓名</th>
                <th>邮箱</th>
                <th>类型</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let contact of filteredContacts">
                <td>{{ contact.createdAt | date: 'yyyy-MM-dd HH:mm' }}</td>
                <td>{{ contact.name }}</td>
                <td>{{ contact.email }}</td>
                <td>
                  <span class="badge" [ngClass]="'badge-' + contact.type">{{
                    contact.typeLabel
                  }}</span>
                </td>
                <td>
                  <span class="status-badge" [ngClass]="'status-' + contact.status">
                    {{ contact.statusLabel }}
                  </span>
                </td>
                <td>
                  <button class="btn-sm btn-primary" (click)="viewContact(contact)">查看</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 订阅用户数据 -->
      <div class="dashboard-section">
        <h2>📧 订阅用户</h2>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>邮箱</th>
                <th>订阅日期</th>
                <th>状态</th>
                <th>偏好</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let subscriber of subscribers">
                <td>{{ subscriber.email }}</td>
                <td>{{ subscriber.subscribedAt | date: 'yyyy-MM-dd' }}</td>
                <td>
                  <span class="status-badge" [ngClass]="'status-' + subscriber.status">
                    {{ subscriber.verified ? '已验证' : '未验证' }}
                  </span>
                </td>
                <td>{{ subscriber.frequency }}</td>
                <td>
                  <button class="btn-sm btn-secondary" (click)="manageSubscriber(subscriber)">
                    管理
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .marketing-dashboard {
        padding: 24px;
      }

      .dashboard-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 32px;
      }

      .dashboard-header h1 {
        font-size: 24px;
        font-weight: 600;
        margin: 0;
      }

      .date-range select {
        padding: 8px 16px;
        border-radius: 8px;
        border: 1px solid #e8e8ed;
        background: white;
        font-size: 14px;
      }

      /* Metrics Grid */
      .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 24px;
        margin-bottom: 32px;
      }

      .metric-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        display: flex;
        gap: 16px;
      }

      .metric-card.primary {
        border-left: 4px solid #007aff;
      }
      .metric-card.success {
        border-left: 4px solid #34c759;
      }
      .metric-card.warning {
        border-left: 4px solid #ff9500;
      }
      .metric-card.info {
        border-left: 4px solid #5856d6;
      }

      .metric-icon {
        font-size: 32px;
      }

      .metric-content {
        flex: 1;
      }

      .metric-label {
        font-size: 12px;
        color: #86868b;
        margin-bottom: 8px;
      }

      .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #1d1d1f;
        margin-bottom: 4px;
      }

      .metric-trend {
        font-size: 12px;
        font-weight: 600;
      }

      .metric-trend.up {
        color: #34c759;
      }
      .metric-trend.down {
        color: #ff3b30;
      }

      /* Dashboard Sections */
      .dashboard-section {
        background: white;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
      }

      .dashboard-section h2 {
        font-size: 18px;
        font-weight: 600;
        margin-top: 0;
        margin-bottom: 16px;
      }

      .toolbar {
        display: flex;
        gap: 12px;
        margin-bottom: 16px;
      }

      .toolbar select,
      .toolbar input {
        padding: 8px 12px;
        border-radius: 6px;
        border: 1px solid #e8e8ed;
        font-size: 14px;
      }

      .toolbar input {
        flex: 1;
        max-width: 300px;
      }

      /* Table Styles */
      .table-container {
        overflow-x: auto;
      }

      .data-table {
        width: 100%;
        border-collapse: collapse;
      }

      .data-table thead {
        background: #f5f5f7;
      }

      .data-table th,
      .data-table td {
        padding: 12px 16px;
        text-align: left;
        border-bottom: 1px solid #e8e8ed;
      }

      .data-table th {
        font-weight: 600;
        font-size: 14px;
        color: #1d1d1f;
      }

      .data-table td {
        font-size: 14px;
        color: #3a3a3c;
      }

      .data-table tbody tr:hover {
        background: #f5f5f7;
      }

      /* Badges */
      .badge {
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
      }

      .badge-business {
        background: #e3f2fd;
        color: #1976d2;
      }
      .badge-school {
        background: #f3e5f5;
        color: #7b1fa2;
      }
      .badge-personal {
        background: #e8f5e9;
        color: #388e3c;
      }
      .badge-technical {
        background: #fff3e0;
        color: #f57c00;
      }

      .status-badge {
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
      }

      .status-pending {
        background: #fff3e0;
        color: #f57c00;
      }
      .status-processing {
        background: #e3f2fd;
        color: #1976d2;
      }
      .status-resolved {
        background: #e8f5e9;
        color: #388e3c;
      }
      .status-true {
        background: #e8f5e9;
        color: #388e3c;
      }
      .status-false {
        background: #ffebee;
        color: #d32f2f;
      }

      /* Buttons */
      .btn-sm {
        padding: 6px 12px;
        border-radius: 6px;
        border: none;
        font-size: 12px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
      }

      .btn-primary {
        background: #007aff;
        color: white;
      }

      .btn-primary:hover {
        background: #0056cc;
      }

      .btn-secondary {
        background: #f5f5f7;
        color: #1d1d1f;
      }

      .btn-secondary:hover {
        background: #e8e8ed;
      }

      @media (max-width: 768px) {
        .dashboard-header {
          flex-direction: column;
          align-items: flex-start;
          gap: 16px;
        }

        .metrics-grid {
          grid-template-columns: 1fr;
        }

        .toolbar {
          flex-direction: column;
        }

        .toolbar input {
          max-width: 100%;
        }
      }
    `,
  ],
})
export class MarketingDashboardComponent implements OnInit {
  dateRange = '7';
  filterType = '';
  searchQuery = '';

  // 核心指标
  metrics: MarketingMetrics = {
    pageViews: 0,
    pageViewsTrend: 0,
    contactForms: 0,
    contactFormsTrend: 0,
    newSubscribers: 0,
    newSubscribersTrend: 0,
    avgTimeOnPage: 0,
    avgTimeOnPageTrend: 0,
  };

  // 页面统计
  pageStats: PageStat[] = [];

  // 联系表单
  contacts: ContactForm[] = [];
  filteredContacts: ContactForm[] = [];

  // 订阅用户
  subscribers: Subscriber[] = [];

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadData();
  }

  /**
   * 加载数据
   */
  loadData(): void {
    this.loadMetrics();
    this.loadPageStats();
    this.loadContacts();
    this.loadSubscribers();
  }

  /**
   * 加载核心指标
   */
  loadMetrics(): void {
    this.http
      .get<MarketingMetrics>(`/api/admin/marketing/metrics?days=${this.dateRange}`)
      .subscribe((data) => {
        this.metrics = data;
      });
  }

  /**
   * 加载页面统计
   */
  loadPageStats(): void {
    this.http.get<PageStat[]>('/api/admin/marketing/page-stats').subscribe((data) => {
      this.pageStats = data;
    });
  }

  /**
   * 加载联系表单
   */
  loadContacts(): void {
    this.http.get<ContactForm[]>('/api/admin/marketing/contacts').subscribe((data) => {
      this.contacts = data;
      this.filteredContacts = [...data];
    });
  }

  /**
   * 加载订阅用户
   */
  loadSubscribers(): void {
    this.http.get<Subscriber[]>('/api/admin/marketing/subscribers').subscribe((data) => {
      this.subscribers = data;
    });
  }

  /**
   * 过滤联系表单
   */
  filterContacts(): void {
    this.filteredContacts = this.contacts.filter((contact) => {
      const typeMatch = !this.filterType || contact.type === this.filterType;
      const searchMatch =
        !this.searchQuery ||
        contact.name.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
        contact.email.toLowerCase().includes(this.searchQuery.toLowerCase());

      return typeMatch && searchMatch;
    });
  }

  /**
   * 查看联系表单详情
   */
  viewContact(contact: ContactForm): void {
    // TODO: 打开详情对话框
    console.log('View contact:', contact);
  }

  /**
   * 管理订阅用户
   */
  manageSubscriber(subscriber: Subscriber): void {
    // TODO: 打开管理对话框
    console.log('Manage subscriber:', subscriber);
  }
}

/**
 * 营销指标接口
 */
export interface MarketingMetrics {
  pageViews: number;
  pageViewsTrend: number;
  contactForms: number;
  contactFormsTrend: number;
  newSubscribers: number;
  newSubscribersTrend: number;
  avgTimeOnPage: number;
  avgTimeOnPageTrend: number;
}

/**
 * 页面统计接口
 */
export interface PageStat {
  name: string;
  views: number;
  uniqueVisitors: number;
  bounceRate: number;
  avgDuration: number;
}

/**
 * 联系表单接口
 */
export interface ContactForm {
  id: string;
  createdAt: string;
  name: string;
  email: string;
  phone?: string;
  type: string;
  typeLabel: string;
  status: string;
  statusLabel: string;
  message: string;
}

/**
 * 订阅用户接口
 */
export interface Subscriber {
  email: string;
  subscribedAt: string;
  status: string;
  verified: boolean;
  frequency: string;
}
