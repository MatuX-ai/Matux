/**
 * 类型安全的JSON解析工具函数
 */

/**
 * 安全地解析JSON字符串，带有类型断言和错误处理
 * @param jsonString JSON字符串
 * @param fallback 默认值（解析失败时返回）
 * @returns 解析后的对象或默认值
 */
export function safeJsonParse<T>(jsonString: string | null | undefined, fallback: T): T {
  if (!jsonString) {
    return fallback;
  }

  try {
    return JSON.parse(jsonString) as T;
  } catch (error) {
    console.warn('JSON解析失败:', error);
    return fallback;
  }
}

/**
 * 安全地解析JSON字符串数组
 * @param jsonString JSON字符串
 * @param fallback 默认值
 * @returns 解析后的数组或默认值
 */
export function safeJsonParseArray<T>(
  jsonString: string | null | undefined,
  fallback: T[] = []
): T[] {
  return safeJsonParse<T[]>(jsonString, fallback);
}

/**
 * 安全地解析JSON字符串对象
 * @param jsonString JSON字符串
 * @param fallback 默认值
 * @returns 解析后的对象或默认值
 */
export function safeJsonParseObject<T extends Record<string, any>>(
  jsonString: string | null | undefined,
  fallback: T = {} as T
): T {
  return safeJsonParse<T>(jsonString, fallback);
}

/**
 * 类型安全的JSON序列化函数
 * @param obj 要序列化的对象
 * @param fallback 序列化失败时的默认值
 * @returns JSON字符串或默认值
 */
export function safeJsonStringify(obj: any, fallback: string = '{}'): string {
  try {
    return JSON.stringify(obj);
  } catch (error) {
    console.warn('JSON序列化失败:', error);
    return fallback;
  }
}

/**
 * 验证对象是否具有必需的属性
 * @param obj 要验证的对象
 * @param requiredKeys 必需的属性键数组
 * @returns 验证结果和缺失的属性
 */
export function validateRequiredProperties<T extends Record<string, any>>(
  obj: T | null | undefined,
  requiredKeys: (keyof T)[]
): { isValid: boolean; missingKeys: (keyof T)[] } {
  if (!obj) {
    return { isValid: false, missingKeys: requiredKeys };
  }

  const missingKeys = requiredKeys.filter(
    (key) => !(key in obj) || obj[key] === undefined || obj[key] === null
  );

  return {
    isValid: missingKeys.length === 0,
    missingKeys,
  };
}

/**
 * 深度合并两个对象，保持类型安全
 * @param target 目标对象
 * @param source 源对象
 * @returns 合并后的对象
 */
export function deepMerge<T extends Record<string, any>>(target: T, source: Partial<T>): T {
  const result = { ...target };

  for (const key in source) {
    if (Object.prototype.hasOwnProperty.call(source, key)) {
      const sourceValue = source[key];
      const targetValue = result[key];

      if (sourceValue !== undefined) {
        if (isObject(sourceValue) && isObject(targetValue)) {
          result[key] = deepMerge(targetValue, sourceValue);
        } else {
          result[key] = sourceValue as T[Extract<keyof T, string>];
        }
      }
    }
  }

  return result;
}

/**
 * 检查值是否为对象（排除null和数组）
 */
function isObject(value: any): value is Record<string, any> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

/**
 * 创建类型安全的对象键枚举
 * @param obj 对象
 * @returns 对象键的只读数组
 */
export function getObjectKeys<T extends Record<string, any>>(obj: T): ReadonlyArray<keyof T> {
  return Object.keys(obj) as (keyof T)[];
}

/**
 * 创建类型安全的对象值数组
 * @param obj 对象
 * @returns 对象值的数组
 */
export function getObjectValues<T extends Record<string, any>>(obj: T): T[keyof T][] {
  return Object.values(obj) as T[keyof T][];
}

/**
 * 创建类型安全的对象条目数组
 * @param obj 对象
 * @returns [key, value]对的数组
 */
export function getObjectEntries<T extends Record<string, any>>(obj: T): [keyof T, T[keyof T]][] {
  return Object.entries(obj) as [keyof T, T[keyof T]][];
}
