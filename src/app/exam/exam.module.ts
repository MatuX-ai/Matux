import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ExamRoutingModule } from './exam-routing.module';
import { ExamListComponent } from './pages/exam-list/exam-list.component';
import { ExamResultComponent } from './pages/exam-result/exam-result.component';
import { ExamTakingComponent } from './pages/exam-taking/exam-taking.component';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ExamRoutingModule,
    ExamListComponent,
    ExamTakingComponent,
    ExamResultComponent,
  ],
  exports: [],
})
export class ExamModule {}
