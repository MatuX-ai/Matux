import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { RouterModule } from '@angular/router';

import { MarketingDashboardComponent } from './marketing-dashboard.component';

/**
 * Admin 营销数据模块
 */
@NgModule({
  imports: [CommonModule, RouterModule, HttpClientModule, MarketingDashboardComponent],
  exports: [MarketingDashboardComponent],
})
export class AdminMarketingModule {}
