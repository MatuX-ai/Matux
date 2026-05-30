/**
 * Token 仪表板模块
 *
 * 封装 Token 管理相关组件和路由
 */

import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
// Angular Material
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule } from '@angular/material/snack-bar';

// Token 组件
import { TokenComponentsModule } from '../../components/token-components.module';
import { TokenPurchaseComponent } from '../../components/token-purchase/token-purchase.component';
import { TokenStatsChartComponent } from '../../components/token-stats-chart/token-stats-chart.component';
import { TokenUsageHistoryComponent } from '../../components/token-usage-history/token-usage-history.component';

// 路由
import { TokenDashboardRoutingModule } from './token-dashboard-routing.module';
// 本模块组件 (standalone，不需要在declarations中声明)
import { UserTokenDashboardComponent } from './user-token-dashboard.component';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    FormsModule,
    TokenDashboardRoutingModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatDialogModule,
    MatSnackBarModule,
    MatProgressSpinnerModule,
    TokenComponentsModule,
    // Standalone组件作为路由导入
    UserTokenDashboardComponent,
    TokenPurchaseComponent,
    TokenUsageHistoryComponent,
    TokenStatsChartComponent,
  ],
  exports: [],
})
export class TokenDashboardModule {}
