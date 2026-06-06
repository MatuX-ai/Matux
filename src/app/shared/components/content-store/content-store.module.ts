import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
// Angular Material Modules
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { RouterModule, Routes } from '@angular/router';

import { StoreContentDetailComponent } from './store-content-detail.component';
import { StoreHomeComponent } from './store-home.component';
import { StoreSearchComponent } from './store-search.component';

const routes: Routes = [
  {
    path: '',
    component: StoreHomeComponent,
  },
  {
    path: 'search',
    component: StoreSearchComponent,
  },
  {
    path: 'content/:id',
    component: StoreContentDetailComponent,
  },
];

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    RouterModule.forChild(routes),
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSnackBarModule,
    MatProgressSpinnerModule,
    MatDialogModule,
    MatChipsModule,
    // Standalone组件
    StoreHomeComponent,
    StoreSearchComponent,
    StoreContentDetailComponent,
  ],
  exports: [RouterModule],
})
export class ContentStoreModule {}
