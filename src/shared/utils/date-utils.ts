/**
 * 日期时间处理工具函数集合
 */

/**
 * 格式化日期时间
 * @param date 日期对象或时间戳
 * @param format 格式字符串，如 'YYYY-MM-DD HH:mm:ss'
 * @returns 格式化后的字符串
 */
export function formatDate(date: Date | number | string, format: string = 'YYYY-MM-DD'): string {
  const d = new Date(date);
  if (isNaN(d.getTime())) {
    return '';
  }

  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  const seconds = String(d.getSeconds()).padStart(2, '0');

  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds);
}

/**
 * 获取相对时间描述
 * @param date 目标日期
 * @param baseDate 基准日期，默认为当前时间
 * @returns 相对时间描述，如"2小时前"
 */
export function getTimeAgo(
  date: Date | number | string,
  baseDate: Date | number | string = new Date()
): string {
  const targetDate = new Date(date);
  const now = new Date(baseDate);
  const diffMs = now.getTime() - targetDate.getTime();

  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);
  const diffWeeks = Math.floor(diffDays / 7);
  const diffMonths = Math.floor(diffDays / 30);
  const diffYears = Math.floor(diffDays / 365);

  if (diffSeconds < 60) {
    return '刚刚';
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分钟前`;
  } else if (diffHours < 24) {
    return `${diffHours}小时前`;
  } else if (diffDays < 7) {
    return `${diffDays}天前`;
  } else if (diffWeeks < 4) {
    return `${diffWeeks}周前`;
  } else if (diffMonths < 12) {
    return `${diffMonths}个月前`;
  } else {
    return `${diffYears}年前`;
  }
}

/**
 * 判断是否为同一天
 * @param date1 日期1
 * @param date2 日期2
 * @returns boolean
 */
export function isSameDay(date1: Date | number | string, date2: Date | number | string): boolean {
  const d1 = new Date(date1);
  const d2 = new Date(date2);

  return (
    d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getDate() === d2.getDate()
  );
}

/**
 * 获取日期范围
 * @param startDate 开始日期
 * @param endDate 结束日期
 * @returns 日期数组
 */
export function getDateRange(startDate: Date | string, endDate: Date | string): Date[] {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const dates: Date[] = [];

  const currentDate = new Date(start);
  while (currentDate <= end) {
    dates.push(new Date(currentDate));
    currentDate.setDate(currentDate.getDate() + 1);
  }

  return dates;
}

/**
 * 添加时间单位到日期
 * @param date 原始日期
 * @param amount 数量
 * @param unit 单位 ('days' | 'hours' | 'minutes' | 'seconds')
 * @returns 新日期
 */
export function addTime(
  date: Date | string,
  amount: number,
  unit: 'days' | 'hours' | 'minutes' | 'seconds'
): Date {
  const d = new Date(date);

  switch (unit) {
    case 'days':
      d.setDate(d.getDate() + amount);
      break;
    case 'hours':
      d.setHours(d.getHours() + amount);
      break;
    case 'minutes':
      d.setMinutes(d.getMinutes() + amount);
      break;
    case 'seconds':
      d.setSeconds(d.getSeconds() + amount);
      break;
  }

  return d;
}

/**
 * 计算两个日期之间的差异
 * @param date1 日期1
 * @param date2 日期2
 * @param unit 返回单位 ('days' | 'hours' | 'minutes' | 'seconds')
 * @returns 差异值
 */
export function dateDiff(
  date1: Date | string,
  date2: Date | string,
  unit: 'days' | 'hours' | 'minutes' | 'seconds' = 'days'
): number {
  const d1 = new Date(date1);
  const d2 = new Date(date2);
  const diffMs = Math.abs(d2.getTime() - d1.getTime());

  switch (unit) {
    case 'days':
      return Math.floor(diffMs / (1000 * 60 * 60 * 24));
    case 'hours':
      return Math.floor(diffMs / (1000 * 60 * 60));
    case 'minutes':
      return Math.floor(diffMs / (1000 * 60));
    case 'seconds':
      return Math.floor(diffMs / 1000);
    default:
      return diffMs;
  }
}

/**
 * 获取月份的第一天
 * @param date 日期
 * @returns 该月第一天的日期
 */
export function getFirstDayOfMonth(date: Date | string): Date {
  const d = new Date(date);
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

/**
 * 获取月份的最后一天
 * @param date 日期
 * @returns 该月最后一天的日期
 */
export function getLastDayOfMonth(date: Date | string): Date {
  const d = new Date(date);
  return new Date(d.getFullYear(), d.getMonth() + 1, 0);
}

/**
 * 判断是否为闰年
 * @param year 年份
 * @returns boolean
 */
export function isLeapYear(year: number): boolean {
  return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
}

/**
 * 获取季度信息
 * @param date 日期
 * @returns 季度信息对象
 */
export function getQuarterInfo(date: Date | string): {
  quarter: number;
  startDate: Date;
  endDate: Date;
} {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = d.getMonth();
  const quarter = Math.floor(month / 3) + 1;

  const startDate = new Date(year, (quarter - 1) * 3, 1);
  const endDate = new Date(year, quarter * 3, 0);

  return { quarter, startDate, endDate };
}

export default {
  formatDate,
  getTimeAgo,
  isSameDay,
  getDateRange,
  addTime,
  dateDiff,
  getFirstDayOfMonth,
  getLastDayOfMonth,
  isLeapYear,
  getQuarterInfo,
};
