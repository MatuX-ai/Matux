import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';

import { AngularAIService } from '../../ai-sdk/angular-wrapper';
import { CodeGenerationResponse, ModelProvider, ProgrammingLanguage } from '../../ai-sdk/types';

/* eslint-disable @typescript-eslint/unbound-method */

@Component({
  selector: 'app-ai-code-generator',
  standalone: false,
  templateUrl: './ai-code-generator.component.html',
  styleUrls: ['./ai-code-generator.component.scss'],
})
export class AICodeGeneratorComponent implements OnInit {
  @ViewChild('codeOutput') codeOutput!: ElementRef;

  // 表单组
  generationForm: FormGroup;

  // 选项数据
  providers = Object.values(ModelProvider);
  languages = Object.values(ProgrammingLanguage);

  // 组件状态
  isGenerating = false;
  generatedCode: string = '';
  generationHistory: CodeGenerationResponse[] = [];
  errorMessage: string = '';
  successMessage: string = '';

  // 预设模板
  templates = [
    { name: 'React组件', value: 'reactComponent' },
    { name: 'API服务', value: 'apiService' },
    { name: '数据模型', value: 'dataModel' },
    { name: '工具函数', value: 'utilityFunction' },
    { name: '单元测试', value: 'unitTest' },
  ];

  selectedTemplate: string = '';
  templateArgs: Array<string | string[]> = [];

  constructor(
    private fb: FormBuilder,
    private aiService: AngularAIService
  ) {
    // 初始化表单
    this.generationForm = this.fb.group({
      prompt: ['', [Validators.required, Validators.minLength(5)]],
      provider: [ModelProvider.OPENAI, Validators.required],
      language: [ProgrammingLanguage.PYTHON],
      temperature: [0.7, [Validators.min(0), Validators.max(1)]],
      maxTokens: [2000, [Validators.min(100), Validators.max(8000)]],
      systemPrompt: [''],
    });
  }

  ngOnInit(): void {
    // 从本地存储恢复历史记录
    this.loadHistory();

    // 设置访问令牌（实际项目中应该从认证服务获取）
    this.aiService.setAccessToken('your-access-token-here');
  }

  /**
   * 生成代码
   */
  async generateCode(): Promise<void> {
    if (this.generationForm.invalid || this.isGenerating) {
      return;
    }

    this.isGenerating = true;
    this.errorMessage = '';
    this.successMessage = '';
    this.generatedCode = '';

    try {
      const response = await this.executeCodeGeneration();
      this.handleGenerationSuccess(response);
    } catch (error) {
      this.errorMessage = (error as Error).message || '代码生成失败，请稍后重试';
    } finally {
      this.isGenerating = false;
    }
  }

  /**
   * 执行代码生成逻辑
   */
  private async executeCodeGeneration(): Promise<CodeGenerationResponse> {
    const formData = this.generationForm.value as {
      prompt: string;
      provider: ModelProvider;
      language: ProgrammingLanguage;
      temperature: number;
      maxTokens: number;
      systemPrompt?: string;
    };

    if (this.selectedTemplate && this.templateArgs.length > 0) {
      // 使用模板生成
      return await this.aiService.generateWithTemplate(
        this.selectedTemplate as
          | 'reactComponent'
          | 'apiService'
          | 'dataModel'
          | 'utilityFunction'
          | 'unitTest',
        ...this.templateArgs
      );
    } else {
      // 使用自定义提示生成
      return await this.aiService.generateCode({
        prompt: formData.prompt,
        provider: formData.provider,
        language: formData.language,
        temperature: formData.temperature,
        maxTokens: formData.maxTokens,
        systemPrompt: formData.systemPrompt,
      });
    }
  }

  /**
   * 处理生成成功
   */
  private handleGenerationSuccess(response: CodeGenerationResponse): void {
    this.generatedCode = response.code;
    this.generationHistory.unshift(response);

    // 限制历史记录数量
    if (this.generationHistory.length > 20) {
      this.generationHistory = this.generationHistory.slice(0, 20);
    }

    // 保存到本地存储
    this.saveHistory();

    this.successMessage = `代码生成成功！使用了 ${response.provider} 的 ${response.model} 模型，耗时 ${response.processingTime.toFixed(2)} 秒`;

    // 滚动到代码输出区域
    setTimeout(() => {
      (this.codeOutput.nativeElement as HTMLElement).scrollIntoView({ behavior: 'smooth' });
    }, 100);
  }

  /**
   * 使用预设模板
   */
  useTemplate(): void {
    this.selectedTemplate = '';
    this.templateArgs = [];
    this.generationForm.reset({
      provider: ModelProvider.OPENAI,
      language: ProgrammingLanguage.PYTHON,
      temperature: 0.7,
      maxTokens: 2000,
    });
  }

