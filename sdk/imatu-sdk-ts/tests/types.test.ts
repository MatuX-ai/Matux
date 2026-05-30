// 类型定义测试
import {
  SDKConfig,
  APIError,
  BaseResponse,
  User,
  LoginRequest,
  AuthResponse,
  Course,
  CodeGenerationRequest
} from '../src/types';

describe('Type Definitions Tests', () => {
  describe('SDKConfig', () => {
    it('should define required properties', () => {
      const config: SDKConfig = {
        baseURL: 'http://localhost:8000'
      };
      
      expect(config.baseURL).toBe('http://localhost:8000');
    });

    it('should allow optional properties', () => {
      const config: SDKConfig = {
        baseURL: 'http://localhost:8000',
        accessToken: 'test-token',
        timeout: 5000,
        retries: 3,
        retryDelay: 1000
      };
      
      expect(config.accessToken).toBe('test-token');
      expect(config.timeout).toBe(5000);
      expect(config.retries).toBe(3);
      expect(config.retryDelay).toBe(1000);
    });
  });

  describe('APIError', () => {
    it('should define error structure', () => {
      const error: APIError = {
        code: 'TEST_ERROR',
        message: 'Test error message',
        status: 400,
        timestamp: new Date().toISOString()
      };
      
      expect(error.code).toBe('TEST_ERROR');
      expect(error.message).toBe('Test error message');
      expect(error.status).toBe(400);
    });
  });

  describe('BaseResponse', () => {
    it('should handle success response', () => {
      const response: BaseResponse<User> = {
        success: true,
        data: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          role: 'user',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        timestamp: new Date().toISOString()
      };
      
      expect(response.success).toBe(true);
      expect(response.data?.username).toBe('testuser');
    });

    it('should handle error response', () => {
      const response: BaseResponse<null> = {
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Invalid input data'
        },
        timestamp: new Date().toISOString()
      };
      
      expect(response.success).toBe(false);
      expect(response.error?.code).toBe('VALIDATION_ERROR');
    });
  });

  describe('Authentication Types', () => {
    it('should validate LoginRequest', () => {
      const loginRequest: LoginRequest = {
        username: 'testuser',
        password: 'password123'
      };
      
      expect(loginRequest.username).toBe('testuser');
      expect(loginRequest.password).toBe('password123');
    });

    it('should validate AuthResponse', () => {
      const authResponse: AuthResponse = {
        access_token: 'jwt-token-here',
        token_type: 'bearer',
        expires_in: 3600,
        user: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          role: 'user',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      };
      
      expect(authResponse.access_token).toBe('jwt-token-here');
      expect(authResponse.token_type).toBe('bearer');
      expect(authResponse.user.username).toBe('testuser');
    });
  });

  describe('Domain Types', () => {
    it('should validate User', () => {
      const user: User = {
        id: 1,
        username: 'john_doe',
        email: 'john@example.com',
        first_name: 'John',
        last_name: 'Doe',
        role: 'student',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      
      expect(user.id).toBe(1);
      expect(user.username).toBe('john_doe');
      expect(user.email).toBe('john@example.com');
    });

    it('should validate Course', () => {
      const course: Course = {
        id: 1,
        title: 'Introduction to TypeScript',
        description: 'Learn TypeScript fundamentals',
        category: 'programming',
        level: 'beginner',
        duration: 120,
        instructor_id: 1,
        price: 99.99,
        is_published: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      
      expect(course.title).toBe('Introduction to TypeScript');
      expect(course.level).toBe('beginner');
      expect(course.price).toBe(99.99);
    });
  });

  describe('AI Types', () => {
    it('should validate CodeGenerationRequest', () => {
      const request: CodeGenerationRequest = {
        prompt: 'Create a function to calculate fibonacci numbers',
        language: 'typescript',
        model: 'gpt-4',
        temperature: 0.7,
        max_tokens: 1000
      };
      
      expect(request.prompt).toBe('Create a function to calculate fibonacci numbers');
      expect(request.language).toBe('typescript');
      expect(request.temperature).toBe(0.7);
    });
  });
});