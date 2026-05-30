/**
 * 多来源学习管理模块
 * 学习来源管理组件
 */

import { Component, Input, OnInit } from '@angular/core';

import { MultiSourceLearningService } from '../../../core/services/multi-source-learning.service';
import {
  LearningSource,
  LearningSourceCreate,
  LearningSourceStats,
  LearningSourceType,
  LearningSourceTypeLabels,
  LearningSourceUpdate,
} from '../../../models/multi-source-learning.models';

@Component({
  selector: 'app-learning-source-manager',
  standalone: false,
  templateUrl: './learning-source-manager.component.html',
  styleUrls: ['./learning-source-manager.component.scss'],
})
export class LearningSourceManagerComponent implements OnInit {
  @Input() userId: number = 0;

  learningSources: LearningSource[] = [];
  stats: LearningSourceStats | null = null;

  // 模态框状态
  showModal: boolean = false;
  modalMode: 'create' | 'edit' = 'create';
  editingSource: LearningSource | null = null;

  // 表单数据
  formData: LearningSourceCreate = this.getEmptyFormData();

  // 状态
  loading: boolean = false;
  saving: boolean = false;
  error: string | null = null;

  // 类型选项
  sourceTypes: LearningSourceType[] = [
    'school_curriculum',
    'school_interest',
    'institution',
    'self_study',
    'online_platform',
    'competition',
  ];
  sourceTypeLabels = LearningSourceTypeLabels;

  constructor(private multiSourceService: MultiSourceLearningService) {}

  ngOnInit(): void {
    if (this.userId) {
      this.loadLearningSources();
      this.loadStats();
    }
  }

  /**
   * 获取空表单数据
   */
  getEmptyFormData(): LearningSourceCreate {
    return {
      user_id: this.userId,
      source_type: 'school_curriculum',
      name: '',
      org_id: 0,
      source_detail: {},
      is_primary: false,
    };
  }

  /**
   * 加载学习来源列表
   */
  loadLearningSources(): void {
    this.loading = true;
    this.error = null;

    this.multiSourceService.getUserLearningSources(this.userId).subscribe({
      next: (response) => {
        this.learningSources = response.items;
        this.loading = false;
      },
      error: (err) => {
        this.error = '加载学习来源失败';
        this.loading = false;
      },
    });
  }

  /**
   * 加载统计信息
   */
  loadStats(): void {
    this.multiSourceService.getUserLearningSourceStats(this.userId).subscribe({
      next: (stats) => {
        this.stats = stats;
      },
      error: (err) => {
        console.error('加载统计失败', err);
      },
    });
  }

  /**
   * 打开创建模态框
   */
  openCreateModal(): void {
    this.modalMode = 'create';
    this.formData = this.getEmptyFormData();
    this.formData.user_id = this.userId;
    this.showModal = true;
  }

  /**
   * 打开编辑模态框
   */
  openEditModal(source: LearningSource): void {
    this.modalMode = 'edit';
    this.editingSource = source;
    this.formData = {
      user_id: source.user_id,
      org_id: source.org_id,
      source_type: source.source_type,
      name: source.name,
      source_detail: source.source_detail,
      start_date: source.start_date ?? undefined,
      end_date: source.end_date ?? undefined,
      role: source.role,
      is_primary: source.is_primary,
      notes: source.notes ?? undefined,
    } as LearningSourceCreate;
    this.showModal = true;
  }

  /**
   * 关闭模态框
   */
  closeModal(): void {
    this.showModal = false;
    this.editingSource = null;
    this.formData = this.getEmptyFormData();
  }

  /**
   * 保存学习来源
   */
  saveSource(): void {
    this.saving = true;

    if (this.modalMode === 'create') {
      this.multiSourceService.createLearningSource(this.formData).subscribe({
        next: (source) => {
          this.learningSources.push(source);
          this.loadStats();
          this.closeModal();
          this.saving = false;
        },
        error: (err) => {
          this.error = '创建失败: ' + (err.message || '未知错误');
          this.saving = false;
        },
      });
    } else if (this.editingSource) {
      const updateData: LearningSourceUpdate = this.formData;
      this.multiSourceService.updateLearningSource(this.editingSource.id, updateData).subscribe({
        next: (source) => {
          const index = this.learningSources.findIndex((s) => s.id === source.id);
          if (index >= 0) {
            this.learningSources[index] = source;
          }
          this.loadStats();
          this.closeModal();
          this.saving = false;
        },
        error: (err) => {
          this.error = '更新失败: ' + (err.message || '未知错误');
          this.saving = false;
        },
      });
    }
  }

  /**
   * 删除学习来源
   */
  deleteSource(source: LearningSource): void {
    if (!confirm(`确定要删除学习来源"${source.name}"吗？`)) {
      return;
    }

    this.multiSourceService.deleteLearningSource(source.id).subscribe({
      next: () => {
        this.learningSources = this.learningSources.filter((s) => s.id !== source.id);
        this.loadStats();
      },
      error: (err) => {
        this.error = '删除失败';
      },
    });
  }

  /**
   * 设置为主来源
   */
  setPrimary(source: LearningSource): void {
    const updateData: LearningSourceUpdate = { is_primary: true };
    this.multiSourceService.updateLearningSource(source.id, updateData).subscribe({
      next: (updated) => {
        // 刷新列表
        this.loadLearningSources();
        this.loadStats();
      },
      error: (err) => {
        this.error = '设置主来源失败';
      },
    });
  }

  /**
   * 获取类型标签
   */
  getTypeLabel(type: LearningSourceType): string {
    return this.sourceTypeLabels[type] || type;
  }

  /**
   * 刷新数据
   */
  refresh(): void {
    this.loadLearningSources();
    this.loadStats();
  }
}
