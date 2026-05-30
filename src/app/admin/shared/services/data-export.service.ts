import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { saveAs } from 'file-saver';
import { jsPDF } from 'jspdf';
import 'jspdf-autotable';
import * as XLSX from 'xlsx';

export interface ExportColumn {
  key: string;
  header: string;
  width?: number;
  format?: (value: unknown) => string;
}

export interface ExportOptions {
  filename: string;
  title?: string;
  description?: string;
  columns: ExportColumn[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any[];
  format: 'pdf' | 'excel' | 'csv';
  /** 桌面端：使用 Electron 原生保存对话框 */
  useNativeDialog?: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class DataExportService {
  private readonly isBrowser: boolean;
  private readonly isElectron: boolean;

  constructor(@Inject(PLATFORM_ID) platformId: object) {
    this.isBrowser = isPlatformBrowser(platformId);
    this.isElectron = this.isBrowser && !!(
      window as unknown as { electronAPI?: unknown }
    ).electronAPI;
  }

  /**
   * 导出数据为主要格式
   */
  async export(options: ExportOptions): Promise<void> {
    switch (options.format) {
      case 'pdf':
        return this.exportToPDFEnhanced(options);
      case 'excel':
        return this.exportToExcel(options);
      case 'csv':
        return this.exportToCSV(options);
      default:
        throw new Error(`不支持的导出格式: ${options.format}`);
    }
  }

  /**
   * 导出为PDF格式
   */
  private async exportToPDF(options: ExportOptions): Promise<void> {
    const doc = new jsPDF({
      orientation: 'landscape',
      unit: 'mm',
      format: 'a4',
    });

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    let currentY = 20;

    // 设置标题
    if (options.title) {
      doc.setFontSize(20);
      doc.setTextColor(40, 40, 40);
      doc.text(options.title, pageWidth / 2, currentY, { align: 'center' });
      currentY += 15;
    }

    // 设置描述
    if (options.description) {
      doc.setFontSize(12);
      doc.setTextColor(80, 80, 80);
      doc.text(options.description, pageWidth / 2, currentY, { align: 'center' });
      currentY += 10;
    }

    // 添加时间和页码信息
    const timestamp = new Date().toLocaleString('zh-CN');
    doc.setFontSize(10);
    doc.setTextColor(100, 100, 100);
    doc.text(`生成时间: ${timestamp}`, 20, currentY);
    doc.text(`数据记录数: ${options.data.length}`, pageWidth - 60, currentY);
    currentY += 15;

    // 准备表格数据
    const headers = options.columns.map((col) => col.header);
    const rows = options.data.map((item) =>
      options.columns.map((col) => {
        const value = item[col.key];
        return col.format ? col.format(value) : String(value ?? '');
      })
    );

    // 添加表格
    (doc as any).autoTable({
      head: [headers],
      body: rows,
      startY: currentY,
      styles: {
        fontSize: 8,
        cellPadding: 3,
      },
      headStyles: {
        fillColor: [63, 81, 181],
        textColor: 255,
        fontStyle: 'bold',
      },
      alternateRowStyles: {
        fillColor: [245, 245, 245],
      },
      theme: 'grid',
    });

    // 添加页脚
    const pageCount = (doc as any).internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(150);
      doc.text(`第 ${i} 页 / 共 ${pageCount} 页`, pageWidth / 2, pageHeight - 10, {
        align: 'center',
      });
    }

    // 保存文件
    doc.save(`${options.filename}.pdf`);
  }

  /**
   * 导出为Excel格式
   */
  private async exportToExcel(options: ExportOptions): Promise<void> {
    // 创建工作簿
    const workbook = XLSX.utils.book_new();

    // 处理数据
    const processedData = options.data.map((item) => {
      const row: any = {};
      options.columns.forEach((col) => {
        const value = item[col.key];
        row[col.header] = col.format ? col.format(value) : (value ?? '');
      });
      return row;
    });

    // 创建主数据工作表
    const worksheet = XLSX.utils.json_to_sheet(processedData);

    // 设置列宽
    const colWidths = options.columns.map((col) => ({
      wch: col.width || Math.max(col.header.length, 15),
    }));
    worksheet['!cols'] = colWidths;

    // 添加工作表到工作簿
    XLSX.utils.book_append_sheet(workbook, worksheet, '数据');

    // 创建元数据工作表
    const metadata = [
      ['报告信息', ''],
      ['报告标题', options.title || options.filename],
      ['生成时间', new Date().toLocaleString('zh-CN')],
      ['数据记录数', options.data.length],
      ['导出格式', 'Excel'],
      ['', ''],
      ['字段说明', ''],
      ...options.columns.map((col) => [col.header, col.key]),
    ];

    const metaWorksheet = XLSX.utils.aoa_to_sheet(metadata);
    XLSX.utils.book_append_sheet(workbook, metaWorksheet, '元数据');

    // 导出文件
    const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'buffer' });
    const blob = new Blob([excelBuffer], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    saveAs(blob, `${options.filename}.xlsx`);
  }

