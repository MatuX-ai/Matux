/**
 * 多来源学习管理模块
 * 组织选择器组件
 */

import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';

import { MultiSourceLearningService } from '../../../core/services/multi-source-learning.service';
import {
  LearningSource,
  LearningSourceType,
  LearningSourceTypeLabels,
  UserOrganization,
  UserOrganizationRoleLabels,
} from '../../../models/multi-source-learning.models';

@Component({
  selector: 'app-organization-selector',
  standalone: false,
  templateUrl: './organization-selector.component.html',
  styleUrls: ['./organization-selector.component.scss'],
})
export class OrganizationSelectorComponent implements OnInit {
  @Input() userId: number = 0;
  @Input() showCreateButton: boolean = true;
  @Input() allowMultiple: boolean = true;
  @Output() organizationSelected = new EventEmitter<UserOrganization | LearningSource>();
  @Output() createNew = new EventEmitter<void>();

  userOrganizations: UserOrganization[] = [];
  learningSources: LearningSource[] = [];
  selectedOrg: UserOrganization | null = null;
  selectedSource: LearningSource | null = null;

  loading: boolean = false;
  error: string | null = null;

  sourceTypeLabels = LearningSourceTypeLabels;
  roleLabels = UserOrganizationRoleLabels;

  constructor(private multiSourceService: MultiSourceLearningService) {}

  ngOnInit(): void {
    if (this.userId) {
      this.loadUserOrganizations();
      this.loadLearningSources();
    }
  }

  /**
   * 加载用户组织关联
   */
  loadUserOrganizations(): void {
    this.loading = true;
    this.error = null;

    this.multiSourceService.getUserOrganizations(this.userId).subscribe({
      next: (response) => {
        this.userOrganizations = response.items;
        this.loading = false;

        // 选中主组织
        const primary = this.userOrganizations.find((org) => org.is_primary);
        if (primary) {
          this.selectOrganization(primary);
        }
      },
      error: (_err) => {
        this.error = '加载组织列表失败';
        this.loading = false;
      },
    });
  }

  /**
   * 加载学习来源
   */
  loadLearningSources(): void {
    this.multiSourceService.getUserLearningSources(this.userId).subscribe({
      next: (response) => {
        this.learningSources = response.items;
      },
      error: (err) => {
        console.error('加载学习来源失败', err);
      },
    });
  }

  /**
   * 选择组织
   */
  selectOrganization(org: UserOrganization): void {
    this.selectedOrg = org;
    this.selectedSource = null;
    this.organizationSelected.emit(org);
  }

  /**
   * 选择学习来源
   */
  selectLearningSource(source: LearningSource): void {
    this.selectedSource = source;
    this.selectedOrg = null;
    this.organizationSelected.emit(source);
  }

  /**
   * 创建新组织关联
   */
  onCreateNew(): void {
    this.createNew.emit();
  }

  /**
   * 刷新数据
   */
  refresh(): void {
    this.loadUserOrganizations();
    this.loadLearningSources();
  }

  /**
   * 获取类型标签
   */
  getTypeLabel(type: LearningSourceType | null | undefined): string {
    if (!type) return '未知';
    return this.sourceTypeLabels[type] || type;
  }
}
