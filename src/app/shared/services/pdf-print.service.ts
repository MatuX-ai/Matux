/**
 * PDF / 打印服务
 *
 * 统一处理 PDF 下载和浏览器打印，支持：
 * 1. 后端返回 Blob 时直接保存为 PDF 文件
 * 2. 后端不可用时回退到浏览器打印对话框（用户可选择"另存为 PDF"）
 * 3. 通过全局 print-stylesheet 控制打印输出
 */
import { Injectable, NgZone } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

export type PdfExportFormat = 'pdf' | 'excel';

export interface PdfDownloadOptions {
  /** 文件名（不含扩展名） */
  filename: string;
  /** 是否在导出失败时回退到打印 */
  fallbackToPrint?: boolean;
  /** 成功提示 */
  successMessage?: string;
  /** 失败提示 */
  errorMessage?: string;
}

export interface PrintOptions {
  /** 打印成功提示 */
  successMessage?: string;
  /** 在打印前是否显示提示 */
  showPreparingMessage?: boolean;
  /** 准备提示的文本 */
  preparingMessage?: string;
}

@Injectable({ providedIn: 'root' })
export class PdfPrintService {
  /** 当前打印状态（用于 UI 展示） */
  private printing = false;
  private exporting = false;

  constructor(
    private snackBar: MatSnackBar,
    private zone: NgZone
  ) {}

  isPrinting(): boolean {
    return this.printing;
  }

  isExporting(): boolean {
    return this.exporting;
  }

  /**
   * 下载后端返回的 Blob 为 PDF 文件
   * @param blob$ 后端返回的 Blob Observable
   * @param options 配置
   */
  downloadPdfBlob(blob$: Observable<Blob>, options: PdfDownloadOptions): Observable<boolean> {
    this.exporting = true;
    const filename = `${options.filename}.pdf`;

    return blob$.pipe(
      map((blob) => {
        // 校验 Blob 是否真的是 PDF/Excel
        if (!blob || blob.size === 0) {
          throw new Error('文件为空');
        }
        this.triggerDownload(blob, filename);
        if (options.successMessage) {
          this.snackBar.open(options.successMessage, '关闭', { duration: 3000 });
        } else {
          this.snackBar.open(`✅ 已导出：${filename}`, '关闭', { duration: 3000 });
        }
        return true;
      }),
      catchError((err) => {
        // 后端不可用 / 错误 → 可选回退到打印
        const msg = options.errorMessage || `PDF 导出失败：${err?.message || '未知错误'}`;
        this.snackBar.open(msg, options.fallbackToPrint ? '使用打印' : '关闭', {
          duration: 5000,
        });
        if (options.fallbackToPrint) {
          // 弹回退提示后，500ms 后触发打印（让用户看到提示）
          setTimeout(() => this.print({}), 500);
        }
        return of(false);
      }),
      map((ok) => {
        this.exporting = false;
        return ok;
      })
    );
  }

  /**
   * 触发浏览器打印对话框
   * - 用户在对话框中可选择"另存为 PDF"
   * - 通过 beforeprint/afterprint 事件感知状态
   */
  print(options: PrintOptions = {}): boolean {
    if (this.printing) {
      return false;
    }

    if (options.showPreparingMessage !== false) {
      this.snackBar.open(options.preparingMessage || '正在打开打印对话框…', '关闭', {
        duration: 2000,
      });
    }

    this.printing = true;
    const afterPrintHandler = () => {
      this.zone.run(() => {
        this.printing = false;
        if (options.successMessage) {
          this.snackBar.open(options.successMessage, '关闭', { duration: 2000 });
        }
      });
      window.removeEventListener('afterprint', afterPrintHandler);
    };
    window.addEventListener('afterprint', afterPrintHandler);

    // 一些浏览器不支持 afterprint，给一个超时兜底
    setTimeout(() => {
      if (this.printing) {
        this.printing = false;
      }
    }, 60_000);

    try {
      window.print();
      return true;
    } catch (e) {
      this.printing = false;
      this.snackBar.open('当前环境不支持打印功能', '关闭', { duration: 3000 });
      return false;
    }
  }

  /**
   * 触发文件下载
   */
  private triggerDownload(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    // 延迟释放 URL，确保下载请求已发出
    setTimeout(() => window.URL.revokeObjectURL(url), 1000);
  }
}
