/**
 * 数组处理工具函数集合
 */

/**
 * 数组去重
 * @param array 原数组
 * @param key 如果是对象数组，指定去重的键名
 * @returns 去重后的数组
 */
export function unique<T>(array: T[], key?: keyof T): T[] {
  if (!Array.isArray(array)) return [];

  if (key) {
    const seen = new Set();
    return array.filter((item) => {
      const keyValue = item[key];
      if (seen.has(keyValue)) {
        return false;
      }
      seen.add(keyValue);
      return true;
    });
  }

  return [...new Set(array)];
}

/**
 * 数组分组
 * @param array 原数组
 * @param key 分组键或回调函数
 * @returns 分组后的对象
 */
export function groupBy<T>(array: T[], key: keyof T | ((item: T) => string)): Record<string, T[]> {
  if (!Array.isArray(array)) return {};

  return array.reduce(
    (groups, item) => {
      const groupKey = typeof key === 'function' ? key(item) : String(item[key]);
      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(item);
      return groups;
    },
    {} as Record<string, T[]>
  );
}

/**
 * 数组排序
 * @param array 原数组
 * @param key 排序键或回调函数
 * @param order 排序方向 'asc' | 'desc'
 * @returns 排序后的数组
 */
export function sortBy<T>(
  array: T[],
  key: keyof T | ((item: T) => number | string),
  order: 'asc' | 'desc' = 'asc'
): T[] {
  if (!Array.isArray(array)) return [];

  return [...array].sort((a, b) => {
    const getValue = (item: T): number | string => {
      return typeof key === 'function' ? key(item) : (item[key] as number | string);
    };
    const valueA = getValue(a);
    const valueB = getValue(b);

    let comparison = 0;
    if (valueA < valueB) {
      comparison = -1;
    } else if (valueA > valueB) {
      comparison = 1;
    }

    return order === 'desc' ? -comparison : comparison;
  });
}

/**
 * 数组扁平化
 * @param array 嵌套数组
 * @param depth 扁平化深度，默认为1
 * @returns 扁平化后的数组
 */
export function flatten<T>(array: T[], depth: number = 1): T[] {
  if (!Array.isArray(array)) return [];

  if (depth <= 0) return array;

  return array.reduce((acc: T[], val: T) => {
    return acc.concat(Array.isArray(val) ? flatten(val as unknown as T[], depth - 1) : val);
  }, [] as T[]);
}

/**
 * 数组交集
 * @param arrays 多个数组
 * @returns 交集数组
 */
export function intersection<T>(...arrays: T[][]): T[] {
  if (arrays.length === 0) return [];
  if (arrays.length === 1) return [...arrays[0]];

  return arrays.reduce((acc, arr) => {
    return acc.filter((item) => arr.includes(item));
  });
}

/**
 * 数组差集
 * @param array 原数组
 * @param exclude 要排除的数组
 * @returns 差集数组
 */
export function difference<T>(array: T[], exclude: T[]): T[] {
  if (!Array.isArray(array) || !Array.isArray(exclude)) return [];

  return array.filter((item) => !exclude.includes(item));
}

/**
 * 数组并集
 * @param arrays 多个数组
 * @returns 并集数组（去重）
 */
export function union<T>(...arrays: T[][]): T[] {
  const allItems = arrays.flat();
  return unique(allItems);
}

/**
 * 数组分块
 * @param array 原数组
 * @param size 每块大小
 * @returns 分块后的二维数组
 */
export function chunk<T>(array: T[], size: number): T[][] {
  if (!Array.isArray(array) || size <= 0) return [];

  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
}

/**
 * 数组采样
 * @param array 原数组
 * @param count 采样数量
 * @returns 采样数组
 */
export function sample<T>(array: T[], count: number): T[] {
  if (!Array.isArray(array) || count <= 0) return [];

  const shuffled = [...array].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
}

/**
 * 数组随机打乱
 * @param array 原数组
 * @returns 打乱后的数组
 */
export function shuffle<T>(array: T[]): T[] {
  if (!Array.isArray(array)) return [];

  const result = [...array];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

/**
 * 查找数组中的最大值
 * @param array 数组
 * @param key 如果是对象数组，指定比较的键名或回调函数
 * @returns 最大值元素
 */
export function maxBy<T>(array: T[], key: keyof T | ((item: T) => number)): T | undefined {
  if (!Array.isArray(array) || array.length === 0) return undefined;

  return array.reduce((max, current) => {
    const getValue = (item: T): number => {
      return typeof key === 'function' ? key(item) : Number(item[key]);
    };
    return getValue(current) > getValue(max) ? current : max;
  }, array[0]);
}

/**
 * 查找数组中的最小值
 * @param array 数组
 * @param key 如果是对象数组，指定比较的键名或回调函数
 * @returns 最小值元素
 */
export function minBy<T>(array: T[], key: keyof T | ((item: T) => number)): T | undefined {
  if (!Array.isArray(array) || array.length === 0) return undefined;

  return array.reduce((min, current) => {
    const getValue = (item: T): number => {
      return typeof key === 'function' ? key(item) : Number(item[key]);
    };
    return getValue(current) < getValue(min) ? current : min;
  }, array[0]);
}

/**
 * 数组求和
 * @param array 数字数组或对象数组
 * @param key 如果是对象数组，指定求和的键名或回调函数
 * @returns 求和结果
 */
export function sumBy<T>(array: T[], key?: keyof T | ((item: T) => number)): number {
  if (!Array.isArray(array)) return 0;

  return array.reduce((sum, item) => {
    let value: number;
    if (key) {
      const getValue = typeof key === 'function' ? key : (item: T) => Number(item[key]);
      value = getValue(item);
    } else {
      value = Number(item);
    }
    return sum + (isNaN(value) ? 0 : value);
  }, 0);
}

/**
 * 数组平均值
 * @param array 数字数组或对象数组
 * @param key 如果是对象数组，指定计算平均值的键名或回调函数
 * @returns 平均值
 */
export function averageBy<T>(array: T[], key?: keyof T | ((item: T) => number)): number {
  if (!Array.isArray(array) || array.length === 0) return 0;

  const sum = sumBy(array, key);
  return sum / array.length;
}

export default {
  unique,
  groupBy,
  sortBy,
  flatten,
  intersection,
  difference,
  union,
  chunk,
  sample,
  shuffle,
  maxBy,
  minBy,
  sumBy,
  averageBy,
};
