import { APIClient } from './client';
import { createConfig, defaultConfig } from './config';
import { SDKConfig, SDKInstance } from './types';
import { createAuthAPI } from './generated/auth';
import { createUsersAPI } from './generated/users';
import { createAIAPI } from './generated/ai';
import { createCoursesAPI } from './generated/courses';

/**
 * 创建完整的SDK实例
 * @param config SDK配置
 * @returns SDK实例
 */
export function createSDK(config?: Partial<SDKConfig>): SDKInstance {
  const finalConfig = createConfig(config);
  const client = new APIClient(finalConfig);
  
  const sdk: SDKInstance = {
    auth: createAuthAPI(client),
    users: createUsersAPI(client),
    ai: createAIAPI(client),
    courses: createCoursesAPI(client),
    
    setAccessToken: (token: string) => {
      client.setAccessToken(token);
    },
    
    clearAccessToken: () => {
      client.clearAccessToken();
    }
  };
  
  return sdk;
}

/**
 * 创建默认SDK实例
 * @returns 默认配置的SDK实例
 */
export function createDefaultSDK(): SDKInstance {
  return createSDK(defaultConfig);
}

// 导出所有类型和接口
export * from './types';
export * from './config';
export { APIClient } from './client';

// 默认导出
export default {
  createSDK,
  createDefaultSDK,
  defaultConfig
};