/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unsafe-return */
/* eslint-disable @typescript-eslint/no-unsafe-call */
/* eslint-disable @typescript-eslint/unbound-method */
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { lastValueFrom } from 'rxjs';

import {
  CreativeIdeaResponse,
  GeneratedImage,
  IdeaCategory,
  IdeaScores,
  PromptTemplateResponse,
} from '../../shared/models/creative-idea.interface';
import { CreativityService } from '../../shared/services/creativity.service';
import { ElectronService } from '../core/services/electron.service';
import { safeJsonParse, safeJsonParseArray } from '../../shared/utils/type-safe-json.utils';

@Component({
  selector: 'app-creativity-engine',
  standalone: false,
  templateUrl: './creativity-engine.component.html',
  styleUrls: ['./creativity-engine.component.scss'],
})
export class CreativityEngineComponent implements OnInit {
  // 表单相关
  ideaForm: FormGroup;
  isGenerating = false;
  isScoring = false;
  isGeneratingImage = false;

  // 数据存储
  generatedIdeas: CreativeIdeaResponse[] = [];
  templates: PromptTemplateResponse[] = [];
  selectedTemplate: PromptTemplateResponse | null = null;
  currentIdea: CreativeIdeaResponse | null = null;

  // 评分相关
  scoreResults: IdeaScores | null = null;
  showScoreDetails = false;

  // 图像生成相关
  generatedImages: string[] = [];
  imageStyles: Array<{ value: string; label: string }> = [
    { value: 'realistic', label: '写实风格' },
    { value: 'artistic', label: '艺术风格' },
    { value: 'cartoon', label: '卡通风格' },
    { value: 'photographic', label: '摄影风格' },
  ];

  // 分类选项
  categories: Array<{ value: string; label: string }> = [
    { value: 'technology', label: '科技' },
    { value: 'business', label: '商业' },
    { value: 'design', label: '设计' },
    { value: 'education', label: '教育' },
    { value: 'healthcare', label: '医疗' },
    { value: 'environment', label: '环保' },
    { value: 'entertainment', label: '娱乐' },
  ];

  constructor(
    private fb: FormBuilder,
    private creativityService: CreativityService,
    private snackBar: MatSnackBar,
    private electronService: ElectronService,
  ) {
    /* eslint-disable @typescript-eslint/unbound-method */
    this.ideaForm = this.fb.group({
      title: ['', [Validators.required, Validators.minLength(3)]],
      description: ['', [Validators.maxLength(500)]],
      category: ['technology'],
      templateId: [null],
      customPrompt: [''],
      temperature: [0.8],
      maxTokens: [1500],
      generateImage: [false],
      imagePrompt: [''],
      imageStyle: ['realistic'],
      imageCount: [1],
    });
    /* eslint-enable @typescript-eslint/unbound-method */
  }

  ngOnInit(): void {
    void this.loadTemplates();
    void this.loadUserIdeas();
  }

  // 加载 Prompt 模板
  async loadTemplates(): Promise<void> {
    try {
      const templates$ = this.creativityService.getTemplates();
      const templatesData = await lastValueFrom(templates$);
      // 将服务返回的类型转换为组件需要的类型
      this.templates = templatesData.map(
        (t) =>
          ({
            ...t,
            template: t.content ?? '',
            is_public: t.isPopular ?? false,
            usage_count: t.usageCount ?? 0,
            creator_id: 0,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }) as unknown as PromptTemplateResponse
      );
    } catch (error) {
      this.snackBar.open('加载模板失败', '关闭', { duration: 3000 });
    }
  }

  // 加载用户创意想法
  async loadUserIdeas(): Promise<void> {
    try {
      const ideas$ = this.creativityService.getUserIdeas();
      const ideasData = await lastValueFrom(ideas$);
      // 将服务返回的类型转换为组件需要的类型
      this.generatedIdeas = ideasData.map(
        (idea) =>
          ({
            ...idea,
            user_id: idea.userId ?? 0,
            likes_count: 0,
            views_count: 0,
            status: 'published' as const,
            created_at: idea.createdAt ?? new Date().toISOString(),
            updated_at: idea.updatedAt ?? new Date().toISOString(),
          }) as unknown as CreativeIdeaResponse
      );
    } catch (error) {
      this.snackBar.open('加载创意想法失败', '关闭', { duration: 3000 });
    }
  }

