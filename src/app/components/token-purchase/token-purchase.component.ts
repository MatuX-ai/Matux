/**
 * Token 购买弹窗组件
 *
 * 提供 Token 套餐选择和购买功能
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { CommonModule } from '@angular/common';
import { Component, Inject, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatRadioModule } from '@angular/material/radio';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { TokenService } from '../../core/services/token.service';
import { TokenPackage } from '../../models/token.models';

/**
 * 弹窗数据类型
 */
export interface TokenPurchaseDialogData {
  selectedPackageId?: string;
}

@Component({
  selector: 'app-token-purchase',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatSnackBarModule,
    MatRadioModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './token-purchase.component.html',
  styleUrls: ['./token-purchase.component.scss'],
})
export class TokenPurchaseComponent implements OnInit {
  /**
   * Token 套餐列表
   */
  packages: TokenPackage[] = [];

  /**
   * 选中的套餐 ID
   */
  selectedPackageId: string | null = null;

  /**
   * 加载中
   */
  loading = false;

  /**
   * 支付方式
   */
  paymentMethod: 'alipay' | 'wechat' | 'credit_card' = 'alipay';

  constructor(
    public dialogRef: MatDialogRef<TokenPurchaseComponent>,
    @Inject(MAT_DIALOG_DATA) public data: TokenPurchaseDialogData,
    private tokenService: TokenService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadPackages();

    if (this.data?.selectedPackageId) {
      this.selectedPackageId = this.data.selectedPackageId;
    }
  }

  /**
   * 加载套餐列表
   */
  loadPackages(): void {
    this.loading = true;
    this.tokenService.getTokenPackages().subscribe({
      next: (packages) => {
        this.packages = packages;
        this.loading = false;

        // 如果没有选中且套餐存在，默认选中第一个
        if (!this.selectedPackageId && packages.length > 0) {
          // 优先选中推荐套餐
          const recommended = packages.find((p) => p.isRecommended) || packages[0];
          this.selectedPackageId = recommended.id;
        }
      },
      error: (error) => {
        console.error('加载套餐失败:', error);
        this.snackBar.open('加载套餐失败，请稍后重试', '关闭', {
          duration: 3000,
        });
        this.loading = false;
      },
    });
  }

  /**
   * 选择套餐
   */
  selectPackage(packageId: string): void {
    this.selectedPackageId = packageId;
  }

  /**
   * 获取选中的套餐
   */
  getSelectedPackage(): TokenPackage | null {
    if (!this.selectedPackageId) return null;
    return this.packages.find((p) => p.id === this.selectedPackageId) || null;
  }

  /**
   * 立即购买
   */
  purchase(): void {
    if (!this.selectedPackageId) {
      this.snackBar.open('请选择一个套餐', '关闭', { duration: 2000 });
      return;
    }

    this.loading = true;

    this.tokenService.purchasePackage(this.selectedPackageId, this.paymentMethod).subscribe({
      next: (response) => {
        this.loading = false;
        this.snackBar.open('订单创建成功！正在跳转支付...', '关闭', { duration: 3000 });

        // TODO: 跳转到支付页面
        // this.router.navigate(['/payment', response.order.id]);

        this.dialogRef.close({ success: true, orderId: response.order.id });
      },
      error: (error) => {
        console.error('购买失败:', error);
        this.snackBar.open(error.message || '购买失败，请稍后重试', '关闭', {
          duration: 3000,
        });
        this.loading = false;
      },
    });
  }

  /**
   * 取消
   */
  cancel(): void {
    this.dialogRef.close({ success: false });
  }

  /**
   * 格式化价格显示（分转元）
   */
  formatPrice(cents: number): string {
    return `¥${(cents / 100).toFixed(2)}`;
  }

  /**
   * 计算折扣
   */
  getDiscount(packageItem: TokenPackage): number | null {
    if (packageItem.discount && packageItem.originalPriceCents) {
      return Math.round((1 - packageItem.discount) * 10);
    }
    return null;
  }
}
