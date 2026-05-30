import { Component } from '@angular/core';

@Component({
  selector: 'app-payment-list',
  template: `
    <div class="payment-list">
      <h1>支付管理</h1>
      <p>支付记录和统计功能</p>
      <div class="placeholder-content">
        <p>这里将显示支付记录和统计功能</p>
      </div>
    </div>
  `,
  styles: [
    `
      .payment-list {
        padding: 20px;
      }

      .placeholder-content {
        margin-top: 20px;
        padding: 20px;
        background: #f5f5f5;
        border-radius: 8px;
        text-align: center;
      }
    `,
  ],
})
export class PaymentListComponent {}