  // 模板选择变化
  onTemplateChange(templateId: number): void {
    const foundTemplate = this.templates.find((t) => t.id === templateId);
    this.selectedTemplate = foundTemplate ?? null;
    if (this.selectedTemplate) {
      this.ideaForm.patchValue({
        category: this.selectedTemplate.category,
      });
    }
  }

  // 构建创意生成请求
  private _buildIdeaRequest(formValue: {
    templateId: unknown;
    customPrompt: unknown;
    category: unknown;
    temperature: unknown;
    maxTokens: unknown;
  }): {
    prompt_template_id: number | null;
    custom_prompt: string;
    category: string;
    temperature: number;
    max_tokens: number;
  } {
    const templateId = formValue.templateId;
    return {
      prompt_template_id: (templateId as number) ?? null,
      custom_prompt: String(formValue.customPrompt ?? ''),
      category: String(formValue.category ?? 'technology'),
      temperature: Number(formValue.temperature ?? 0.8),
      max_tokens: Number(formValue.maxTokens ?? 1500),
    };
  }

  // 转换 API 响应为组件需要的格式
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private _convertIdeaResponse(result: any): CreativeIdeaResponse {
    return {
      ...result,
      id: result.id ?? 0,
      user_id: result.userId ?? 0,
      likes_count: 0,
      views_count: 0,
      status: 'published' as const,
      created_at: result.createdAt ?? new Date().toISOString(),
      updated_at: result.updatedAt ?? new Date().toISOString(),
      category: result.category as IdeaCategory,
    };
  }

  // 重置表单为默认状态
  private _resetIdeaForm(): void {
    this.ideaForm.reset({
      category: 'technology',
      temperature: 0.8,
      maxTokens: 1500,
      generateImage: false,
      imageCount: 1,
    });
  }

  // 生成创意想法
  async generateIdea(): Promise<void> {
    if (this.ideaForm.invalid) {
      this.snackBar.open('请填写必要信息', '关闭', { duration: 3000 });
      return;
    }

    this.isGenerating = true;
    try {
      const formValue = {
        templateId: this.ideaForm.get('templateId')?.value,
        customPrompt: this.ideaForm.get('customPrompt')?.value,
        category: this.ideaForm.get('category')?.value,
        temperature: this.ideaForm.get('temperature')?.value,
        maxTokens: this.ideaForm.get('maxTokens')?.value,
        generateImage: this.ideaForm.get('generateImage')?.value,
        imagePrompt: this.ideaForm.get('imagePrompt')?.value,
      };

      const request = this._buildIdeaRequest(formValue);
      const result = await lastValueFrom(this.creativityService.generateIdea(request));
      const convertedResult = this._convertIdeaResponse(result);

      const ideaId = convertedResult.id;

      // 如果需要生成图像
      if (formValue.generateImage && formValue.imagePrompt) {
        await this.generateAccompanyingImage(ideaId, formValue.imagePrompt as string);
      }

      this.currentIdea = convertedResult;
      this.generatedIdeas.unshift(convertedResult);

      this.snackBar.open('创意生成成功!', '关闭', { duration: 3000 });
      this._resetIdeaForm();
    } catch (error) {
      this.snackBar.open('创意生成失败，请重试', '关闭', { duration: 3000 });
    } finally {
      this.isGenerating = false;
    }
  }

