// 数据库注册表相关的TypeScript模型定义

export interface ModuleMetadata {
  name: string;
  table_name: string;
  category: string;
  version: string;
  description?: string;
  dependencies: string[];
  is_active: boolean;
  created_at?: string;
}

export interface ModuleInstance {
  name: string;
  class_name: string;
  is_initialized: boolean;
  has_instance: boolean;
}

export interface RegistryStats {
  registry_stats: {
    total_modules: number;
    active_modules: number;
    inactive_modules: number;
    total_instances: number;
    categories: number;
    tables: number;
    initialized: boolean;
  };
  modules_by_category: { [key: string]: ModuleInfo[] };
  total_categories: number;
  mode?: string;
}

export interface ModuleInfo extends ModuleMetadata {
  has_instance: boolean;
  is_initialized: boolean;
  class_name: string;
}

export interface RegistryHealth {
  registry_status: 'healthy' | 'degraded' | 'uninitialized';
  stats: any;
  modules_status: Array<{
    name: string;
    registered: boolean;
    instance_created: boolean;
    initialized: boolean;
    active: boolean;
  }>;
  issues: string[];
  status?: string;
  database_registry_error?: string;
}

export interface ModuleActivationRequest {
  module_name: string;
  action: 'activate' | 'deactivate';
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

// 分类统计接口
export interface CategoryStat {
  category: string;
  count: number;
  percentage: number;
}

// 模块操作结果
export interface ModuleOperationResult {
  success: boolean;
  message: string;
  module?: ModuleInfo;
}

// 注册表配置
export interface RegistryConfig {
  auto_discovery_enabled: boolean;
  health_check_enabled: boolean;
  initialized: boolean;
  stats: any;
}
