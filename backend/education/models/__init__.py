"""
iMato 教育培训管理系统 - 排课模块数据模型
"""
from .attendance import Attendance, AttendanceStatus, LeaveType
from .classroom import Classroom, ClassroomEquipment
from .order import Order, OrderItem, OrderStatus, PaymentMethod
from .salary import PerformanceBonus, SalaryDetail
from .schedule import CourseSchedule, ScheduleConflict
from .student import ParentInfo, StudentProfile, StudentStatus
from .teacher import Teacher, TeacherSalary, TeachingRecord

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
