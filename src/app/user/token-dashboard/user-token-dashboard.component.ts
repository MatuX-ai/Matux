/**
 * 用户 Token 仪表板组件
 *
 * 集成 Token 余额、购买、使用记录和消费趋势图表
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule } from '@angular/material/dialog';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSnackBar } from '@angular/material/snack-bar';
import { RouterModule } from '@angular/router';

import { TokenPurchaseComponent } from '../../components/token-purchase/token-purchase.component';
import { TokenService } from '../../core/services/token.service';
import { UserTokenBalance } from '../../models/token.models';

interface TokenPackage {
  id: string;
  name: string;
  price: number;
  tokens: number;
  isPopular?: boolean;
}

@Component({
  selector: 'app-user-token-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatDialogModule,
    MatSnackBarModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './user-token-dashboard.component.html',
  styleUrls: ['./user-token-dashboard.component.scss'],
})
export class UserTokenDashboardComponent implements OnInit {
  userBalance: UserTokenBalance | null = null;
  loading = false;
  error: string | null = null;

  packages: TokenPackage[] = [
    { id: '1', name: '基础套餐', price: 9.9, tokens: 100 },
    { id: '2', name: '标准套餐', price: 49, tokens: 600, isPopular: true },
    { id: '3', name: '高级套餐', price: 99, tokens: 1500 },
    { id: '4', name: '豪华套餐', price: 299, tokens: 5000 },
  ];

  constructor(
    private tokenService: TokenService,
    private dialog: MatDialog,
    private snackBar: MatSnackBar,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadBalance();
  }

  loadBalance(): void {
    this.loading = true;
    this.error = null;

    this.tokenService.getBalance().subscribe({
      next: (balance) => {
        this.userBalance = balance;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (error: unknown) => {
        const errorMessage = (error as { message?: string }).message ?? '加载数据失败';
        this.error = errorMessage;
        this.loading = false;
        this.snackBar.open(errorMessage, '关闭', { duration: 3000 });
      },
    });
  }

  openPurchaseDialog(): void {
    const dialogRef = this.dialog.open(TokenPurchaseComponent, {
      width: '800px',
      maxWidth: '90vw',
      data: {},
    });

    dialogRef.afterClosed().subscribe((result: unknown) => {
      if ((result as { success?: boolean })?.success) {
        this.snackBar.open('购买成功！Token 已到账', '关闭', { duration: 3000 });
        this.loadBalance();
      }
    });
  }

  refreshData(): void {
    this.loadBalance();
    this.snackBar.open('数据已刷新', '关闭', { duration: 2000 });
  }

  selectPackage(_pkg: TokenPackage): void {
    this.openPurchaseDialog();
  }
}
