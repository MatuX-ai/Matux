/**
 * DailyTasksWidgetComponent 冒烟测试
 *
 * 验证每日任务组件基本功能：进度计算、任务点击、全完成状态
 */

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

import { DailyTasksWidgetComponent } from './daily-tasks-widget.component';
import type { DailyTask } from '../services/student-dashboard-data.service';

describe('DailyTasksWidgetComponent', () => {
  let component: DailyTasksWidgetComponent;
  let fixture: ComponentFixture<DailyTasksWidgetComponent>;

  const mockTasks: DailyTask[] = [
    {
      id: 't1',
      title: '完成一个课程',
      description: '观看任意一个课程视频',
      icon: 'play_circle',
      rewardExp: 20,
      rarity: 'common',
      completed: true,
      category: 'course',
    },
    {
      id: 't2',
      title: 'AI 对话练习',
      description: '与 AI 助手进行 3 次对话',
      icon: 'smart_toy',
      rewardExp: 30,
      rarity: 'rare',
      completed: false,
      progress: { current: 1, total: 3 },
      category: 'ai',
    },
    {
      id: 't3',
      title: '每日测验',
      description: '完成一次知识测验',
      icon: 'quiz',
      rewardExp: 50,
      rarity: 'epic',
      completed: false,
      category: 'quiz',
    },
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DailyTasksWidgetComponent, NoopAnimationsModule],
    }).compileComponents();

    fixture = TestBed.createComponent(DailyTasksWidgetComponent);
    component = fixture.componentInstance;
    component.tasks = mockTasks;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('completedCount', () => {
    it('should count only completed tasks', () => {
      expect(component.completedCount).toBe(1);
    });

    it('should return 0 when no tasks completed', () => {
      component.tasks = mockTasks.map((t) => ({ ...t, completed: false }));
      expect(component.completedCount).toBe(0);
    });
  });

  describe('progressPercent', () => {
    it('should calculate correct percentage', () => {
      // 1 of 3 = 33%
      expect(component.progressPercent).toBe(33);
    });

    it('should return 0 when tasks array is empty', () => {
      component.tasks = [];
      expect(component.progressPercent).toBe(0);
    });

    it('should return 100 when all completed', () => {
      component.tasks = mockTasks.map((t) => ({ ...t, completed: true }));
      expect(component.progressPercent).toBe(100);
    });
  });

  describe('allCompleted', () => {
    it('should be false when some tasks remain', () => {
      expect(component.allCompleted).toBeFalse();
    });

    it('should be true when all tasks completed', () => {
      component.tasks = mockTasks.map((t) => ({ ...t, completed: true }));
      expect(component.allCompleted).toBeTrue();
    });

    it('should be false when tasks array is empty', () => {
      component.tasks = [];
      expect(component.allCompleted).toBeFalse();
    });
  });

  describe('onTaskClick', () => {
    it('should emit taskCompleted for uncompleted task', () => {
      spyOn(component.taskCompleted, 'emit');
      const task = mockTasks[1]; // uncompleted
      component.onTaskClick(task);
      expect(component.taskCompleted.emit).toHaveBeenCalledWith(task);
    });

    it('should NOT emit for already completed task', () => {
      spyOn(component.taskCompleted, 'emit');
      const task = mockTasks[0]; // completed
      component.onTaskClick(task);
      expect(component.taskCompleted.emit).not.toHaveBeenCalled();
    });
  });

  describe('trackByTaskId', () => {
    it('should return task id', () => {
      expect(component.trackByTaskId(0, mockTasks[0])).toBe('t1');
    });
  });

  describe('template rendering', () => {
    it('should render task items', () => {
      const el: HTMLElement = fixture.nativeElement;
      const items = el.querySelectorAll('.task-item');
      expect(items.length).toBe(3);
    });

    it('should show completed class for completed tasks', () => {
      const el: HTMLElement = fixture.nativeElement;
      const items = el.querySelectorAll('.task-item');
      expect(items[0].classList.contains('completed')).toBeTrue();
    });

    it('should display progress text', () => {
      const el: HTMLElement = fixture.nativeElement;
      const progressText = el.querySelector('.progress-text');
      expect(progressText?.textContent).toContain('1 / 3');
    });

    it('should display all-done banner when all completed', () => {
      // 使用 setInput 触发 OnPush 组件的 input setter + ngOnChanges,
      // 直接赋值 component.tasks 不会驱动视图更新
      fixture.componentRef.setInput(
        'tasks',
        mockTasks.map((t) => ({ ...t, completed: true }))
      );
      fixture.detectChanges();
      const el: HTMLElement = fixture.nativeElement;
      const banner = el.querySelector('.all-done-banner');
      expect(banner).toBeTruthy();
    });
  });
});
