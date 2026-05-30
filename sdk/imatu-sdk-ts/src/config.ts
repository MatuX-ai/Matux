import { SDKConfig } from './types';

// 从环境变量或进程中获取 API URL
const getApiBaseUrl = (): string => {
  // 浏览器环境
  if (typeof window !== 'undefined') {
    return (window as any).__API_BASE_URL__ ||
           process.env.REACT_APP_API_URL ||
           'http://localhost:8000';
  }
  // Node.js 环境
  if (typeof process !== 'undefined' && process.env) {
    return process.env.API_BASE_URL || 'http://localhost:8000';
  }
  return 'http://localhost:8000';
};

export const defaultConfig: SDKConfig = {
  baseURL: getApiBaseUrl(),
  timeout: 10000,
  headers: {
    'X-API-Version': '1.0.0'
  }
};

export function createConfig(overrides?: Partial<SDKConfig>): SDKConfig {
  return {
    ...defaultConfig,
    ...overrides
  };
}
