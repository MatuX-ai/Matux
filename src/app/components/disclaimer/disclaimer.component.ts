import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-disclaimer',
  template: `
    <div class="disclaimer-banner">
      <div class="container">
        <div class="disclaimer-content">
          <mat-icon class="disclaimer-icon">info</mat-icon>
          <div class="disclaimer-text">
            <h3 class="disclaimer-title">重要声明</h3>
            <div class="disclaimer-items">
              <p>
                <strong>项目性质：</strong>iMato
                是一个开源教育平台项目，旨在提供机器人教育的教学资源和工具
              </p>
              <p><strong>功能状态：</strong>部分功能处于开发阶段，实际可用功能以代码实现为准</p>
              <p><strong>技术指标：</strong>文档中的性能数据基于内部测试，实际表现可能有所不同</p>
              <p><strong>商业用途：</strong>本项目仅供学习和研究使用，商业应用请联系维护者</p>
            </div>
            <p class="disclaimer-note">本网站部分内容可能涉及未来规划，不构成任何承诺或保证</p>
          </div>
          <button mat-icon-button (click)="dismiss()" class="dismiss-btn" title="不再显示">
            <mat-icon>close</mat-icon>
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .disclaimer-banner {
        background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%);
        border-bottom: 2px solid #ffc107;
        padding: 20px 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }

      .disclaimer-content {
        display: flex;
        align-items: flex-start;
        gap: 16px;
        position: relative;
      }

      .disclaimer-icon {
        font-size: 32px;
        width: 32px;
        height: 32px;
        color: #ffc107;
        flex-shrink: 0;
      }

      .disclaimer-text {
        flex: 1;
      }

      .disclaimer-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #856404;
        margin-bottom: 12px;
      }

      .disclaimer-items {
        p {
          color: #856404;
          font-size: 0.9rem;
          line-height: 1.6;
          margin-bottom: 8px;

          strong {
            color: #664d03;
          }
        }
      }

      .disclaimer-note {
        color: #664d03 !important;
        font-size: 0.85rem !important;
        font-style: italic;
        margin-top: 12px !important;
        padding-top: 8px !important;
        border-top: 1px dashed #ffc107 !important;
      }

      .dismiss-btn {
        position: absolute;
        top: 0;
        right: 0;
        color: #856404;

        &:hover {
          background: rgba(133, 100, 4, 0.1);
        }
      }

      .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 24px;
      }

      @media (max-width: 768px) {
        .disclaimer-content {
          flex-direction: column;
          gap: 12px;
        }

        .dismiss-btn {
          position: static;
          align-self: flex-end;
        }

        .disclaimer-title {
          font-size: 1.1rem;
        }

        .disclaimer-items p {
          font-size: 0.85rem;
        }
      }
    `,
  ],
  imports: [CommonModule, MatButtonModule, MatIconModule],
})
export class DisclaimerComponent implements OnInit {
  constructor() {}

  ngOnInit(): void {}

  dismiss(): void {
    // 可以添加本地存储逻辑来记住用户的选择
    const element = document.querySelector('.disclaimer-banner');
    if (element) {
      element.remove();
    }
  }
}
