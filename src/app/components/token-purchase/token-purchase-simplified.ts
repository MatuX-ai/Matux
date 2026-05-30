/**
 * Token 购买弹窗组件 - 简化版本
 *
 * 使用统一价格服务，简化Token套餐选择
 *
 * @author iMatu Development Team
 * @version 2.0.0
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

import { formatPrice, PriceType, UnifiedPriceItem } from '../../core/models/pricing.models';
import { PricingService } from '../../core/services/pricing.service';

/**
 * 弹窗数据类型
 */
export interface TokenPurchaseDialogData {
  selectedPackageId?: string;
}

@Component({
  selector: 'app-token-purchase-simplified',
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
  template: `
    <div class="token-purchase-dialog">
      <div class="dialog-header">
        <h2 class="dialog-title">购买 Token</h2>
        <button mat-icon-button class="close-button" (click)="onCancel()">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <div class="dialog-content">
        <!-- 加载状态 -->
        <div *ngIf="isLoading" class="loading-state">
          <mat-spinner diameter="40"></mat-spinner>
          <p>正在加载套餐...</p>
        </div>

        <!-- 错误状态 -->
        <div *ngIf="errorMessage" class="error-state">
          <mat-icon class="error-icon">error</mat-icon>
          <p>{{ errorMessage }}</p>
          <button mat-button (click)="loadPackages()">重试</button>
        </div>

        <!-- 套餐选择 -->
        <div *ngIf="!isLoading && !errorMessage" class="packages-section">
          <div class="section-header">
            <h3 class="section-title">选择 Token 套餐</h3>
            <p class="section-subtitle">按需购买，灵活使用</p>
          </div>

          <div class="packages-grid">
            <div
              *ngFor="let package of packages"
              [class.selected]="selectedPackageId === package.id"
              [class.popular]="package.isPopular"
              class="package-card"
              (click)="selectPackage(package.id)"
            >
              <!-- 热门标识 -->
              <div *ngIf="package.isPopular" class="popular-badge">🔥 热门</div>

              <!-- 套餐信息 -->
              <div class="package-header">
                <h4 class="package-name">{{ package.name }}</h4>
                <p class="package-desc" *ngIf="package.description">
                  {{ package.description }}
                </p>
              </div>

              <!-- Token数量 -->
              <div class="token-amount">
                <span class="amount">{{
                  package.metadata.tokenAmount?.toLocaleString() || '自定义'
                }}</span>
                <span class="unit">Token</span>
              </div>

              <!-- 价格信息 -->
              <div class="price-info">
                <div class="current-price">
                  {{ formatPrice(package.price.current) }}
                </div>
                <div *ngIf="package.price.original" class="original-price">
                  {{ formatPrice(package.price.original) }}
                </div>
                <div *ngIf="package.price.discount" class="discount-badge">
                  -{{ (package.price.discount * 100).toFixed(0) }}%
                </div>
              </div>

              <!-- 有效期 -->
              <div class="validity" *ngIf="package.metadata.validityDays">
                有效期: {{ package.metadata.validityDays }}天
              </div>

              <!-- 选择指示器 -->
              <div class="selection-indicator">
                <div class="radio-circle">
                  <div *ngIf="selectedPackageId === package.id" class="radio-selected"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- 功能列表 -->
          <div class="features-section" *ngIf="selectedPackage">
            <h4 class="features-title">包含功能</h4>
            <div class="features-list">
              <div *ngFor="let feature of selectedPackage.features" class="feature-item">
                <mat-icon class="feature-icon">check_circle</mat-icon>
                <span>{{ feature }}</span>
              </div>
            </div>
          </div>

          <!-- 支付方式 -->
          <div class="payment-section">
            <h4 class="payment-title">选择支付方式</h4>
            <div class="payment-options">
              <label class="payment-option">
                <input
                  type="radio"
                  name="paymentMethod"
                  [(ngModel)]="paymentMethod"
                  value="alipay"
                />
                <div class="option-content">
                  <mat-icon class="option-icon">payment</mat-icon>
                  <span class="option-text">支付宝</span>
                </div>
              </label>

              <label class="payment-option">
                <input
                  type="radio"
                  name="paymentMethod"
                  [(ngModel)]="paymentMethod"
                  value="wechat"
                />
                <div class="option-content">
                  <mat-icon class="option-icon">payment</mat-icon>
                  <span class="option-text">微信支付</span>
                </div>
              </label>

              <label class="payment-option">
                <input
                  type="radio"
                  name="paymentMethod"
                  [(ngModel)]="paymentMethod"
                  value="credit_card"
                />
                <div class="option-content">
                  <mat-icon class="option-icon">credit_card</mat-icon>
                  <span class="option-text">信用卡</span>
                </div>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- 对话框底部 -->
      <div class="dialog-footer">
        <div class="summary-section" *ngIf="selectedPackage">
          <div class="summary-row">
            <span>套餐:</span>
            <strong>{{ selectedPackage.name }}</strong>
          </div>
          <div class="summary-row">
            <span>Token数量:</span>
            <strong
              >{{
                selectedPackage.metadata.tokenAmount?.toLocaleString() || '自定义'
              }}
              Token</strong
            >
          </div>
          <div class="summary-row total">
            <span>总金额:</span>
            <strong class="total-amount">
              {{ formatPrice(selectedPackage.price.current) }}
            </strong>
          </div>
        </div>

        <div class="action-buttons">
          <button mat-button class="cancel-button" (click)="onCancel()">取消</button>
          <button
            mat-raised-button
            class="purchase-button"
            [disabled]="!selectedPackageId || isPurchasing"
            (click)="onPurchase()"
          >
            <mat-spinner *ngIf="isPurchasing" diameter="20"></mat-spinner>
            <span *ngIf="!isPurchasing"
              >立即支付
              {{ selectedPackage ? formatPrice(selectedPackage.price.current) : '' }}</span
            >
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .token-purchase-dialog {
        width: 100%;
        max-width: 800px;
        background: white;
        border-radius: 12px;
        overflow: hidden;
      }

      .dialog-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 24px;
        border-bottom: 1px solid #e8e8ed;
      }

      .dialog-title {
        margin: 0;
        font-size: 24px;
        font-weight: 600;
        color: #1d1d1f;
      }

      .close-button {
        color: #86868b;
      }

      .dialog-content {
        padding: 24px;
        max-height: 600px;
        overflow-y: auto;
      }

      .loading-state,
      .error-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px 24px;
        text-align: center;
      }

      .loading-state p {
        margin-top: 16px;
        color: #86868b;
      }

      .error-state {
        color: #dc2626;
      }

      .error-icon {
        font-size: 48px;
        width: 48px;
        height: 48px;
        margin-bottom: 16px;
      }

      .section-header {
        margin-bottom: 24px;
      }

      .section-title {
        margin: 0 0 8px 0;
        font-size: 18px;
        font-weight: 600;
        color: #1d1d1f;
      }

      .section-subtitle {
        margin: 0;
        font-size: 14px;
        color: #86868b;
      }

      .packages-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 16px;
        margin-bottom: 32px;
      }

      .package-card {
        position: relative;
        padding: 20px;
        border: 2px solid #e8e8ed;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .package-card:hover {
        border-color: #667eea;
        transform: translateY(-2px);
      }

      .package-card.selected {
        border-color: #667eea;
        background: linear-gradient(
          135deg,
          rgba(102, 126, 234, 0.05) 0%,
          rgba(118, 75, 162, 0.05) 100%
        );
      }

      .package-card.popular {
        border-color: #f59e0b;
      }

      .popular-badge {
        position: absolute;
        top: -10px;
        right: 16px;
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
      }

      .package-header {
        margin-bottom: 16px;
      }

      .package-name {
        margin: 0 0 4px 0;
        font-size: 16px;
        font-weight: 600;
        color: #1d1d1f;
      }

      .package-desc {
        margin: 0;
        font-size: 13px;
        color: #86868b;
        line-height: 1.4;
      }

      .token-amount {
        text-align: center;
        margin-bottom: 16px;
        padding: 12px;
        background: #f5f5f7;
        border-radius: 8px;
      }

      .amount {
        font-size: 24px;
        font-weight: 700;
        color: #1d1d1f;
      }

      .unit {
        font-size: 14px;
        color: #86868b;
        margin-left: 4px;
      }

      .price-info {
        text-align: center;
        margin-bottom: 12px;
      }

      .current-price {
        font-size: 20px;
        font-weight: 700;
        color: #1d1d1f;
      }

      .original-price {
        font-size: 14px;
        color: #86868b;
        text-decoration: line-through;
        margin-top: 4px;
      }

      .discount-badge {
        display: inline-block;
        background: #10b981;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
        margin-top: 4px;
      }

      .validity {
        text-align: center;
        font-size: 12px;
        color: #86868b;
        margin-bottom: 16px;
      }

      .selection-indicator {
        display: flex;
        justify-content: center;
      }

      .radio-circle {
        width: 20px;
        height: 20px;
        border: 2px solid #e8e8ed;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .radio-selected {
        width: 10px;
        height: 10px;
        background: #667eea;
        border-radius: 50%;
      }

      .features-section {
        margin: 32px 0;
        padding: 20px;
        background: #f8f9fa;
        border-radius: 12px;
      }

      .features-title {
        margin: 0 0 16px 0;
        font-size: 16px;
        font-weight: 600;
        color: #1d1d1f;
      }

      .features-list {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
      }

      .feature-item {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .feature-icon {
        color: #10b981;
        font-size: 16px;
        width: 16px;
        height: 16px;
      }

      .feature-item span {
        font-size: 14px;
        color: #3a3a3c;
      }

      .payment-section {
        margin: 32px 0;
      }

      .payment-title {
        margin: 0 0 16px 0;
        font-size: 16px;
        font-weight: 600;
        color: #1d1d1f;
      }

      .payment-options {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
      }

      .payment-option {
        flex: 1;
        min-width: 120px;
      }

      .payment-option input {
        display: none;
      }

      .option-content {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 16px;
        border: 2px solid #e8e8ed;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .payment-option input:checked + .option-content {
        border-color: #667eea;
        background: rgba(102, 126, 234, 0.05);
      }

      .option-icon {
        color: #86868b;
      }

      .option-text {
        font-size: 14px;
        font-weight: 500;
        color: #3a3a3c;
      }

      .dialog-footer {
        padding: 24px;
        border-top: 1px solid #e8e8ed;
      }

      .summary-section {
        margin-bottom: 24px;
        padding: 20px;
        background: #f8f9fa;
        border-radius: 12px;
      }

      .summary-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        font-size: 14px;
      }

      .summary-row:last-child {
        margin-bottom: 0;
      }

      .summary-row.total {
        padding-top: 12px;
        border-top: 1px solid #e8e8ed;
      }

      .total-amount {
        font-size: 18px;
        color: #1d1d1f;
      }

      .action-buttons {
        display: flex;
        justify-content: flex-end;
        gap: 12px;
      }

      .cancel-button {
        color: #86868b;
      }

      .purchase-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        min-width: 160px;
      }

      .purchase-button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }

      /* Responsive */
      @media (max-width: 768px) {
        .packages-grid {
          grid-template-columns: 1fr;
        }

        .payment-options {
          flex-direction: column;
        }

        .payment-option {
          min-width: auto;
        }

        .action-buttons {
          flex-direction: column;
        }

        .purchase-button {
          width: 100%;
        }
      }
    `,
  ],
})
export class TokenPurchaseSimplifiedComponent implements OnInit {
  /** Token套餐列表 */
  packages: UnifiedPriceItem[] = [];

