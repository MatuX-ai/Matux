"""
教育培训管理系统配置
"""
from pydantic import BaseSettings


class EducationSettings(BaseSettings):
    """教育业务配置"""

    # 排课相关配置
    SCHEDULING_POPULATION_SIZE: int = 100  # 遗传算法种群大小
    SCHEDULING_GENERATIONS: int = 1000     # 迭代代数
    SCHEDULING_MUTATION_RATE: float = 0.1  # 变异率

    # 课时预警阈值
    LOW_BALANCE_THRESHOLD: int = 5  # 剩余课时低于此值触发预警

    # 考勤相关
    ALLOW_LATE_MINUTES: int = 15  # 允许迟到分钟数

    # 薪酬计算相关
    HOURLY_RATE_ONE_ON_ONE: float = 100.0   # 一对一课时费
    HOURLY_RATE_SMALL_CLASS: float = 150.0  # 小班 (1-6 人) 课时费
    HOURLY_RATE_MEDIUM_CLASS: float = 200.0 # 中班 (7-20 人) 课时费
    HOURLY_RATE_LARGE_CLASS: float = 300.0  # 大班 (21+ 人) 课时费

    # 绩效奖金标准
    BONUS_ATTENDANCE_RATE: float = 500.0    # 出勤率奖 (>90%)
    BONUS_RENEWAL_RATE: float = 1000.0      # 续班率奖 (>80%)
    BONUS_SATISFACTION: float = 800.0       # 满意度奖 (评分>4.8)

    # 扣款标准
    DEDUCTION_LATE: float = 50.0            # 迟到/早退扣款
    DEDUCTION_ACCIDENT: float = 200.0       # 教学事故扣款
    DEDUCTION_COMPLAINT: float = 200.0      # 投诉扣款

    class Config:
        env_prefix = 'EDU_'
        env_file = '.env'
        env_file_encoding = 'utf-8'


# 全局配置实例
education_settings = EducationSettings()
