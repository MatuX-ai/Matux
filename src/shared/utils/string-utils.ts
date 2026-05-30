/**
 * 字符串处理工具函数集合
 */

/**
 * 判断字符串是否为空或仅包含空白字符
 * @param str 待检查的字符串
 * @returns boolean
 */
export function isEmpty(str: string | null | undefined): boolean {
  return str === null || str === undefined || str.trim() === '';
}

/**
 * 判断字符串是否非空
 * @param str 待检查的字符串
 * @returns boolean
 */
export function isNotEmpty(str: string | null | undefined): boolean {
  return !isEmpty(str);
}

/**
 * 截取字符串并添加省略号
 * @param str 原始字符串
 * @param maxLength 最大长度
 * @param suffix 后缀，默认为'...'
 * @returns 处理后的字符串
 */
export function truncate(str: string, maxLength: number, suffix: string = '...'): string {
  if (!str || str.length <= maxLength) {
    return str;
  }
  return str.substring(0, maxLength) + suffix;
}

/**
 * 首字母大写
 * @param str 输入字符串
 * @returns 首字母大写的字符串
 */
export function capitalize(str: string): string {
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * 驼峰命名转换为下划线命名
 * @param str 驼峰命名字符串
 * @returns 下划线命名字符串
 */
export function camelToSnake(str: string): string {
  return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
}

/**
 * 下划线命名转换为驼峰命名
 * @param str 下划线命名字符串
 * @returns 驼峰命名字符串
 */
export function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (match, letter: string) => {
    return letter.toUpperCase();
  });
}

/**
 * 生成随机字符串
 * @param length 字符串长度
 * @returns 随机字符串
 */
export function randomString(length: number = 8): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

/**
 * 移除字符串两端的指定字符
 * @param str 原始字符串
 * @param chars 要移除的字符
 * @returns 处理后的字符串
 */
export function trimChars(str: string, chars: string): string {
  if (!str || !chars) return str;

  // 转义特殊字符
  const escapedChars = chars.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`^[${escapedChars}]+|[${escapedChars}]+$`, 'g');
  return str.replace(regex, '');
}

/**
 * 字符串模板替换
 * @param template 模板字符串，如 "Hello {name}"
 * @param data 替换数据对象
 * @returns 替换后的字符串
 */
export function template(template: string, data: Record<string, unknown>): string {
  return template.replace(/\{([^}]+)\}/g, (match, key: string) => {
    const value = data[key];
    return value !== undefined ? String(value) : match;
  });
}

/**
 * 检查字符串是否包含敏感词
 * @param str 待检查字符串
 * @param sensitiveWords 敏感词数组
 * @returns boolean
 */
export function containsSensitiveWords(str: string, sensitiveWords: string[]): boolean {
  if (!str || !sensitiveWords || sensitiveWords.length === 0) {
    return false;
  }

  const lowerStr = str.toLowerCase();
  return sensitiveWords.some((word) => lowerStr.includes(word.toLowerCase()));
}

/**
 * 过滤敏感词
 * @param str 待过滤字符串
 * @param sensitiveWords 敏感词数组
 * @param replacement 替换字符，默认为'*'
 * @returns 过滤后的字符串
 */
export function filterSensitiveWords(
  str: string,
  sensitiveWords: string[],
  replacement: string = '*'
): string {
  if (!str || !sensitiveWords || sensitiveWords.length === 0) {
    return str;
  }

  let result = str;
  sensitiveWords.forEach((word) => {
    const regex = new RegExp(word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
    result = result.replace(regex, replacement.repeat(word.length));
  });

  return result;
}

export default {
  isEmpty,
  isNotEmpty,
  truncate,
  capitalize,
  camelToSnake,
  snakeToCamel,
  randomString,
  trimChars,
  template,
  containsSensitiveWords,
  filterSensitiveWords,
};
