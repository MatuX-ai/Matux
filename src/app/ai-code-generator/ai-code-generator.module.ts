import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { CodeGenerationFormComponent } from './components/code-generation-form/code-generation-form.component';
import { CodeOutputDisplayComponent } from './components/code-output-display/code-output-display.component';
import { GenerationHistoryComponent } from './components/generation-history/generation-history.component';
import { AICodeGeneratorComponent } from './ai-code-generator.component';

@NgModule({
  declarations: [
    AICodeGeneratorComponent,
    CodeGenerationFormComponent,
    CodeOutputDisplayComponent,
    GenerationHistoryComponent,
  ],
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  exports: [AICodeGeneratorComponent],
})
export class AICodeGeneratorModule {}
