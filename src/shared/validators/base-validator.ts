/**
 * 通用表单验证器基类
 */

export interface ValidationResult {
  isValid: boolean;
  errorMessage?: string;
  errorCode?: string;
}

export abstract class BaseValidator<T = any> {
  protected fieldName: string;

  constructor(fieldName: string = '') {
    this.fieldName = fieldName;
  }

  /**
   * 验证值
   */
  abstract validate(value: T): ValidationResult;

  /**
   * 验证值并抛出异常（如果无效）
   */
  validateOrThrow(value: T): T {
    const result = this.validate(value);
    if (!result.isValid) {
      throw new ValidationError(
        result.errorMessage || '验证失败',
        result.errorCode,
        this.fieldName
      );
    }
    return value;
  }

  /**
   * 组合验证器（AND关系）
   */
  and(other: BaseValidator<T>): BaseValidator<T> {
    return new CompositeValidator.And(this, other);
  }

  /**
   * 或者验证器（OR关系）
   */
  or(other: BaseValidator<T>): BaseValidator<T> {
    return new CompositeValidator.Or(this, other);
  }

  /**
   * 非验证器（NOT关系）
   */
  not(): BaseValidator<T> {
    return new CompositeValidator.Not(this);
  }
}

/**
 * 验证错误类
 */
export class ValidationError extends Error {
  errorCode?: string;
  fieldName?: string;

  constructor(message: string, errorCode?: string, fieldName?: string) {
    super(message);
    this.name = 'ValidationError';
    this.errorCode = errorCode;
    this.fieldName = fieldName;
  }
}

/**
 * 组合验证器
 */
export namespace CompositeValidator {
  export class And<T> extends BaseValidator<T> {
    constructor(
      private validator1: BaseValidator<T>,
      private validator2: BaseValidator<T>
    ) {
      super();
    }

    validate(value: T): ValidationResult {
      const result1 = this.validator1.validate(value);
      if (!result1.isValid) {
        return result1;
      }
      return this.validator2.validate(value);
    }
  }

  export class Or<T> extends BaseValidator<T> {
    constructor(
      private validator1: BaseValidator<T>,
      private validator2: BaseValidator<T>
    ) {
      super();
    }

    validate(value: T): ValidationResult {
      const result1 = this.validator1.validate(value);
      if (result1.isValid) {
        return result1;
      }
      return this.validator2.validate(value);
    }
  }

  export class Not<T> extends BaseValidator<T> {
    constructor(private validator: BaseValidator<T>) {
      super();
    }

    validate(value: T): ValidationResult {
      const result = this.validator.validate(value);
      return {
        isValid: !result.isValid,
        errorMessage: result.isValid ? '验证应该失败' : undefined,
        errorCode: result.isValid ? 'NOT_VALIDATION_FAILED' : undefined,
      };
    }
  }
}

/**
 * 字符串验证器
 */
export class StringValidator extends BaseValidator<string> {
  protected minLength?: number;
  protected maxLength?: number;
  protected patternRegex?: RegExp;
  protected isRequired: boolean = false;
  protected trim: boolean = true;

  constructor(fieldName: string = '字符串') {
    super(fieldName);
  }

  /**
   * 设置必填
   */
  required(): this {
    this.isRequired = true;
    return this;
  }

  /**
   * 设置最小长度
   */
  min(length: number): this {
    this.minLength = length;
    return this;
  }

  /**
   * 设置最大长度
   */
  max(length: number): this {
    this.maxLength = length;
    return this;
  }

  /**
   * 设置正则表达式模式
   */
  pattern(regex: RegExp, errorCode?: string): this {
    this.patternRegex = regex;
    this.patternErrorCode = errorCode;
    return this;
  }

  /**
   * 设置是否去除首尾空格
   */
  trimSpaces(trim: boolean = true): this {
    this.trim = trim;
    return this;
  }

  private patternErrorCode?: string;

  validate(value: string): ValidationResult {
    // 处理空值
    if (value === null || value === undefined) {
      value = '';
    }

    let strValue = String(value);

    // 去除首尾空格
    if (this.trim) {
      strValue = strValue.trim();
    }

    // 必填验证
    if (this.isRequired && strValue.length === 0) {
      return {
        isValid: false,
        errorMessage: `${this.fieldName}不能为空`,
        errorCode: 'REQUIRED',
      };
    }

    // 空值且非必填，验证通过
    if (!this.isRequired && strValue.length === 0) {
      return { isValid: true };
    }

    // 最小长度验证
    if (this.minLength !== undefined && strValue.length < this.minLength) {
      return {
        isValid: false,
        errorMessage: `${this.fieldName}长度不能少于${this.minLength}个字符`,
        errorCode: 'MIN_LENGTH',
      };
    }

    // 最大长度验证
    if (this.maxLength !== undefined && strValue.length > this.maxLength) {
      return {
        isValid: false,
        errorMessage: `${this.fieldName}长度不能超过${this.maxLength}个字符`,
        errorCode: 'MAX_LENGTH',
      };
    }

    // 正则表达式验证
    if (this.patternRegex && !this.patternRegex.test(strValue)) {
      return {
        isValid: false,
        errorMessage: `${this.fieldName}格式不正确`,
        errorCode: this.patternErrorCode || 'PATTERN_MISMATCH',
      };
    }

    return { isValid: true };
  }
}

/**
 * 数字验证器
 */
export class NumberValidator extends BaseValidator<number> {
  protected minValue?: number;
  protected maxValue?: number;
  protected integerOnly: boolean = false;
  protected isRequired: boolean = false;

  constructor(fieldName: string = '数字') {
    super(fieldName);
  }

