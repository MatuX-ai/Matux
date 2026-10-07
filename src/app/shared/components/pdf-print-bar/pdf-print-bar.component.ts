/**
 * 通用打印/PDF 操作栏组件 (P4-F)
 *
 * 用法：
 * <app-pdf-print-bar
 *   title="学习报告"
 *   [pdfBlob]="pdfBlob$"
 *   [pdfFilename]="'学习报告_2026Q1'"
 *   [showPdf]="true"
 *   [showPrint]="true"
 *   (printed)="onPrinted()"
 * ></app-pdf-print-bar>
 *
 * - 当后端不可用时，PDF 按钮会自动回退到浏览器打印对话框
 * - 全局打印样式已经处理好，无需每个页面单独写 @media print
 */
import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Observable, of } from 'rxjs';

import { PdfPrintService } from '../../services/pdf-print.service';

@Component({
  selector: 'app-pdf-print-bar',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatTooltipModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="pdf-print-bar" *ngIf="showPdf || showPrint">
      <button
        *ngIf="showPdf"
        mat-raised-button
        color="primary"
        class="pdf-btn"
        (click)="onExportPdf()"
        [disabled]="exporting || !pdfBlob"
        [matTooltip]="pdfTooltip || '导出为 PDF'"
      >
        <mat-icon>picture_as_pdf</mat-icon>
        {{ exporting ? '导出中...' : (pdfLabel || '导出PDF') }}
      </button>
      <button
        *ngIf="showPrint"
        mat-stroked-button
        class="print-btn"
        (click)="onPrint()"
        [matTooltip]="'打印当前' + (title || '页面')"
      >
        <mat-icon>print</mat-icon>
      </button>
    </div>
  `,
  styles: [
    `
      .pdf-print-bar {
        display: inline-flex;
        gap: 8px;
        align-items: center;
      }
    `,
  ],
})
export class PdfPrintBarComponent implements OnChanges {
  /** 后端 PDF Blob Observable（可选） */
  @Input() pdfBlob: Observable<Blob> | null = null;

  /** 导出的 PDF 文件名（不含扩展名） */
  @Input() pdfFilename = 'document';

  /** 按钮文本 */
  @Input() pdfLabel = '导出PDF';

  /** Tooltip */
  @Input() pdfTooltip = '';

  /** 标题（用于打印 tooltip） */
  @Input() title = '页面';

  /** 是否显示 PDF 按钮 */
  @Input() showPdf = true;

  /** 是否显示打印按钮 */
  @Input() showPrint = true;

  /** 是否在 PDF 失败时回退到打印 */
  @Input() fallbackToPrint = true;

  /** 自定义 PDF 成功提示 */
  @Input() pdfSuccessMessage = '';

  /** 自定义 PDF 失败提示 */
  @Input() pdfErrorMessage = '';

  @Output() pdfExported = new EventEmitter<boolean>();
  @Output() printed = new EventEmitter<void>();

  exporting = false;

  constructor(
    private pdfPrint: PdfPrintService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnChanges(changes: SimpleChanges): void {
    // 文件名变化时无需处理，仅在 PDF 按钮渲染时使用
  }

  onExportPdf(): void {
    if (!this.pdfBlob) {
      // 没传 Blob Observable，直接走打印
      this.pdfPrint.print({
        preparingMessage: '未配置 PDF 源，已切换到浏览器打印',
        successMessage: '打印任务已结束',
      });
      this.printed.emit();
      return;
    }
    this.exporting = true;
    this.cdr.markForCheck();

    this.pdfPrint
      .downloadPdfBlob(this.pdfBlob, {
        filename: this.pdfFilename,
        fallbackToPrint: this.fallbackToPrint,
        successMessage: this.pdfSuccessMessage || `✅ 已导出：${this.pdfFilename}.pdf`,
        errorMessage: this.pdfErrorMessage || '后端 PDF 导出失败，已切换到浏览器打印',
      })
      .subscribe({
        next: (ok) => {
          this.exporting = false;
          this.pdfExported.emit(ok);
          this.cdr.markForCheck();
          if (!ok) {
            // eslint-disable-next-line no-console
            console.warn('[P4-F] PDF 导出失败（已回退到打印）');
          }
        },
        error: () => {
          this.exporting = false;
          this.pdfExported.emit(false);
          this.cdr.markForCheck();
        },
      });
  }

  onPrint(): void {
    const ok = this.pdfPrint.print({
      preparingMessage: '正在打开打印对话框…请选择"另存为 PDF"',
      successMessage: '打印任务已结束',
    });
    if (ok) {
      this.printed.emit();
    }
  }

  /** 静态方法：生成空白 Observable（供模板用） */
  static emptyBlob(): Observable<Blob> {
    return of(new Blob());
  }
}
