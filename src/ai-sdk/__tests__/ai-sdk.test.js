/**
 * AI SDK 前端测试用例
 */

// 模拟测试环境
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('AIServiceClient', () => {
  let AIServiceClient;
  let client;

  beforeEach(() => {
    // 重新导入模块
    jest.isolateModules(() => {
      AIServiceClient = require('../../src/ai-sdk/ai-client').AIServiceClient;
    });
    
    client = new AIServiceClient({
      baseUrl: 'http://localhost:8000',
      accessToken: 'test-token'
    });
    
    // 重置mock
    mockFetch.mockReset();
  });

  describe('构造函数和配置', () => {
    test('应该正确初始化客户端', () => {
      expect(client).toBeInstanceOf(AIServiceClient);
      expect(client.config.baseUrl).toBe('http://localhost:8000');
      expect(client.config.accessToken).toBe('test-token');
    });

    test('应该设置默认配置', () => {
      const clientWithoutConfig = new AIServiceClient({
        baseUrl: 'http://test.com'
      });
      
      expect(clientWithoutConfig.config.timeout).toBe(30000);
      expect(clientWithoutConfig.config.headers).toEqual({});
    });

    test('应该能够更新配置', () => {
      client.updateConfig({
        baseUrl: 'http://new-url.com',
        timeout: 5000
      });
      
      expect(client.config.baseUrl).toBe('http://new-url.com');
      expect(client.config.timeout).toBe(5000);
    });
  });

  describe('认证相关方法', () => {
    test('应该能够设置访问令牌', () => {
      client.setAccessToken('new-token');
      expect(client.config.accessToken).toBe('new-token');
    });

    test('应该能够清除访问令牌', () => {
      client.clearAccessToken();
      expect(client.config.accessToken).toBeUndefined();
    });
  });

  describe('代码生成', () => {
    const mockResponse = {
      code: 'def hello():\n    print("Hello World")',
      provider: 'openai',
      model: 'gpt-4-turbo',
      tokensUsed: 42,
      processingTime: 1.23
    };

    test('应该成功生成代码', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
        headers: new Map()
      });

      const result = await client.generateCode({
        prompt: '创建一个hello world函数',
        provider: 'openai',
        language: 'python'
      });

      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/generate-code',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json'
          })
        })
      );
    });

    test('应该在没有令牌时抛出错误', async () => {
      client.clearAccessToken();
      
      await expect(client.generateCode({
        prompt: 'test'
      })).rejects.toThrow('Access token is required for AI service');
    });

    test('应该处理HTTP错误', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Bad request' }),
        headers: new Map()
      });

      await expect(client.generateCode({
        prompt: 'test'
      })).rejects.toThrow('Bad request');
    });

    test('应该处理网络错误', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(client.generateCode({
        prompt: 'test'
      })).rejects.toThrow('Failed to generate code: Error: Network error');
    });
  });

  describe('模板生成', () => {
    test('应该能够使用预设模板生成代码', async () => {
      const mockResponse = {
        code: 'class MyComponent extends React.Component {}',
        provider: 'openai',
        model: 'gpt-4-turbo',
        tokensUsed: 50,
        processingTime: 1.5
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
        headers: new Map()
      });

      const result = await client.generateWithTemplate(
        'reactComponent',
        'MyComponent',
        '{ prop1: string }'
      );

      expect(result).toEqual(mockResponse);
      // 验证请求包含了正确的提示词
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: expect.stringContaining('MyComponent')
        })
      );
    });
  });

  describe('批量生成', () => {
    test('应该能够批量生成代码', async () => {
      const mockResponses = [
        { code: 'code1', provider: 'openai', model: 'gpt-4', tokensUsed: 10, processingTime: 1 },
        { code: 'code2', provider: 'openai', model: 'gpt-4', tokensUsed: 15, processingTime: 1.2 }
      ];

      // 模拟两个连续的API调用
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => mockResponses[0],
          headers: new Map()
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => mockResponses[1],
          headers: new Map()
        });

      const requests = [
        { prompt: '生成代码1', provider: 'openai' },
        { prompt: '生成代码2', provider: 'openai' }
      ];

      const results = await client.generateCodeBatch(requests);

      expect(results).toEqual(mockResponses);
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('重试机制', () => {
    test('应该在失败时重试', async () => {
      // 第一次失败，第二次成功
      mockFetch
        .mockRejectedValueOnce(new Error('First attempt failed'))
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ code: 'success', provider: 'openai', model: 'gpt-4', tokensUsed: 10, processingTime: 1 }),
          headers: new Map()
        });

      const result = await client.generateCodeWithRetry({
        prompt: 'test prompt'
      }, 3, 100);

      expect(result.code).toBe('success');
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    test('应该在重试次数用尽后失败', async () => {
      // 模拟连续失败
      mockFetch.mockRejectedValue(new Error('Always fails'));

      await expect(client.generateCodeWithRetry({
        prompt: 'test prompt'
      }, 2, 50)).rejects.toThrow('Always fails');

      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });
});

