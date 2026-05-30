"""
教育机构综合管理服务
整合教师、学生、教室、课程安排等核心功能
"""

from datetime import date, datetime
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from models.classroom import Classroom, ClassSchedule
from models.course import Course, CourseEnrollment
from models.student import Student
from models.teacher import Teacher, TeacherCreate
from models.user import User, UserRole

logger = logging.getLogger(__name__)


class EducationalInstitutionService:
    """教育机构综合管理服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 教师管理 ====================

    def create_teacher(
        self, org_id: int, teacher_data: TeacherCreate, current_user: User
    ) -> Teacher:
        """创建教师档案"""
        try:
            # 验证用户权限
            if not self._can_manage_teachers(current_user):
                raise ValueError("无权管理教师信息")

            # 验证工号唯一性
            existing_teacher = (
                self.db.query(Teacher)
                .filter(
                    Teacher.employee_id == teacher_data.employee_id,
                    Teacher.org_id == org_id,
                )
                .first()
            )

            if existing_teacher:
                raise ValueError(f"工号 '{teacher_data.employee_id}' 已存在")

            # 验证用户是否存在且未关联其他教师档案
            user = self.db.query(User).filter(User.id == teacher_data.user_id).first()
            if not user:
                raise ValueError("指定的用户不存在")

            existing_user_teacher = (
                self.db.query(Teacher)
                .filter(Teacher.user_id == teacher_data.user_id)
                .first()
            )

            if existing_user_teacher:
                raise ValueError("该用户已有关联的教师档案")

            # 创建教师档案
            teacher = Teacher(
                org_id=org_id,
                user_id=teacher_data.user_id,
                employee_id=teacher_data.employee_id,
                department=teacher_data.department,
                position=teacher_data.position,
                hire_date=teacher_data.hire_date,
                qualification=teacher_data.qualification,
                specialization=teacher_data.specialization,
                teaching_subjects=(
                    str(teacher_data.teaching_subjects)
                    if teacher_data.teaching_subjects
                    else None
                ),
                max_classes=teacher_data.max_classes,
            )

            self.db.add(teacher)
            self.db.commit()
            self.db.refresh(teacher)

            logger.info(f"教师档案创建成功: {teacher.employee_id} (ID: {teacher.id})")
            return teacher

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建教师档案失败: {e}")
            raise

    def get_teacher_schedule(
        self,
        org_id: int,
        teacher_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """获取教师课表"""
        try:
            # 验证教师是否存在
            teacher = (
                self.db.query(Teacher)
                .filter(Teacher.id == teacher_id, Teacher.org_id == org_id)
                .first()
            )

            if not teacher:
                raise ValueError("教师不存在")

            # 查询课程安排
            query = self.db.query(ClassSchedule).filter(
                ClassSchedule.teacher_id == teacher_id,
                ClassSchedule.org_id == org_id,
                ClassSchedule.is_active == True,
            )

            # 添加日期筛选
            if start_date:
                query = query.filter(ClassSchedule.start_date >= start_date)
            if end_date:
                query = query.filter(ClassSchedule.end_date <= end_date)

            schedules = query.order_by(
                ClassSchedule.day_of_week, ClassSchedule.start_time
            ).all()

            # 格式化返回数据
            schedule_data = []
            for schedule in schedules:
                schedule_data.append(
                    {
                        "schedule_id": schedule.id,
                        "day_of_week": schedule.day_of_week,
                        "start_time": schedule.start_time.isoformat(),
                        "end_time": schedule.end_time.isoformat(),
                        "duration_minutes": schedule.duration_minutes,
                        "course_name": (
                            schedule.course.title if schedule.course else "未知课程"
                        ),
                        "classroom": (
                            f"{schedule.classroom.building} {schedule.classroom.room_number}"
                            if schedule.classroom
                            else "未分配"
                        ),
                        "is_confirmed": schedule.is_confirmed,
                    }
                )

            return schedule_data

        except Exception as e:
            logger.error(f"获取教师课表失败: {e}")
            return []

    # ==================== 学生管理 ====================

    def create_student(
        self, org_id: int, student_data: "StudentCreate", current_user: User
    ) -> Student:
        """创建学生档案"""
        try:
            # 验证用户权限
            if not self._can_manage_students(current_user):
                raise ValueError("无权管理学生信息")

            # 验证学号唯一性
            existing_student = (
                self.db.query(Student)
                .filter(
                    Student.student_id == student_data.student_id,
                    Student.org_id == org_id,
                )
                .first()
            )

            if existing_student:
                raise ValueError(f"学号 '{student_data.student_id}' 已存在")

            # 验证用户是否存在且未关联其他学生档案
            user = self.db.query(User).filter(User.id == student_data.user_id).first()
            if not user:
                raise ValueError("指定的用户不存在")

            existing_user_student = (
                self.db.query(Student)
                .filter(Student.user_id == student_data.user_id)
                .first()
            )

            if existing_user_student:
                raise ValueError("该用户已有关联的学生档案")

            # 验证导师存在性
            if student_data.advisor_id:
                advisor = (
                    self.db.query(Teacher)
                    .filter(
                        Teacher.id == student_data.advisor_id, Teacher.org_id == org_id
                    )
                    .first()
                )

                if not advisor:
                    raise ValueError("指定的导师不存在")

            # 创建学生档案
            student = Student(
                org_id=org_id,
                user_id=student_data.user_id,
                student_id=student_data.student_id,
                grade=student_data.grade,
                class_name=student_data.class_name,
                enrollment_date=student_data.enrollment_date,
                graduation_date=student_data.graduation_date,
                major=student_data.major,
                advisor_id=student_data.advisor_id,
                parent_name=student_data.parent_name,
                parent_phone=student_data.parent_phone,
                emergency_contact=student_data.emergency_contact,
                emergency_phone=student_data.emergency_phone,
            )

            self.db.add(student)
            self.db.commit()
            self.db.refresh(student)

            logger.info(f"学生档案创建成功: {student.student_id} (ID: {student.id})")
            return student

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建学生档案失败: {e}")
            raise

    def get_student_schedule(
        self,
        org_id: int,
        student_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """获取学生课表"""
        try:
            # 验证学生是否存在
            student = (
                self.db.query(Student)
                .filter(Student.id == student_id, Student.org_id == org_id)
                .first()
            )

            if not student:
                raise ValueError("学生不存在")

            # 查询学生的课程选课记录
            enrollments = (
                self.db.query(CourseEnrollment)
                .filter(
                    CourseEnrollment.student_id == student.user_id,
                    CourseEnrollment.org_id == org_id,
                    CourseEnrollment.status == "enrolled",
                )
                .all()
            )

            course_ids = [enrollment.course_id for enrollment in enrollments]

            if not course_ids:
                return []

            # 查询相关课程的时间安排
            query = self.db.query(ClassSchedule).filter(
                ClassSchedule.course_id.in_(course_ids),
                ClassSchedule.org_id == org_id,
                ClassSchedule.is_active == True,
            )

            # 添加日期筛选
            if start_date:
                query = query.filter(ClassSchedule.start_date >= start_date)
            if end_date:
                query = query.filter(ClassSchedule.end_date <= end_date)

            schedules = query.order_by(
                ClassSchedule.day_of_week, ClassSchedule.start_time
            ).all()

            # 格式化返回数据
            schedule_data = []
            for schedule in schedules:
                schedule_data.append(
                    {
                        "schedule_id": schedule.id,
                        "day_of_week": schedule.day_of_week,
                        "start_time": schedule.start_time.isoformat(),
                        "end_time": schedule.end_time.isoformat(),
                        "duration_minutes": schedule.duration_minutes,
                        "course_name": (
                            schedule.course.title if schedule.course else "未知课程"
                        ),
                        "teacher_name": (
                            schedule.teacher.user.username
                            if schedule.teacher and schedule.teacher.user
                            else "未分配"
                        ),
                        "classroom": (
                            f"{schedule.classroom.building} {schedule.classroom.room_number}"
                            if schedule.classroom
                            else "未分配"
                        ),
                        "is_confirmed": schedule.is_confirmed,
                    }
                )

            return schedule_data

        except Exception as e:
            logger.error(f"获取学生课表失败: {e}")
            return []

    # ==================== 教室管理 ====================

    def get_available_classrooms(
        self,
        org_id: int,
        capacity_needed: int = 1,
        date_filter: Optional[date] = None,
        time_start: Optional[datetime] = None,
        time_end: Optional[datetime] = None,
    ) -> List[Classroom]:
        """获取可用教室"""
        try:
            # 基本查询：满足容量和可用性要求的教室
            query = self.db.query(Classroom).filter(
                Classroom.org_id == org_id,
                Classroom.capacity >= capacity_needed,
                Classroom.is_available == True,
            )

            available_classrooms = query.all()

            # 如果指定了时间和日期，进一步筛选没有冲突的教室
            if date_filter and time_start and time_end:
                conflicting_classroom_ids = self._get_conflicting_classroom_ids(
                    org_id, date_filter, time_start, time_end
                )

                available_classrooms = [
                    room
                    for room in available_classrooms
                    if room.id not in conflicting_classroom_ids
                ]

            return available_classrooms

        except Exception as e:
            logger.error(f"获取可用教室失败: {e}")
            return []

    def _get_conflicting_classroom_ids(
        self, org_id: int, check_date: date, time_start: datetime, time_end: datetime
    ) -> List[int]:
        """获取在指定时间有冲突的教室ID列表"""
        try:
            # 查询在指定时间范围内的课程安排
            conflicting_schedules = (
                self.db.query(ClassSchedule)
                .filter(
                    ClassSchedule.org_id == org_id,
                    ClassSchedule.is_active == True,
                    ClassSchedule.day_of_week
                    == check_date.weekday() + 1,  # Python weekday: 0-6, 数据库: 1-7
                    or_(
                        and_(
                            ClassSchedule.start_time <= time_start,
                            ClassSchedule.end_time > time_start,
                        ),
                        and_(
                            ClassSchedule.start_time < time_end,
                            ClassSchedule.end_time >= time_end,
                        ),
                        and_(
                            ClassSchedule.start_time >= time_start,
                            ClassSchedule.end_time <= time_end,
                        ),
                    ),
                )
                .all()
            )

            return [schedule.classroom_id for schedule in conflicting_schedules]

        except Exception as e:
            logger.error(f"检查教室冲突失败: {e}")
            return []

    # ==================== 排课管理 ====================

    def schedule_class(
        self, org_id: int, schedule_data: "ClassScheduleCreate", current_user: User
    ) -> ClassSchedule:
        """安排课程"""
        try:
            # 验证权限
            if not self._can_manage_schedules(current_user):
                raise ValueError("无权管理课程安排")

            # 验证教室、课程、教师存在性
            classroom = (
                self.db.query(Classroom)
                .filter(
                    Classroom.id == schedule_data.classroom_id,
                    Classroom.org_id == org_id,
                )
                .first()
            )

            if not classroom:
                raise ValueError("指定的教室不存在")

            course = (
                self.db.query(Course)
                .filter(Course.id == schedule_data.course_id, Course.org_id == org_id)
                .first()
            )

            if not course:
                raise ValueError("指定的课程不存在")

            if schedule_data.teacher_id:
                teacher = (
                    self.db.query(Teacher)
                    .filter(
                        Teacher.id == schedule_data.teacher_id, Teacher.org_id == org_id
                    )
                    .first()
                )

                if not teacher:
                    raise ValueError("指定的教师不存在")

            # 检查时间冲突
            conflict_check = self._check_schedule_conflict(
                org_id,
                schedule_data.classroom_id,
                schedule_data.day_of_week,
                schedule_data.start_time,
                schedule_data.end_time,
                schedule_data.start_date,
                schedule_data.end_date,
            )

            if conflict_check["has_conflict"]:
                raise ValueError(f"时间安排冲突: {conflict_check['conflict_details']}")

            # 创建课程安排
            schedule = ClassSchedule(
                org_id=org_id,
                classroom_id=schedule_data.classroom_id,
                course_id=schedule_data.course_id,
                teacher_id=schedule_data.teacher_id,
                day_of_week=schedule_data.day_of_week,
                start_time=schedule_data.start_time,
                end_time=schedule_data.end_time,
                start_date=schedule_data.start_date,
                end_date=schedule_data.end_date,
                recurrence_pattern=schedule_data.recurrence_pattern,
            )

            # 计算持续时间
            duration = (
                schedule_data.end_time - schedule_data.start_time
            ).total_seconds() / 60
            schedule.duration_minutes = int(duration)

            self.db.add(schedule)

            # 更新教师的教学负荷（如果有指定教师）
            if schedule_data.teacher_id:
                teacher.current_classes += 1
                teacher.teaching_load += schedule.duration_minutes

            self.db.commit()
            self.db.refresh(schedule)

            logger.info(
                f"课程安排创建成功: 教室{classroom.room_number}, 课程{course.code}"
            )
            return schedule

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建课程安排失败: {e}")
            raise

    def _check_schedule_conflict(
        self,
        org_id: int,
        classroom_id: int,
        day_of_week: int,
        start_time: datetime,
        end_time: datetime,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> Dict[str, Any]:
        """检查排课冲突"""
        try:
            # 查询同一教室在同一星期的其他安排
            query = self.db.query(ClassSchedule).filter(
                ClassSchedule.classroom_id == classroom_id,
                ClassSchedule.org_id == org_id,
                ClassSchedule.day_of_week == day_of_week,
                ClassSchedule.is_active == True,
            )

            # 添加时间重叠检查
            query = query.filter(
                or_(
                    and_(
                        ClassSchedule.start_time <= start_time,
                        ClassSchedule.end_time > start_time,
                    ),
                    and_(
                        ClassSchedule.start_time < end_time,
                        ClassSchedule.end_time >= end_time,
                    ),
                    and_(
                        ClassSchedule.start_time >= start_time,
                        ClassSchedule.end_time <= end_time,
                    ),
                )
            )

            # 如果指定了日期范围，添加日期检查
            if start_date and end_date:
                query = query.filter(
                    or_(
                        and_(
                            ClassSchedule.start_date <= start_date,
                            ClassSchedule.end_date >= start_date,
                        ),
                        and_(
                            ClassSchedule.start_date <= end_date,
                            ClassSchedule.end_date >= end_date,
                        ),
                        and_(
                            ClassSchedule.start_date >= start_date,
                            ClassSchedule.end_date <= end_date,
                        ),
                    )
                )

            conflicting_schedules = query.all()

            if conflicting_schedules:
                conflict_details = []
                for schedule in conflicting_schedules:
                    conflict_details.append(
                        {
                            "course": (
                                schedule.course.title if schedule.course else "未知课程"
                            ),
                            "time": f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}",
                            "teacher": (
                                schedule.teacher.user.username
                                if schedule.teacher and schedule.teacher.user
                                else "未分配"
                            ),
                        }
                    )

                return {
                    "has_conflict": True,
                    "conflict_details": "; ".join(
                        [
                            f"{detail['course']} ({detail['time']}) - {detail['teacher']}"
                            for detail in conflict_details
                        ]
                    ),
                }

            return {"has_conflict": False}

        except Exception as e:
            logger.error(f"检查排课冲突失败: {e}")
            return {"has_conflict": False}

    # ==================== 综合查询 ====================

    def get_institution_overview(self, org_id: int) -> Dict[str, Any]:
        """获取教育机构概览信息"""
        try:
            # 统计各类人员数量
            teacher_count = (
                self.db.query(Teacher)
                .filter(Teacher.org_id == org_id, Teacher.is_active == True)
                .count()
            )

            student_count = (
                self.db.query(Student)
                .filter(Student.org_id == org_id, Student.is_active == True)
                .count()
            )

            # 统计教室资源
            classroom_count = (
                self.db.query(Classroom).filter(Classroom.org_id == org_id).count()
            )

            available_classroom_count = (
                self.db.query(Classroom)
                .filter(Classroom.org_id == org_id, Classroom.is_available == True)
                .count()
            )

            # 统计课程信息
            course_count = self.db.query(Course).filter(Course.org_id == org_id).count()

            active_course_count = (
                self.db.query(Course)
                .filter(Course.org_id == org_id, Course.status == "published")
                .count()
            )

            # 获取今日课程安排
            today = date.today()
            today_schedules = (
                self.db.query(ClassSchedule)
                .filter(
                    ClassSchedule.org_id == org_id,
                    ClassSchedule.is_active == True,
                    ClassSchedule.day_of_week == today.weekday() + 1,
                )
                .count()
            )

            return {
                "personnel": {"teachers": teacher_count, "students": student_count},
                "resources": {
                    "total_classrooms": classroom_count,
                    "available_classrooms": available_classroom_count,
                },
                "academics": {
                    "total_courses": course_count,
                    "active_courses": active_course_count,
                    "today_schedules": today_schedules,
                },
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"获取机构概览失败: {e}")
            return {"error": str(e)}

    # ==================== 权限检查 ====================

    def _can_manage_teachers(self, user: User) -> bool:
        """检查用户是否有管理教师的权限"""
        return user.is_superuser or user.role in [UserRole.ADMIN, UserRole.ORG_ADMIN]

    def _can_manage_students(self, user: User) -> bool:
        """检查用户是否有管理学生的权限"""
        return user.is_superuser or user.role in [UserRole.ADMIN, UserRole.ORG_ADMIN]

    def _can_manage_schedules(self, user: User) -> bool:
        """检查用户是否有管理课程安排的权限"""
        return user.is_superuser or user.role in [UserRole.ADMIN, UserRole.ORG_ADMIN]

    def _can_view_schedules(
        self, user: User, target_user_id: Optional[int] = None
    ) -> bool:
        """检查用户是否有查看课表的权限"""
        # 管理员可以查看所有课表
        if user.is_superuser or user.role in [UserRole.ADMIN, UserRole.ORG_ADMIN]:
            return True

        # 用户可以查看自己的课表
        if target_user_id is None or user.id == target_user_id:
            return True

        # 教师可以查看自己授课的课程安排
        if user.role == UserRole.USER:
            teacher = self.db.query(Teacher).filter(Teacher.user_id == user.id).first()
            if teacher:
                return True

        return False
