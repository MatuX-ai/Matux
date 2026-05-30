/**
 * React Admin管理后台主应用组件
 * @description 基于React Admin框架的企业级管理后台
 * @author iMatuProject Team
 * @version 1.0.0
 */

import React from 'react';
import { Admin, Resource } from 'react-admin';
import { createTheme } from '@mui/material/styles';

// 数据提供者
import { mockDataProvider } from './dataProvider/mockDataProvider';

// 资源组件
import { LicenseList } from './resources/licenses/LicenseList';
import { LicenseEdit } from './resources/licenses/LicenseEdit';
import { LicenseCreate } from './resources/licenses/LicenseCreate';

// 自定义组件
import { LicenseBulkCreate } from './components/LicenseBulkCreate';
import { UserBulkImport } from './components/UserBulkImport';
import { LicenseRenew } from './components/LicenseRenew';
import { LicenseRevoke } from './components/LicenseRevoke';
import { ExportButton } from './components/ExportFeature';

/**
 * 自定义主题配置
 * 继承项目Design Token系统，保持视觉一致性
 */
const theme = createTheme({
  palette: {
    primary: {
      main: '#2196F3', // 主品牌色，用于按钮和链接
      light: '#64B5F6',
      dark: '#1976D2',
      contrastText: '#fff'
    },
    secondary: {
      main: '#4CAF50', // 辅助色，用于成功状态
      light: '#81C784',
      dark: '#388E3C',
      contrastText: '#fff'
    },
    error: {
      main: '#F44336' // 错误色，用于危险操作
    },
    warning: {
      main: '#FF9800' // 警告色
    },
    info: {
      main: '#2196F3' // 信息色
    },
    success: {
      main: '#4CAF50' // 成功色
    }
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 500
    },
    body1: {
      fontSize: '1rem'
    },
    body2: {
      fontSize: '0.875rem'
    }
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          textTransform: 'none',
          fontWeight: 500
        }
      }
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }
      }
    }
  }
});

/**
 * 自定义布局组件
 * @param {Object} props - 组件属性
 */
const CustomLayout = (props) => {
  return (
    <div className="admin-layout">
      {props.children}
    </div>
  );
};

/**
 * 自定义列表操作组件
 * @param {Object} props - 组件属性
 */
const CustomListActions = () => {
  return (
    <div style={{ display: 'flex', alignItems: 'center' }}>
      <ExportButton />
    </div>
  );
};

/**
 * 主应用组件
 * 配置React Admin的基础设置和资源注册
 */
const App = () => {
  return (
    <Admin 
      dataProvider={mockDataProvider}
      theme={theme}
      layout={CustomLayout}
      title="iMatuProject 管理后台"
    >
      {/* 许可证管理资源 */}
      <Resource 
        name="licenses" 
        list={LicenseList}
        edit={LicenseEdit}
        create={LicenseCreate}
        options={{ label: '许可证管理' }}
      />
      
      {/* 批量操作自定义页面 */}
      <Resource 
        name="bulk-create" 
        create={LicenseBulkCreate}
        options={{ label: '批量生成' }}
      />
      
      {/* 用户批量导入自定义页面 */}
      <Resource 
        name="user-bulk-import" 
        create={UserBulkImport}
        options={{ label: '批量导入用户' }}
      />
      
      {/* 续费管理自定义页面 */}
      <Resource 
        name="renew" 
        edit={LicenseRenew}
        options={{ label: '许可证续费' }}
      />
      
      {/* 吊销管理自定义页面 */}
      <Resource 
        name="revoke" 
        edit={LicenseRevoke}
        options={{ label: '许可证吊销' }}
      />
    </Admin>
  );
};

export default App;