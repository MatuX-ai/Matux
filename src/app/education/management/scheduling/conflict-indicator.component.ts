/**
 * 冲突指示器组件 - 显示课表冲突信息
 */

import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';

import { ConflictType, ScheduleConflict } from '../../models/scheduling.models';

@Component({
  selector: 'edu-conflict-indicator',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatChipsModule],
  templateUrl: './conflict-indicator.component.html',
  styleUrls: ['./conflict-indicator.component.scss'],
})
export class ConflictIndicatorComponent {
  @Input() conflicts: ScheduleConflict[] = [];
  @Input() showDetails = true;

  /**
   * 获取冲突类型标签
   */
  getConflictTypeLabel(type: ConflictType): string {
    const labels: Record<ConflictType, string> = {
      teacher_conflict: '教师冲突',
      classroom_conflict: '教室冲突',
      student_conflict: '学生冲突',
      capacity_conflict: '容量冲突',
    };

    return labels[type] || '未知冲突';
  }

  /**
   * 获取冲突类型图标
   */
  getConflictTypeIcon(type: ConflictType): string {
    const icons: Record<ConflictType, string> = {
      teacher_conflict: 'person_off',
      classroom_conflict: 'meeting_room',
      student_conflict: 'people_outline',
      capacity_conflict: 'warning',
    };

    return icons[type] || 'error_outline';
  }

  /**
   * 获取冲突严重性等级
   */
  getSeverityClass(conflict: ScheduleConflict): string {
    switch (conflict.conflictType) {
      case 'teacher_conflict':
        return 'severity-high';
      case 'classroom_conflict':
        return 'severity-high';
      case 'student_conflict':
        return 'severity-medium';
      case 'capacity_conflict':
        return 'severity-low';
      default:
        return 'severity-medium';
    }
  }

  /**
   * 是否有冲突
   */
  get hasConflict(): boolean {
    return this.conflicts && this.conflicts.length > 0;
  }

  /**
   * 获取高亮颜色
   */
  getHighlightColor(conflict: ScheduleConflict): string {
    switch (conflict.conflictType) {
      case 'teacher_conflict':
        return '#f44336'; // 红色
      case 'classroom_conflict':
        return '#ff9800'; // 橙色
      case 'student_conflict':
        return '#ffc107'; // 黄色
      case 'capacity_conflict':
        return '#2196f3'; // 蓝色
      default:
        return '#9e9e9e'; // 灰色
    }
  }

  /**
   * 解决冲突
   */
  resolveConflict(_conflictId: string): void {
    // TODO: 调用 API 解决冲突
  }

  /**
   * 忽略冲突
   */
  ignoreConflict(_conflictId: string): void {
    // TODO: 调用 API 忽略冲突
  }
}
