// APIClient测试
import { APIClient } from '../src/client';
import { SDKConfig } from '../src/types';

describe('APIClient Tests', () => {
  let client: APIClient;
  let mockConfig: SDKConfig;

  beforeEach(() => {
    mockConfig = {
      baseURL: 'http://localhost:8000',
      timeout: 5000
    };
    client = new APIClient(mockConfig);
  });

  describe('Constructor', () => {
    it('should create client with default configuration', () => {
      const defaultClient = new APIClient({
        baseURL: 'http://localhost:8000'
      });
      
      expect(defaultClient).toBeDefined();
    });

    it('should accept custom configuration', () => {
      const customConfig: SDKConfig = {
        baseURL: 'https://api.example.com',
        timeout: 10000,
        retries: 5,
        retryDelay: 2000,
        headers: {
          'X-API-Key': 'test-key'
        }
      };
      
      const customClient = new APIClient(customConfig);
      const config = customClient.getConfig();
      
      expect(config.baseURL).toBe('https://api.example.com');
      expect(config.timeout).toBe(10000);
      expect(config.retries).toBe(5);
      expect(config.retryDelay).toBe(2000);
    });
  });

  describe('Authentication', () => {
    it('should set access token', () => {
      const token = 'test-access-token';
      client.setAccessToken(token);
      
      // 验证token被设置（通过getConfig间接验证）
      const config = client.getConfig();
      expect(config.accessToken).toBe(token);
    });

    it('should clear access token', () => {
      client.setAccessToken('test-token');
      client.clearAccessToken();
      
      const config = client.getConfig();
      expect(config.accessToken).toBeUndefined();
    });
  });

  describe('HTTP Methods', () => {
    // 注意：这些测试需要mock网络请求
    // 在实际项目中应该使用nock或类似的库
    
    it('should have GET method', () => {
      expect(typeof client.get).toBe('function');
    });

    it('should have POST method', () => {
      expect(typeof client.post).toBe('function');
    });

    it('should have PUT method', () => {
      expect(typeof client.put).toBe('function');
    });

    it('should have DELETE method', () => {
      expect(typeof client.delete).toBe('function');
    });

    it('should have PATCH method', () => {
      expect(typeof client.patch).toBe('function');
    });
  });

  describe('Configuration Access', () => {
    it('should return readonly configuration', () => {
      const config = client.getConfig();
      
      expect(config).toBeDefined();
      expect(config.baseURL).toBe('http://localhost:8000');
      
      // 验证返回的是副本而不是引用
      config.baseURL = 'modified';
      const freshConfig = client.getConfig();
      expect(freshConfig.baseURL).toBe('http://localhost:8000');
    });
  });
});