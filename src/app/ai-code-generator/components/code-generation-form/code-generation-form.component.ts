import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormGroup } from '@angular/forms';

import { ModelProvider, ProgrammingLanguage } from '../../../../ai-sdk/types';

@Component({
  selector: 'app-code-generation-form',
  standalone: false,
  templateUrl: './code-generation-form.component.html',
  styleUrls: ['./code-generation-form.component.scss'],
})
export class CodeGenerationFormComponent {
  @Input() generationForm!: FormGroup;
  @Input() isGenerating = false;
  @Input() templates: { name: string; value: string }[] = [];
  @Input() selectedTemplate = '';
  @Input() templateArgs: any[] = [];
  @Input() providers: ModelProvider[] = [];
  @Input() languages: ProgrammingLanguage[] = [];

  @Output() formSubmit = new EventEmitter<void>();
  @Output() clearResult = new EventEmitter<void>();
  @Output() templateSelected = new EventEmitter<string>();
  @Output() useCustomTemplate = new EventEmitter<void>();

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

  onTemplateChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.templateSelected.emit(target.value);
  }

  getSelectedTemplateName(): string {
    const template = this.templates.find((t) => t.value === this.selectedTemplate);
    return template?.name || '';
  }
}
