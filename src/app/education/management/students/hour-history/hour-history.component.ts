/**
 * 课时流水记录组件 - 学员/管理员查看
 */

import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSortModule } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';

interface HourTransaction {
  id: string;
  transactionType: 'purchase' | 'consumption' | 'refund' | 'adjustment';
  changeHours: number;
  balanceBefore: number;
  balanceAfter: number;
  createdAt: Date;
  notes?: string;
}

@Component({
  selector: 'app-hour-history',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatChipsModule,
    MatIconModule,
    MatProgressBarModule,
  ],
  template: `
    <div class="hour-history-container">
      <mat-card>
        <mat-card-header>
          <mat-card-title>课时流水记录</mat-card-title>
          <mat-card-subtitle>记录所有课时的变动情况</mat-card-subtitle>
        </mat-card-header>

        <mat-card-content>
          <!-- 余额概览 -->
          <div class="balance-overview">
            <div class="balance-card">
              <mat-icon>account_balance_wallet</mat-icon>
              <div class="balance-info">
                <div class="label">当前余额</div>
                <div class="value">{{ currentBalance }} 课时</div>
              </div>
            </div>
          </div>

          <!-- 加载状态 -->
          <div *ngIf="loading" class="loading-state">
            <mat-progress-bar mode="indeterminate"></mat-progress-bar>
          </div>

          <!-- 数据表格 -->
          <div *ngIf="!loading" class="table-container">
            <table mat-table [dataSource]="transactions" matSort>
              <ng-container matColumnDef="transactionType">
                <th mat-header-cell *matHeaderCellDef mat-sort-header>类型</th>
                <td mat-cell *matCellDef="let record">
                  <mat-chip-set>
                    <mat-chip [color]="getTypeColor(record.transactionType)">
                      {{ getTypeLabel(record.transactionType) }}
                    </mat-chip>
                  </mat-chip-set>
                </td>
              </ng-container>

              <ng-container matColumnDef="changeHours">
                <th mat-header-cell *matHeaderCellDef mat-sort-header>变动课时</th>
                <td mat-cell *matCellDef="let record">
                  <span
                    [class.positive]="record.changeHours > 0"
                    [class.negative]="record.changeHours < 0"
                  >
                    {{ record.changeHours > 0 ? '+' : '' }}{{ record.changeHours }}
                  </span>
                </td>
              </ng-container>

              <ng-container matColumnDef="balanceBefore">
                <th mat-header-cell *matHeaderCellDef mat-sort-header>变动前余额</th>
                <td mat-cell *matCellDef="let record">{{ record.balanceBefore }}</td>
              </ng-container>

              <ng-container matColumnDef="balanceAfter">
                <th mat-header-cell *matHeaderCellDef mat-sort-header>变动后余额</th>
                <td mat-cell *matCellDef="let record">{{ record.balanceAfter }}</td>
              </ng-container>

              <ng-container matColumnDef="createdAt">
                <th mat-header-cell *matHeaderCellDef mat-sort-header>时间</th>
                <td mat-cell *matCellDef="let record">
                  {{ record.createdAt | date: 'yyyy-MM-dd HH:mm:ss' }}
                </td>
              </ng-container>

              <ng-container matColumnDef="notes">
                <th mat-header-cell *matHeaderCellDef>备注</th>
                <td mat-cell *matCellDef="let record">{{ record.notes || '-' }}</td>
              </ng-container>

              <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
              <tr mat-row *matRowDef="let row; columns: displayedColumns"></tr>
            </table>

            <mat-paginator [pageSizeOptions]="[10, 20, 50]" showFirstLastButtons></mat-paginator>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [
    `
      .hour-history-container {
        padding: 20px;
      }

      .balance-overview {
        margin-bottom: 20px;

        .balance-card {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 20px;
          background: linear-gradient(135deg, #3f51b5 0%, #7986cb 100%);
          color: white;
          border-radius: 8px;

          mat-icon {
            font-size: 48px;
            width: 48px;
            height: 48px;
          }

          .balance-info {
            .label {
              font-size: 14px;
              opacity: 0.9;
            }

            .value {
              font-size: 32px;
              font-weight: bold;
            }
          }
        }
      }

      .loading-state {
        padding: 40px 0;
      }

      .table-container {
        overflow-x: auto;
      }

      table {
        width: 100%;
      }

      .positive {
        color: #4caf50;
        font-weight: bold;
      }

      .negative {
        color: #f44336;
        font-weight: bold;
      }
    `,
  ],
})
export class HourHistoryComponent implements OnInit {
  loading = false;
  transactions: HourTransaction[] = [];
  currentBalance = 0;
  displayedColumns: string[] = [
    'transactionType',
    'changeHours',
    'balanceBefore',
    'balanceAfter',
    'createdAt',
    'notes',
  ];

  ngOnInit(): void {
    this.loadTransactions();
  }

  loadTransactions(): void {
    this.loading = true;

    // TODO: 调用后端 API
    setTimeout(() => {
      this.transactions = [
        {
          id: '1',
          transactionType: 'purchase',
          changeHours: 100,
          balanceBefore: 0,
          balanceAfter: 100,
          createdAt: new Date('2024-01-01'),
          notes: '购买课程包',
        },
        {
          id: '2',
          transactionType: 'consumption',
          changeHours: -2,
          balanceBefore: 100,
          balanceAfter: 98,
          createdAt: new Date(),
          notes: '数学课签到扣减',
        },
      ];
      this.currentBalance = 98;
      this.loading = false;
    }, 1000);
  }

  getTypeColor(type: string): 'primary' | 'accent' | 'warn' {
    switch (type) {
      case 'purchase':
        return 'primary';
      case 'consumption':
        return 'warn';
      case 'refund':
        return 'accent';
      default:
        return 'primary';
    }
  }

  getTypeLabel(type: string): string {
    switch (type) {
      case 'purchase':
        return '购买';
      case 'consumption':
        return '消耗';
      case 'refund':
        return '退费';
      default:
        return type;
    }
  }
}
