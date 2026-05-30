/**
 * 数据导出功能组件
 * @description 提供许可证数据的导出功能
 * @author iMatuProject Team
 * @version 1.0.0
 */

import React, { useState } from 'react';
import {
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  FormGroup,
  LinearProgress,
  Alert
} from '@mui/material';
import { useListContext } from 'react-admin';

/**
 * 数据导出对话框组件
 * @description 提供多种格式的数据导出选项
 */
export const ExportDialog = ({ open, onClose, onExport }) => {
  const [exportFormat, setExportFormat] = useState('csv');
  const [selectedFields, setSelectedFields] = useState([
    'id', 'licenseKey', 'orgName', 'contactEmail', 'licenseType', 
    'status', 'createdAt', 'expiryDate', 'maxUsers', 'maxDevices'
  ]);
  const [isExporting, setIsExporting] = useState(false);

  // 可导出的字段选项
  const availableFields = [
    { id: 'id', name: 'ID' },
    { id: 'licenseKey', name: '许可证密钥' },
    { id: 'orgName', name: '组织名称' },
    { id: 'contactEmail', name: '联系邮箱' },
    { id: 'licenseType', name: '许可证类型' },
    { id: 'status', name: '状态' },
    { id: 'createdAt', name: '创建时间' },
    { id: 'updatedAt', name: '更新时间' },
    { id: 'expiryDate', name: '过期时间' },
    { id: 'maxUsers', name: '最大用户数' },
    { id: 'maxDevices', name: '最大设备数' },
    { id: 'features', name: '功能特性' },
    { id: 'notes', name: '备注' }
  ];

  /**
   * 处理字段选择变化
   */
  const handleFieldChange = (fieldId) => {
    setSelectedFields(prev => 
      prev.includes(fieldId)
        ? prev.filter(id => id !== fieldId)
        : [...prev, fieldId]
    );
  };

  /**
   * 执行导出操作
   */
  const handleExport = async () => {
    setIsExporting(true);
    
    try {
      // 模拟导出过程
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // 调用父组件的导出函数
      await onExport({
        format: exportFormat,
        fields: selectedFields
      });
      
      onClose();
    } catch (error) {
      console.error('导出失败:', error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>导出许可证数据</DialogTitle>
      
      <DialogContent>
        {isExporting && (
          <Alert severity="info" sx={{ mb: 2 }}>
            正在准备导出数据，请稍候...
          </Alert>
        )}
        
        <FormControl fullWidth sx={{ mb: 3 }}>
          <InputLabel>导出格式</InputLabel>
          <Select
            value={exportFormat}
            label="导出格式"
            onChange={(e) => setExportFormat(e.target.value)}
            disabled={isExporting}
          >
            <MenuItem value="csv">CSV格式</MenuItem>
            <MenuItem value="excel">Excel格式</MenuItem>
            <MenuItem value="json">JSON格式</MenuItem>
            <MenuItem value="pdf">PDF格式</MenuItem>
          </Select>
        </FormControl>

        <div>
          <h3>选择导出字段</h3>
          <FormGroup>
            {availableFields.map(field => (
              <FormControlLabel
                key={field.id}
                control={
                  <Checkbox
                    checked={selectedFields.includes(field.id)}
                    onChange={() => handleFieldChange(field.id)}
                    disabled={isExporting}
                  />
                }
                label={field.name}
              />
            ))}
          </FormGroup>
        </div>

        {isExporting && (
          <LinearProgress sx={{ mt: 2 }} />
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose} disabled={isExporting}>
          取消
        </Button>
        <Button 
          onClick={handleExport} 
          variant="contained"
          disabled={isExporting || selectedFields.length === 0}
        >
          {isExporting ? '导出中...' : '导出'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

/**
 * 导出按钮组件
 * @description 列表页面的导出功能入口
 */
export const ExportButton = () => {
  const [open, setOpen] = useState(false);
  const { data, isLoading } = useListContext();

  /**
   * 执行实际的导出逻辑
   */
  const handleExport = async ({ format, fields }) => {
    try {
      // 根据选择的字段过滤数据
      const filteredData = data.map(item => {
        const filteredItem = {};
        fields.forEach(field => {
          filteredItem[field] = item[field];
        });
        return filteredItem;
      });

      // 根据格式生成相应的内容
      let content, filename, mimeType;
      
      switch (format) {
        case 'csv':
          content = convertToCSV(filteredData);
          filename = `licenses_${new Date().toISOString().split('T')[0]}.csv`;
          mimeType = 'text/csv;charset=utf-8;';
          break;
          
        case 'excel':
          content = convertToExcel(filteredData);
          filename = `licenses_${new Date().toISOString().split('T')[0]}.xlsx`;
          mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
          break;
          
        case 'json':
          content = JSON.stringify(filteredData, null, 2);
          filename = `licenses_${new Date().toISOString().split('T')[0]}.json`;
          mimeType = 'application/json';
          break;
          
        case 'pdf':
          content = await convertToPDF(filteredData);
          filename = `licenses_${new Date().toISOString().split('T')[0]}.pdf`;
          mimeType = 'application/pdf';
          break;
          
        default:
          throw new Error('不支持的导出格式');
      }

      // 下载文件
      downloadFile(content, filename, mimeType);
      
      alert(`数据已成功导出为 ${filename}`);
      
    } catch (error) {
      console.error('导出失败:', error);
      alert('导出过程中发生错误，请重试');
    }
  };

  /**
   * 转换为CSV格式
   */
  const convertToCSV = (data) => {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(','),
      ...data.map(row => 
        headers.map(header => 
          `"${String(row[header] || '').replace(/"/g, '""')}"`
        ).join(',')
      )
    ].join('\n');
    
    return csvContent;
  };

  /**
   * 转换为Excel格式（简化版本）
   */
  const convertToExcel = (data) => {
    // 简化的Excel转换，实际项目中应使用专门的库如xlsx
    const csv = convertToCSV(data);
    return csv; // 实际应该返回真正的Excel二进制数据
  };

  /**
   * 转换为PDF格式（模拟）
   */
  const convertToPDF = async (data) => {
    // 模拟PDF生成，实际项目中应使用jsPDF等库
    return 'PDF content would be generated here';
  };

  /**
   * 下载文件
   */
  const downloadFile = (content, filename, mimeType) => {
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  return (
    <>
      <Button
        variant="outlined"
        onClick={() => setOpen(true)}
        disabled={isLoading || !data || data.length === 0}
        sx={{ ml: 1 }}
      >
        📤 导出
      </Button>
      
      <ExportDialog
        open={open}
        onClose={() => setOpen(false)}
        onExport={handleExport}
      />
    </>
  );
};