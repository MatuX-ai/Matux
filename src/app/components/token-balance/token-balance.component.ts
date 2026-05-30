/**
 * Token 余额显示组件
 *
 * 显示用户当前 Token 余额信息，包括：
 * - 总余额
 * - 已用额度
 * - 剩余额度
 * - 进度条可视化
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { CommonModule } from '@angular/common';
import { Component, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';

import { UserTokenBalance } from '../../models/token.models';

@Component({
  selector: 'app-token-balance',
  standalone: true,
  imports: [CommonModule, MatProgressBarModule, MatIconModule],
  templateUrl: './token-balance.component.html',
  styleUrls: ['./token-balance.component.scss'],
})
export class TokenBalanceComponent implements OnInit, OnChanges {
  /**
   * 用户 Token 余额数据
   */
  @Input() balance: UserTokenBalance | null = null;

  /**
   * 是否显示详细统计
   */
  @Input() showDetails: boolean = true;

  /**
   * 进度条颜色
   */
  @Input() color: 'primary' | 'warn' | 'accent' = 'primary';

  // 计算属性
  totalTokens: number = 0;
  usedTokens: number = 0;
  remainingTokens: number = 0;
  usagePercent: number = 0;

  constructor() {}

  ngOnInit(): void {
    this.updateBalanceData();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['balance']) {
      this.updateBalanceData();
    }
  }

  /**
   * 更新余额数据
   */
  private updateBalanceData(): void {
    if (this.balance) {
      this.totalTokens = this.balance.totalPurchased || 0;
      this.usedTokens = this.balance.totalConsumed || 0;
      this.remainingTokens = this.balance.availableBalance || 0;

      // 计算使用百分比
      if (this.totalTokens > 0) {
        this.usagePercent = (this.usedTokens / this.totalTokens) * 100;
      } else {
        this.usagePercent = 0;
      }
    } else {
      this.totalTokens = 0;
      this.usedTokens = 0;
      this.remainingTokens = 0;
      this.usagePercent = 0;
    }
  }

  /**
   * 获取进度条颜色
   */
  getProgressColor(): string {
    if (this.usagePercent >= 90) {
      return 'warn'; // 红色警告
    } else if (this.usagePercent >= 70) {
      return 'accent'; // 橙色提醒
    } else {
      return this.color; // 默认颜色
    }
  }

  /**
   * 格式化数字显示
   */
  formatNumber(num: number): string {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  }

  /**
   * 获取余额状态文本
   */
  getStatusText(): string {
    if (!this.balance || this.totalTokens === 0) {
      return '暂无 Token';
    }

    if (this.remainingTokens === 0) {
      return 'Token 已耗尽';
    }

    if (this.usagePercent >= 90) {
      return 'Token 即将耗尽';
    }

    if (this.usagePercent >= 70) {
      return 'Token 不足';
    }

    return 'Token 充足';
  }

  /**
   * 获取状态图标
   */
  getStatusIcon(): string {
    if (!this.balance || this.totalTokens === 0) {
      return 'account_balance_wallet';
    }

    if (this.remainingTokens === 0) {
      return 'warning';
    }

    if (this.usagePercent >= 90) {
      return 'error_outline';
    }

    if (this.usagePercent >= 70) {
      return 'info';
    }

    return 'check_circle';
  }
}
