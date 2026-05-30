import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MonacoEditorModule } from 'ngx-monaco-editor-v2';

export interface QuizQuestion {
  id: number;
  type: 'choice' | 'fill' | 'code' | 'matching';
  content: string;
  options?: string[];
  correct_answer?: string | string[];
  points: number;
  difficulty: number;
}

@Component({
  selector: 'app-quiz-question-display',
  standalone: true,
  templateUrl: './quiz-question-display.component.html',
  styleUrls: ['./quiz-question-display.component.scss'],
  imports: [CommonModule, FormsModule, MonacoEditorModule],
  schemas: [NO_ERRORS_SCHEMA],
})
export class QuizQuestionDisplayComponent {
  @Input() question!: QuizQuestion;
  @Input() userAnswer: string | number | string[] | undefined;
  @Input() submitted = false;
  @Input() showCorrectAnswer = false;
  @Input() showWrongAnswer = false;

  @Output() answerChanged = new EventEmitter<string | number | string[]>();
  @Output() codeRun = new EventEmitter<void>();

  editorOptions = {
    theme: 'vs-dark',
    language: 'python',
    minimap: { enabled: false },
    fontSize: 14,
    lineNumbers: 'on',
    automaticLayout: true,
  };

  getQuestionTypeLabel(type: string): string {
    const labels: { [key: string]: string } = {
      choice: '选择题',
      fill: '填空题',
      code: '编程题',
      matching: '匹配题',
    };
    return labels[type] || type;
  }

  getOptionLabel(index: number): string {
    return String.fromCharCode(65 + index);
  }

  isCorrectChoice(optionIndex: number): boolean {
    if (!this.question.correct_answer) return false;

    if (Array.isArray(this.question.correct_answer)) {
      return this.question.correct_answer.includes(optionIndex.toString());
    }
    return Number(this.question.correct_answer) === optionIndex;
  }

  selectChoice(optionIndex: number): void {
    if (this.submitted) return;
    this.answerChanged.emit(optionIndex);
  }

  onFillAnswerChanged(value: string): void {
    if (this.submitted) return;
    this.answerChanged.emit(value);
  }

  onCodeChanged(value: string): void {
    if (this.submitted) return;
    this.answerChanged.emit(value);
  }

  runCode(): void {
    this.codeRun.emit();
  }
}
