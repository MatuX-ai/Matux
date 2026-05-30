import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-quiz-result-panel',
  standalone: true,
  templateUrl: './quiz-result-panel.component.html',
  styleUrls: ['./quiz-result-panel.component.scss'],
  imports: [CommonModule, MatIconModule],
})
export class QuizResultPanelComponent {
  @Input() showResult = false;
  @Input() finalScore = 0;
  @Input() totalPossibleScore = 0;
  @Input() earnedPoints = 0;
  @Input() accuracyRate = 0;
  @Input() timeSpent = '';
  @Input() antiCheatingReport: any = null;

  @Output() reviewAnswers = new EventEmitter<void>();
  @Output() retryQuiz = new EventEmitter<void>();
  @Output() closeResult = new EventEmitter<void>();

  get scorePercentage(): number {
    if (this.totalPossibleScore === 0) return 0;
    return Math.round((this.finalScore / this.totalPossibleScore) * 100);
  }
}
