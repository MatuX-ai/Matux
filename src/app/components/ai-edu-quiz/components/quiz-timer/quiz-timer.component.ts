import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-quiz-timer',
  standalone: true,
  templateUrl: './quiz-timer.component.html',
  styleUrls: ['./quiz-timer.component.scss'],
  imports: [CommonModule, MatProgressSpinnerModule],
})
export class QuizTimerComponent implements OnInit, OnDestroy {
  @Input() timeLimitMinutes = 0;
  @Input() autoSubmit = true;

  @Output() timeUpdated = new EventEmitter<number>();
  @Output() timeExpired = new EventEmitter<void>();

  remainingTime = 0;
  private timerInterval?: ReturnType<typeof setInterval>;

  ngOnInit(): void {
    this.startTimer();
  }

  ngOnDestroy(): void {
    this.stopTimer();
  }

  startTimer(): void {
    this.remainingTime = this.timeLimitMinutes > 0 ? this.timeLimitMinutes * 60 : 9999;

    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }

    this.timerInterval = setInterval(() => {
      if (this.remainingTime > 0) {
        this.remainingTime--;
        this.timeUpdated.emit(this.remainingTime);

        if (this.remainingTime <= 0 && this.autoSubmit) {
          this.timeExpired.emit();
          this.stopTimer();
        }
      } else if (this.autoSubmit) {
        this.timeExpired.emit();
        this.stopTimer();
      }
    }, 1000);
  }

  stopTimer(): void {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = undefined;
    }
  }

  formatTime(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }
}
