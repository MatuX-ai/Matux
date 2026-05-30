/**
 * 许可证创建组件
 * @description 提供新建许可证的功能
 * @author iMatuProject Team
 * @version 1.0.0
 */

import React from 'react';
import {
  Create,
  SimpleForm,
  TextInput,
  SelectInput,
  NumberInput,
  DateInput,
  ArrayInput,
  SimpleFormIterator,
  required,
  minLength,
  minValue,
  maxValue,
  email
} from 'react-admin';

/**
 * 许可证创建组件
 * @description 创建新的许可证记录
 */
export const LicenseCreate = (props) => (
  <Create {...props} title="创建许可证">
    <SimpleForm>
      {/* 基础信息 */}
      <TextInput 
        source="orgName" 
        label="组织名称" 
        fullWidth 
        validate={[required(), minLength(2)]}
        helperText="请输入组织的全称"
      />
      
      <TextInput 
        source="contactEmail" 
        label="联系邮箱" 
        fullWidth 
        validate={[required(), email()]}
        helperText="用于接收许可证相关信息"
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
        helperText="选择合适的许可证类型"
      />
      
      <SelectInput 
        source="status" 
        label="初始状态" 
        choices={[
          { id: 'ACTIVE', name: '激活' },
          { id: 'INACTIVE', name: '未激活' },
          { id: 'PENDING', name: '待审核' }
        ]}
        validate={[required()]}
        defaultValue="PENDING"
        fullWidth
        helperText="新许可证的初始状态"
      />
      
      {/* 限制配置 */}
      <NumberInput 
        source="maxUsers" 
        label="最大用户数" 
        validate={[required(), minValue(1), maxValue(10000)]}
        defaultValue={100}
        fullWidth
        helperText="许可证允许的最大用户数量"
      />
      
      <NumberInput 
        source="maxDevices" 
        label="最大设备数" 
        validate={[required(), minValue(1), maxValue(5000)]}
        defaultValue={50}
        fullWidth
        helperText="许可证允许的最大设备数量"
      />
      
      {/* 日期配置 */}
      <DateInput 
        source="expiryDate" 
        label="过期日期" 
        validate={[required()]}
        fullWidth
        helperText="许可证的有效截止日期"
      />
      
      {/* 功能特性 */}
      <ArrayInput 
        source="features" 
        label="功能特性"
        defaultValue={['core_features']}
      >
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
        helperText="可选的额外说明信息"
      />
    </SimpleForm>
  </Create>
);