/**
 * 共享工具函数库入口文件
 */

// 导入各个工具模块
import * as arrayUtils from './array-utils';
import * as dateUtils from './date-utils';
import * as stringUtils from './string-utils';

// 创建统一的工具对象
export const utils = {
  string: stringUtils,
  date: dateUtils,
  array: arrayUtils,
};

// 同时导出所有函数，方便直接使用
export * from './array-utils';
export * from './date-utils';
export * from './string-utils';

// 默认导出
export default utils;

// 类型定义
export type {} from // 可以在这里添加常用的类型定义
'./string-utils';
