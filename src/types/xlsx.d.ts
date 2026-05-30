/**
 * XLSX 库的类型定义扩展
 * 补充 @types/xlsx 中缺失的类型定义
 */

import 'xlsx';

declare module 'xlsx' {
  interface IUtils {
    /** 创建一个新的工作簿 */
    book_new(): IWorkBook;

    /** 将 JSON 数据转换为工作表 */
    json_to_sheet<T>(data: T[], opts?: Partial<XLSX.JSON2SheetOpts>): IWorkSheet;

    /** 将工作表添加到工作簿 */
    book_append_sheet(workbook: IWorkBook, worksheet: IWorkSheet, sheetName?: string): void;
  }

  interface IWritingOptions {
    /**
     * Output data encoding - extended to include 'array'
     */
    type?: 'base64' | 'binary' | 'buffer' | 'file' | 'array';
  }
}
