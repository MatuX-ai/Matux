import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTableModule } from '@angular/material/table';

import { OfflineStorageKey, OfflineTaskData } from '../../../core/models/offline.models';
import { OfflineStorageService } from '../../../core/services/offline-storage.service';

@Component({
  selector: 'app-offline-task-list',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatTableModule,
    MatIconModule,
    MatButtonModule,
    MatChipsModule,
    MatProgressBarModule,
  ],
  templateUrl: './offline-task-list.component.html',
  styleUrls: ['./offline-task-list.component.scss'],
})
export class OfflineTaskListComponent implements OnInit {
  /** 任务数据 */
  tasks: OfflineTaskData[] = [];
  /** 表格列定义 */
  displayedColumns: string[] = ['title', 'type', 'priority', 'status', 'dueDate', 'actions'];
  /** 加载状态 */
  isLoading = true;

  constructor(private offlineStorage: OfflineStorageService) {}

  /** 获取待办任务数量 */
  get todoCount(): number {
    return this.tasks.filter((t) => t.status === 'todo').length;
  }

  /** 获取进行中任务数量 */
  get inProgressCount(): number {
    return this.tasks.filter((t) => t.status === 'in-progress').length;
  }

  /** 获取已完成任务数量 */
  get completedCount(): number {
    return this.tasks.filter((t) => t.status === 'completed').length;
  }

  ngOnInit(): void {
    this.loadTasks().catch(console.error);
  }

  /**
   * 加载任务数据
   */
  private async loadTasks(): Promise<void> {
    try {
      this.tasks = await this.offlineStorage.getAllData<OfflineTaskData>(
        OfflineStorageKey.TASK_DATA
      );
    } catch (error) {
      // 创建一些示例数据用于演示
      this.createSampleTasks();
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * 创建示例任务数据
   */
  private createSampleTasks(): void {
    const now = new Date();
    this.tasks = [
      {
        id: 'task-1',
        title: '完成数学第一章练习',
        description: '完成微积分基础概念的相关习题',
        type: 'exercise',
        assigneeId: 'user-1',
        creatorId: 'teacher-1',
        dueDate: new Date(now.getTime() + 2 * 24 * 60 * 60 * 1000), // 2天后
        priority: 'high',
        status: 'todo',
        courseId: 'course-1',
        tags: ['数学', '微积分', '基础'],
        createdAt: now,
        updatedAt: now,
        version: 1,
      },
      {
        id: 'task-2',
        title: '阅读英语语法资料',
        description: '阅读并理解被动语态的使用规则',
        type: 'reading',
        assigneeId: 'user-1',
        creatorId: 'teacher-2',
        dueDate: new Date(now.getTime() + 5 * 24 * 60 * 60 * 1000), // 5天后
        priority: 'medium',
        status: 'in-progress',
        courseId: 'course-2',
        tags: ['英语', '语法', '被动语态'],
        createdAt: new Date(now.getTime() - 1 * 24 * 60 * 60 * 1000),
        updatedAt: new Date(now.getTime() - 1 * 60 * 60 * 1000),
        version: 1,
      },
      {
        id: 'task-3',
        title: '物理实验报告撰写',
        description: '完成牛顿第二定律验证实验的报告',
        type: 'writing',
        assigneeId: 'user-1',
        creatorId: 'teacher-3',
        dueDate: new Date(now.getTime() - 1 * 24 * 60 * 60 * 1000), // 已过期
        priority: 'high',
        status: 'todo',
        courseId: 'course-3',
        tags: ['物理', '实验', '力学'],
        createdAt: new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000),
        updatedAt: new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000),
        version: 1,
      },
    ];
  }

  /**
   * 获取优先级显示文本
   */
  getPriorityText(priority: string): string {
    switch (priority) {
      case 'high':
        return '高';
      case 'medium':
        return '中';
      case 'low':
        return '低';
      default:
        return priority;
    }
  }

  /**
   * 获取优先级颜色
   */
  getPriorityColor(priority: string): string {
    switch (priority) {
      case 'high':
        return 'warn';
      case 'medium':
        return 'accent';
      case 'low':
        return 'primary';
      default:
        return 'primary';
    }
  }

  /**
   * 获取状态显示文本
   */
  getStatusText(status: string): string {
    switch (status) {
      case 'todo':
        return '待办';
      case 'in-progress':
        return '进行中';
      case 'completed':
        return '已完成';
      case 'cancelled':
        return '已取消';
      default:
        return status;
    }
  }

  /**
   * 获取状态颜色
   */
  getStatusColor(status: string): string {
    switch (status) {
      case 'todo':
        return 'primary';
      case 'in-progress':
        return 'accent';
      case 'completed':
        return 'success';
      case 'cancelled':
        return 'warn';
      default:
        return 'primary';
    }
  }

  /**
   * 格式化日期显示
   */
  formatDate(date?: Date): string {
    if (!date) return '无截止日期';

    const now = new Date();
    const diffTime = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return `已过期 ${Math.abs(diffDays)} 天`;
    } else if (diffDays === 0) {
      return '今天到期';
    } else if (diffDays === 1) {
      return '明天到期';
    } else {
      return `${diffDays} 天后到期`;
    }
  }

  /**
   * 检查任务是否紧急
   */
  isTaskUrgent(task: OfflineTaskData): boolean {
    if (!task.dueDate) return false;

    const now = new Date();
    const diffTime = task.dueDate.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    return diffDays <= 1 && task.status !== 'completed';
  }

  /**
   * 开始任务
   */
  startTask(_task: OfflineTaskData): void {
    // 这里可以添加实际的任务开始逻辑
  }

  /**
   * 完成任务
   */
  completeTask(_task: OfflineTaskData): void {
    // 这里可以添加实际的任务完成逻辑
  }

  /**
   * 查看任务详情
   */
  viewTaskDetails(_task: OfflineTaskData): void {
    // 这里可以导航到任务详情页面
  }
}
