/**
 * AI SDK 使用示例
 */

import {
  AIServiceClient,
  CodeGenerationRequest,
  ModelProvider,
  ProgrammingLanguage,
} from './index';

// 示例1: 基础代码生成
async function basicCodeGeneration() {
  const client = new AIServiceClient({
    baseUrl: 'http://localhost:8000',
    accessToken: 'your-access-token-here',
  });

  try {
    const response = await client.generateCode({
      prompt: '创建一个Python函数来验证电子邮件地址格式',
      provider: ModelProvider.OPENAI,
      language: ProgrammingLanguage.PYTHON,
      temperature: 0.7,
      maxTokens: 1000,
    });

    console.log('生成的代码:');
    console.log(response.code);
    console.log('使用的模型:', response.model);
    console.log('消耗令牌数:', response.tokensUsed);
    console.log('处理时间:', response.processingTime, '秒');
  } catch (error) {
    console.error('代码生成失败:', error);
  }
}

// 示例2: 使用预设模板
async function templateBasedGeneration() {
  const client = new AIServiceClient({
    baseUrl: 'http://localhost:8000',
    accessToken: 'your-access-token-here',
  });

  try {
    // 生成React组件
    const reactResponse = await client.generateWithTemplate(
      'reactComponent',
      'UserProfileCard',
      '{ name: string; email: string; avatar: string }'
    );

    console.log('React组件代码:');
    console.log(reactResponse.code);

    // 生成API服务
    const apiResponse = await client.generateWithTemplate('apiService', 'UserService', [
      'getUserById',
      'createUser',
      'updateUser',
      'deleteUser',
    ]);

    console.log('API服务代码:');
    console.log(apiResponse.code);
  } catch (error) {
    console.error('模板生成失败:', error);
  }
}

// 示例3: 批量生成代码
async function batchGeneration() {
  const client = new AIServiceClient({
    baseUrl: 'http://localhost:8000',
    accessToken: 'your-access-token-here',
  });

  const requests: CodeGenerationRequest[] = [
    {
      prompt: '创建一个JavaScript数组去重函数',
      provider: ModelProvider.OPENAI,
      language: ProgrammingLanguage.JAVASCRIPT,
    },
    {
      prompt: '创建一个TypeScript接口定义用户信息',
      provider: ModelProvider.DEEPSEEK,
      language: ProgrammingLanguage.TYPESCRIPT,
    },
    {
      prompt: '创建一个Python类表示商品信息',
      provider: ModelProvider.LINGMA,
      language: ProgrammingLanguage.PYTHON,
    },
  ];

  try {
    const responses = await client.generateCodeBatch(requests);

    responses.forEach((response, index) => {
      console.log(`\n=== 请求 ${index + 1} 结果 ===`);
      console.log('代码:', response.code);
      console.log('提供商:', response.provider);
      console.log('模型:', response.model);
    });
  } catch (error) {
    console.error('批量生成失败:', error);
  }
}

// 示例4: 带重试的代码生成
async function generationWithRetry() {
  const client = new AIServiceClient({
    baseUrl: 'http://localhost:8000',
    accessToken: 'your-access-token-here',
  });

  try {
    const response = await client.generateCodeWithRetry(
      {
        prompt: '创建一个复杂的算法解决背包问题',
        provider: ModelProvider.OPENAI,
        language: ProgrammingLanguage.PYTHON,
        maxTokens: 2000,
      },
      3, // 最多重试3次
      2000 // 重试间隔2秒
    );

    console.log('最终生成的代码:');
    console.log(response.code);
  } catch (error) {
    console.error('重试后仍然失败:', error);
  }
}

// 示例5: 获取模型信息和统计
async function getModelInfoAndStats() {
  const client = new AIServiceClient({
    baseUrl: 'http://localhost:8000',
    accessToken: 'your-access-token-here',
  });

  try {
    // 获取可用模型
    const models = await client.getAvailableModels();
    console.log('可用模型:');
    models.models.forEach((model) => {
      console.log(`- ${model.provider}: ${model.modelName} (${model.description})`);
    });

    // 获取使用统计
    const stats = await client.getUsageStats();
    console.log('\n使用统计:');
    console.log('总请求数:', stats.totalRequests);
    console.log('成功率:', stats.successRate.toFixed(2) + '%');
    console.log('按提供商统计:');
    stats.providerStats.forEach((stat) => {
      console.log(
        `  ${stat.provider}: ${stat.requestCount} 次请求, 平均耗时 ${stat.averageProcessingTime.toFixed(2)} 秒`
      );
    });

    // 获取最近请求记录
    const recentRequests = await client.getRecentRequests(5);
    console.log('\n最近5次请求:');
    recentRequests.forEach((req) => {
      console.log(
        `- [${req.createdAt}] ${req.modelProvider}/${req.modelName}: ${req.prompt.substring(0, 50)}...`
      );
    });
  } catch (error) {
    console.error('获取信息失败:', error);
  }
}

// 示例6: 动态配置切换
async function dynamicConfiguration() {
  const client = new AIServiceClient({
    baseUrl: 'http://localhost:8000',
    accessToken: 'your-access-token-here',
  });

  // 切换到不同的AI提供商
  const providers = [ModelProvider.OPENAI, ModelProvider.LINGMA, ModelProvider.DEEPSEEK];

  for (const provider of providers) {
    try {
      console.log(`\n=== 使用 ${provider} 生成代码 ===`);

      const response = await client.generateCode({
        prompt: '创建一个简单的问候函数',
        provider,
        language: ProgrammingLanguage.PYTHON,
      });

      console.log('生成结果:');
      console.log(response.code);
      console.log('处理时间:', response.processingTime.toFixed(2), '秒');
    } catch (error) {
      console.error(`${provider} 生成失败:`, error);
    }
  }
}

// 运行所有示例
async function runAllExamples() {
  console.log('🚀 开始运行AI SDK示例...\n');

  await basicCodeGeneration();
  await templateBasedGeneration();
  await batchGeneration();
  await generationWithRetry();
  await getModelInfoAndStats();
  await dynamicConfiguration();

  console.log('\n✅ 所有示例运行完成!');
}

// 注意：在浏览器环境中可以直接调用各个示例函数
// 例如：basicCodeGeneration()

// 导出示例函数供其他模块使用
export {
  basicCodeGeneration,
  batchGeneration,
  dynamicConfiguration,
  generationWithRetry,
  getModelInfoAndStats,
  runAllExamples,
  templateBasedGeneration,
};
