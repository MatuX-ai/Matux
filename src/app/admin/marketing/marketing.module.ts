import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';

import { MarketingDashboardComponent } from './marketing-dashboard.component';
import { AdminMarketingRoutingModule } from './marketing-routing.module';

/**
 * Admin 营销数据模块
 */
@NgModule({
  imports: [CommonModule, HttpClientModule, AdminMarketingRoutingModule, MarketingDashboardComponent],
  exports: [MarketingDashboardComponent],
})
export class AdminMarketingModule {}
