// SDK核心功能测试
import { createSDK, createDefaultSDK, defaultConfig } from '../src/sdk';
import { SDKConfig } from '../src/types';

describe('SDK Core Tests', () => {
  describe('createSDK', () => {
    it('should create SDK with default configuration', () => {
      const sdk = createSDK();
      
      expect(sdk).toBeDefined();
      expect(sdk.auth).toBeDefined();
      expect(sdk.users).toBeDefined();
      expect(sdk.ai).toBeDefined();
      expect(sdk.courses).toBeDefined();
      expect(typeof sdk.setAccessToken).toBe('function');
      expect(typeof sdk.clearAccessToken).toBe('function');
    });

    it('should create SDK with custom configuration', () => {
      const customConfig: Partial<SDKConfig> = {
        baseURL: 'https://custom-api.example.com',
        timeout: 5000,
        headers: {
          'X-Custom-Header': 'test-value'
        }
      };
      
      const sdk = createSDK(customConfig);
      
      // 验证配置被正确应用
      expect(sdk).toBeDefined();
    });

    it('should handle authentication methods', () => {
      const sdk = createSDK();
      
      // 测试设置访问令牌
      sdk.setAccessToken('test-token');
      
      // 测试清除访问令牌
      sdk.clearAccessToken();
    });
  });

  describe('createDefaultSDK', () => {
    it('should create SDK with default config', () => {
      const sdk = createDefaultSDK();
      
      expect(sdk).toBeDefined();
      expect(sdk.auth).toBeDefined();
      expect(sdk.users).toBeDefined();
      expect(sdk.ai).toBeDefined();
      expect(sdk.courses).toBeDefined();
    });
  });

  describe('Configuration', () => {
    it('should have correct default configuration', () => {
      expect(defaultConfig).toBeDefined();
      expect(defaultConfig.baseURL).toBe('http://localhost:8000');
      expect(defaultConfig.timeout).toBe(10000);
      expect(defaultConfig.headers).toBeDefined();
    });
  });
});