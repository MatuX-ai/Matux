/**
 * Token 使用历史记录组件
 *
 * 显示 Token 使用历史记录的表格
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { CommonModule } from '@angular/common';
import { Component, OnInit, ViewChild } from '@angular/core';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';

import { TokenService } from '../../core/services/token.service';
import { TokenTransaction } from '../../models/token.models';

export interface TransactionDisplay {
  id: string;
  type: string;
  amount: number;
  balanceAfter: number;
  source: string;
  description: string;
  createdAt: string;
}

@Component({
  selector: 'app-token-usage-history',
  standalone: true,
  imports: [
    CommonModule,
    MatTableModule,
    MatSortModule,
    MatPaginatorModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatChipsModule,
  ],
  templateUrl: './token-usage-history.component.html',
  styleUrls: ['./token-usage-history.component.scss'],
})
export class TokenUsageHistoryComponent implements OnInit {
  displayedColumns: string[] = [
    'id',
    'type',
    'amount',
    'balanceAfter',
    'source',
    'description',
    'createdAt',
  ];

  dataSource: MatTableDataSource<TransactionDisplay> = new MatTableDataSource();

  loading = false;
  error: string | null = null;

  totalRecords = 0;
  currentPage = 1;
  pageSize = 20;
  totalPages = 0;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor(private tokenService: TokenService) {}

  ngOnInit(): void {
    this.loadTransactions();
  }

  /**
   * 加载交易记录
   */
  loadTransactions(): void {
    this.loading = true;
    this.error = null;

    this.tokenService.getTransactions(this.currentPage, this.pageSize).subscribe({
      next: (response) => {
        this.dataSource.data = response.data.map(this.formatTransaction);
        this.totalRecords = response.total;
        this.totalPages = response.totalPages;
        this.loading = false;
      },
      error: (error) => {
        console.error('加载交易记录失败:', error);
        this.error = error.message || '加载失败，请稍后重试';
        this.loading = false;
      },
    });
  }

  /**
   * 格式化交易数据
   */
  private formatTransaction(transaction: TokenTransaction): TransactionDisplay {
    return {
      id: transaction.id,
      type: transaction.type,
      amount: transaction.amount,
      balanceAfter: transaction.balanceAfter,
      source: transaction.source,
      description: transaction.description || '-',
      createdAt: new Date(transaction.createdAt).toLocaleString('zh-CN'),
    };
  }

  /**
   * 分页变化
   */
  onPageChange(event: any): void {
    this.currentPage = event.pageIndex + 1;
    this.pageSize = event.pageSize;
    this.loadTransactions();
  }

  /**
   * 获取类型标签颜色
   */
  getTypeColor(type: string): string {
    switch (type) {
      case 'income':
        return 'success';
      case 'expense':
        return 'warn';
      case 'freeze':
      case 'unfreeze':
        return 'accent';
      default:
        return '';
    }
  }

  /**
   * 获取类型文本
   */
  getTypeText(type: string): string {
    const typeMap: Record<string, string> = {
      income: '收入',
      expense: '支出',
      freeze: '冻结',
      unfreeze: '解冻',
      expire: '过期',
    };
    return typeMap[type] || type;
  }

  /**
   * 获取来源文本
   */
  getSourceText(source: string): string {
    const sourceMap: Record<string, string> = {
      purchase: '购买',
      reward: '奖励',
      refund: '退款',
      transfer: '转账',
      promotion: '活动',
    };
    return sourceMap[source] || source;
  }

  /**
   * 格式化金额显示
   */
  formatAmount(amount: number): string {
    const sign = amount >= 0 ? '+' : '';
    return `${sign}${amount.toLocaleString()}`;
  }

  /**
   * 刷新数据
   */
  refresh(): void {
    this.loadTransactions();
  }
}
