/**
 * 批量生成许可证组件
 * @description 提供批量创建许可证的功能
 * @author iMatuProject Team
 * @version 1.0.0
 */

import React, { useState } from 'react';
import {
  Create,
  SimpleForm,
  TextInput,
  SelectInput,
  NumberInput,
  DateInput,
  ArrayInput,
  SimpleFormIterator,
  SaveButton,
  Toolbar,
  useNotify,
  useRedirect,
  required,
  minLength,
  minValue,
  maxValue,
  email
} from 'react-admin';

/**
 * 自定义工具栏组件
 * @description 添加批量生成功能按钮
 */
const BulkCreateToolbar = props => (
  <Toolbar {...props}>
    <SaveButton
      label="批量生成"
      icon={<span>🚀</span>}
      variant="contained"
      sx={{ mr: 2 }}
    />
    <SaveButton
      label="预览生成"
      icon={<span>👁️</span>}
      variant="outlined"
    />
  </Toolbar>
);

/**
 * 批量生成许可证组件
 * @description 支持批量创建多个许可证
 */
export const LicenseBulkCreate = (props) => {
  const [generatedCount, setGeneratedCount] = useState(0);
  const notify = useNotify();
  const redirect = useRedirect();

  /**
   * 处理批量生成逻辑
   * @param {Object} data - 表单数据
   */
  const handleBulkCreate = async (data) => {
    try {
      // 模拟批量生成过程
      const count = data.batchCount || 10;
      setGeneratedCount(count);
      
      // 这里应该调用实际的批量创建API
      // 暂时使用模拟数据
      
      notify(`成功生成 ${count} 个许可证`, { type: 'success' });
      
      // 3秒后跳转到许可证列表页
      setTimeout(() => {
        redirect('/licenses');
      }, 3000);
      
    } catch (error) {
      notify('批量生成失败', { type: 'error' });
    }
  };

  return (
    <Create 
      {...props} 
      title="批量生成许可证"
      transform={handleBulkCreate}
    >
      <SimpleForm toolbar={<BulkCreateToolbar />}>
        {/* 批量生成配置 */}
        <NumberInput 
          source="batchCount" 
          label="生成数量" 
          validate={[required(), minValue(1), maxValue(100)]}
          defaultValue={10}
          fullWidth
          helperText="一次性生成的许可证数量（最多100个）"
        />
        
        <SelectInput 
          source="generationStrategy" 
          label="生成策略" 
          choices={[
            { id: 'sequential', name: '顺序编号' },
            { id: 'random', name: '随机编号' },
            { id: 'timestamp', name: '时间戳编号' }
          ]}
          defaultValue="sequential"
          fullWidth
          helperText="许可证编号的生成方式"
        />
        
        {/* 组织信息模板 */}
        <TextInput 
          source="orgNameTemplate" 
          label="组织名称模板" 
          fullWidth 
          defaultValue="组织{index}"
          helperText="使用 {index} 作为序号占位符，如：组织{index}"
        />
        
        <TextInput 
          source="emailDomain" 
          label="邮箱域名" 
          fullWidth 
          defaultValue="@company.com"
          validate={[required()]}
          helperText="生成邮箱的域名部分"
        />
        
        {/* 许可证配置模板 */}
        <SelectInput 
          source="licenseType" 
          label="许可证类型" 
          choices={[
            { id: 'COMMERCIAL', name: '商业版' },
            { id: 'ENTERPRISE', name: '企业版' },
            { id: 'TRIAL', name: '试用版' }
          ]}
          defaultValue="COMMERCIAL"
          fullWidth
        />
        
        <SelectInput 
          source="initialStatus" 
          label="初始状态" 
          choices={[
            { id: 'ACTIVE', name: '激活' },
            { id: 'INACTIVE', name: '未激活' },
            { id: 'PENDING', name: '待审核' }
          ]}
          defaultValue="PENDING"
          fullWidth
        />
        
        {/* 限制配置 */}
        <NumberInput 
          source="maxUsers" 
          label="最大用户数" 
          validate={[required(), minValue(1), maxValue(10000)]}
          defaultValue={100}
          fullWidth
        />
        
        <NumberInput 
          source="maxDevices" 
          label="最大设备数" 
          validate={[required(), minValue(1), maxValue(5000)]}
          defaultValue={50}
          fullWidth
        />
        
        {/* 有效期配置 */}
        <NumberInput 
          source="validityDays" 
          label="有效期（天）" 
          validate={[required(), minValue(1), maxValue(3650)]}
          defaultValue={365}
          fullWidth
          helperText="从今天开始计算的有效天数"
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
        
        {/* 高级选项 */}
        <div style={{ 
          border: '1px solid #e0e0e0', 
          borderRadius: '8px', 
          padding: '16px', 
          marginTop: '20px',
          backgroundColor: '#fafafa'
        }}>
          <h3 style={{ marginTop: 0, color: '#2196F3' }}>高级选项</h3>
          
          <TextInput 
            source="prefix" 
            label="许可证前缀" 
            fullWidth 
            helperText="许可证编号的自定义前缀"
          />
          
          <TextInput 
            source="notesTemplate" 
            label="备注模板" 
            fullWidth 
            multiline
            rows={3}
            helperText="批量生成的统一备注信息"
          />
        </div>
        
        {/* 生成预览 */}
        {generatedCount > 0 && (
          <div style={{
            padding: '16px',
            backgroundColor: '#e8f5e8',
            border: '1px solid #c8e6c9',
            borderRadius: '8px',
            marginTop: '20px'
          }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#2e7d32' }}>
              🚀 批量生成完成！
            </h4>
            <p style={{ margin: 0 }}>
              已成功生成 <strong>{generatedCount}</strong> 个许可证
            </p>
            <p style={{ margin: '8px 0 0 0', fontSize: '0.875rem', color: '#666' }}>
              正在跳转到许可证列表页面...
            </p>
          </div>
        )}
      </SimpleForm>
    </Create>
  );
};