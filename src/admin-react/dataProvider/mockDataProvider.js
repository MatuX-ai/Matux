/**
 * Mock数据提供者
 * @description 为React Admin提供模拟数据服务，便于开发和测试
 * @author iMatuProject Team
 * @version 1.0.0
 */

import { DataProvider } from 'react-admin';

/**
 * 许可证数据模型
 * @typedef {Object} License
 * @property {number} id - 许可证唯一标识
 * @property {string} licenseKey - 许可证密钥
 * @property {string} orgName - 组织名称
 * @property {string} contactEmail - 联系邮箱
 * @property {string} licenseType - 许可证类型 (COMMERCIAL/ENTERPRISE/TRIAL)
 * @property {string} status - 许可证状态 (ACTIVE/INACTIVE/EXPIRED/PENDING)
 * @property {Date} createdAt - 创建时间
 * @property {Date} updatedAt - 更新时间
 * @property {Date} expiryDate - 过期时间
 * @property {number} maxUsers - 最大用户数
 * @property {number} maxDevices - 最大设备数
 * @property {string[]} features - 功能列表
 * @property {string} notes - 备注信息
 */

/**
 * 生成随机许可证数据
 * @returns {License[]} 随机生成的许可证数组
 */
const generateMockLicenses = () => {
  const licenseTypes = ['COMMERCIAL', 'ENTERPRISE', 'TRIAL'];
  const statuses = ['ACTIVE', 'INACTIVE', 'EXPIRED', 'PENDING'];
  const organizations = [
    '科技有限公司',
    '软件开发公司',
    '信息技术集团',
    '数字创新企业',
    '云端服务提供商'
  ];
  
  const licenses = [];
  
  for (let i = 1; i <= 50; i++) {
    const orgIndex = Math.floor(Math.random() * organizations.length);
    const licenseType = licenseTypes[Math.floor(Math.random() * licenseTypes.length)];
    const status = statuses[Math.floor(Math.random() * statuses.length)];
    
    // 生成合理的过期日期
    const createdDate = new Date(2023, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1);
    const expiryDate = new Date(createdDate);
    expiryDate.setFullYear(expiryDate.getFullYear() + (Math.random() > 0.7 ? 2 : 1)); // 70%一年，30%两年
    
    licenses.push({
      id: i,
      licenseKey: `LICENSE-${String(i).padStart(6, '0')}-${Math.random().toString(36).substr(2, 8).toUpperCase()}`,
      orgName: `${organizations[orgIndex]}${Math.floor(Math.random() * 100) + 1}`,
      contactEmail: `contact${i}@${organizations[orgIndex].toLowerCase().replace(/\s+/g, '')}.com`,
      licenseType: licenseType,
      status: status,
      createdAt: createdDate.toISOString(),
      updatedAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
      expiryDate: expiryDate.toISOString(),
      maxUsers: Math.floor(Math.random() * 1000) + 10,
      maxDevices: Math.floor(Math.random() * 500) + 5,
      features: [
        'core_features',
        Math.random() > 0.5 ? 'advanced_analytics' : null,
        Math.random() > 0.7 ? 'premium_support' : null
      ].filter(Boolean),
      notes: Math.random() > 0.8 ? `这是第${i}个许可证的备注信息` : ''
    });
  }
  
  return licenses;
};

/**
 * Mock数据存储
 */
const mockData = {
  licenses: generateMockLicenses()
};

/**
 * 模拟异步延迟
 * @param {number} ms - 延迟毫秒数
 * @returns {Promise} 延迟Promise
 */
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Mock数据提供者实现
 * @type {DataProvider}
 */
