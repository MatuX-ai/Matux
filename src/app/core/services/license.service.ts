import { Injectable } from '@angular/core';

import { unifiedHttpClient } from '../../core/services/unified-http-client';

/**
 * 许可证状态枚举
 */
export enum LicenseStatus {
  ACTIVE = 'active',
  EXPIRED = 'expired',
  REVOKED = 'revoked',
  PENDING = 'pending',
}

/**
 * 许可证类型枚举
 */
export enum LicenseType {
  TRIAL = 'trial',
  COMMERCIAL = 'commercial',
  EDUCATION = 'education',
  ENTERPRISE = 'enterprise',
}

/**
 * 组织接口
 */
export interface Organization {
  id: number;
  name: string;
  contact_email: string;
  phone?: string;
  address?: string;
  website?: string;
  license_count: number;
  max_users: number;
  current_users: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * 许可证接口
 */
export interface License {
  id: number;
  license_key: string;
  organization_id: number;
  product_id?: number;
  license_type: LicenseType;
  status: LicenseStatus;
  issued_at: string;
  expires_at: string;
  activated_at?: string;
  max_users: number;
  max_devices: number;
  current_users: number;
  current_devices: number;
  features: string[];
  restrictions: any;
  metadata: any;
  notes?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  is_expired: boolean;
  is_valid: boolean;
  days_until_expiry?: number;
}

/**
 * 创建组织请求接口
 */
export interface CreateOrganizationRequest {
  name: string;
  contact_email: string;
  phone?: string;
  address?: string;
  website?: string;
  max_users?: number;
}

/**
 * 创建许可证请求接口
 */
export interface CreateLicenseRequest {
  organization_id: number;
  product_id?: number;
  license_type?: LicenseType;
  duration_days?: number;
  max_users?: number;
  max_devices?: number;
  features?: string[];
  notes?: string;
}

/**
 * 更新许可证请求接口
 */
export interface UpdateLicenseRequest {
  status?: LicenseStatus;
  max_users?: number;
  max_devices?: number;
  features?: string[];
  notes?: string;
  is_active?: boolean;
}

/**
 * 验证结果接口
 */
export interface LicenseValidationResult {
  valid: boolean;
  license_info?: License;
  error?: string;
}

/**
 * 统计信息接口
 */
export interface LicenseStatistics {
  database_stats: {
    total_licenses: number;
    active_licenses: number;
    expired_licenses: number;
    revoked_licenses: number;
  };
  cache_stats: any;
  generated_at: string;
}

@Injectable({
  providedIn: 'root',
})
export class LicenseService {
  private baseUrl = '/api/v1'; // 根据实际情况调整

  constructor() {}

  /**
   * 创建新组织
   */
  async createOrganization(orgData: CreateOrganizationRequest): Promise<Organization> {
    const response = await unifiedHttpClient.post<Organization>(
      `${this.baseUrl}/organizations`,
      orgData
    );
    return response.data;
  }

  /**
   * 获取组织列表
   */
  async getOrganizations(
    skip: number = 0,
    limit: number = 100,
    isActive?: boolean
  ): Promise<Organization[]> {
    let url = `${this.baseUrl}/organizations?skip=${skip}&limit=${limit}`;

    if (isActive !== undefined) {
      url += `&is_active=${isActive}`;
    }

    const response = await unifiedHttpClient.get<Organization[]>(url);
    return response.data;
  }

  /**
   * 获取组织详情
   */
  async getOrganization(orgId: number): Promise<Organization> {
    const response = await unifiedHttpClient.get<Organization>(
      `${this.baseUrl}/organizations/${orgId}`
    );
    return response.data;
  }

  /**
   * 更新组织信息
   */
  async updateOrganization(
    orgId: number,
    updateData: Partial<CreateOrganizationRequest>
  ): Promise<Organization> {
    const response = await unifiedHttpClient.put<Organization>(
      `${this.baseUrl}/organizations/${orgId}`,
      updateData
    );
    return response.data;
  }

  /**
   * 生成新许可证
   */
  async generateLicense(licenseData: CreateLicenseRequest): Promise<License> {
    const response = await unifiedHttpClient.post<License>(`${this.baseUrl}/licenses`, licenseData);
    return response.data;
  }

  /**
   * 获取许可证列表
   */
  async getLicenses(
    skip: number = 0,
    limit: number = 100,
    organizationId?: number,
    status?: LicenseStatus
  ): Promise<License[]> {
    let url = `${this.baseUrl}/licenses?skip=${skip}&limit=${limit}`;

    if (organizationId !== undefined) {
      url += `&organization_id=${organizationId}`;
    }

    if (status !== undefined) {
      url += `&status=${status}`;
    }

    const response = await unifiedHttpClient.get<License[]>(url);
    return response.data;
  }

  /**
   * 获取许可证详情
   */
  async getLicense(licenseKey: string): Promise<License> {
    const response = await unifiedHttpClient.get<License>(`${this.baseUrl}/licenses/${licenseKey}`);
    return response.data;
  }

  /**
   * 验证许可证
   */
  async validateLicense(licenseKey: string): Promise<LicenseValidationResult> {
    const response = await unifiedHttpClient.post<LicenseValidationResult>(
      `${this.baseUrl}/licenses/${licenseKey}/validate`,
      {}
    );
    return response.data;
  }

  /**
   * 更新许可证
   */
  async updateLicense(licenseKey: string, updateData: UpdateLicenseRequest): Promise<License> {
    const response = await unifiedHttpClient.put<License>(
      `${this.baseUrl}/licenses/${licenseKey}`,
      updateData
    );
    return response.data;
  }

  /**
   * 撤销许可证
   */
  async revokeLicense(licenseKey: string, reason?: string): Promise<any> {
    const body = reason ? { reason } : {};
    const response = await unifiedHttpClient.post(
      `${this.baseUrl}/licenses/${licenseKey}/revoke`,
      body
    );
    return response.data;
  }

  /**
   * 获取组织的所有许可证
   */
  async getOrganizationLicenses(orgId: number): Promise<License[]> {
    const response = await unifiedHttpClient.get<License[]>(
      `${this.baseUrl}/organizations/${orgId}/licenses`
    );
    return response.data;
  }

  /**
   * 获取许可证统计信息
   */
  async getStatistics(): Promise<LicenseStatistics> {
    const response = await unifiedHttpClient.get<LicenseStatistics>(`${this.baseUrl}/statistics`);
    return response.data;
  }

  /**
   * 健康检查
   */
  async healthCheck(): Promise<any> {
    const response = await unifiedHttpClient.get(`${this.baseUrl}/health`);
    return response.data;
  }

  /**
   * 设置请求头中的许可证密钥
   */
  setLicenseHeader(licenseKey: string): Record<string, string> {
    return {
      'X-License-Key': licenseKey,
    };
  }
}
