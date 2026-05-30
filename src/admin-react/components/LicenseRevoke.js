/**
 * 许可证吊销组件
 * @description 提供许可证吊销功能
 * @author iMatuProject Team
 * @version 1.0.0
 */

import React, { useState } from 'react';
import {
  Edit,
  SimpleForm,
  TextInput,
  SelectInput,
  DateField,
  SaveButton,
  Toolbar,
  useNotify,
  useRedirect,
  required
} from 'react-admin';

/**
 * 自定义吊销工具栏
 * @description 添加吊销确认按钮
 */
const RevokeToolbar = props => (
  <Toolbar {...props}>
    <SaveButton
      label="确认吊销"
      icon={<span>🚫</span>}
      variant="contained"
      sx={{ 
        mr: 2,
        backgroundColor: '#f44336',
        '&:hover': {
          backgroundColor: '#d32f2f'
        }
      }}
    />
    <SaveButton
      label="取消操作"
      variant="outlined"
    />
  </Toolbar>
);

/**
 * 许可证吊销组件
 * @description 永久吊销许可证使用权
 */
export const LicenseRevoke = (props) => {
  const [revocationInfo, setRevocationInfo] = useState(null);
  const notify = useNotify();
  const redirect = useRedirect();

  /**
   * 处理吊销逻辑
   * @param {Object} data - 吊销表单数据
   */
  const handleRevoke = async (data) => {
    try {
      // 验证必需字段
      if (!data.revocationReason) {
        notify('请选择吊销原因', { type: 'warning' });
        return;
      }

      // 准备吊销信息
      const revocationDetails = {
        licenseId: data.id,
        orgName: data.orgName,
        licenseKey: data.licenseKey,
        revocationReason: data.revocationReason,
        revocationNotes: data.revocationNotes,
        revocationDate: new Date().toLocaleDateString()
      };
      
      setRevocationInfo(revocationDetails);
      
      // 模拟吊销API调用
      setTimeout(() => {
        notify(`许可证 ${data.orgName} 已成功吊销`, { type: 'success' });
        redirect('/licenses');
      }, 2000);
      
    } catch (error) {
      notify('吊销操作失败', { type: 'error' });
    }
  };

  return (
    <Edit 
      {...props} 
      title="吊销许可证"
      transform={handleRevoke}
    >
      <SimpleForm toolbar={<RevokeToolbar />}>
        {/* 许可证基本信息（只读）*/}
        <TextInput 
          source="licenseKey" 
          label="许可证密钥" 
          fullWidth 
          disabled
        />
        
        <TextInput 
          source="orgName" 
          label="组织名称" 
          fullWidth 
          disabled
        />
        
        <TextInput 
          source="contactEmail" 
          label="联系邮箱" 
          fullWidth 
          disabled
        />
        
        <DateField 
          source="createdAt" 
          label="创建日期" 
          showTime
        />
        
        <DateField 
          source="expiryDate" 
          label="到期日期" 
          showTime
        />
        
        {/* 吊销原因 */}
        <SelectInput 
          source="revocationReason" 
          label="吊销原因 *" 
          choices={[
            { id: 'contract_violation', name: '违反合同条款' },
            { id: 'non_payment', name: '未按时付款' },
            { id: 'security_breach', name: '安全违规' },
            { id: 'fraudulent_use', name: '欺诈使用' },
            { id: 'license_expiration', name: '许可证到期' },
            { id: 'customer_request', name: '客户主动申请' },
            { id: 'technical_issues', name: '技术问题' },
            { id: 'other', name: '其他原因' }
          ]}
          validate={[required()]}
          fullWidth
          helperText="请选择吊销的具体原因"
        />
        
        {/* 吊销详情说明 */}
        <TextInput 
          source="revocationNotes" 
          label="详细说明" 
          multiline 
          rows={4}
          fullWidth
          helperText="请详细描述吊销的原因和相关情况"
        />
        
        {/* 影响范围说明 */}
        <div style={{
          border: '1px solid #e0e0e0',
          borderRadius: '8px',
          padding: '16px',
          marginTop: '20px',
          backgroundColor: '#fafafa'
        }}>
          <h3 style={{ marginTop: 0, color: '#2196F3' }}>影响范围</h3>
          <ul style={{ paddingLeft: '20px', margin: '8px 0' }}>
            <li>吊销后该许可证将立即失效</li>
            <li>所有关联的用户和服务将失去访问权限</li>
            <li>已产生的数据将按政策保留或删除</li>
            <li>吊销操作不可逆转</li>
          </ul>
        </div>
        
        {/* 法律声明 */}
        <div style={{
          border: '2px solid #f44336',
          borderRadius: '8px',
          padding: '16px',
          marginTop: '20px',
          backgroundColor: '#ffebee'
        }}>
          <h3 style={{ marginTop: 0, color: '#f44336' }}>⚠️ 重要法律声明</h3>
          <ul style={{ paddingLeft: '20px', margin: '8px 0' }}>
            <li>请确保吊销决定符合相关法律法规</li>
            <li>建议在吊销前与法务部门确认</li>
            <li>保留所有吊销相关的证据和记录</li>
            <li>及时通知相关利益方</li>
          </ul>
        </div>
        
        {/* 吊销确认区域 */}
        <div style={{
          border: '3px solid #f44336',
          borderRadius: '8px',
          padding: '20px',
          marginTop: '20px',
          textAlign: 'center',
          backgroundColor: '#ffcdd2'
        }}>
          <h2 style={{ 
            margin: '0 0 16px 0', 
            color: '#c62828',
            fontSize: '1.5rem'
          }}>
            ⚠️ 确认吊销操作
          </h2>
          <p style={{ 
            margin: '0 0 16px 0', 
            fontSize: '1.1rem',
            fontWeight: '500'
          }}>
            此操作将永久吊销该许可证的所有权限
          </p>
          <p style={{ margin: 0, color: '#666' }}>
            请输入完整组织名称以确认操作：<strong>{/* 这里应该是动态的组织名称 */}</strong>
          </p>
        </div>
        
        {/* 吊销处理状态 */}
        {revocationInfo && (
          <div style={{
            padding: '16px',
            backgroundColor: '#fff3e0',
            border: '1px solid #ffe0b2',
            borderRadius: '8px',
            marginTop: '20px'
          }}>
            <h4 style={{ margin: '0 0 12px 0', color: '#ef6c00' }}>
              🚫 正在处理吊销请求...
            </h4>
            <div style={{ fontSize: '0.875rem' }}>
              <p style={{ margin: '4px 0' }}>
                <strong>许可证：</strong> {revocationInfo.licenseKey}
              </p>
              <p style={{ margin: '4px 0' }}>
                <strong>组织：</strong> {revocationInfo.orgName}
              </p>
              <p style={{ margin: '4px 0' }}>
                <strong>吊销原因：</strong> {revocationInfo.revocationReason}
              </p>
              <p style={{ margin: '4px 0' }}>
                <strong>处理时间：</strong> {revocationInfo.revocationDate}
              </p>
            </div>
          </div>
        )}
      </SimpleForm>
    </Edit>
  );
};