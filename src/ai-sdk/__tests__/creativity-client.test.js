/**
 * AI创意引擎客户端测试用例
 */

import { CreativityClient } from '../creativity-client';
import { IdeaCategory, ImageStyle } from '../creativity-types';

// Mock fetch globally
global.fetch = jest.fn();

describe('CreativityClient', () => {
  let client;
  let mockConfig;

  beforeEach(() => {
    mockConfig = {
      baseUrl: 'http://localhost:8000',
      accessToken: 'test-token',
      timeout: 5000
    };
    
    client = new CreativityClient(mockConfig);
    
    // Reset fetch mock
    global.fetch.mockReset();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('构造函数和配置', () => {
    test('应该正确初始化客户端', () => {
      expect(client).toBeDefined();
      expect(client.config).toEqual(mockConfig);
    });

    test('没有访问令牌时应该抛出错误', () => {
      const clientWithoutToken = new CreativityClient({
        ...mockConfig,
        accessToken: undefined
      });
      
      expect(() => {
        clientWithoutToken.generateIdea({});
      }).toThrow('Access token is required for creativity service operations');
    });
  });

  describe('创意生成', () => {
    test('应该成功生成创意想法', async () => {
      const mockResponse = {
        status: 200,
        data: {
          idea_id: 1,
          title: '智能家居创新方案',
          content: '这是一个基于AI的智能家居控制系统...',
          category: 'technology',
          processing_time: 2.5,
          tokens_used: 150
        },
        headers: { 'content-type': 'application/json' }
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Map([['content-type', 'application/json']]),
        json: () => Promise.resolve(mockResponse.data)
      });

      const request = {
        category: IdeaCategory.TECHNOLOGY,
        custom_prompt: '生成一个智能家居创新方案',
        temperature: 0.8
      };

      const result = await client.generateIdea(request);

      expect(result).toEqual(mockResponse.data);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/creativity/generate-idea',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify(request)
        })
      );
    });

    test('API错误时应该抛出异常', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        headers: new Map([['content-type', 'application/json']]),
        json: () => Promise.resolve({ detail: 'Invalid request' })
      });

      await expect(client.generateIdea({}))
        .rejects
        .toThrow('Invalid request');
    });
  });

  describe('Prompt模板管理', () => {
    test('应该成功获取模板列表', async () => {
      const mockTemplates = [
        {
          id: 1,
          name: '低成本IoT解决方案',
          category: 'technology',
          template: '为{场景}设计低成本IoT方案',
          usage_count: 15
        }
      ];

      global.fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Map([['content-type', 'application/json']]),
        json: () => Promise.resolve(mockTemplates)
      });

      const result = await client.getTemplates({ category: 'technology' });

      expect(result).toEqual(mockTemplates);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/creativity/templates?category=technology',
        expect.objectContaining({
          method: 'GET'
        })
      );
    });

    test('应该成功搜索模板', async () => {
      const mockTemplates = [
        { id: 1, name: 'IoT解决方案', category: 'technology' }
      ];

      global.fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Map([['content-type', 'application/json']]),
        json: () => Promise.resolve(mockTemplates)
      });

      const result = await client.searchTemplates('IoT', 10);

      expect(result).toEqual(mockTemplates);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/creativity/templates/search/IoT?limit=10',
        expect.any(Object)
      );
    });
  });

  describe('创意评分', () => {
    test('应该成功评分创意想法', async () => {
      const mockScoreResponse = {
        total_score: 8.5,
        creativity: 9.0,
        feasibility: 7.5,
        commercial_value: 8.0,
        detailed_analysis: {
          analysis_text: '这是一个很有潜力的创意...',
          strengths: ['创新性强', '市场需求明确'],
          risks: ['技术实现复杂'],
          improvement_areas: ['需要更详细的技术方案']
        },
        recommendations: [
          '完善技术实现细节',
          '进行市场调研验证'
        ]
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Map([['content-type', 'application/json']]),
        json: () => Promise.resolve(mockScoreResponse)
      });

      const request = {
        idea_content: '基于AI的个性化学习平台...',
        technical_requirements: '需要机器学习算法',
        business_model: 'SaaS订阅模式'
      };

      const result = await client.scoreIdea(request);

      expect(result).toEqual(mockScoreResponse);
      expect(result.total_score).toBeGreaterThanOrEqual(0);
      expect(result.total_score).toBeLessThanOrEqual(10);
    });
  });

  describe('图像生成', () => {
    test('应该成功生成创意图像', async () => {
      const mockImageResponse = {
        images: [
          {
            url: 'https://example.com/image1.png',
            revised_prompt: '现代智能家居控制面板'
          },
          {
            url: 'https://example.com/image2.png',
            revised_prompt: '现代智能家居控制面板'
          }
        ],
        processing_time: 4.2,
        total_cost: 0.08
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Map([['content-type', 'application/json']]),
        json: () => Promise.resolve(mockImageResponse)
      });

      const request = {
        prompt: '现代智能家居控制面板的界面设计',
        style: ImageStyle.REALISTIC,
        n: 2
      };

      const result = await client.generateImage(request);

      expect(result).toEqual(mockImageResponse);
      expect(result.images).toHaveLength(2);
      expect(result.total_cost).toBeGreaterThan(0);
    });
  });

  describe('商业价值评估', () => {
    test('应该成功评估商业价值', async () => {
      const mockBusinessResponse = {
        cost_benefit_ratio: 2.5,
        market_potential: 8.0,
        risk_assessment: {
          overall_risk: '中等风险',
          market_risk: '低风险',
          technical_risk: '中等风险',
          financial_risk: '中等风险',
          operational_risk: '低风险',
          risk_factors: ['市场竞争激烈', '技术实现复杂度高']
        },
        investment_recommendation: '建议谨慎投资',
        timeline_estimate: '12-18个月',
        resource_requirements: ['技术团队', '市场推广资金', '运营管理']
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Map([['content-type', 'application/json']]),
        json: () => Promise.resolve(mockBusinessResponse)
      });

      const request = {
        idea_description: 'AI驱动的个性化健康管理应用',
        target_market: '健康意识强的年轻人群',
        estimated_costs: { 开发: 500000, 运营: 100000 },
        revenue_projections: { 第一年: 100000, 第二年: 500000 },
        competition_analysis: '市场上有类似产品但我们的算法更有优势'
      };

      const result = await client.evaluateBusiness(request);

      expect(result).toEqual(mockBusinessResponse);
      expect(result.cost_benefit_ratio).toBeGreaterThan(0);
      expect(result.market_potential).toBeGreaterThanOrEqual(0);
      expect(result.market_potential).toBeLessThanOrEqual(10);
    });
  });

  describe('用户创意管理', () => {
    test('应该成功获取用户创意列表', async () => {
      const mockIdeas = [
        {
          id: 1,
          title: '智能家居控制系统',
          category: 'technology',
          created_at: '2024-01-15T10:30:00Z'
        }
      ];

      global.fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Map([['content-type', 'application/json']]),
        json: () => Promise.resolve(mockIdeas)
      });

      const result = await client.getUserIdeas({ category: 'technology' });

      expect(result).toEqual(mockIdeas);
      expect(Array.isArray(result)).toBe(true);
    });

    test('应该成功创建创意想法', async () => {
      const mockCreateResponse = {
        message: '创意想法创建成功',
        idea_id: 123
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Map([['content-type', 'application/json']]),
        json: () => Promise.resolve(mockCreateResponse)
      });

      const ideaData = {
        title: '新的创意想法',
        description: '这是一个创新的想法',
        category: IdeaCategory.BUSINESS,
        is_public: false
      };

      const result = await client.createIdea(ideaData);

      expect(result).toEqual(mockCreateResponse);
      expect(result.idea_id).toBeDefined();
    });
  });

  describe('数据验证', () => {
    test('应该正确验证创意想法数据', () => {
      // 有效数据
      const validIdea = {
        title: '有效的创意标题',
        description: '这是一个很好的创意描述',
        tags: ['创新', '科技']
      };

      const validResult = client.validateIdea(validIdea);
      expect(validResult.isValid).toBe(true);
      expect(validResult.errors).toHaveLength(0);

      // 无效数据
      const invalidIdea = {
        title: '', // 空标题
        description: 'a'.repeat(2001), // 超长描述
        tags: Array(11).fill('tag') // 超过10个标签
      };

      const invalidResult = client.validateIdea(invalidIdea);
      expect(invalidResult.isValid).toBe(false);
      expect(invalidResult.errors).toHaveLength(3);
    });

    test('应该正确验证模板数据', () => {
      // 有效模板
      const validTemplate = {
        name: '有效的模板名称',
        template: '这是一个有效的模板内容，足够长',
        description: '模板描述'
      };

      const validResult = client.validateTemplate(validTemplate);
      expect(validResult.isValid).toBe(true);

      // 无效模板
      const invalidTemplate = {
        name: '', // 空名称
        template: '短' // 太短
      };

      const invalidResult = client.validateTemplate(invalidTemplate);
      expect(invalidResult.isValid).toBe(false);
      expect(invalidResult.errors).toContain('模板名称不能为空');
      expect(invalidResult.errors).toContain('模板内容至少需要10个字符');
    });
  });

  describe('工具方法', () => {
    test('应该正确获取评分颜色', () => {
      expect(client.getScoreColor(8.5)).toBe('success');
      expect(client.getScoreColor(7.0)).toBe('warning');
      expect(client.getScoreColor(3.0)).toBe('error');
    });

    test('应该正确获取评分描述', () => {
      expect(client.getScoreDescription(8.5)).toBe('优秀');
      expect(client.getScoreDescription(6.5)).toBe('良好');
      expect(client.getScoreDescription(4.5)).toBe('一般');
      expect(client.getScoreDescription(2.0)).toBe('需要改进');
    });

    test('应该正确导出创意为JSON', () => {
      const mockIdea = {
        title: '测试创意',
        description: '测试描述',
        category: 'technology',
        created_at: '2024-01-15T10:30:00Z'
      };

      const jsonString = client.exportIdeaToJson(mockIdea);
      const parsed = JSON.parse(jsonString);

      expect(parsed.title).toBe(mockIdea.title);
      expect(parsed.exported_at).toBeDefined();
    });

    test('应该正确导出创意为文本', () => {
      const mockIdea = {
        title: '测试创意',
        description: '测试描述',
        category: 'technology',
        created_at: '2024-01-15T10:30:00Z'
      };

      const textString = client.exportIdeaToText(mockIdea);
      
      expect(textString).toContain('# 测试创意');
      expect(textString).toContain('**分类:** technology');
      expect(textString).toContain('**创建时间:**');
    });
  });

  describe('便捷方法', () => {
    test('应该成功生成并保存创意', async () => {
      // Mock generateIdea
      client.generateIdea = jest.fn().mockResolvedValue({
        title: '生成的创意',
        content: '创意内容',
        processing_time: 2.5
      });

      // Mock createIdea
      client.createIdea = jest.fn().mockResolvedValue({
        message: '创建成功',
        idea_id: 123
      });

      // Mock getIdeaById
      client.getIdeaById = jest.fn().mockResolvedValue({
        id: 123,
        title: '生成的创意',
        description: '创意内容'
      });

      const request = { category: IdeaCategory.TECHNOLOGY };

      const result = await client.generateAndSaveIdea(request);

      expect(result.idea.id).toBe(123);
      expect(result.processing_time).toBe(2.5);
      expect(client.generateIdea).toHaveBeenCalledWith(request);
      expect(client.createIdea).toHaveBeenCalled();
    });
  });
});

// 测试网络错误处理
describe('网络错误处理', () => {
  let client;

  beforeEach(() => {
    client = new CreativityClient({
      baseUrl: 'http://localhost:8000',
      accessToken: 'test-token'
    });
  });

  test('应该处理网络超时', async () => {
    global.fetch.mockImplementationOnce(() => {
      return new Promise((_, reject) => {
        setTimeout(() => reject(new Error('timeout')), 100);
      });
    });

    await expect(client.generateIdea({}))
      .rejects
      .toThrow('Network error');
  });

  test('应该处理网络中断', async () => {
    global.fetch.mockRejectedValueOnce(new Error('Network failure'));

    await expect(client.getTemplates())
      .rejects
      .toThrow('Network error');
  });
});