/**
 * Token 组件使用示例模块
 *
 * 演示如何在实际项目中使用 Token 管理组件
 */

import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
// Angular Material
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSortModule } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';
import { RouterModule } from '@angular/router';

// Token 组件
import { TokenBalanceComponent } from './token-balance/token-balance.component';

/**
 * Token 组件模块
 *
 * 使用方法:
 * 1. 在需要的模块中导入 TokenComponentsModule
 * 2. 在模板中使用对应的组件标签
 */
@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatProgressBarModule,
    MatDialogModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatChipsModule,
    MatSnackBarModule,
    TokenBalanceComponent,
  ],
  exports: [TokenBalanceComponent],
})
export class TokenComponentsModule {
  // 注意：TokenPurchaseComponent, TokenUsageHistoryComponent,
  // TokenStatsChartComponent 是 standalone 组件
  // 直接使用它们的文件路径导入即可，无需通过此模块
}
