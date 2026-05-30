import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

import { QuizQuestion } from '../../services/quiz-state.service';

@Component({
  selector: 'app-question-display',
  templateUrl: './question-display.component.html',
  styleUrls: ['./question-display.component.scss'],
  imports: [CommonModule, FormsModule, MatFormFieldModule, MatInputModule],
})
export class QuestionDisplayComponent {
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

  onFillAnswerChanged(event: Event): void {
    if (this.submitted) return;
    const target = event.target as HTMLInputElement;
    this.answerChanged.emit(target.value);
  }

  onCodeChanged(value: string): void {
    if (this.submitted) return;
    this.answerChanged.emit(value);
  }

  runCode(): void {
    this.codeRun.emit();
  }
}