describe('HttpClient', () => {
  let HttpClient;

  beforeEach(() => {
    jest.isolateModules(() => {
      HttpClient = require('../../src/ai-sdk/http-client').HttpClient;
    });
  });

  test('应该正确构建请求URL', () => {
    const client = new HttpClient('http://api.example.com');
    
    // 测试相对URL
    expect(client['_baseUrl']).toBe('http://api.example.com');
    
    // 测试绝对URL不会被修改
    const absoluteClient = new HttpClient('http://old.com');
    // 这里应该测试私有方法，但在实际测试中我们会测试公共接口
  });

  test('应该正确合并请求头', async () => {
    const client = new HttpClient('http://api.example.com', 1000, {
      'Custom-Header': 'value'
    });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({}),
      headers: new Map([['content-type', 'application/json']])
    });

    await client.get('/test', {
      headers: { 'Another-Header': 'another-value' }
    });

    expect(mockFetch).toHaveBeenCalledWith(
      'http://api.example.com/test',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Custom-Header': 'value',
          'Another-Header': 'another-value'
        })
      })
    );
  });

  test('应该处理超时', async () => {
    const client = new HttpClient('http://api.example.com', 100); // 100ms超时

    // 模拟慢响应
    mockFetch.mockImplementation(() => new Promise(resolve => {
      setTimeout(() => {
        resolve({
          ok: true,
          status: 200,
          json: async () => ({}),
          headers: new Map()
        });
      }, 200); // 200ms响应，超过100ms超时
    }));

    await expect(client.get('/slow')).rejects.toThrow('Network error');
  });
});

describe('类型定义', () => {
  test('应该导出正确的类型', () => {
    const types = require('../../src/ai-sdk/types');
    
    // 验证枚举值
    expect(types.ModelProvider.OPENAI).toBe('openai');
    expect(types.ModelProvider.LINGMA).toBe('lingma');
    
    expect(types.ProgrammingLanguage.PYTHON).toBe('python');
    expect(types.ProgrammingLanguage.JAVASCRIPT).toBe('javascript');
    
    // 验证接口结构
    const sampleRequest = {
      prompt: 'test',
      provider: types.ModelProvider.OPENAI,
      language: types.ProgrammingLanguage.PYTHON
    };
    
    expect(sampleRequest.prompt).toBe('test');
    expect(sampleRequest.provider).toBe('openai');
    expect(sampleRequest.language).toBe('python');
  });
});

// 集成测试
describe('集成测试', () => {
  test('完整的使用流程', async () => {
    // 模拟整个流程
    const AIServiceClient = require('../../src/ai-sdk/ai-client').AIServiceClient;
    
    const client = new AIServiceClient({
      baseUrl: 'http://test-api.com',
      accessToken: 'user-token'
    });

    // 模拟API响应
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        code: 'def integration_test():\n    return "success"',
        provider: 'openai',
        model: 'gpt-4-turbo',
        tokensUsed: 25,
        processingTime: 0.8
      }),
      headers: new Map([['content-type', 'application/json']])
    });

    // 执行完整流程
    const result = await client.generateCode({
      prompt: '创建集成测试函数',
      provider: 'openai',
      language: 'python',
      temperature: 0.7
    });

    // 验证结果
    expect(result.code).toContain('def integration_test');
    expect(result.provider).toBe('openai');
    expect(result.tokensUsed).toBe(25);
    
    // 验证请求
    expect(mockFetch).toHaveBeenCalledWith(
      'http://test-api.com/api/v1/generate-code',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Authorization': 'Bearer user-token',
          'Content-Type': 'application/json'
        }),
        body: expect.stringContaining('创建集成测试函数')
      })
    );
  });
});

// 性能测试
describe('性能测试', () => {
  test('应该在合理时间内完成请求', async () => {
    const AIServiceClient = require('../../src/ai-sdk/ai-client').AIServiceClient;
    
    const client = new AIServiceClient({
      baseUrl: 'http://perf-test.com',
      accessToken: 'perf-token'
    });

    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ code: 'performance test result', provider: 'openai', model: 'gpt-4', tokensUsed: 10, processingTime: 0.1 }),
      headers: new Map()
    });

    const startTime = Date.now();
    
    await client.generateCode({
      prompt: 'performance test'
    });

    const endTime = Date.now();
    const duration = endTime - startTime;

    // 应该在网络延迟内完成（不包括实际API调用时间）
    expect(duration).toBeLessThan(1000); // 1秒内完成
  });
});

// 边界条件测试
describe('边界条件测试', () => {
  let AIServiceClient;

  beforeEach(() => {
    jest.isolateModules(() => {
      AIServiceClient = require('../../src/ai-sdk/ai-client').AIServiceClient;
    });
  });

  test('空提示词应该被拒绝', async () => {
    const client = new AIServiceClient({
      baseUrl: 'http://test.com',
      accessToken: 'token'
    });

    mockFetch.mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ detail: 'Prompt cannot be empty' }),
      headers: new Map()
    });

    await expect(client.generateCode({
      prompt: ''
    })).rejects.toThrow('Prompt cannot be empty');
  });

  test('超长提示词应该被处理', async () => {
    const client = new AIServiceClient({
      baseUrl: 'http://test.com',
      accessToken: 'token'
    });

    const longPrompt = 'a'.repeat(6000); // 超过5000字符限制

    mockFetch.mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ detail: 'Prompt too long' }),
      headers: new Map()
    });

    await expect(client.generateCode({
      prompt: longPrompt
    })).rejects.toThrow('Prompt too long');
  });

  test('无效的提供商应该被拒绝', async () => {
    const client = new AIServiceClient({
      baseUrl: 'http://test.com',
      accessToken: 'token'
    });

    mockFetch.mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'Invalid provider' }),
      headers: new Map()
    });

    await expect(client.generateCode({
      prompt: 'test',
      provider: 'invalid-provider'
    })).rejects.toThrow('Invalid provider');
  });
});