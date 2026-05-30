"""
排课调度服务
============

整合遗传算法和冲突检测，提供完整的排课功能。
"""

from typing import List, Dict, Tuple, Optional
import logging

from .genetic_algorithm import GeneticSchedulingAlgorithm
from .conflict_detector import ConflictDetector

logger = logging.getLogger(__name__)


class SchedulingService:
    """排课调度服务"""

    def __init__(self):
        self.genetic_algorithm = None
        self.conflict_detector = ConflictDetector()

    def generate_schedule(
        self,
        courses: List[Dict],
        teachers: List[Dict],
        classrooms: List[Dict],
        classes: List[Dict],
        hard_constraints: List[Dict] = None,
        soft_constraints: List[Dict] = None,
        options: Dict = None
    ) -> Dict:
        """
        生成课表

        Args:
            courses: 课程列表
                [{id, name, total_hours, course_type, teacher_ids}, ...]
            teachers: 教师列表
                [{id, name, available_time_slots, max_weekly_hours, teaching_subjects}, ...]
            classrooms: 教室列表
                [{id, name, capacity, equipment}, ...]
            classes: 班级列表
                [{id, name, student_count, students}, ...]
            hard_constraints: 硬约束列表
            soft_constraints: 软约束列表
            options: 排课选项 {population_size, generations, mutation_rate}

        Returns:
            {
                'success': bool,
                'schedule': List[Dict],
                'conflicts': List[Dict],
                'score': float,
                'message': str
            }
        """
        logger.info("开始生成课表")

        try:
            # 1. 初始化遗传算法
            options = options or {}
            self.genetic_algorithm = GeneticSchedulingAlgorithm(
                population_size=options.get('population_size', 100),
                generations=options.get('generations', 1000),
                mutation_rate=options.get('mutation_rate', 0.1)
            )

            # 2. 运行遗传算法
            schedule, conflicts, score = self.genetic_algorithm.generate(
                courses=courses,
                teachers=teachers,
                classrooms=classrooms,
                classes=classes,
                hard_constraints=hard_constraints,
                soft_constraints=soft_constraints
            )

            # 3. 二次冲突检测 (确保无遗漏)
            detailed_conflicts = self._detailed_conflict_check(
                schedule, teachers, classrooms, classes
            )

            # 4. 合并冲突
            all_conflicts = conflicts + detailed_conflicts

            # 5. 返回结果
            success = len(all_conflicts) == 0

            result = {
                'success': success,
                'schedule': schedule,
                'conflicts': all_conflicts,
                'score': score,
                'message': '课表生成成功' if success else f'课表生成完成，发现 {len(all_conflicts)} 个冲突'
            }

            logger.info(f"课表生成完成，成功：{success}, 得分：{score}, 冲突数：{len(all_conflicts)}")

            return result

        except Exception as e:
            logger.error(f"课表生成失败：{str(e)}", exc_info=True)
            return {
                'success': False,
                'schedule': [],
                'conflicts': [],
                'score': 0.0,
                'message': f'课表生成失败：{str(e)}'
            }

    def _detailed_conflict_check(
        self,
        schedule: List[Dict],
        teachers: List[Dict],
        classrooms: List[Dict],
        classes: List[Dict]
    ) -> List[Dict]:
        """详细的冲突检查"""
        teachers_dict = {t['id']: t for t in teachers}
        classrooms_dict = {c['id']: c for c in classrooms}
        classes_dict = {c['id']: c for c in classes}

        conflicts = self.conflict_detector.detect_conflicts(
            schedules=schedule,
            teachers=teachers_dict,
            classrooms=classrooms_dict,
            classes=classes_dict
        )

        return conflicts

    def adjust_schedule(
        self,
        schedule_id: str,
        new_time_slot: Dict,
        schedule: List[Dict]
    ) -> Dict:
        """
        手动调整课表

        Args:
            schedule_id: 课表 ID
            new_time_slot: 新的时间段
                {day_of_week, start_time, end_time}
            schedule: 当前课表

        Returns:
            {
                'success': bool,
                'updated_schedule': List[Dict],
                'new_conflicts': List[Dict],
                'message': str
            }
        """
        logger.info(f"调整课表 {schedule_id}")

        try:
            # 1. 找到要调整的课程
            target_schedule = None
            for s in schedule:
                if s.get('id') == schedule_id or s.get('course_id') == schedule_id:
                    target_schedule = s
                    break

            if not target_schedule:
                return {
                    'success': False,
                    'updated_schedule': schedule,
                    'new_conflicts': [],
                    'message': '未找到要调整的课程'
                }

            # 2. 更新时间槽
            old_day = target_schedule.get('day_of_week')
            old_start = target_schedule.get('start_time')
            old_end = target_schedule.get('end_time')

            target_schedule['day_of_week'] = new_time_slot.get('day_of_week')
            target_schedule['start_time'] = new_time_slot.get('start_time')
            target_schedule['end_time'] = new_time_slot.get('end_time')

            # 3. 检查新时间是否产生冲突
            conflicts = self.conflict_detector.detect_conflicts(schedules=schedule)

            # 4. 过滤出与该课程相关的冲突
            related_conflicts = [
                c for c in conflicts
                if any(g.get('course_id') == schedule_id for g in c.get('schedules', []))
            ]

            message = '调整成功' if len(related_conflicts) == 0 else '调整成功，但存在冲突'

            return {
                'success': len(related_conflicts) == 0,
                'updated_schedule': schedule,
                'new_conflicts': related_conflicts,
                'message': message
            }

        except Exception as e:
            logger.error(f"课表调整失败：{str(e)}", exc_info=True)
            return {
                'success': False,
                'updated_schedule': schedule,
                'new_conflicts': [],
                'message': f'调整失败：{str(e)}'
            }

    def get_schedule_statistics(self, schedule: List[Dict]) -> Dict:
        """
        获取课表统计信息

        Args:
            schedule: 课表列表

        Returns:
            统计信息字典
        """
        stats = {
            'total_courses': len(schedule),
            'by_teacher': {},
            'by_classroom': {},
            'by_class': {},
            'by_day': {},
            'total_hours': 0
        }

        for s in schedule:
            # 按教师统计
            teacher_id = s.get('teacher_id')
            if teacher_id:
                stats['by_teacher'][teacher_id] = stats['by_teacher'].get(teacher_id, 0) + 1

            # 按教室统计
            classroom_id = s.get('classroom_id')
            if classroom_id:
                stats['by_classroom'][classroom_id] = stats['by_classroom'].get(classroom_id, 0) + 1

            # 按班级统计
            class_id = s.get('class_id')
            if class_id:
                stats['by_class'][class_id] = stats['by_class'].get(class_id, 0) + 1

            # 按星期统计
            day = s.get('day_of_week')
            if day is not None:
                stats['by_day'][day] = stats['by_day'].get(day, 0) + 1

            # 计算总课时
            start_time = s.get('start_time', '00:00')
            end_time = s.get('end_time', '00:00')

            try:
                start_hour, start_min = map(int, start_time.split(':'))
                end_hour, end_min = map(int, end_time.split(':'))
                duration = (end_hour * 60 + end_min) - (start_hour * 60 + start_min)
                stats['total_hours'] += duration / 60
            except:
                pass

        return stats
