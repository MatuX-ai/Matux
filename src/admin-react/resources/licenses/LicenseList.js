/**
 * 许可证列表组件
 * @description 展示许可证列表，支持筛选、排序和批量操作
 * @author iMatuProject Team
 * @version 1.0.0
 */

import React from 'react';
import {
  List,
  Datagrid,
  TextField,
  DateField,
  SelectField,
  BooleanField,
  EditButton,
  DeleteButton,
  BulkDeleteButton,
  Filter,
  TextInput,
  SelectInput,
  DateInput,
  ChipField,
  FunctionField
} from 'react-admin';

/**
 * 许可证筛选器组件
 * @description 提供多种筛选条件
 */
const LicenseFilter = (props) => (
  <Filter {...props}>
    <TextInput label="搜索组织名称" source="orgName" alwaysOn />
    <TextInput label="许可证密钥" source="licenseKey" />
    <SelectInput 
      label="许可证类型" 
      source="licenseType" 
      choices={[
        { id: 'COMMERCIAL', name: '商业版' },
        { id: 'ENTERPRISE', name: '企业版' },
        { id: 'TRIAL', name: '试用版' }
      ]}
    />
    <SelectInput 
      label="状态" 
      source="status" 
      choices={[
        { id: 'ACTIVE', name: '激活' },
        { id: 'INACTIVE', name: '未激活' },
        { id: 'EXPIRED', name: '已过期' },
        { id: 'PENDING', name: '待审核' }
      ]}
    />
    <DateInput label="创建日期从" source="createdAt_gte" />
    <DateInput label="创建日期到" source="createdAt_lte" />
  </Filter>
);

/**
 * 状态字段组件
 * @description 自定义状态显示样式
 */
const StatusField = ({ record = {} }) => {
  const statusConfig = {
    ACTIVE: { label: '激活', className: 'status-active' },
    INACTIVE: { label: '未激活', className: 'status-inactive' },
    EXPIRED: { label: '已过期', className: 'status-expired' },
    PENDING: { label: '待审核', className: 'status-pending' }
  };
  
  const config = statusConfig[record.status] || { label: record.status, className: '' };
  
  return (
    <span className={`status-indicator ${config.className}`}>
      {config.label}
    </span>
  );
};

/**
 * 许可证类型字段组件
 * @description 显示友好的许可证类型名称
 */
const LicenseTypeField = ({ record = {} }) => {
  const typeConfig = {
    COMMERCIAL: { label: '商业版', color: '#2196F3' },
    ENTERPRISE: { label: '企业版', color: '#9C27B0' },
    TRIAL: { label: '试用版', color: '#FF9800' }
  };
  
  const config = typeConfig[record.licenseType] || { label: record.licenseType, color: '#666' };
  
  return (
    <span style={{ 
      backgroundColor: config.color, 
      color: 'white', 
      padding: '4px 8px', 
      borderRadius: '4px',
      fontSize: '0.75rem',
      fontWeight: '500'
    }}>
      {config.label}
    </span>
  );
};

/**
 * 批量操作按钮组
 * @description 定义列表页的批量操作功能
 */
const LicenseBulkActionButtons = () => (
  <>
    <BulkDeleteButton />
  </>
);

/**
 * 许可证列表组件
 * @description 主要的许可证列表展示页面
 */
export const LicenseList = (props) => (
  <List 
    {...props}
    filters={<LicenseFilter />}
    sort={{ field: 'createdAt', order: 'DESC' }}
    perPage={25}
    bulkActionButtons={<LicenseBulkActionButtons />}
  >
    <Datagrid rowClick="edit">
      {/* 基础信息字段 */}
      <TextField source="id" label="ID" />
      <TextField source="licenseKey" label="许可证密钥" />
      <TextField source="orgName" label="组织名称" />
      <TextField source="contactEmail" label="联系邮箱" />
      
      {/* 类型和状态字段 */}
      <FunctionField 
        label="许可证类型" 
        render={record => <LicenseTypeField record={record} />}
      />
      <FunctionField 
        label="状态" 
        render={record => <StatusField record={record} />}
      />
      
      {/* 数量限制字段 */}
      <TextField source="maxUsers" label="最大用户数" />
      <TextField source="maxDevices" label="最大设备数" />
      
      {/* 功能特性 */}
      <ChipField source="features" label="功能特性" />
      
      {/* 日期字段 */}
      <DateField source="createdAt" label="创建时间" showTime />
      <DateField source="expiryDate" label="过期时间" showTime />
      
      {/* 操作按钮 */}
      <EditButton />
      <DeleteButton />
    </Datagrid>
  </List>
);