  /**
   * 导出为CSV格式
   */
  private async exportToCSV(options: ExportOptions): Promise<void> {
    // 创建CSV内容
    let csvContent = '';

    // 添加BOM以支持中文
    csvContent += '\uFEFF';

    // 添加标题行
    const headers = options.columns.map((col) => `"${col.header}"`).join(',');
    csvContent += headers + '\n';

    // 添加数据行
    options.data.forEach((item) => {
      const row = options.columns
        .map((col) => {
          const value = item[col.key];
          const formattedValue = col.format ? col.format(value) : String(value ?? '');
          // 转义引号并用引号包围
          return `"${formattedValue.replace(/"/g, '""')}"`;
        })
        .join(',');
      csvContent += row + '\n';
    });

    // 创建并下载文件
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    saveAs(blob, `${options.filename}.csv`);
  }

  /**
   * 快速导出表格数据
   */
  async quickExport(
    data: any[],
    filename: string,
    format: 'excel' | 'csv' = 'excel'
  ): Promise<void> {
    if (!data || data.length === 0) {
      throw new Error('没有数据可供导出');
    }

    // 自动推断列信息
    const keys = Object.keys(data[0]);
    const columns: ExportColumn[] = keys.map((key) => ({
      key,
      header: this.formatHeader(key),
      width: 15,
    }));

    const options: ExportOptions = {
      filename,
      title: filename,
      description: `包含 ${data.length} 条记录的数据导出`,
      columns,
      data,
      format,
    };

    return this.export(options);
  }

  /**
   * 导出图表数据
   */
  async exportChartData(chartData: any, filename: string, chartType: string): Promise<void> {
    const data = Array.isArray(chartData) ? chartData : [chartData];

    const options: ExportOptions = {
      filename: `${filename}_${chartType}`,
      title: `${filename} - ${chartType}图表数据`,
      columns: [
        { key: 'label', header: '标签', width: 20 },
        { key: 'value', header: '数值', width: 15 },
      ],
      data: data.map((item, index) => ({
        label: item.label || `数据点 ${index + 1}`,
        value: item.value || 0,
      })),
      format: 'excel',
    };

    return this.export(options);
  }

  /**
   * 格式化表头（将驼峰命名转为中文）
   */
  private formatHeader(key: string): string {
    const headerMap: { [key: string]: string } = {
      id: 'ID',
      name: '名称',
      email: '邮箱',
      phone: '电话',
      status: '状态',
      createdAt: '创建时间',
      updatedAt: '更新时间',
      total: '总计',
      count: '数量',
      amount: '金额',
      price: '价格',
      date: '日期',
      type: '类型',
      category: '分类',
    };

    return headerMap[key] || this.camelCaseToWords(key);
  }

