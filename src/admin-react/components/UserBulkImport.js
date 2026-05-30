/**
 * 用户批量导入组件
 * @description 提供CSV/Excel文件批量导入用户的功能
 * @author iMatuProject Team
 * @version 1.0.0
 */

import React, { useState } from 'react';
import {
  Create,
  SimpleForm,
  useNotify,
  useRedirect,
  SaveButton,
  Toolbar
} from 'react-admin';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  LinearProgress,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Divider
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';

/**
 * 冲突解决策略枚举
 */
const ConflictResolution = {
  SKIP: 'skip',
  UPDATE: 'update',
  OVERWRITE: 'overwrite',
  ERROR: 'error'
};

/**
 * 自定义工具栏组件
 */
const ImportToolbar = props => (
  <Toolbar {...props} sx={{ display: 'flex', justifyContent: 'space-between' }}>
    <SaveButton
      label="开始导入"
      icon={<CloudUploadIcon />}
      variant="contained"
      type="submit"
    />
    <Button
      variant="outlined"
      onClick={() => window.history.back()}
    >
      取消
    </Button>
  </Toolbar>
);

/**
 * 文件上传区域组件
 */
const FileUploadArea = ({ onFileSelect, selectedFile }) => {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  const handleFileInput = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  return (
    <Box
      sx={{
        border: '2px dashed',
        borderColor: isDragOver ? 'primary.main' : 'grey.300',
        borderRadius: 2,
        p: 4,
        textAlign: 'center',
        backgroundColor: isDragOver ? 'primary.light' : 'background.paper',
        transition: 'all 0.3s ease',
        cursor: 'pointer'
      }}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => document.getElementById('file-input').click()}
    >
      <input
        id="file-input"
        type="file"
        accept=".csv,.xlsx,.xls"
        onChange={handleFileInput}
        style={{ display: 'none' }}
      />
      
      <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
      <Typography variant="h6" gutterBottom>
        {selectedFile ? selectedFile.name : '拖拽文件到这里或点击选择文件'}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        支持 CSV 和 Excel 格式 (.csv, .xlsx, .xls)
      </Typography>
      {selectedFile && (
        <Chip
          label={`文件大小: ${(selectedFile.size / 1024).toFixed(1)} KB`}
          size="small"
          sx={{ mt: 1 }}
        />
      )}
    </Box>
  );
};

/**
 * 导入配置表单
 */
const ImportConfiguration = ({ 
  conflictResolution, 
  setConflictResolution,
  generatePassword,
  setGeneratePassword 
}) => (
  <Card sx={{ mb: 3 }}>
    <CardContent>
      <Typography variant="h6" gutterBottom>
        导入配置
      </Typography>
      
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>冲突处理策略</InputLabel>
        <Select
          value={conflictResolution}
          onChange={(e) => setConflictResolution(e.target.value)}
          label="冲突处理策略"
        >
          <MenuItem value={ConflictResolution.SKIP}>
            跳过重复项
          </MenuItem>
          <MenuItem value={ConflictResolution.UPDATE}>
            更新现有用户
          </MenuItem>
          <MenuItem value={ConflictResolution.OVERWRITE}>
            完全覆盖
          </MenuItem>
          <MenuItem value={ConflictResolution.ERROR}>
            发现冲突时停止
          </MenuItem>
        </Select>
      </FormControl>
      
      <FormControlLabel
        control={
          <Checkbox
            checked={generatePassword}
            onChange={(e) => setGeneratePassword(e.target.checked)}
          />
        }
        label="自动生成随机密码"
      />
      
      <Alert severity="info" sx={{ mt: 2 }}>
        <Typography variant="body2">
          <strong>字段映射说明：</strong><br/>
          • 用户名: username, Username, 用户名<br/>
          • 邮箱: email, Email, 邮箱<br/>
          • 角色: role, Role, 角色 (可选，默认为 user)
        </Typography>
      </Alert>
    </CardContent>
  </Card>
);

/**
 * 导入结果显示组件
 */
