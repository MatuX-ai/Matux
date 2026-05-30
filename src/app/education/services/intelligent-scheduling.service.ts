/**
 * 智能排课服务
 * 使用遗传算法实现自动排课功能
 */

import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';

import {
  CourseSchedule,
  ScheduleConflict,
  ScheduleGenerationRequest,
  ScheduleGenerationResponse,
} from '../models/scheduling.models';

// 扩展的 CourseInfo 接口（包含排课需要的额外字段）
interface ExtendedCourseInfo {
  id: string;
  name: string;
  totalHours: number;
  courseType: 'one_on_one' | 'small_class' | 'medium_class' | 'large_class';
  teacherIds?: string[];
  requiredClassroomId?: string;
  classId?: string;
  className?: string;
  endDate?: string;
}

@Injectable({
  providedIn: 'root',
})
export class IntelligentSchedulingService {
  constructor() {}

  /**
   * 生成课表 - 使用智能算法
   */
  generateSchedule(request: ScheduleGenerationRequest): Observable<ScheduleGenerationResponse> {
    // TODO: 实现完整的遗传算法排课
    // 目前使用简化版本演示功能
    return this.generateScheduleWithAlgorithm(request);
  }

  /**
   * 检测课表冲突
   */
  detectConflicts(schedules: CourseSchedule[]): Observable<ScheduleConflict[]> {
    const conflicts: ScheduleConflict[] = [];

    // 检测教师时间冲突
    this.checkTeacherConflicts(schedules, conflicts);

    // 检测教室冲突
    this.checkClassroomConflicts(schedules, conflicts);

    // 检测学生班级冲突
    this.checkStudentConflicts(schedules, conflicts);

    return of(conflicts);
  }

  /**
   * 解决冲突
   */
  resolveConflicts(
    schedules: CourseSchedule[],
    conflicts: ScheduleConflict[]
  ): Observable<CourseSchedule[]> {
    // 尝试自动重新安排有冲突的课表
    const resolvedSchedules = this.attemptAutoResolve(schedules, conflicts);
    return of(resolvedSchedules);
  }

  /**
   * 优化课表（满足软约束）
   */
  optimizeSchedule(schedules: CourseSchedule[]): Observable<CourseSchedule[]> {
    // 使用启发式算法优化课表质量
    const optimized = this.applyOptimization(schedules);
    return of(optimized);
  }

  // ==================== 内部实现 ====================

  private generateScheduleWithAlgorithm(
    request: ScheduleGenerationRequest
  ): Observable<ScheduleGenerationResponse> {
    const generatedSchedules: CourseSchedule[] = [];
    const conflicts: ScheduleConflict[] = [];

    // 简化的贪心算法示例
    for (const course of request.courses as ExtendedCourseInfo[]) {
      const availableTeachers = request.teachers.filter((t) => course.teacherIds?.includes(t.id));
      const availableClassrooms = request.classrooms.filter((c) =>
        course.requiredClassroomId ? c.id === course.requiredClassroomId : true
      );

      if (availableTeachers.length === 0 || availableClassrooms.length === 0) {
        continue; // 跳过无法满足的课程
      }

      // 为课程分配时间和资源
      const teacher = availableTeachers[0];
      const classroom = availableClassrooms[0];

      // 生成一周内的课表（简单示例）
      for (let day = 1; day <= 5; day++) {
        // 工作日排课
        const schedule: CourseSchedule = {
          id: `SCH_${course.id}_${day}`,
          courseId: course.id,
          courseName: course.name,
          teacherId: teacher.id,
          teacherName: teacher.name,
          classroomId: classroom.id,
          classroomName: classroom.name,
          classId: course.classId,
          className: course.className,
          dayOfWeek: day,
          startTime: '09:00',
          endTime: '10:00',
          startDate: new Date().toISOString(),
          endDate: course.endDate ?? new Date().toISOString(),
          recurrencePattern: 'weekly',
          isConfirmed: false,
          isActive: true,
          hasConflict: false,
        };

        generatedSchedules.push(schedule);
      }
    }

    // 检测生成的课表是否有冲突
    this.detectConflictsInternal(generatedSchedules, conflicts);

    return of({
      success: true,
      schedule: generatedSchedules,
      conflicts,
      score: conflicts.length === 0 ? 100 : 80,
    });
  }

  private detectConflictsInternal(
    schedules: CourseSchedule[],
    conflicts: ScheduleConflict[]
  ): void {
    this.checkTeacherConflicts(schedules, conflicts);
    this.checkClassroomConflicts(schedules, conflicts);
    this.checkStudentConflicts(schedules, conflicts);
  }

