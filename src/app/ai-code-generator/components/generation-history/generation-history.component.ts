import { Component, EventEmitter, Input, Output } from '@angular/core';

import { CodeGenerationResponse, ModelProvider } from '../../../../ai-sdk/types';

@Component({
  selector: 'app-generation-history',
  standalone: false,
  templateUrl: './generation-history.component.html',
  styleUrls: ['./generation-history.component.scss'],
})
export class GenerationHistoryComponent {
  @Input() generationHistory: CodeGenerationResponse[] = [];

  @Output() historyItemSelected = new EventEmitter<CodeGenerationResponse>();
  @Output() historyCleared = new EventEmitter<void>();

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
