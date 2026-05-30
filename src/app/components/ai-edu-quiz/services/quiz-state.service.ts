import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface QuizQuestion {
  id: number;
  type: 'choice' | 'fill' | 'code' | 'matching';
  content: string;
  options?: string[];
  correct_answer?: string | string[];
  points: number;
  difficulty: number;
}

export interface QuizState {
  quiz_id: number;
  lesson_id: number;
  questions: QuizQuestion[];
  current_question_index: number;
  answers: Map<number, unknown>;
  started_at: string;
  time_limit_minutes?: number;
}

@Injectable({
  providedIn: 'root',
})
export class QuizStateService {
  private quizStateSubject = new BehaviorSubject<QuizState | null>(null);
  private userAnswersSubject = new BehaviorSubject<{ [key: number]: string | number | string[] }>(
    {}
  );

  quizState$: Observable<QuizState | null> = this.quizStateSubject.asObservable();
  userAnswers$: Observable<{ [key: number]: string | number | string[] }> =
    this.userAnswersSubject.asObservable();

  get currentQuizState(): QuizState | null {
    return this.quizStateSubject.value;
  }

  get currentUserAnswers(): { [key: number]: string | number | string[] } {
    return this.userAnswersSubject.value;
  }

  setQuizState(state: QuizState): void {
    this.quizStateSubject.next(state);
  }

  setUserAnswer(questionId: number, answer: string | number | string[]): void {
    const currentAnswers = { ...this.userAnswersSubject.value };
    currentAnswers[questionId] = answer;
    this.userAnswersSubject.next(currentAnswers);
  }

  getUserAnswer(questionId: number): string | number | string[] | undefined {
    return this.userAnswersSubject.value[questionId];
  }

  hasAnswered(questionId: number): boolean {
    return this.userAnswersSubject.value[questionId] !== undefined;
  }

  nextQuestion(): void {
    const state = this.quizStateSubject.value;
    if (state && state.current_question_index < state.questions.length - 1) {
      state.current_question_index++;
      this.quizStateSubject.next({ ...state });
    }
  }

  previousQuestion(): void {
    const state = this.quizStateSubject.value;
    if (state && state.current_question_index > 0) {
      state.current_question_index--;
      this.quizStateSubject.next({ ...state });
    }
  }

  goToQuestion(index: number): void {
    const state = this.quizStateSubject.value;
    if (state && index >= 0 && index < state.questions.length) {
      state.current_question_index = index;
      this.quizStateSubject.next({ ...state });
    }
  }

  reset(): void {
    this.quizStateSubject.next(null);
    this.userAnswersSubject.next({});
  }
}
