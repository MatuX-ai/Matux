/**
 * 简化版表单验证器（避免复杂的继承问题）
 */

export interface ValidationResult {
  isValid: boolean;
  errorMessage?: string;
  errorCode?: string;
}

// 基础验证函数
export function validateRequired(value: any, fieldName: string = '字段'): ValidationResult {
  if (value === null || value === undefined || value === '') {
    return {
      isValid: false,
      errorMessage: `${fieldName}不能为空`,
      errorCode: 'REQUIRED',
    };
  }
  return { isValid: true };
}

export function validateStringLength(
  value: string,
  min: number,
  max: number,
  fieldName: string = '字符串'
): ValidationResult {
  const str = String(value);
  if (str.length < min) {
    return {
      isValid: false,
      errorMessage: `${fieldName}长度不能少于${min}个字符`,
      errorCode: 'MIN_LENGTH',
    };
  }
  if (str.length > max) {
    return {
      isValid: false,
      errorMessage: `${fieldName}长度不能超过${max}个字符`,
      errorCode: 'MAX_LENGTH',
    };
  }
  return { isValid: true };
}

export function validateEmail(email: string, fieldName: string = '邮箱'): ValidationResult {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return {
      isValid: false,
      errorMessage: `${fieldName}格式不正确`,
      errorCode: 'INVALID_EMAIL',
    };
  }
  return { isValid: true };
}

export function validateUsername(username: string, fieldName: string = '用户名'): ValidationResult {
  if (username.length < 3 || username.length > 50) {
    return {
      isValid: false,
      errorMessage: `${fieldName}长度必须在3-50个字符之间`,
      errorCode: 'INVALID_USERNAME_LENGTH',
    };
  }

  const usernameRegex = /^[a-zA-Z0-9_\u4e00-\u9fa5]+$/;
  if (!usernameRegex.test(username)) {
    return {
      isValid: false,
      errorMessage: `${fieldName}只能包含字母、数字、下划线和中文字符`,
      errorCode: 'INVALID_USERNAME_FORMAT',
    };
  }

  return { isValid: true };
}

export function validatePassword(password: string, fieldName: string = '密码'): ValidationResult {
  if (password.length < 8) {
    return {
      isValid: false,
      errorMessage: `${fieldName}长度不能少于8个字符`,
      errorCode: 'PASSWORD_TOO_SHORT',
    };
  }

  // 可以添加更多密码复杂度验证
  return { isValid: true };
}

export function validateNumber(
  value: any,
  min?: number,
  max?: number,
  fieldName: string = '数字'
): ValidationResult {
  const num = Number(value);
  if (isNaN(num)) {
    return {
      isValid: false,
      errorMessage: `${fieldName}必须是有效数字`,
      errorCode: 'INVALID_NUMBER',
    };
  }

  if (min !== undefined && num < min) {
    return {
      isValid: false,
      errorMessage: `${fieldName}不能小于${min}`,
      errorCode: 'NUMBER_TOO_SMALL',
    };
  }

  if (max !== undefined && num > max) {
    return {
      isValid: false,
      errorMessage: `${fieldName}不能大于${max}`,
      errorCode: 'NUMBER_TOO_LARGE',
    };
  }

  return { isValid: true };
}

// 验证器工厂
export class SimpleValidatorFactory {
  static required(fieldName: string = '字段') {
    return (value: any) => validateRequired(value, fieldName);
  }

  static email(fieldName: string = '邮箱') {
    return (value: string) => validateEmail(value, fieldName);
  }

  static username(fieldName: string = '用户名') {
    return (value: string) => validateUsername(value, fieldName);
  }

  static password(fieldName: string = '密码') {
    return (value: string) => validatePassword(value, fieldName);
  }

  static stringLength(min: number, max: number, fieldName: string = '字符串') {
    return (value: string) => validateStringLength(value, min, max, fieldName);
  }

  static number(min?: number, max?: number, fieldName: string = '数字') {
    return (value: any) => validateNumber(value, min, max, fieldName);
  }

  // 组合验证器
  static combine(...validators: Array<(value: any) => ValidationResult>) {
    return (value: any): ValidationResult => {
      for (const validator of validators) {
        const result = validator(value);
        if (!result.isValid) {
          return result;
        }
      }
      return { isValid: true };
    };
  }
}

// 表单验证器
export class SimpleFormValidator {
  private rules: Record<string, (value: any) => ValidationResult> = {};

  addRule(field: string, validator: (value: any) => ValidationResult): this {
    this.rules[field] = validator;
    return this;
  }

  validate(data: Record<string, any>): {
    isValid: boolean;
    errors: Record<string, string>;
  } {
    const errors: Record<string, string> = {};

    for (const [field, validator] of Object.entries(this.rules)) {
      if (Object.prototype.hasOwnProperty.call(data, field)) {
        const result = validator(data[field]);
        if (!result.isValid && result.errorMessage) {
          errors[field] = result.errorMessage;
        }
      }
    }

    return {
      isValid: Object.keys(errors).length === 0,
      errors,
    };
  }

  static create() {
    return new SimpleFormValidator();
  }
}

export default {
  validateRequired,
  validateStringLength,
  validateEmail,
  validateUsername,
  validatePassword,
  validateNumber,
  SimpleValidatorFactory,
  SimpleFormValidator,
};
