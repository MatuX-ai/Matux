"""
iMato 教育培训管理系统 - 排课模块数据模型
"""
from .schedule import CourseSchedule, ScheduleConflict
from .student import StudentProfile, ParentInfo, StudentStatus
from .teacher import Teacher, TeachingRecord, TeacherSalary
from .classroom import Classroom, ClassroomEquipment
from .attendance import Attendance, AttendanceStatus, LeaveType
from .order import Order, OrderItem, PaymentMethod, OrderStatus
from .salary import SalaryDetail, PerformanceBonus

__all__ = [
    # 排课相关
    'CourseSchedule',
    'ScheduleConflict',

    # 学员相关
    'StudentProfile',
    'ParentInfo',
    'StudentStatus',

    # 教师相关
    'Teacher',
    'TeachingRecord',
    'TeacherSalary',

    # 教室相关
    'Classroom',
    'ClassroomEquipment',

    # 考勤相关
    'Attendance',
    'AttendanceStatus',
    'LeaveType',

    # 订单相关
    'Order',
    'OrderItem',
    'PaymentMethod',
    'OrderStatus',

    # 薪酬相关
    'SalaryDetail',
    'PerformanceBonus',
]
