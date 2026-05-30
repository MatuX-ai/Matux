import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
// Angular Material Modules
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterModule } from '@angular/router';

// Feature Modules
import { AdminAuthModule } from './auth/auth.module';
import { DashboardModule } from './dashboard/dashboard.module';
import { DatabaseRegistryModule } from './database-registry/database-registry.module'; // 新增
import { LicensesModule } from './licenses/licenses.module';
import { AdminMarketingModule } from './marketing/marketing.module'; // 新增营销数据模块
import { PaymentsModule } from './payments/payments.module';
import { SponsorshipDashboardModule } from './sponsorship-dashboard/sponsorship-dashboard.module';
import { UsersModule } from './users/users.module';
// Routing
import { AdminRoutingModule } from './admin-routing.module';

@NgModule({
  imports: [
    CommonModule,
    RouterModule,
    AdminRoutingModule,

    // Angular Material Modules
    MatIconModule,
    MatListModule,
    MatButtonModule,
    MatToolbarModule,
    MatSidenavModule,
    MatMenuModule,
    MatTooltipModule,
    MatCardModule,
    MatProgressSpinnerModule,

    // Feature Modules
    AdminAuthModule,
    DashboardModule,
    LicensesModule,
    PaymentsModule,
    UsersModule,
    SponsorshipDashboardModule,
    DatabaseRegistryModule, // 新增数据库注册表模块
    AdminMarketingModule, // 新增营销数据模块
  ],
})
export class AdminModule {}
