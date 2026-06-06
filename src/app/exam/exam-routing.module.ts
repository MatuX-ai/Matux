import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { ExamListComponent } from './pages/exam-list/exam-list.component';
import { ExamResultComponent } from './pages/exam-result/exam-result.component';
import { ExamTakingComponent } from './pages/exam-taking/exam-taking.component';

const routes: Routes = [
  {
    path: '',
    component: ExamListComponent,
    data: { title: '在线测验' },
  },
  {
    path: ':examId/take',
    component: ExamTakingComponent,
    data: { title: '答题中' },
  },
  {
    path: 'attempts/:attemptId/result',
    component: ExamResultComponent,
    data: { title: '测验结果' },
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class ExamRoutingModule {}
