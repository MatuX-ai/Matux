// Jest测试环境设置
import { jest } from '@jest/globals';

// 全局测试设置
beforeAll(() => {
  // 设置全局mock
  global.console = {
    ...console,
    log: jest.fn(),
    debug: jest.fn(),
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
  };
});

afterAll(() => {
  // 清理工作
  jest.restoreAllMocks();
});

// Mock环境变量
process.env.NODE_ENV = 'test';
process.env.API_BASE_URL = 'http://localhost:8000';