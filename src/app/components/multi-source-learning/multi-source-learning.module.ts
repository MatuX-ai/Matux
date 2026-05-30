/**
 * 多来源学习管理模块
 * 导出组织选择器、学习来源管理组件
 */

import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { LearningSourceManagerComponent } from './learning-source-manager/learning-source-manager.component';
import { OrganizationSelectorComponent } from './organization-selector/organization-selector.component';

@NgModule({
  declarations: [OrganizationSelectorComponent, LearningSourceManagerComponent],
  imports: [CommonModule, FormsModule],
  exports: [OrganizationSelectorComponent, LearningSourceManagerComponent],
})
export class MultiSourceLearningModule {}
