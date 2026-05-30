/**
 * 用户批量导入组件测试
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UserBulkImport } from './UserBulkImport';
import { TestContext } from './TestContext'; // 假设的测试上下文

// Mock react-admin
jest.mock('react-admin', () => ({
  Create: ({ children, ...props }) => <div data-testid="create-form">{children}</div>,
  SimpleForm: ({ children, onSubmit }) => (
    <form onSubmit={(e) => {
      e.preventDefault();
      onSubmit({});
    }}>
      {children}
    </form>
  ),
  useNotify: () => jest.fn(),
  useRedirect: () => jest.fn(),
  SaveButton: ({ onClick, children }) => (
    <button onClick={onClick}>{children}</button>
  ),
  Toolbar: ({ children }) => <div>{children}</div>
}));

// Mock fetch
global.fetch = jest.fn();

describe('UserBulkImport Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders upload area correctly', () => {
    render(
      <TestContext>
        <UserBulkImport />
      </TestContext>
    );
    
    expect(screen.getByText('拖拽文件到这里或点击选择文件')).toBeInTheDocument();
    expect(screen.getByText('支持 CSV 和 Excel 格式 (.csv, .xlsx, .xls)')).toBeInTheDocument();
  });

  test('handles file selection', () => {
    render(
      <TestContext>
        <UserBulkImport />
      </TestContext>
    );
    
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByTestId('file-input') || document.querySelector('input[type="file"]');
    
    fireEvent.change(input, { target: { files: [file] } });
    
    expect(screen.getByText('test.csv')).toBeInTheDocument();
  });

  test('validates file type', async () => {
    const mockNotify = jest.fn();
    jest.mock('react-admin', () => ({
      ...jest.requireActual('react-admin'),
      useNotify: () => mockNotify
    }));
    
    render(
      <TestContext>
        <UserBulkImport />
      </TestContext>
    );
    
    const invalidFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByTestId('file-input') || document.querySelector('input[type="file"]');
    
    fireEvent.change(input, { target: { files: [invalidFile] } });
    
    await waitFor(() => {
      expect(mockNotify).toHaveBeenCalledWith('请选择有效的CSV或Excel文件', { type: 'error' });
    });
  });

  test('validates file size', async () => {
    const mockNotify = jest.fn();
    jest.mock('react-admin', () => ({
      ...jest.requireActual('react-admin'),
      useNotify: () => mockNotify
    }));
    
    render(
      <TestContext>
        <UserBulkImport />
      </TestContext>
    );
    
    // 创建一个大于10MB的文件
    const largeFile = new File([new ArrayBuffer(11 * 1024 * 1024)], 'large.csv', { type: 'text/csv' });
    const input = screen.getByTestId('file-input') || document.querySelector('input[type="file"]');
    
    fireEvent.change(input, { target: { files: [largeFile] } });
    
    await waitFor(() => {
      expect(mockNotify).toHaveBeenCalledWith('文件大小不能超过10MB', { type: 'error' });
    });
  });

  test('shows import configuration when file is selected', () => {
    render(
      <TestContext>
        <UserBulkImport />
      </TestContext>
    );
    
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByTestId('file-input') || document.querySelector('input[type="file"]');
    
    fireEvent.change(input, { target: { files: [file] } });
    
    expect(screen.getByText('导入配置')).toBeInTheDocument();
    expect(screen.getByText('冲突处理策略')).toBeInTheDocument();
    expect(screen.getByText('自动生成随机密码')).toBeInTheDocument();
  });

  test('handles successful import', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success_count: 2,
        failed_count: 0,
        conflicts_count: 0,
        errors: [],
        conflicts: {},
        imported_users: [
          { id: 1, username: 'user1', email: 'user1@example.com', role: 'user' },
          { id: 2, username: 'user2', email: 'user2@example.com', role: 'admin' }
        ]
      })
    });
    
    render(
      <TestContext>
        <UserBulkImport />
      </TestContext>
    );
    
    // 选择文件
    const file = new File(['username,email,role\nuser1,user1@example.com,user'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByTestId('file-input') || document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });
    
    // 点击导入按钮
    const importButton = screen.getByText('开始导入');
    fireEvent.click(importButton);
    
    await waitFor(() => {
      expect(screen.getByText('导入结果')).toBeInTheDocument();
      expect(screen.getByText('2 成功')).toBeInTheDocument();
    });
  });

  test('handles import with conflicts', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success_count: 1,
        failed_count: 0,
        conflicts_count: 1,
        errors: [],
        conflicts: {
          email_conflicts: [{ row: 2, email: 'existing@example.com', existing: true }]
        },
        imported_users: [
          { id: 1, username: 'newuser', email: 'new@example.com', role: 'user' }
        ]
      })
    });
    
    render(
      <TestContext>
        <UserBulkImport />
      </TestContext>
    );
    
    // 选择文件
    const file = new File(['username,email,role\nnewuser,new@example.com,user'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByTestId('file-input') || document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });
    
    // 点击导入按钮
    const importButton = screen.getByText('开始导入');
    fireEvent.click(importButton);
    
    await waitFor(() => {
      expect(screen.getByText('冲突详情:')).toBeInTheDocument();
      expect(screen.getByText('邮箱冲突:')).toBeInTheDocument();
    });
  });

  test('handles import error', async () => {
    global.fetch.mockRejectedValueOnce(new Error('Network error'));
    
    const mockNotify = jest.fn();
    jest.mock('react-admin', () => ({
      ...jest.requireActual('react-admin'),
      useNotify: () => mockNotify
    }));
    
    render(
      <TestContext>
        <UserBulkImport />
      </TestContext>
    );
    
    // 选择文件
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByTestId('file-input') || document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });
    
    // 点击导入按钮
    const importButton = screen.getByText('开始导入');
    fireEvent.click(importButton);
    
    await waitFor(() => {
      expect(mockNotify).toHaveBeenCalledWith('导入失败: Network error', { type: 'error' });
    });
  });

  test('shows progress during import', async () => {
    global.fetch.mockImplementationOnce(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: async () => ({ success_count: 1, failed_count: 0, conflicts_count: 0 })
        }), 100)
      )
    );
    
    render(
      <TestContext>
        <UserBulkImport />
      </TestContext>
    );
    
    // 选择文件
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByTestId('file-input') || document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });
    
    // 点击导入按钮
    const importButton = screen.getByText('开始导入');
    fireEvent.click(importButton);
    
    // 应该显示进度条
    await waitFor(() => {
      expect(screen.getByText(/正在导入/)).toBeInTheDocument();
    });
  });

  test('provides field mapping information', () => {
    render(
      <TestContext>
        <UserBulkImport />
      </TestContext>
    );
    
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByTestId('file-input') || document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });
    
    const helpButton = screen.getByText('字段映射说明');
    fireEvent.click(helpButton);
    
    expect(screen.getByText('用户名: username, Username, 用户名')).toBeInTheDocument();
    expect(screen.getByText('邮箱: email, Email, 邮箱')).toBeInTheDocument();
    expect(screen.getByText('角色: role, Role, 角色 (可选，默认为 user)')).toBeInTheDocument();
  });
});

describe('Conflict Resolution Options', () => {
  test('shows all conflict resolution options', () => {
    render(
      <TestContext>
        <UserBulkImport />
      </TestContext>
    );
    
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByTestId('file-input') || document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });
    
    expect(screen.getByText('跳过重复项')).toBeInTheDocument();
    expect(screen.getByText('更新现有用户')).toBeInTheDocument();
    expect(screen.getByText('完全覆盖')).toBeInTheDocument();
    expect(screen.getByText('发现冲突时停止')).toBeInTheDocument();
  });
});