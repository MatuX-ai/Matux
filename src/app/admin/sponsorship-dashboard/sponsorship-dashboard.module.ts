import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { BaseChartDirective, provideCharts, withDefaultRegisterables } from 'ng2-charts';

import {
  EChartsVisualizationComponent,
  SponsorshipAnalyticsDashboardComponent,
} from './echarts-visualizations.component';
import {
  SponsorshipCreateDialogComponent,
  SponsorshipDashboardComponent,
} from './sponsorship-dashboard.component';
import { SponsorshipDashboardService } from './sponsorship-dashboard.service';
import { SponsorshipDashboardRoutingModule } from './sponsorship-dashboard-routing.module';

@NgModule({
  declarations: [
    SponsorshipAnalyticsDashboardComponent,
    SponsorshipCreateDialogComponent,
    SponsorshipDashboardComponent,
    EChartsVisualizationComponent,
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    SponsorshipDashboardRoutingModule,
    BaseChartDirective,

    // Angular Material 模块
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatFormFieldModule,
    MatInputModule,
    MatDialogModule,
    MatSnackBarModule,
    MatDatepickerModule,
    MatSelectModule,
    MatNativeDateModule,
  ],
  providers: [SponsorshipDashboardService, provideCharts(withDefaultRegisterables())],
})
export class SponsorshipDashboardModule {}