  /** 选中的套餐ID */
  selectedPackageId: string | null = null;

  /** 选中的套餐 */
  selectedPackage: UnifiedPriceItem | null = null;

  /** 支付方式 */
  paymentMethod: 'alipay' | 'wechat' | 'credit_card' = 'alipay';

  /** 加载状态 */
  isLoading = false;

  /** 购买处理状态 */
  isPurchasing = false;

  /** 错误信息 */
  errorMessage: string | null = null;

  constructor(
    public dialogRef: MatDialogRef<TokenPurchaseSimplifiedComponent>,
    @Inject(MAT_DIALOG_DATA) public data: TokenPurchaseDialogData,
    private pricingService: PricingService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadPackages();

    if (this.data?.selectedPackageId) {
      this.selectedPackageId = this.data.selectedPackageId;
    }
  }

  /**
   * 加载Token套餐
   */
  loadPackages(): void {
    this.isLoading = true;
    this.errorMessage = null;

    this.pricingService
      .getPricesByType(PriceType.TOKEN_PACKAGE, {
        activeOnly: true,
        sortBy: 'price',
        sortOrder: 'asc',
      })
      .subscribe({
        next: (packages) => {
          this.packages = packages;
          this.isLoading = false;

          // 自动选择推荐套餐
          if (!this.selectedPackageId && packages.length > 0) {
            const recommended = packages.find((p) => p.isRecommended) || packages[0];
            this.selectPackage(recommended.id);
          }
        },
        error: (error) => {
          console.error('加载Token套餐失败:', error);
          this.errorMessage = '加载套餐失败，请稍后重试';
          this.isLoading = false;
        },
      });
  }

  /**
   * 选择套餐
   */
  selectPackage(packageId: string): void {
    this.selectedPackageId = packageId;
    this.selectedPackage = this.packages.find((p) => p.id === packageId) || null;
  }

  /**
   * 格式化价格显示
   */
  formatPrice(priceCents: number): string {
    return formatPrice(priceCents, 'CNY');
  }

  /**
   * 取消购买
   */
  onCancel(): void {
    this.dialogRef.close();
  }

  /**
   * 执行购买
   */
  onPurchase(): void {
    if (!this.selectedPackageId || !this.selectedPackage) {
      return;
    }

    this.isPurchasing = true;

    // 模拟购买过程
    setTimeout(() => {
      this.isPurchasing = false;
      this.snackBar.open('购买成功！Token已添加到您的账户', '关闭', {
        duration: 3000,
      });
      this.dialogRef.close({ success: true, packageId: this.selectedPackageId });
    }, 1500);
  }
}