  // 生成配套图像
  async generateAccompanyingImage(ideaId: number | string, imagePrompt: string): Promise<void> {
    this.isGeneratingImage = true;
    try {
      const formValue = this.ideaForm.getRawValue();
      const imageRequest = {
        prompt: imagePrompt,
        style: formValue.imageStyle,
        n: formValue.imageCount,
      };

      const imageResult = await lastValueFrom(this.creativityService.generateImage(imageRequest));
      // 处理响应格式 - 使用正确的属性名
      const imagesArray: string[] = [imageResult.imageUrl].filter((url) => url !== '');
      this.generatedImages = imagesArray;

      // 更新创意想法，关联图像 - 使用正确的接口
      // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-argument
      void this.creativityService.updateIdea(Number(ideaId), {
        images: JSON.stringify(
          this.generatedImages.map((url) => ({ url, generated_at: new Date().toISOString() }))
        ),
      } as any);
    } catch (error) {
      console.error('图像生成失败:', error);
      this.snackBar.open('图像生成失败', '关闭', { duration: 3000 });
    } finally {
      this.isGeneratingImage = false;
    }
  }

  // 评分创意想法
  async scoreIdea(ideaContent: string): Promise<void> {
    this.isScoring = true;
    try {
      const scoreRequest = {
        ideaText: ideaContent,
        scoring_criteria: ['creativity', 'feasibility', 'commercial_value'],
      };

      const scoreResponse = await lastValueFrom(this.creativityService.scoreIdea(scoreRequest));
      // 映射评分字段到 IdeaScores 接口
      this.scoreResults = {
        innovation: scoreResponse.score ?? 0,
        practicality: scoreResponse.score ?? 0,
        business_value: scoreResponse.score ?? 0,
        technical_feasibility: scoreResponse.score ?? 0,
        overall_score: scoreResponse.score ?? 0,
        detailed_feedback: scoreResponse.feedback,
      } as IdeaScores;
      this.showScoreDetails = true;

      this.snackBar.open('创意评分完成!', '关闭', { duration: 3000 });
    } catch (error) {
      this.snackBar.open('创意评分失败', '关闭', { duration: 3000 });
    } finally {
      this.isScoring = false;
    }
  }

  // 保存创意想法
  async saveIdea(): Promise<void> {
    if (!this.currentIdea) return;

    try {
      const saveData = {
        title: this.ideaForm.get('title')?.value ?? this.currentIdea.title,
        description: this.ideaForm.get('description')?.value,
        category: this.ideaForm.get('category')?.value,
        is_public: false,
      };

      this.creativityService.createIdea(saveData);
      this.snackBar.open('创意想法保存成功!', '关闭', { duration: 3000 });

      // 重新加载用户创意
      await this.loadUserIdeas();
    } catch (error) {
      this.snackBar.open('保存失败', '关闭', { duration: 3000 });
    }
  }

  // 查看创意详情
  viewIdeaDetails(idea: CreativeIdeaResponse): void {
    this.currentIdea = idea;

    // 使用类型安全的 JSON 解析
    this.scoreResults = safeJsonParse<IdeaScores | null>(idea.scores, null);

    // 解析图像数据并提取 URL
    const parsedImages = safeJsonParseArray<GeneratedImage>(idea.images, []);
    this.generatedImages = parsedImages
      .map((img) => img.url ?? '')
      .filter((url: string) => url !== '');

    this.showScoreDetails = !!this.scoreResults;
  }

  // 删除创意想法
  deleteIdea(ideaId: number): void {
    if (!confirm('确定要删除这个创意想法吗？')) return;

    try {
      void this.creativityService.deleteIdea(ideaId);
      this.generatedIdeas = this.generatedIdeas.filter(
        (idea: CreativeIdeaResponse) => idea.id !== ideaId
      );
      this.snackBar.open('删除成功!', '关闭', { duration: 3000 });

      if (this.currentIdea?.id === ideaId) {
        this.currentIdea = null;
        this.scoreResults = null;
        this.generatedImages = [];
      }
    } catch (error) {
      this.snackBar.open('删除失败', '关闭', { duration: 3000 });
    }
  }