export const mockDataProvider = {
  /**
   * 获取资源列表
   * @param {string} resource - 资源名称
   * @param {Object} params - 查询参数
   * @returns {Promise<Object>} 包含数据和总数的对象
   */
  getList: async (resource, params) => {
    await delay(500); // 模拟网络延迟
    
    const { page, perPage } = params.pagination;
    const { field, order } = params.sort;
    const filters = params.filter;
    
    let data = [...mockData[resource]];
    
    // 应用过滤器
    if (filters) {
      Object.keys(filters).forEach(key => {
        if (filters[key]) {
          data = data.filter(record => 
            String(record[key]).toLowerCase().includes(String(filters[key]).toLowerCase())
          );
        }
      });
    }
    
    // 应用排序
    if (field) {
      data.sort((a, b) => {
        const aVal = a[field];
        const bVal = b[field];
        
        if (order === 'DESC') {
          return aVal > bVal ? -1 : 1;
        }
        return aVal < bVal ? -1 : 1;
      });
    }
    
    // 应用分页
    const start = (page - 1) * perPage;
    const end = start + perPage;
    const paginatedData = data.slice(start, end);
    
    return {
      data: paginatedData,
      total: data.length
    };
  },

  /**
   * 获取单个资源
   * @param {string} resource - 资源名称
   * @param {Object} params - 查询参数
   * @returns {Promise<Object>} 资源数据
   */
  getOne: async (resource, params) => {
    await delay(300);
    
    const record = mockData[resource].find(item => item.id === params.id);
    
    if (!record) {
      throw new Error(`${resource} with id ${params.id} not found`);
    }
    
    return { data: record };
  },

  /**
   * 获取多个资源
   * @param {string} resource - 资源名称
   * @param {Object} params - 查询参数
   * @returns {Promise<Object>} 资源数据数组
   */
  getMany: async (resource, params) => {
    await delay(300);
    
    const records = mockData[resource].filter(item => 
      params.ids.includes(item.id)
    );
    
    return { data: records };
  },

  /**
   * 根据外键获取资源
   * @param {string} resource - 资源名称
   * @param {Object} params - 查询参数
   * @returns {Promise<Object>} 资源数据数组
   */
  getManyReference: async (resource, params) => {
    await delay(500);
    
    const { page, perPage } = params.pagination;
    const { field, order } = params.sort;
    
    let data = mockData[resource].filter(record => 
      record[params.target] === params.id
    );
    
    // 应用排序
    if (field) {
      data.sort((a, b) => {
        const aVal = a[field];
        const bVal = b[field];
        return order === 'DESC' ? (aVal > bVal ? -1 : 1) : (aVal < bVal ? -1 : 1);
      });
    }
    
    // 应用分页
    const start = (page - 1) * perPage;
    const end = start + perPage;
    const paginatedData = data.slice(start, end);
    
    return {
      data: paginatedData,
      total: data.length
    };
  },

  /**
   * 创建资源
   * @param {string} resource - 资源名称
   * @param {Object} params - 创建参数
   * @returns {Promise<Object>} 创建的资源数据
   */
  create: async (resource, params) => {
    await delay(800);
    
    const newId = Math.max(...mockData[resource].map(item => item.id)) + 1;
    const newRecord = {
      id: newId,
      ...params.data,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    
    mockData[resource].push(newRecord);
    
    return { data: newRecord };
  },

  /**
   * 更新资源
   * @param {string} resource - 资源名称
   * @param {Object} params - 更新参数
   * @returns {Promise<Object>} 更新后的资源数据
   */
  update: async (resource, params) => {
    await delay(600);
    
    const index = mockData[resource].findIndex(item => item.id === params.id);
    
    if (index === -1) {
      throw new Error(`${resource} with id ${params.id} not found`);
    }
    
    const updatedRecord = {
      ...mockData[resource][index],
      ...params.data,
      id: params.id,
      updatedAt: new Date().toISOString()
    };
    
    mockData[resource][index] = updatedRecord;
    
    return { data: updatedRecord };
  },

  /**
   * 更新多个资源
   * @param {string} resource - 资源名称
   * @param {Object} params - 更新参数
   * @returns {Promise<Object>} 更新后的资源数据数组
   */
  updateMany: async (resource, params) => {
    await delay(800);
    
    const updatedRecords = [];
    
    params.ids.forEach(id => {
      const index = mockData[resource].findIndex(item => item.id === id);
      if (index !== -1) {
        mockData[resource][index] = {
          ...mockData[resource][index],
          ...params.data,
          updatedAt: new Date().toISOString()
        };
        updatedRecords.push(mockData[resource][index]);
      }
    });
    
    return { data: params.ids };
  },

  /**
   * 删除资源
   * @param {string} resource - 资源名称
   * @param {Object} params - 删除参数
   * @returns {Promise<Object>} 删除的资源数据
   */
  delete: async (resource, params) => {
    await delay(400);
    
    const index = mockData[resource].findIndex(item => item.id === params.id);
    
    if (index === -1) {
      throw new Error(`${resource} with id ${params.id} not found`);
    }
    
    const deletedRecord = mockData[resource][index];
    mockData[resource].splice(index, 1);
    
    return { data: deletedRecord };
  },

  /**
   * 删除多个资源
   * @param {string} resource - 资源名称
   * @param {Object} params - 删除参数
   * @returns {Promise<Object>} 删除的资源ID数组
   */
  deleteMany: async (resource, params) => {
    await delay(600);
    
    const deletedIds = [];
    
    params.ids.forEach(id => {
      const index = mockData[resource].findIndex(item => item.id === id);
      if (index !== -1) {
        mockData[resource].splice(index, 1);
        deletedIds.push(id);
      }
    });
    
    return { data: deletedIds };
  }
};

// 导出数据生成函数，便于测试使用
export { generateMockLicenses };