const ImportResults = ({ results }) => {
  if (!results) return null;

  const { success_count, failed_count, conflicts_count, errors, conflicts, imported_users } = results;

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          导入结果
        </Typography>
        
        {/* 统计信息 */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <Chip
            icon={<CheckCircleIcon />}
            label={`${success_count} 成功`}
            color="success"
            variant="outlined"
          />
          <Chip
            icon={<ErrorIcon />}
            label={`${failed_count} 失败`}
            color="error"
            variant="outlined"
          />
          <Chip
            icon={<WarningIcon />}
            label={`${conflicts_count} 冲突`}
            color="warning"
            variant="outlined"
          />
        </Box>
        
        {/* 错误信息 */}
        {errors && errors.length > 0 && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="subtitle2">错误信息:</Typography>
            {errors.map((error, index) => (
              <Typography key={index} variant="body2">{error}</Typography>
            ))}
          </Alert>
        )}
        
        {/* 冲突详情 */}
        {conflicts && Object.keys(conflicts).length > 0 && (
          <>
            <Typography variant="subtitle1" gutterBottom>
              冲突详情:
            </Typography>
            {Object.entries(conflicts).map(([conflictType, conflictList]) => (
              <Box key={conflictType} sx={{ mb: 2 }}>
                <Typography variant="body2" fontWeight="bold">
                  {conflictType === 'email_conflicts' && '邮箱冲突:'}
                  {conflictType === 'username_conflicts' && '用户名冲突:'}
                  {conflictType === 'invalid_data' && '数据验证失败:'}
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>行号</TableCell>
                        <TableCell>值</TableCell>
                        <TableCell>问题</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {conflictList.map((conflict, index) => (
                        <TableRow key={index}>
                          <TableCell>{conflict.row}</TableCell>
                          <TableCell>
                            {conflict.username || conflict.email || conflict.value}
                          </TableCell>
                          <TableCell>
                            {conflict.error || (conflict.existing ? '已存在' : '')}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            ))}
          </>
        )}
        
        {/* 成功导入的用户列表 */}
        {imported_users && imported_users.length > 0 && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" gutterBottom>
              成功导入的用户:
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>用户名</TableCell>
                    <TableCell>邮箱</TableCell>
                    <TableCell>角色</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {imported_users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>{user.id}</TableCell>
                      <TableCell>{user.username}</TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>{user.role || 'user'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * 用户批量导入主组件
 */
export const UserBulkImport = (props) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [conflictResolution, setConflictResolution] = useState(ConflictResolution.SKIP);
  const [generatePassword, setGeneratePassword] = useState(true);
  const [isImporting, setIsImporting] = useState(false);
  const [importResults, setImportResults] = useState(null);
  const [progress, setProgress] = useState(0);
  
  const notify = useNotify();
  const redirect = useRedirect();

  /**
   * 处理文件选择
   */
  const handleFileSelect = (file) => {
    // 验证文件类型
    const validTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
    if (!validTypes.includes(file.type)) {
      notify('请选择有效的CSV或Excel文件', { type: 'error' });
      return;
    }
    
    // 验证文件大小 (限制为10MB)
    if (file.size > 10 * 1024 * 1024) {
      notify('文件大小不能超过10MB', { type: 'error' });
      return;
    }
    
    setSelectedFile(file);
    setImportResults(null); // 清除之前的导入结果
  };

  /**
   * 处理批量导入
   */
  const handleImport = async (data) => {
    if (!selectedFile) {
      notify('请先选择要导入的文件', { type: 'error' });
      return;
    }

    setIsImporting(true);
    setProgress(0);
    setImportResults(null);

    try {
      // 创建FormData
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('conflict_resolution', conflictResolution);
      formData.append('generate_password', generatePassword.toString());

      // 模拟进度更新
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      // 发送请求到后端API
      const response = await fetch('/api/v1/auth/bulk-import', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      clearInterval(progressInterval);
      setProgress(100);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '导入失败');
      }

      const result = await response.json();
      setImportResults(result);
      
      if (result.success_count > 0) {
        notify(`成功导入 ${result.success_count} 个用户`, { type: 'success' });
      }
      
      if (result.failed_count > 0 || result.conflicts_count > 0) {
        notify(`导入完成，但有 ${result.failed_count + result.conflicts_count} 条记录存在问题`, { type: 'warning' });
      }

    } catch (error) {
      console.error('导入失败:', error);
      notify(`导入失败: ${error.message}`, { type: 'error' });
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <Create {...props} title="批量导入用户">
      <SimpleForm
        toolbar={<ImportToolbar />}
        onSubmit={handleImport}
        sanitizeEmptyValues
      >
        <Box sx={{ width: '100%', maxWidth: 800, mx: 'auto' }}>
          <Typography variant="h4" gutterBottom align="center">
            批量导入用户
          </Typography>
          
          <FileUploadArea 
            onFileSelect={handleFileSelect} 
            selectedFile={selectedFile}
          />
          
          {selectedFile && (
            <>
              <ImportConfiguration
                conflictResolution={conflictResolution}
                setConflictResolution={setConflictResolution}
                generatePassword={generatePassword}
                setGeneratePassword={setGeneratePassword}
              />
              
              {isImporting && (
                <Box sx={{ mb: 3 }}>
                  <LinearProgress variant="determinate" value={progress} />
                  <Typography variant="body2" align="center" sx={{ mt: 1 }}>
                    正在导入... {progress}%
                  </Typography>
                </Box>
              )}
              
              <ImportResults results={importResults} />
            </>
          )}
        </Box>
      </SimpleForm>
    </Create>
  );
};