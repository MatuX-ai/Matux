/**
 * 课表日历组件 - 支持日/周/月视图切换
 */

import { CdkDragDrop, DragDropModule } from '@angular/cdk/drag-drop';
import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { CourseSchedule, ScheduleConflict, ScheduleFilters } from '../../models/scheduling.models';
import { IntelligentSchedulingService } from '../../services/intelligent-scheduling.service';
import { ScheduleService } from '../../services/scheduling.service';

@Component({
  selector: 'edu-schedule-calendar',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatDialogModule,
    DragDropModule,
  ],
  templateUrl: './schedule-calendar.component.html',
  styleUrls: ['./schedule-calendar.component.scss'],
})
export class ScheduleCalendarComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  // 视图相关
  viewMode: 'day' | 'week' | 'month' = 'week';
  currentDate: Date = new Date();
  viewDates: Date[] = []; // 当前视图显示的日期列表

  // 数据
  schedules: CourseSchedule[] = [];
  filteredSchedules: CourseSchedule[] = [];
  loading = false;

  // 筛选表单
  filterForm: FormGroup;
  filterOptions: {
    teachers: Array<{ id: string; name: string }>;
    classrooms: Array<{ id: string; name: string }>;
    classes: Array<{ id: string; name: string }>;
    courseTypes: Array<{ value: string; label: string }>;
  } = {
    teachers: [],
    classrooms: [],
    classes: [],
    courseTypes: [
      { value: 'one_on_one', label: '一对一' },
      { value: 'small_class', label: '小班 (1-6 人)' },
      { value: 'medium_class', label: '中班 (7-20 人)' },
      { value: 'large_class', label: '大班 (21+ 人)' },
    ],
  };

  // 日历网格数据
  calendarGrid: Array<{
    date: Date;
    dayOfWeek: number;
    schedules: CourseSchedule[];
    hours: number[];
  }> = [];

  constructor(
    private fb: FormBuilder,
    private scheduleService: ScheduleService,
    private intelligentSchedulingService: IntelligentSchedulingService,
    private snackBar: MatSnackBar,
    private dialog: MatDialog
  ) {
    this.filterForm = this.fb.group({
      teacherId: [''],
      classroomId: [''],
      classId: [''],
      courseType: [''],
    });
  }

  ngOnInit(): void {
    this.initViewDates();
    this.loadSchedules();
    this.setupFilterListeners();
    this.generateCalendarGrid();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * 初始化视图日期范围
   */
  private initViewDates(): void {
    const startOfWeek = this.getStartOfWeek(this.currentDate);

    switch (this.viewMode) {
      case 'day':
        this.viewDates = [this.currentDate];
        break;

      case 'week':
        this.viewDates = [];
        for (let i = 0; i < 7; i++) {
          const date = new Date(startOfWeek);
          date.setDate(date.getDate() + i);
          this.viewDates.push(date);
        }
        break;

      case 'month':
        this.viewDates = this.getDaysInMonth(this.currentDate);
        break;
    }
  }

  /**
   * 加载课表数据
   */
  loadSchedules(): void {
    this.loading = true;

    // TODO: 从 API 加载数据，暂时使用模拟数据
    setTimeout(() => {
      this.schedules = this.getMockSchedules();
      this.applyFilters();
      this.loading = false;
    }, 500);
  }

  /**
   * 应用筛选条件
   */
  applyFilters(): void {
    const filters = this.filterForm.value as ScheduleFilters;

    this.filteredSchedules = this.schedules.filter((schedule) => {
      if (filters.teacherId && schedule.teacherId !== filters.teacherId) return false;
      if (filters.classroomId && schedule.classroomId !== filters.classroomId) return false;
      if (filters.classId && schedule.classId !== filters.classId) return false;
      if (filters.courseType) return true; // TODO: 需要课程类型字段

      return true;
    });
  }

  /**
   * 设置筛选监听器
   */
  private setupFilterListeners(): void {
    this.filterForm.valueChanges.pipe(takeUntil(this.destroy$)).subscribe(() => {
      this.applyFilters();
    });
  }

  /**
   * 生成日历网格数据
   */
  generateCalendarGrid(): void {
    this.calendarGrid = [];

    const hours: number[] = [];
    for (let i = 8; i <= 21; i++) {
      hours.push(i);
    }

    this.viewDates.forEach((date) => {
      const daySchedules = this.getSchedulesForDate(date);

      this.calendarGrid.push({
        date,
        dayOfWeek: date.getDay(),
        schedules: daySchedules,
        hours,
      });
    });
  }

  /**
   * 获取指定日期的课表
   */
  getSchedulesForDate(date: Date): CourseSchedule[] {
    const dayOfWeek = date.getDay();

    return this.filteredSchedules.filter((schedule) => {
      // 简单匹配星期几，实际应该匹配具体日期范围
      return schedule.dayOfWeek === dayOfWeek;
    });
  }

  /**
   * 切换视图模式
   */
  switchView(mode: 'day' | 'week' | 'month'): void {
    this.viewMode = mode;
    this.initViewDates();
    this.generateCalendarGrid();
  }

  /**
   * 上周/上月
   */
  previousPeriod(): void {
    switch (this.viewMode) {
      case 'day':
        this.currentDate.setDate(this.currentDate.getDate() - 1);
        break;
      case 'week':
        this.currentDate.setDate(this.currentDate.getDate() - 7);
        break;
      case 'month':
        this.currentDate.setMonth(this.currentDate.getMonth() - 1);
        break;
    }

    this.initViewDates();
    this.generateCalendarGrid();
  }

  /**
   * 下周/下月
   */
  nextPeriod(): void {
    switch (this.viewMode) {
      case 'day':
        this.currentDate.setDate(this.currentDate.getDate() + 1);
        break;
      case 'week':
        this.currentDate.setDate(this.currentDate.getDate() + 7);
        break;
      case 'month':
        this.currentDate.setMonth(this.currentDate.getMonth() + 1);
        break;
    }

    this.initViewDates();
    this.generateCalendarGrid();
  }

  /**
   * 跳转到今天
   */
  goToToday(): void {
    this.currentDate = new Date();
    this.initViewDates();
    this.generateCalendarGrid();
  }

  /**
   * 处理拖拽放置事件
   */
  onDrop(event: CdkDragDrop<{ date: Date; hour: number }>): void {
    const schedule = event.item.data as CourseSchedule;

    if (schedule) {
      // 获取新的时间槽信息（从 drop list 的 data 中）
      const newTimeSlot = event.container.data;

      if (newTimeSlot) {
        this.adjustScheduleTime(schedule, newTimeSlot);
      }
    }
  }

  /**
   * 点击课程卡片
   */
  onScheduleClick(schedule: CourseSchedule): void {
    // 显示课程详情或编辑对话框
    console.log('点击课程:', schedule);
    // TODO: 打开编辑对话框
  }

  /**
   * 点击时间槽
   */
  onTimeSlotClick(date: Date, hour: number): void {
    // 创建新课程
    console.log('点击时间槽:', date, hour);
    // TODO: 打开新建课程对话框
  }

  /**
   * 调整课表时间
   */
  private adjustScheduleTime(
    schedule: CourseSchedule,
    newTimeSlot: { date: Date; hour: number }
  ): void {
    const updatedSchedule: CourseSchedule = {
      ...schedule,
      dayOfWeek: newTimeSlot.date.getDay(),
      startTime: `${String(newTimeSlot.hour).padStart(2, '0')}:00`,
      endTime: `${String(newTimeSlot.hour + 1).padStart(2, '0')}:00`,
    };

    // TODO: 调用 API 更新课表
    console.log('调整课表时间:', updatedSchedule);

    this.snackBar.open('课表已调整', '关闭', { duration: 3000 });
    this.loadSchedules();
  }

  /**
   * 检测并显示冲突
   */
  detectAndShowConflicts(): void {
    this.intelligentSchedulingService.detectConflicts(this.schedules).subscribe((conflicts) => {
      if (conflicts.length > 0) {
        this.showConflictsDialog(conflicts);
      } else {
        this.snackBar.open('没有检测到冲突', '关闭', { duration: 3000 });
      }
    });
  }

  /**
   * 自动解决冲突
   */
  autoResolveConflicts(): void {
    this.intelligentSchedulingService
      .resolveConflicts(this.schedules, [])
      .subscribe((resolvedSchedules) => {
        this.schedules = resolvedSchedules;
        this.applyFilters();
        this.generateCalendarGrid();
        this.snackBar.open('已自动解决冲突', '关闭', { duration: 3000 });
      });
  }

  /**
   * 显示冲突对话框
   */
  private showConflictsDialog(conflicts: ScheduleConflict[]): void {
    // TODO: 实现冲突对话框
    console.log('冲突列表:', conflicts);
    this.snackBar.open(`发现 ${conflicts.length} 个冲突`, '查看', { duration: 5000 });
  }
  getScheduleStyle(schedule: CourseSchedule): { [key: string]: string } {
    const styles: { [key: string]: string } = {};

    // 根据课程类型设置颜色
    if (schedule.hasConflict) {
      styles['background'] = '#ffebee';
      styles['border-left-color'] = '#f44336';
    } else {
      styles['background'] = '#e6f7ff';
      styles['border-left-color'] = '#1890ff';
    }

    return styles;
  }

  /**
   * 判断是否是今天
   */
  isToday(date: Date): boolean {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  }

  /**
   * 判断是否是周末
   */
  isWeekend(date: Date): boolean {
    const day = date.getDay();
    return day === 0 || day === 6;
  }

  /**
   * 获取星期名称
   */
  getDayName(dayIndex: number): string {
    const days = ['日', '一', '二', '三', '四', '五', '六'];
    return `周${days[dayIndex]}`;
  }

  /**
   * 格式化日期显示
   */
  formatDate(date: Date): string {
    return `${date.getMonth() + 1}/${date.getDate()}`;
  }

  /**
   * 获取视图标题
   */
  getViewTitle(): string {
    const year = this.currentDate.getFullYear();
    const month = this.currentDate.getMonth() + 1;

    switch (this.viewMode) {
      case 'day':
        return `${year}年${month}月${this.currentDate.getDate()}日`;
      case 'week': {
        const start = this.viewDates[0];
        const end = this.viewDates[this.viewDates.length - 1];
        return `${year}年${start.getMonth() + 1}月${start.getDate()}日 - ${end.getMonth() + 1}月${end.getDate()}日`;
      }
      case 'month':
        return `${year}年${month}月`;
    }
  }

  // ==================== 辅助方法 ====================

  private getStartOfWeek(date: Date): Date {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day;
    return new Date(d.setDate(diff));
  }

  private getDaysInMonth(date: Date): Date[] {
    const year = date.getFullYear();
    const month = date.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    const days: Date[] = [];
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(new Date(year, month, i));
    }

    return days;
  }

  // ==================== 模拟数据 ====================

  private getMockSchedules(): CourseSchedule[] {
    return [
      {
        id: 'SCH001',
        courseId: 'C001',
        courseName: '数学',
        teacherId: 'T001',
        teacherName: '张老师',
        classroomId: 'R001',
        classroomName: '教室 A101',
        classId: 'CL001',
        className: '初三 (1) 班',
        dayOfWeek: 1,
        startTime: '09:00',
        endTime: '10:00',
        startDate: '2026-03-01',
        endDate: '2026-06-30',
        recurrencePattern: 'weekly',
        isConfirmed: false,
        isActive: true,
        hasConflict: false,
      },
      {
        id: 'SCH002',
        courseId: 'C002',
        courseName: '英语',
        teacherId: 'T002',
        teacherName: '李老师',
        classroomId: 'R001',
        classroomName: '教室 A101',
        classId: 'CL001',
        className: '初三 (1) 班',
        dayOfWeek: 1,
        startTime: '10:00',
        endTime: '11:00',
        startDate: '2026-03-01',
        endDate: '2026-06-30',
        recurrencePattern: 'weekly',
        isConfirmed: false,
        isActive: true,
        hasConflict: false,
      },
      {
        id: 'SCH003',
        courseId: 'C003',
        courseName: '物理',
        teacherId: 'T003',
        teacherName: '王老师',
        classroomId: 'R002',
        classroomName: '实验室 B201',
        classId: 'CL001',
        className: '初三 (1) 班',
        dayOfWeek: 2,
        startTime: '14:00',
        endTime: '15:30',
        startDate: '2026-03-01',
        endDate: '2026-06-30',
        recurrencePattern: 'weekly',
        isConfirmed: false,
        isActive: true,
        hasConflict: false,
      },
    ];
  }
}