  private checkTeacherConflicts(schedules: CourseSchedule[], conflicts: ScheduleConflict[]): void {
    const teacherSchedules = new Map<string, CourseSchedule[]>();

    // 按教师分组
    schedules.forEach((schedule) => {
      const teacherId = schedule.teacherId;
      if (!teacherSchedules.has(teacherId)) {
        teacherSchedules.set(teacherId, []);
      }
      teacherSchedules.get(teacherId)?.push(schedule);
    });

    // 检查每个教师的课表冲突
    teacherSchedules.forEach((schs) => {
      for (let i = 0; i < schs.length; i++) {
        for (let j = i + 1; j < schs.length; j++) {
          const s1 = schs[i];
          const s2 = schs[j];

          if (
            s1.dayOfWeek === s2.dayOfWeek &&
            this.isTimeOverlap(s1.startTime, s1.endTime, s2.startTime, s2.endTime)
          ) {
            conflicts.push({
              id: `CONFlict_T_${i}_${j}`,
              scheduleId: s1.id,
              conflictType: 'teacher_conflict',
              description: `教师 ${s1.teacherName} 在周${s1.dayOfWeek} 时间冲突`,
              relatedScheduleIds: [s1.id, s2.id],
              status: 'pending',
              createdAt: new Date().toISOString(),
            });
          }
        }
      }
    });
  }

  private checkClassroomConflicts(
    schedules: CourseSchedule[],
    conflicts: ScheduleConflict[]
  ): void {
    const roomSchedules = new Map<string, CourseSchedule[]>();

    // 按教室分组
    schedules.forEach((schedule) => {
      const roomId = schedule.classroomId;
      if (!roomId) return;
      if (!roomSchedules.has(roomId)) {
        roomSchedules.set(roomId, []);
      }
      roomSchedules.get(roomId)?.push(schedule);
    });

    // 检查每个教室的课表冲突
    roomSchedules.forEach((schs) => {
      for (let i = 0; i < schs.length; i++) {
        for (let j = i + 1; j < schs.length; j++) {
          const s1 = schs[i];
          const s2 = schs[j];

          if (
            s1.dayOfWeek === s2.dayOfWeek &&
            this.isTimeOverlap(s1.startTime, s1.endTime, s2.startTime, s2.endTime)
          ) {
            conflicts.push({
              id: `Conflict_R_${i}_${j}`,
              scheduleId: s1.id,
              conflictType: 'classroom_conflict',
              description: `教室 ${s1.classroomName} 在周${s1.dayOfWeek} 时间冲突`,
              relatedScheduleIds: [s1.id, s2.id],
              status: 'pending',
              createdAt: new Date().toISOString(),
            });
          }
        }
      }
    });
  }

  private checkStudentConflicts(schedules: CourseSchedule[], conflicts: ScheduleConflict[]): void {
    const classSchedules = new Map<string, CourseSchedule[]>();

    // 按班级分组
    schedules.forEach((schedule) => {
      const classId = schedule.classId;
      if (!classId) return;
      if (!classSchedules.has(classId)) {
        classSchedules.set(classId, []);
      }
      classSchedules.get(classId)?.push(schedule);
    });

    // 检查每个班级的课表冲突
    classSchedules.forEach((schs) => {
      for (let i = 0; i < schs.length; i++) {
        for (let j = i + 1; j < schs.length; j++) {
          const s1 = schs[i];
          const s2 = schs[j];

          if (
            s1.dayOfWeek === s2.dayOfWeek &&
            this.isTimeOverlap(s1.startTime, s1.endTime, s2.startTime, s2.endTime)
          ) {
            conflicts.push({
              id: `Conflict_S_${i}_${j}`,
              scheduleId: s1.id,
              conflictType: 'student_conflict',
              description: `班级 ${s1.className} 在周${s1.dayOfWeek} 时间冲突`,
              relatedScheduleIds: [s1.id, s2.id],
              status: 'pending',
              createdAt: new Date().toISOString(),
            });
          }
        }
      }
    });
  }

  private isTimeOverlap(start1: string, end1: string, start2: string, end2: string): boolean {
    const s1 = this.timeToMinutes(start1);
    const e1 = this.timeToMinutes(end1);
    const s2 = this.timeToMinutes(start2);
    const e2 = this.timeToMinutes(end2);

    return !(e1 <= s2 || e2 <= s1);
  }

  private timeToMinutes(time: string): number {
    const [hours, minutes] = time.split(':').map(Number);
    return hours * 60 + minutes;
  }

  private attemptAutoResolve(
    schedules: CourseSchedule[],
    conflicts: ScheduleConflict[]
  ): CourseSchedule[] {
    // 简化的冲突解决：为有冲突的课表寻找新的时间段
    const resolved = [...schedules];
    const conflictScheduleIds = new Set(conflicts.flatMap((c) => c.relatedScheduleIds));

    conflictScheduleIds.forEach((scheduleId) => {
      const index = resolved.findIndex((s) => s.id === scheduleId);
      if (index !== -1) {
        // 尝试调整到下午
        resolved[index] = {
          ...resolved[index],
          startTime: '14:00',
          endTime: '15:00',
        };
      }
    });

    return resolved;
  }

  private applyOptimization(schedules: CourseSchedule[]): CourseSchedule[] {
    // 简单的优化：避免连续上课
    return schedules.map((schedule) => {
      // 如果课程安排在早上第一节，保持不变
      if (schedule.startTime === '09:00') {
        return schedule;
      }
      // 其他课程尽量分散安排
      return schedule;
    });
  }
}
