"""
课表冲突检测引擎
================

实时检测各类排课冲突，包括:
- 教师时间冲突 (同一教师同一时间多处授课)
- 教室时间冲突 (同一教室同一时间多个班级)
- 学生时间冲突 (同一学生同一时间多门课程)
- 容量冲突 (班级人数超过教室容量)
"""

from typing import List, Dict, Set, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ConflictDetector:
    """课表冲突检测器"""

    def __init__(self):
        self.schedules = []
        self.teachers = {}
        self.classrooms = {}
        self.classes = {}
        self.students = {}

    def detect_conflicts(
        self,
        schedules: List[Dict],
        teachers: Dict = None,
        classrooms: Dict = None,
        classes: Dict = None,
        students: Dict = None
    ) -> List[Dict]:
        """
        检测课表冲突

        Args:
            schedules: 课表列表
            teachers: 教师字典 {id: teacher_data}
            classrooms: 教室字典 {id: classroom_data}
            classes: 班级字典 {id: class_data}
            students: 学生字典 {id: student_data}

        Returns:
            冲突列表
        """
        logger.info(f"开始冲突检测，课表数：{len(schedules)}")

        self.schedules = schedules
        self.teachers = teachers or {}
        self.classrooms = classrooms or {}
        self.classes = classes or {}
        self.students = students or {}

        all_conflicts = []

        # 1. 检测教师冲突
        teacher_conflicts = self._detect_teacher_conflicts()
        all_conflicts.extend(teacher_conflicts)
        logger.info(f"发现教师冲突：{len(teacher_conflicts)}")

        # 2. 检测教室冲突
        classroom_conflicts = self._detect_classroom_conflicts()
        all_conflicts.extend(classroom_conflicts)
        logger.info(f"发现教室冲突：{len(classroom_conflicts)}")

        # 3. 检测学生冲突
        student_conflicts = self._detect_student_conflicts()
        all_conflicts.extend(student_conflicts)
        logger.info(f"发现学生冲突：{len(student_conflicts)}")

        # 4. 检测容量冲突
        capacity_conflicts = self._detect_capacity_conflicts()
        all_conflicts.extend(capacity_conflicts)
        logger.info(f"发现容量冲突：{len(capacity_conflicts)}")

        return all_conflicts

    def _detect_teacher_conflicts(self) -> List[Dict]:
        """检测教师时间冲突"""
        conflicts = []

        # 按教师分组
        teacher_schedules = defaultdict(list)
        for schedule in self.schedules:
            teacher_id = schedule.get('teacher_id')
            if teacher_id:
                key = (
                    schedule.get('day_of_week'),
                    schedule.get('start_time'),
                    schedule.get('end_time')
                )
                teacher_schedules[(teacher_id, key)].append(schedule)

        # 检查冲突
        for (teacher_id, time_key), schedules_at_time in teacher_schedules.items():
            if len(schedules_at_time) > 1:
                conflicts.append({
                    'conflict_type': 'teacher_conflict',
                    'teacher_id': teacher_id,
                    'teacher_name': self.teachers.get(teacher_id, {}).get('name'),
                    'time': time_key,
                    'schedules': schedules_at_time,
                    'description': f"教师 {self.teachers.get(teacher_id, {}).get('name')} 在 {time_key} 时间段有多个课程安排"
                })

        return conflicts

    def _detect_classroom_conflicts(self) -> List[Dict]:
        """检测教室时间冲突"""
        conflicts = []

        # 按教室分组
        classroom_schedules = defaultdict(list)
        for schedule in self.schedules:
            classroom_id = schedule.get('classroom_id')
            if classroom_id:
                key = (
                    schedule.get('day_of_week'),
                    schedule.get('start_time'),
                    schedule.get('end_time')
                )
                classroom_schedules[(classroom_id, key)].append(schedule)

        # 检查冲突
        for (classroom_id, time_key), schedules_at_time in classroom_schedules.items():
            if len(schedules_at_time) > 1:
                conflicts.append({
                    'conflict_type': 'classroom_conflict',
                    'classroom_id': classroom_id,
                    'classroom_name': self.classrooms.get(classroom_id, {}).get('name'),
                    'time': time_key,
                    'schedules': schedules_at_time,
                    'description': f"教室 {self.classrooms.get(classroom_id, {}).get('name')} 在 {time_key} 时间段有多个课程安排"
                })

        return conflicts

    def _detect_student_conflicts(self) -> List[Dict]:
        """检测学生时间冲突"""
        conflicts = []

        # 收集每个班级的课程
        class_schedules = defaultdict(list)
        for schedule in self.schedules:
            class_id = schedule.get('class_id')
            if class_id:
                key = (
                    schedule.get('day_of_week'),
                    schedule.get('start_time'),
                    schedule.get('end_time')
                )
                class_schedules[(class_id, key)].append(schedule)

        # 检查冲突
        for (class_id, time_key), schedules_at_time in class_schedules.items():
            if len(schedules_at_time) > 1:
                conflicts.append({
                    'conflict_type': 'student_conflict',
                    'class_id': class_id,
                    'class_name': self.classes.get(class_id, {}).get('name'),
                    'time': time_key,
                    'schedules': schedules_at_time,
                    'description': f"班级 {self.classes.get(class_id, {}).get('name')} 在 {time_key} 时间段有多个课程安排"
                })

        return conflicts

    def _detect_capacity_conflicts(self) -> List[Dict]:
        """检测容量冲突"""
        conflicts = []

        for schedule in self.schedules:
            classroom_id = schedule.get('classroom_id')
            class_id = schedule.get('class_id')

            if not classroom_id or not class_id:
                continue

            classroom = self.classrooms.get(classroom_id, {})
            class_group = self.classes.get(class_id, {})

            classroom_capacity = classroom.get('capacity', 0)
            class_size = class_group.get('student_count', 0)

            if class_size > classroom_capacity:
                conflicts.append({
                    'conflict_type': 'capacity_conflict',
                    'schedule_id': schedule.get('id'),
                    'classroom_id': classroom_id,
                    'classroom_name': classroom.get('name'),
                    'class_id': class_id,
                    'class_name': class_group.get('name'),
                    'class_size': class_size,
                    'classroom_capacity': classroom_capacity,
                    'description': f"班级 {class_group.get('name')} 有 {class_size} 人，超过教室 {classroom.get('name')} 的容量 {classroom_capacity}"
                })

        return conflicts

    def has_time_overlap(
        self,
        start1: str,
        end1: str,
        start2: str,
        end2: str
    ) -> bool:
        """
        判断两个时间段是否重叠

        Args:
            start1, end1: 第一个时间段 (格式：HH:mm)
            start2, end2: 第二个时间段

        Returns:
            是否重叠
        """
        def time_to_minutes(time_str: str) -> int:
            """将 HH:mm 转换为分钟数"""
            hours, minutes = map(int, time_str.split(':'))
            return hours * 60 + minutes

        start1_min = time_to_minutes(start1)
        end1_min = time_to_minutes(end1)
        start2_min = time_to_minutes(start2)
        end2_min = time_to_minutes(end2)

        # 判断是否不重叠
        non_overlapping = (end1_min <= start2_min) or (end2_min <= start1_min)

        return not non_overlapping

    def get_available_time_slots(
        self,
        teacher_id: str,
        classroom_id: str,
        class_id: str,
        day_of_week: int
    ) -> List[Tuple[str, str]]:
        """
        获取可用时间段

        Args:
            teacher_id: 教师 ID
            classroom_id: 教室 ID
            class_id: 班级 ID
            day_of_week: 星期几

        Returns:
            可用时间段列表 [(start_time, end_time), ...]
        """
        # 假设每天 8:00-21:00
        all_slots = [(f"{h:02d}:00", f"{h+1:02d}:00") for h in range(8, 21)]

        # 找出已占用的时间段
        occupied_slots = set()

        for schedule in self.schedules:
            if schedule.get('day_of_week') != day_of_week:
                continue

            # 检查是否与该教师、教室或班级冲突
            if (schedule.get('teacher_id') == teacher_id or
                schedule.get('classroom_id') == classroom_id or
                schedule.get('class_id') == class_id):

                slot = (schedule.get('start_time'), schedule.get('end_time'))
                occupied_slots.add(slot)

        # 返回可用时间段
        available_slots = [slot for slot in all_slots if slot not in occupied_slots]

        return available_slots