  /**
   * 应用模板
   */
  applyTemplate(template: string): void {
    this.selectedTemplate = template;
    this.templateArgs = [];

    switch (template) {
      case 'reactComponent':
        this.templateArgs = ['MyComponent', '{ prop1: string; prop2: number }'];
        break;
      case 'apiService':
        this.templateArgs = ['UserService', ['getUser', 'createUser', 'updateUser']];
        break;
      case 'dataModel':
        this.templateArgs = ['User', ['id', 'name', 'email']];
        break;
      case 'utilityFunction':
        this.templateArgs = ['formatDate', '格式化日期字符串'];
        break;
      case 'unitTest':
        this.templateArgs = ['calculateSum', ['positive numbers', 'negative numbers']];
        break;
    }
  }

  /**
   * 复制代码到剪贴板
   */
  copyCode(): void {
    if (!this.generatedCode) return;

    navigator.clipboard
      .writeText(this.generatedCode)
      .then(() => {
        this.successMessage = '代码已复制到剪贴板';
        setTimeout(() => (this.successMessage = ''), 3000);
      })
      .catch((_err) => {
        this.errorMessage = '复制到剪贴板失败';
      });
  }

  /**
   * 下载代码文件
   */
  downloadCode(): void {
    if (!this.generatedCode) return;

    const language =
      (this.generationForm.get('language')?.value as ProgrammingLanguage) ||
      ProgrammingLanguage.PYTHON;
    const extension = this.getFileExtension(language);
    const filename = `generated_code_${new Date().getTime()}.${extension}`;

    const blob = new Blob([this.generatedCode], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();

    window.URL.revokeObjectURL(url);
    this.successMessage = `代码已下载为 ${filename}`;
    setTimeout(() => (this.successMessage = ''), 3000);
  }

  /**
   * 获取文件扩展名
   */
  private getFileExtension(language: ProgrammingLanguage): string {
    const extensions: Record<ProgrammingLanguage, string> = {
      [ProgrammingLanguage.PYTHON]: 'py',
      [ProgrammingLanguage.JAVASCRIPT]: 'js',
      [ProgrammingLanguage.TYPESCRIPT]: 'ts',
      [ProgrammingLanguage.JAVA]: 'java',
      [ProgrammingLanguage.CSHARP]: 'cs',
      [ProgrammingLanguage.GO]: 'go',
      [ProgrammingLanguage.RUST]: 'rs',
      [ProgrammingLanguage.CPP]: 'cpp',
      [ProgrammingLanguage.PHP]: 'php',
      [ProgrammingLanguage.RUBY]: 'rb',
    };

    return extensions[language] || 'txt';
  }

  /**
   * 清除生成结果
   */
  clearResult(): void {
    this.generatedCode = '';
    this.errorMessage = '';
    this.successMessage = '';
    this.selectedTemplate = '';
  }

  /**
   * 加载历史记录
   */
  private loadHistory(): void {
    try {
      const saved = localStorage.getItem('ai-code-generation-history');
      if (saved) {
        const parsed = JSON.parse(saved) as unknown;
        if (Array.isArray(parsed)) {
          this.generationHistory = parsed as CodeGenerationResponse[];
        }
      }
    } catch (error) {
      console.error('加载历史记录失败:', error);
    }
  }

  /**
   * 保存历史记录
   */
  private saveHistory(): void {
    try {
      localStorage.setItem('ai-code-generation-history', JSON.stringify(this.generationHistory));
    } catch (error) {
      console.error('保存历史记录失败:', error);
    }
  }

  /**
   * 从历史记录中选择
   */
  selectFromHistory(historyItem: CodeGenerationResponse): void {
    this.generatedCode = historyItem.code;
    this.generationForm.patchValue({
      provider: historyItem.provider,
      language: historyItem.languageDetected ?? ProgrammingLanguage.PYTHON,
    });
  }

  /**
   * 清除历史记录
   */
  clearHistory(): void {
    this.generationHistory = [];
    localStorage.removeItem('ai-code-generation-history');
  }

  /**
   * 获取语言显示名称
   */
  getLanguageDisplayName(language: ProgrammingLanguage): string {
    const names: Record<ProgrammingLanguage, string> = {
      [ProgrammingLanguage.PYTHON]: 'Python',
      [ProgrammingLanguage.JAVASCRIPT]: 'JavaScript',
      [ProgrammingLanguage.TYPESCRIPT]: 'TypeScript',
      [ProgrammingLanguage.JAVA]: 'Java',
      [ProgrammingLanguage.CSHARP]: 'C#',
      [ProgrammingLanguage.GO]: 'Go',
      [ProgrammingLanguage.RUST]: 'Rust',
      [ProgrammingLanguage.CPP]: 'C++',
      [ProgrammingLanguage.PHP]: 'PHP',
      [ProgrammingLanguage.RUBY]: 'Ruby',
    };

    return names[language] || language;
  }

  /**
   * 获取提供商显示名称
   */
  getProviderDisplayName(provider: ModelProvider): string {
    const names: Record<ModelProvider, string> = {
      [ModelProvider.OPENAI]: 'OpenAI',
      [ModelProvider.LINGMA]: 'Lingma',
      [ModelProvider.DEEPSEEK]: 'DeepSeek',
      [ModelProvider.ANTHROPIC]: 'Anthropic',
      [ModelProvider.GOOGLE]: 'Google',
    };

    return names[provider] || provider;
  }
}