  // 导出创意想法（支持 .imato 格式和 JSON 格式）
  exportIdea(idea: CreativeIdeaResponse): void {
    try {
      const exportData = {
        title: idea.title,
        description: idea.description,
        ai_generated_content: idea.ai_generated_content,
        category: idea.category,
        scores: idea.scores,
        images: idea.images,
        created_at: idea.created_at,
        // .imato 格式特有元数据
        _format: 'imato',
        _version: '1.0',
        _exportedAt: new Date().toISOString(),
      };

      if (this.electronService.isElectron) {
        // 桌面端：使用 Electron 文件保存对话框，保存为 .imato 格式
        this.electronService.showSaveDialog().subscribe((result) => {
          if (result.success && result.filePath) {
            const filePath = result.filePath.endsWith('.imato')
              ? result.filePath
              : result.filePath + '.imato';
            this.electronService.writeFile(
              filePath,
              JSON.stringify(exportData, null, 2),
            ).subscribe((writeResult) => {
              if (writeResult.success) {
                this.snackBar.open('已保存为 .imato 文件', '关闭', { duration: 3000 });
              } else {
                this.snackBar.open('保存失败', '关闭', { duration: 3000 });
              }
            });
          }
        });
      } else {
        // 浏览器端：下载为 JSON 文件
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `创意想法_${idea.title}_${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
        window.URL.revokeObjectURL(url);

        this.snackBar.open('导出成功!', '关闭', { duration: 3000 });
      }
    } catch (error) {
      console.error('导出创意想法失败:', error);
      this.snackBar.open('导出失败', '关闭', { duration: 3000 });
    }
  }

  // 打开本地 .imato 项目文件
  openLocalProject(): void {
    if (!this.electronService.isElectron) {
      this.snackBar.open('此功能仅在桌面端可用', '关闭', { duration: 3000 });
      return;
    }

    this.electronService.showOpenDialog().subscribe((result) => {
      if (result.success && result.content) {
        try {
          const projectData = JSON.parse(result.content);
          if (projectData._format === 'imato') {
            // 加载 .imato 项目文件
            this.snackBar.open(`已加载项目: ${projectData.title}`, '关闭', { duration: 3000 });
          } else {
            this.snackBar.open('不是有效的 .imato 文件', '关闭', { duration: 3000 });
          }
        } catch {
          this.snackBar.open('文件解析失败', '关闭', { duration: 3000 });
        }
      }
    });
  }

  // 获取评分颜色
  getScoreColor(score: number): string {
    if (score >= 8) return 'success';
    if (score >= 6) return 'warning';
    return 'error';
  }

  // 获取评分描述
  getScoreDescription(score: number): string {
    if (score >= 8) return '优秀';
    if (score >= 6) return '良好';
    if (score >= 4) return '一般';
    return '需要改进';
  }

  // 格式化时间为友好显示
  formatTime(dateString: string | undefined): string {
    if (!dateString) return '未知时间';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return '今天';
    } else if (diffDays === 1) {
      return '昨天';
    } else if (diffDays < 7) {
      return `${diffDays}天前`;
    } else {
      return date.toLocaleDateString();
    }
  }

  // 获取分类标签
  getCategoryLabel(category: string | undefined): string {
    if (!category) return '未知';
    const categoryObj = this.categories.find((c) => c.value === category);
    return categoryObj ? categoryObj.label : category;
  }

  getIdeaContent(idea: CreativeIdeaResponse | null): string {
    if (!idea) return '';

    if (typeof idea.ai_generated_content === 'string') {
      return idea.ai_generated_content;
    } else if (typeof idea.description === 'string') {
      return idea.description;
    } else if (idea.ai_generated_content && typeof idea.ai_generated_content === 'object') {
      return JSON.stringify(idea.ai_generated_content);
    }

    return '';
  }

  // 检查表单有效性
  isFormValid(): boolean {
    return (
      this.ideaForm.valid &&
      (this.ideaForm.get('templateId')?.value || this.ideaForm.get('customPrompt')?.value)
    );
  }
}