  /**
   * 设置必填
   */
  required(): this {
    this.isRequired = true;
    return this;
  }

  /**
   * 设置最小值
   */
  min(value: number): this {
    this.minValue = value;
    return this;
  }

  /**
   * 设置最大值
   */
  max(value: number): this {
    this.maxValue = value;
    return this;
  }

  /**
   * 设置只能是整数
   */
  integer(): this {
    this.integerOnly = true;
    return this;
  }

  validate(value: number): ValidationResult {
    // 处理空值
    if (value === null || value === undefined) {
      if (this.isRequired) {
        return {
          isValid: false,
          errorMessage: `${this.fieldName}不能为空`,
          errorCode: 'REQUIRED',
        };
      }
      return { isValid: true };
    }

    const numValue = Number(value);

    // 检查是否为有效数字
    if (isNaN(numValue)) {
      return {
        isValid: false,
        errorMessage: `${this.fieldName}必须是有效数字`,
        errorCode: 'INVALID_NUMBER',
      };
    }

    // 整数验证
    if (this.integerOnly && !Number.isInteger(numValue)) {
      return {
        isValid: false,
        errorMessage: `${this.fieldName}必须是整数`,
        errorCode: 'NOT_INTEGER',
      };
    }

    // 最小值验证
    if (this.minValue !== undefined && numValue < this.minValue) {
      return {
        isValid: false,
        errorMessage: `${this.fieldName}不能小于${this.minValue}`,
        errorCode: 'MIN_VALUE',
      };
    }

    // 最大值验证
    if (this.maxValue !== undefined && numValue > this.maxValue) {
      return {
        isValid: false,
        errorMessage: `${this.fieldName}不能大于${this.maxValue}`,
        errorCode: 'MAX_VALUE',
      };
    }

    return { isValid: true };
  }
}

/**
 * 邮箱验证器
 */
export class EmailValidator extends StringValidator {
  private emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  constructor(fieldName: string = '邮箱') {
    super(fieldName);
    this.pattern(this.emailPattern, 'INVALID_EMAIL');
  }

  override validate(value: string): ValidationResult {
    // 先执行父类验证
    const parentResult = super.validate(value);
    if (!parentResult.isValid) {
      return parentResult;
    }

    // 空值且非必填，验证通过
    const strValue = String(value).trim();
    if (!this.isRequired && strValue.length === 0) {
      return { isValid: true };
    }

    // 邮箱格式验证
    if (!this.emailPattern.test(strValue)) {
      return {
        isValid: false,
        errorMessage: `${this.fieldName}格式不正确`,
        errorCode: 'INVALID_EMAIL',
      };
    }

    return { isValid: true };
  }
}

/**
 * 用户名验证器
 */
export class UsernameValidator extends StringValidator {
  constructor(fieldName: string = '用户名') {
    super(fieldName);
    this.min(3)
      .max(50)
      .pattern(/^[a-zA-Z0-9_\u4e00-\u9fa5]+$/, 'INVALID_USERNAME');
  }

  override validate(value: string): ValidationResult {
    const parentResult = super.validate(value);
    if (!parentResult.isValid) {
      return parentResult;
    }

    const strValue = String(value).trim();
    if (!this.isRequired && strValue.length === 0) {
      return { isValid: true };
    }

    // 额外的用户名规则验证
    if (strValue.length > 0 && !/^[a-zA-Z0-9_\u4e00-\u9fa5]+$/.test(strValue)) {
      return {
        isValid: false,
        errorMessage: `${this.fieldName}只能包含字母、数字、下划线和中文字符`,
        errorCode: 'INVALID_USERNAME',
      };
    }

    return { isValid: true };
  }
}

/**
 * 密码验证器
 */
export class PasswordValidator extends StringValidator {
  protected override minLength: number = 8;
  private requireUppercase: boolean = false;
  private requireLowercase: boolean = false;
  private requireNumbers: boolean = false;
  private requireSpecialChars: boolean = false;

  constructor(fieldName: string = '密码') {
    super(fieldName);
    this.min(this.minLength);
  }

  /**
   * 要求包含大写字母
   */
  uppercase(): this {
    this.requireUppercase = true;
    return this;
  }

  /**
   * 要求包含小写字母
   */
  lowercase(): this {
    this.requireLowercase = true;
    return this;
  }

  /**
   * 要求包含数字
   */
  numbers(): this {
    this.requireNumbers = true;
    return this;
  }

  /**
   * 要求包含特殊字符
   */
  specialChars(): this {
    this.requireSpecialChars = true;
    return this;
  }

  override validate(value: string): ValidationResult {
    const parentResult = super.validate(value);
    if (!parentResult.isValid) {
      return parentResult;
    }

    const strValue = String(value);
    if (!this.isRequired && strValue.length === 0) {
      return { isValid: true };
    }

    const errors: string[] = [];

    // 大写字母验证
    if (this.requireUppercase && !/[A-Z]/.test(strValue)) {
      errors.push('必须包含大写字母');
    }

    // 小写字母验证
    if (this.requireLowercase && !/[a-z]/.test(strValue)) {
      errors.push('必须包含小写字母');
    }

    // 数字验证
    if (this.requireNumbers && !/\d/.test(strValue)) {
      errors.push('必须包含数字');
    }

    // 特殊字符验证
    if (this.requireSpecialChars && !/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(strValue)) {
      errors.push('必须包含特殊字符');
    }

    if (errors.length > 0) {
      return {
        isValid: false,
        errorMessage: `${this.fieldName}${errors.join('，')}`,
        errorCode: 'WEAK_PASSWORD',
      };
    }

    return { isValid: true };
  }
}
