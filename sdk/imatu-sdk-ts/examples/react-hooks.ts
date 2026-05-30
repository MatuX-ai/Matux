// React Hook示例 - 展示如何在React项目中使用SDK
import { useState, useEffect, useCallback } from 'react';
import { createSDK, SDKInstance, User, Course } from '@imatuproject/sdk';

// 创建全局SDK实例
const sdk: SDKInstance = createSDK({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  onUnauthorized: () => {
    console.warn('用户未授权，请重新登录');
    // 可以在这里处理登出逻辑
  }
});

// 自定义Hook用于用户认证
export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (username: string, password: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await sdk.auth.login({ username, password });
      if (response.success && response.data) {
        setUser(response.data.user);
        sdk.setAccessToken(response.data.access_token);
        return { success: true, user: response.data.user };
      } else {
        throw new Error(response.error?.message || '登录失败');
      }
    } catch (err: any) {
      const errorMessage = err.message || '登录过程中发生错误';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await sdk.auth.logout();
    } finally {
      setUser(null);
      sdk.clearAccessToken();
    }
  }, []);

  const getCurrentUser = useCallback(async () => {
    try {
      const response = await sdk.users.getCurrentUser();
      if (response.success && response.data) {
        setUser(response.data);
        return response.data;
      }
    } catch (err) {
      console.error('获取当前用户失败:', err);
    }
    return null;
  }, []);

  return {
    user,
    loading,
    error,
    login,
    logout,
    getCurrentUser
  };
}

// 自定义Hook用于课程管理
export function useCourses() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCourses = useCallback(async (page: number = 1, limit: number = 20) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await sdk.courses.getCourses({ page, limit });
      if (response.success && response.data) {
        setCourses(response.data.data);
        return { courses: response.data.data, total: response.data.total };
      } else {
        throw new Error(response.error?.message || '获取课程失败');
      }
    } catch (err: any) {
      const errorMessage = err.message || '获取课程过程中发生错误';
      setError(errorMessage);
      return { courses: [], total: 0, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, []);

  const searchCourses = useCallback(async (query: string, page: number = 1) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await sdk.courses.searchCourses(query, { page, limit: 20 });
      if (response.success && response.data) {
        setCourses(response.data.data);
        return { courses: response.data.data, total: response.data.total };
      } else {
        throw new Error(response.error?.message || '搜索课程失败');
      }
    } catch (err: any) {
      const errorMessage = err.message || '搜索课程过程中发生错误';
      setError(errorMessage);
      return { courses: [], total: 0, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    courses,
    loading,
    error,
    fetchCourses,
    searchCourses
  };
}

// 自定义Hook用于AI功能
export function useAI() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateCode = useCallback(async (prompt: string, language: string = 'typescript') => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await sdk.ai.generateCode({
        prompt,
        language,
        model: 'gpt-4',
        temperature: 0.7
      });
      
      if (response.success && response.data) {
        return { success: true, code: response.data.code, explanation: response.data.explanation };
      } else {
        throw new Error(response.error?.message || '代码生成失败');
      }
    } catch (err: any) {
      const errorMessage = err.message || '代码生成过程中发生错误';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    generateCode
  };
}

// 工具函数
export function setAuthToken(token: string) {
  sdk.setAccessToken(token);
}

export function clearAuthToken() {
  sdk.clearAccessToken();
}