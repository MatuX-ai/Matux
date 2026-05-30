import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MonacoEditorModule } from 'ngx-monaco-editor-v2';

import { AIEduQuizComponent } from './ai-edu-quiz.component';

@NgModule({
  imports: [CommonModule, FormsModule, MatIconModule, MonacoEditorModule, AIEduQuizComponent],
  exports: [AIEduQuizComponent],
})
export class AIEduQuizModule {}