  /**
   * 驼峰命名转为词语
   */
  private camelCaseToWords(str: string): string {
    return str
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, (s) => s.toUpperCase())
      .trim();
  }

  /**
   * Electron 原生保存对话框（桌面端增强）
   */
  private async saveViaElectronDialog(
    blob: Blob,
    defaultName: string,
    filterName: string,
    extensions: string[]
  ): Promise<void> {
    const electronAPI = (window as unknown as {
      electronAPI?: {
        showSaveDialog?: (opts: {
          defaultPath: string;
          filters: Array<{ name: string; extensions: string[] }>;
        }) => Promise<{ filePath?: string; canceled: boolean }>;
        writeFile?: (path: string, data: ArrayBuffer) => Promise<void>;
      };
    }).electronAPI;

    if (!electronAPI?.showSaveDialog || !electronAPI?.writeFile) {
      // 回退到浏览器下载
      saveAs(blob, defaultName);
      return;
    }

    try {
      const result = await electronAPI.showSaveDialog({
        defaultPath: defaultName,
        filters: [{ name: filterName, extensions }],
      });

      if (!result.canceled && result.filePath) {
        const arrayBuffer = await blob.arrayBuffer();
        await electronAPI.writeFile(result.filePath, arrayBuffer);
      }
    } catch {
      // 回退
      saveAs(blob, defaultName);
    }
  }

  /**
   * 增强型 PDF 导出（大屏桌面优化：A3 横向、小字号）
   */
  private async exportToPDFEnhanced(options: ExportOptions): Promise<void> {
    // 桌面大屏使用 A3 横向以容纳更多列
    const isLargeScreen = window.innerWidth >= 1600;
    const pageFormat = isLargeScreen ? 'a3' : 'a4';

    const doc = new jsPDF({
      orientation: 'landscape',
      unit: 'mm',
      format: pageFormat,
    });

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    let currentY = 15;

    // 标题
    if (options.title) {
      doc.setFontSize(isLargeScreen ? 22 : 18);
      doc.setTextColor(40, 40, 40);
      doc.text(options.title, pageWidth / 2, currentY, { align: 'center' });
      currentY += 12;
    }

    // 描述
    if (options.description) {
      doc.setFontSize(11);
      doc.setTextColor(80, 80, 80);
      doc.text(options.description, pageWidth / 2, currentY, { align: 'center' });
      currentY += 8;
    }

    // 元信息
    const timestamp = new Date().toLocaleString('zh-CN');
    doc.setFontSize(9);
    doc.setTextColor(100, 100, 100);
    doc.text(`生成时间: ${timestamp}`, 15, currentY);
    doc.text(`记录数: ${options.data.length}`, pageWidth - 50, currentY);
    currentY += 12;

    // 表格
    const headers = options.columns.map((col) => col.header);
    const rows = options.data.map((item) =>
      options.columns.map((col) => {
        const value = item[col.key];
        return col.format ? col.format(value) : String(value ?? '');
      })
    );

    (doc as unknown as { autoTable: (opts: Record<string, unknown>) => void }).autoTable({
      head: [headers],
      body: rows,
      startY: currentY,
      styles: {
        fontSize: isLargeScreen ? 8 : 7,
        cellPadding: isLargeScreen ? 3 : 2,
      },
      headStyles: {
        fillColor: [63, 81, 181],
        textColor: 255,
        fontStyle: 'bold',
      },
      alternateRowStyles: {
        fillColor: [245, 245, 245],
      },
      theme: 'grid',
    });

    // 页脚
    const pageCount = (doc as unknown as { internal: { getNumberOfPages: () => number } })
      .internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(7);
      doc.setTextColor(150);
      doc.text(`第 ${i} 页 / 共 ${pageCount} 页`, pageWidth / 2, pageHeight - 8, {
        align: 'center',
      });
    }

    const pdfBlob = doc.output('blob');

    if (options.useNativeDialog && this.isElectron) {
      await this.saveViaElectronDialog(pdfBlob, `${options.filename}.pdf`, 'PDF 文档', ['pdf']);
    } else {
      saveAs(pdfBlob, `${options.filename}.pdf`);
    }
  }
}
