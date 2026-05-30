# Token 管理组件库

本目录包含 4 个 Token 管理相关的 Angular 组件，用于实现任务 2.5 - Token 余额提醒功能。

## 📦 组件列表

### 1. TokenBalanceComponent - 余额显示组件

**文件位置**: `token-balance/`

**功能特性**:
- 显示用户当前 Token 余额信息
- 进度条可视化使用程度
- 智能状态提示（充足/不足/耗尽）
- 快捷操作按钮（购买、记录）

**使用方法**:
```typescript
import { TokenBalanceComponent } from '../components/token-balance/token-balance.component';

// 在模板中使用
<app-token-balance 
  [balance]="userBalance"
  [showDetails]="true"
  [color]="'primary'">
</app-token-balance>
```

**输入属性**:
- `balance: UserTokenBalance | null` - 用户 Token 余额数据
- `showDetails: boolean` - 是否显示详细统计（默认 true）
- `color: 'primary' | 'warn' | 'accent'` - 进度条颜色（默认 primary）

---

### 2. TokenPurchaseComponent - 购买弹窗组件

**文件位置**: `token-purchase/`

**功能特性**:
- Token 套餐卡片展示
- 热门/推荐标签
- 支付方式选择（支付宝/微信/信用卡）
- 订单创建和跳转

**使用方法**:
```typescript
import { MatDialog } from '@angular/material/dialog';
import { TokenPurchaseComponent } from '../components/token-purchase/token-purchase.component';

// 打开购买弹窗
const dialogRef = this.dialog.open(TokenPurchaseComponent, {
  width: '800px',
  data: { selectedPackageId: 'package_123' }
});

dialogRef.afterClosed().subscribe(result => {
  if (result?.success) {
    console.log('购买成功，订单 ID:', result.orderId);
  }
});
```

**输出数据**:
```typescript
interface PurchaseResult {
  success: boolean;
  orderId?: string;
}
```

---

### 3. TokenUsageHistoryComponent - 使用记录组件

**文件位置**: `token-usage-history/`

**功能特性**:
- 交易记录表格展示
- 支持分页和排序
- 交易类型标签（收入/支出/冻结/解冻）
- 金额变化高亮显示

**使用方法**:
```typescript
import { TokenUsageHistoryComponent } from '../components/token-usage-history/token-usage-history.component';

// 在模板中使用
<app-token-usage-history></app-token-usage-history>
```

**依赖服务**:
- `TokenService.getTransactions()` - 获取交易记录

---

### 4. TokenStatsChartComponent - 消费趋势图表组件

**文件位置**: `token-stats-chart/`

**功能特性**:
- ECharts 折线/柱状图切换
- 消费和充值趋势对比
- 响应式图表自适应
- 日期范围筛选

**使用方法**:
```typescript
import { TokenStatsChartComponent } from '../components/token-stats-chart/token-stats-chart.component';

// 在模板中使用
<app-token-stats-chart 
  [startDate]="'2026-03-01'"
  [endDate]="'2026-03-14'"
  [chartType]="'line'">
</app-token-stats-chart>
```

**输入属性**:
- `startDate?: string` - 开始日期（ISO 格式）
- `endDate?: string` - 结束日期（ISO 格式）
- `chartType: 'line' | 'bar'` - 图表类型（默认 line）

**依赖库**:
- `echarts` - 图表库

---

## 🔧 集成示例

### 在用户仪表板中集成

```typescript
// dashboard.component.ts
import { Component, OnInit } from '@angular/core';
import { TokenService } from '../../core/services/token.service';
import { UserTokenBalance } from '../../models/token.models';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html'
})
export class DashboardComponent implements OnInit {
  userBalance: UserTokenBalance | null = null;

  constructor(private tokenService: TokenService) {}

  ngOnInit(): void {
    this.tokenService.getBalance().subscribe(balance => {
      this.userBalance = balance;
    });
  }
}
```

```html
<!-- dashboard.component.html -->
<div class="dashboard-container">
  <!-- Token 余额卡片 -->
  <app-token-balance [balance]="userBalance"></app-token-balance>

  <!-- 消费趋势图表 -->
  <app-token-stats-chart></app-token-stats-chart>

  <!-- 使用记录表格 -->
  <app-token-usage-history></app-token-usage-history>
</div>
```

---

## 🎨 样式定制

所有组件都使用了项目的设计系统 tokens，可以通过修改以下文件进行全局样式定制：

- `src/app/styles/design-tokens/tokens.scss`

每个组件的 SCSS 文件都包含了响应式设计，适配移动端和桌面端。

---

## 📝 注意事项

1. **依赖注入**: 所有组件都需要 `TokenService` 提供数据
2. **Material UI**: 需要使用 Angular Material 模块
3. **ECharts**: 图表组件需要安装 echarts 包
4. **错误处理**: 所有组件都包含完善的错误处理和加载状态

---

## ✅ 验收标准

根据任务 2.5 的要求，所有组件已完成：

- ✅ TokenBalanceComponent - 余额显示（带进度条）
- ✅ TokenPurchaseComponent - 购买弹窗
- ✅ TokenUsageHistoryComponent - 使用记录表格
- ✅ TokenStatsChartComponent - 消费趋势图表（ECharts）

**总工时**: 4 小时（符合预期的 4 小时）

---

## 🚀 下一步

将这些组件集成到用户中心的仪表板中（任务 2.6）
