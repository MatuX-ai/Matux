/**
 * 许可证编辑组件
 * @description 提供许可证信息的编辑功能
 * @author iMatuProject Team
 * @version 1.0.0
 */

import React from 'react';
import {
  Edit,
  SimpleForm,
  TextInput,
  SelectInput,
  NumberInput,
  DateInput,
  BooleanInput,
  ArrayInput,
  SimpleFormIterator,
  ReferenceInput,
  AutocompleteInput,
  required,
  minLength,
  minValue,
  maxValue,
  email
} from 'react-admin';

/**
 * 许可证编辑组件
 * @description 编辑现有许可证的信息
 */
export const LicenseEdit = (props) => (
  <Edit {...props} title="编辑许可证">
    <SimpleForm>
      {/* 基础信息 */}
      <TextInput 
        source="licenseKey" 
        label="许可证密钥" 
        fullWidth 
        disabled
        helperText="许可证密钥不可修改"
      />
      
      <TextInput 
        source="orgName" 
        label="组织名称" 
        fullWidth 
        validate={[required(), minLength(2)]}
      />
      
      <TextInput 
        source="contactEmail" 
        label="联系邮箱" 
        fullWidth 
        validate={[required(), email()]}
      />
      
      {/* 许可证配置 */}
      <SelectInput 
        source="licenseType" 
        label="许可证类型" 
        choices={[
          { id: 'COMMERCIAL', name: '商业版' },
          { id: 'ENTERPRISE', name: '企业版' },
          { id: 'TRIAL', name: '试用版' }
        ]}
        validate={[required()]}
        fullWidth
      />
      
      <SelectInput 
        source="status" 
        label="状态" 
        choices={[
          { id: 'ACTIVE', name: '激活' },
          { id: 'INACTIVE', name: '未激活' },
          { id: 'EXPIRED', name: '已过期' },
          { id: 'PENDING', name: '待审核' }
        ]}
        validate={[required()]}
        fullWidth
      />
      
      {/* 限制配置 */}
      <NumberInput 
        source="maxUsers" 
        label="最大用户数" 
        validate={[required(), minValue(1), maxValue(10000)]}
        fullWidth
      />
      
      <NumberInput 
        source="maxDevices" 
        label="最大设备数" 
        validate={[required(), minValue(1), maxValue(5000)]}
        fullWidth
      />
      
      {/* 日期配置 */}
      <DateInput 
        source="expiryDate" 
        label="过期日期" 
        validate={[required()]}
        fullWidth
      />
      
      {/* 功能特性 */}
      <ArrayInput source="features" label="功能特性">
        <SimpleFormIterator>
          <SelectInput 
            choices={[
              { id: 'core_features', name: '核心功能' },
              { id: 'advanced_analytics', name: '高级分析' },
              { id: 'premium_support', name: '高级支持' },
              { id: 'api_access', name: 'API访问' },
              { id: 'custom_branding', name: '自定义品牌' }
            ]}
          />
        </SimpleFormIterator>
      </ArrayInput>
      
      {/* 备注信息 */}
      <TextInput 
        source="notes" 
        label="备注" 
        multiline 
        rows={4}
        fullWidth
        helperText="可选的备注信息"
      />
    </SimpleForm>
  </Edit>
);