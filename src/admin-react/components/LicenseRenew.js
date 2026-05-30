/**
 * 许可证续费组件
 * @description 提供许可证续费功能
 * @author iMatuProject Team
 * @version 1.0.0
 */

import React, { useState } from 'react';
import {
  Edit,
  SimpleForm,
  TextInput,
  SelectInput,
  NumberInput,
  DateInput,
  ReferenceInput,
  AutocompleteInput,
  SaveButton,
  Toolbar,
  useNotify,
  useRedirect,
  required,
  minValue
} from 'react-admin';

/**
 * 自定义续费工具栏
 * @description 添加续费专用按钮
 */
const RenewToolbar = props => (
  <Toolbar {...props}>
    <SaveButton
      label="确认续费"
      icon={<span>🔄</span>}
      variant="contained"
      sx={{ mr: 2 }}
    />
    <SaveButton
      label="预览续费"
      icon={<span>👁️</span>}
      variant="outlined"
    />
  </Toolbar>
);

/**
 * 许可证续费组件
 * @description 为现有许可证延长有效期
 */
export const LicenseRenew = (props) => {
  const [renewalInfo, setRenewalInfo] = useState(null);
  const notify = useNotify();
  const redirect = useRedirect();

  /**
   * 处理续费逻辑
   * @param {Object} data - 续费表单数据
   */
  const handleRenew = async (data) => {
    try {
      // 计算新的过期日期
      const currentExpiry = new Date(data.currentExpiryDate);
      const renewalDays = data.renewalDays;
      const newExpiryDate = new Date(currentExpiry);
      newExpiryDate.setDate(newExpiryDate.getDate() + renewalDays);
      
      // 准备续费信息用于预览
      const renewalDetails = {
        licenseId: data.id,
        orgName: data.orgName,
        currentExpiry: currentExpiry.toLocaleDateString(),
        newExpiry: newExpiryDate.toLocaleDateString(),
        renewalDays: renewalDays,
        renewalFee: calculateRenewalFee(data.licenseType, renewalDays)
      };
      
      setRenewalInfo(renewalDetails);
      
      // 模拟续费API调用
      setTimeout(() => {
        notify(`许可证 ${data.orgName} 续费成功！新到期日：${newExpiryDate.toLocaleDateString()}`, 
               { type: 'success' });
        redirect('/licenses');
      }, 2000);
      
    } catch (error) {
      notify('续费操作失败', { type: 'error' });
    }
  };

  /**
   * 计算续费费用
   * @param {string} licenseType - 许可证类型
   * @param {number} days - 续费天数
   * @returns {number} 续费费用
   */
  const calculateRenewalFee = (licenseType, days) => {
    const dailyRates = {
      COMMERCIAL: 10,
      ENTERPRISE: 25,
      TRIAL: 0
    };
    
    const rate = dailyRates[licenseType] || 0;
    return rate * days;
  };

  return (
    <Edit 
      {...props} 
      title="许可证续费"
      transform={handleRenew}
    >
      <SimpleForm toolbar={<RenewToolbar />}>
        {/* 许可证基本信息（只读） */}
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
        
        <SelectInput 
          source="licenseType" 
          label="许可证类型" 
          choices={[
            { id: 'COMMERCIAL', name: '商业版' },
            { id: 'ENTERPRISE', name: '企业版' },
            { id: 'TRIAL', name: '试用版' }
          ]}
          fullWidth
          disabled
        />
        
        <DateInput 
          source="currentExpiryDate" 
          label="当前到期日" 
          fullWidth 
          disabled
        />
        
        {/* 续费配置 */}
        <NumberInput 
          source="renewalDays" 
          label="续费天数" 
          validate={[required(), minValue(1)]}
          defaultValue={365}
          fullWidth
          helperText="需要延长的有效期天数"
        />
        
        <SelectInput 
          source="renewalReason" 
          label="续费原因" 
          choices={[
            { id: 'contract_extension', name: '合同延期' },
            { id: 'business_growth', name: '业务扩展' },
            { id: 'feature_upgrade', name: '功能升级' },
            { id: 'other', name: '其他原因' }
          ]}
          defaultValue="contract_extension"
          fullWidth
        />
        
        {/* 费用计算 */}
        <div style={{
          border: '1px solid #e0e0e0',
          borderRadius: '8px',
          padding: '16px',
          marginTop: '20px',
          backgroundColor: '#fafafa'
        }}>
          <h3 style={{ marginTop: 0, color: '#2196F3' }}>费用预估</h3>
          
          <ReferenceInput source="licenseType" reference="licenses">
            <AutocompleteInput 
              optionText="licenseType" 
              sx={{ display: 'none' }}
            />
          </ReferenceInput>
          
          <div style={{ marginBottom: '12px' }}>
            <strong>续费天数：</strong>
            <span id="renewal-days-display">365天</span>
          </div>
          
          <div style={{ marginBottom: '12px' }}>
            <strong>日费率：</strong>
            <span id="daily-rate-display">¥10/天</span>
          </div>
          
          <div style={{ 
            borderTop: '1px solid #e0e0e0', 
            paddingTop: '12px',
            fontWeight: 'bold',
            fontSize: '1.1em'
          }}>
            <strong>预估总费用：</strong>
            <span id="total-fee-display" style={{ color: '#4CAF50' }}>
              ¥3,650
            </span>
          </div>
        </div>
        
        {/* 续费确认 */}
        <div style={{
          border: '2px solid #FF9800',
          borderRadius: '8px',
          padding: '16px',
          marginTop: '20px',
          backgroundColor: '#fff8e1'
        }}>
          <h3 style={{ marginTop: 0, color: '#FF9800' }}>⚠️ 续费提醒</h3>
          <ul style={{ paddingLeft: '20px', margin: '8px 0' }}>
            <li>续费后原许可证将继续有效至新到期日</li>
            <li>续费费用将在确认后立即扣除</li>
            <li>续费操作不可撤销</li>
            <li>如有疑问请联系技术支持</li>
          </ul>
        </div>
        
        {/* 续费结果预览 */}
        {renewalInfo && (
          <div style={{
            padding: '16px',
            backgroundColor: '#e8f5e8',
            border: '1px solid #c8e6c9',
            borderRadius: '8px',
            marginTop: '20px'
          }}>
            <h4 style={{ margin: '0 0 12px 0', color: '#2e7d32' }}>
              🔄 续费处理中...
            </h4>
            <div style={{ fontSize: '0.875rem' }}>
              <p style={{ margin: '4px 0' }}>
                <strong>组织：</strong> {renewalInfo.orgName}
              </p>
              <p style={{ margin: '4px 0' }}>
                <strong>原到期日：</strong> {renewalInfo.currentExpiry}
              </p>
              <p style={{ margin: '4px 0' }}>
                <strong>新到期日：</strong> {renewalInfo.newExpiry}
              </p>
              <p style={{ margin: '4px 0' }}>
                <strong>延长期限：</strong> {renewalInfo.renewalDays}天
              </p>
              <p style={{ margin: '4px 0' }}>
                <strong>续费费用：</strong> ¥{renewalInfo.renewalFee}
              </p>
            </div>
          </div>
        )}
      </SimpleForm>
    </Edit>
  );
};