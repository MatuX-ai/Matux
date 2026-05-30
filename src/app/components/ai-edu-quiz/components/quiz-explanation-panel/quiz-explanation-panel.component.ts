import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

export interface QuestionExplanation {
  question_number: number;
  question_type: string;
  difficulty: number;
  question_content: string;
  options?: string[];
  correct_answer: number | string | string[];
  explanation?: string;
  knowledge_points?: string[];
  tips?: string[];
  general_feedback?: string;
}

@Component({
  selector: 'app-quiz-explanation-panel',
  standalone: true,
  templateUrl: './quiz-explanation-panel.component.html',
  styleUrls: ['./quiz-explanation-panel.component.scss'],
  imports: [CommonModule, MatIconModule],
})
export class QuizExplanationPanelComponent {
  @Input() showExplanationPanel = false;
  @Input() questionExplanations: QuestionExplanation[] = [];
  @Input() quizResult: { score: number; total_score: number; points_earned: number } | null = null;

  @Output() close = new EventEmitter<void>();

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

  formatCorrectAnswer(explanation: {
    question_type: string;
    correct_answer: number | string | string[];
  }): string {
    if (explanation.question_type === 'choice') {
      const answerIndex =
        typeof explanation.correct_answer === 'string'
          ? Number(explanation.correct_answer)
          : (explanation.correct_answer as number);
      return this.getOptionLabel(answerIndex);
    }
    return String(explanation.correct_answer);
  }
}
