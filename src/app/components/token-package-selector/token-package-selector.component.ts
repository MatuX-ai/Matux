import { CommonModule } from '@angular/common';
import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Router, RouterModule } from '@angular/router';

import { TokenBalance, TokenPackage } from '../../models/license.models';
import { LicenseManagementService } from '../../services/license-management.service';

@Component({
  selector: 'app-token-package-selector',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatDialogModule,
    MatSnackBarModule,
  ],
  templateUrl: './token-package-selector.component.html',
  styleUrls: ['./token-package-selector.component.scss'],
})
export class TokenPackageSelectorComponent implements OnInit {
  @ViewChild('purchaseDialog') purchaseDialog!: TemplateRef<any>;

  packages: TokenPackage[] = [];
  balance: TokenBalance | null = null;
  selectedPackageId: number | null = null;
  isLoading = true;

  constructor(
    private licenseService: LicenseManagementService,
    private snackBar: MatSnackBar,
    private dialog: MatDialog,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadPackages();
    this.loadBalance();
  }

  loadPackages(): void {
    this.isLoading = true;
    this.licenseService.getTokenPackages().subscribe({
      next: (packages) => {
        this.packages = packages;
        // 默认选择推荐套餐
        const recommended = packages.find((p) => p.isRecommended);
        if (recommended) {
          this.selectedPackageId = recommended.id;
        }
        this.isLoading = false;
      },
      error: (error) => {
        console.error('加载套餐列表失败:', error);
        this.snackBar.open('加载套餐列表失败，请稍后重试', '关闭', { duration: 3000 });
        this.isLoading = false;
      },
    });
  }

  loadBalance(): void {
    this.licenseService.getTokenBalance().subscribe({
      next: (balance) => {
        this.balance = balance;
      },
      error: (error) => {
        console.error('查询余额失败:', error);
      },
    });
  }

  selectPackage(packageId: number): void {
    this.selectedPackageId = packageId;
  }

  onPurchase(event: Event, pkg: TokenPackage): void {
    event.stopPropagation();

    const dialogRef = this.dialog.open(this.purchaseDialog, {
      width: '500px',
      data: {
        packageName: pkg.name,
        tokenAmount: pkg.tokenAmount,
        price: pkg.price,
        validityDays: pkg.validityDays,
      },
    });
  }

  cancelPurchase(): void {
    this.dialog.closeAll();
  }

  confirmPurchase(): void {
    // TODO: 实现真实购买流程
    this.dialog.closeAll();

    // 模拟购买成功
    setTimeout(() => {
      this.snackBar.open('购买成功！Token 已充值到账户', '关闭', { duration: 3000 });
      this.loadBalance();
    }, 500);
  }

  viewTransactions(): void {
    // TODO: 导航到交易记录页面
    this.snackBar.open('交易记录功能开发中...', '关闭', { duration: 2000 });
    // this.router.navigate(['/management/token/transactions']);
  }
}
