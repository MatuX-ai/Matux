"""
日期时间处理工具函数集合
"""

import calendar
from datetime import datetime, timedelta
from typing import Optional, Union


def format_date(
    date_input: Union[datetime, int, float, str], format_str: str = "%Y-%m-%d"
) -> str:
    """
    格式化日期时间

    Args:
        date_input: 日期对象、时间戳或字符串
        format_str: 格式字符串，如 '%Y-%m-%d %H:%M:%S'

    Returns:
        str: 格式化后的字符串
    """
    if isinstance(date_input, str):
        try:
            dt = datetime.fromisoformat(date_input.replace("Z", "+00:00"))
        except ValueError:
            return ""
    elif isinstance(date_input, (int, float)):
        dt = datetime.fromtimestamp(date_input)
    elif isinstance(date_input, datetime):
        dt = date_input
    else:
        return ""

    return dt.strftime(format_str)


def get_time_ago(
    date_input: Union[datetime, int, float, str],
    base_date: Union[datetime, int, float, str] = None,
) -> str:
    """
    获取相对时间描述

    Args:
        date_input: 目标日期
        base_date: 基准日期，默认为当前时间

    Returns:
        str: 相对时间描述，如"2小时前"
    """
    if isinstance(date_input, str):
        target_date = datetime.fromisoformat(date_input.replace("Z", "+00:00"))
    elif isinstance(date_input, (int, float)):
        target_date = datetime.fromtimestamp(date_input)
    elif isinstance(date_input, datetime):
        target_date = date_input
    else:
        return ""

    if base_date is None:
        now = datetime.now()
    elif isinstance(base_date, str):
        now = datetime.fromisoformat(base_date.replace("Z", "+00:00"))
    elif isinstance(base_date, (int, float)):
        now = datetime.fromtimestamp(base_date)
    else:
        now = base_date

    diff = now - target_date
    diff_seconds = int(diff.total_seconds())

    if diff_seconds < 60:
        return "刚刚"
    elif diff_seconds < 3600:
        minutes = diff_seconds // 60
        return f"{minutes}分钟前"
    elif diff_seconds < 86400:
        hours = diff_seconds // 3600
        return f"{hours}小时前"
    elif diff_seconds < 604800:
        days = diff_seconds // 86400
        return f"{days}天前"
    elif diff_seconds < 2419200:
        weeks = diff_seconds // 604800
        return f"{weeks}周前"
    elif diff_seconds < 31536000:
        months = diff_seconds // 2419200
        return f"{months}个月前"
    else:
        years = diff_seconds // 31536000
        return f"{years}年前"


def is_same_day(
    date1: Union[datetime, int, float, str], date2: Union[datetime, int, float, str]
) -> bool:
    """
    判断是否为同一天

    Args:
        date1: 日期1
        date2: 日期2

    Returns:
        bool: 是否为同一天
    """

    def parse_date(date_input):
        if isinstance(date_input, str):
            return datetime.fromisoformat(date_input.replace("Z", "+00:00")).date()
        elif isinstance(date_input, (int, float)):
            return datetime.fromtimestamp(date_input).date()
        elif isinstance(date_input, datetime):
            return date_input.date()
        else:
            raise ValueError("Invalid date input")

    return parse_date(date1) == parse_date(date2)


def get_date_range(
    start_date: Union[datetime, str], end_date: Union[datetime, str]
) -> list:
    """
    获取日期范围

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        list: 日期列表
    """
    if isinstance(start_date, str):
        start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    else:
        start = start_date

    if isinstance(end_date, str):
        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    else:
        end = end_date

    dates = []
    current = start.date()
    end_date_obj = end.date()

    while current <= end_date_obj:
        dates.append(current)
        current += timedelta(days=1)

    return dates


def add_time(date_input: Union[datetime, str], amount: int, unit: str) -> datetime:
    """
    添加时间单位到日期

    Args:
        date_input: 原始日期
        amount: 数量
        unit: 单位 ('days', 'hours', 'minutes', 'seconds')

    Returns:
        datetime: 新日期
    """
    if isinstance(date_input, str):
        dt = datetime.fromisoformat(date_input.replace("Z", "+00:00"))
    else:
        dt = date_input

    if unit == "days":
        return dt + timedelta(days=amount)
    elif unit == "hours":
        return dt + timedelta(hours=amount)
    elif unit == "minutes":
        return dt + timedelta(minutes=amount)
    elif unit == "seconds":
        return dt + timedelta(seconds=amount)
    else:
        raise ValueError("Invalid time unit")


def date_diff(
    date1: Union[datetime, str], date2: Union[datetime, str], unit: str = "days"
) -> int:
    """
    计算两个日期之间的差异

    Args:
        date1: 日期1
        date2: 日期2
        unit: 返回单位 ('days', 'hours', 'minutes', 'seconds')

    Returns:
        int: 差异值
    """
    if isinstance(date1, str):
        d1 = datetime.fromisoformat(date1.replace("Z", "+00:00"))
    else:
        d1 = date1

    if isinstance(date2, str):
        d2 = datetime.fromisoformat(date2.replace("Z", "+00:00"))
    else:
        d2 = date2

    diff = abs(d2 - d1)

    if unit == "days":
        return diff.days
    elif unit == "hours":
        return int(diff.total_seconds() // 3600)
    elif unit == "minutes":
        return int(diff.total_seconds() // 60)
    elif unit == "seconds":
        return int(diff.total_seconds())
    else:
        raise ValueError("Invalid time unit")


def get_first_day_of_month(date_input: Union[datetime, str]) -> datetime:
    """
    获取月份的第一天

    Args:
        date_input: 日期

    Returns:
        datetime: 该月第一天的日期
    """
    if isinstance(date_input, str):
        dt = datetime.fromisoformat(date_input.replace("Z", "+00:00"))
    else:
        dt = date_input

    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_last_day_of_month(date_input: Union[datetime, str]) -> datetime:
    """
    获取月份的最后一天

    Args:
        date_input: 日期

    Returns:
        datetime: 该月最后一天的日期
    """
    if isinstance(date_input, str):
        dt = datetime.fromisoformat(date_input.replace("Z", "+00:00"))
    else:
        dt = date_input

    # 获取下个月的第一天，然后减去一天
    if dt.month == 12:
        next_month = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        next_month = dt.replace(month=dt.month + 1, day=1)

    return next_month - timedelta(days=1)


def is_leap_year(year: int) -> bool:
    """
    判断是否为闰年

    Args:
        year: 年份

    Returns:
        bool: 是否为闰年
    """
    return calendar.isleap(year)


def get_quarter_info(date_input: Union[datetime, str]) -> dict:
    """
    获取季度信息

    Args:
        date_input: 日期

    Returns:
        dict: 季度信息 {'quarter': int, 'start_date': datetime, 'end_date': datetime}
    """
    if isinstance(date_input, str):
        dt = datetime.fromisoformat(date_input.replace("Z", "+00:00"))
    else:
        dt = date_input

    year = dt.year
    month = dt.month
    quarter = (month - 1) // 3 + 1

    start_month = (quarter - 1) * 3 + 1
    end_month = quarter * 3

    start_date = datetime(year, start_month, 1)
    if end_month == 12:
        end_date = datetime(year, 12, 31, 23, 59, 59)
    else:
        end_date = datetime(year, end_month + 1, 1) - timedelta(seconds=1)

    return {"quarter": quarter, "start_date": start_date, "end_date": end_date}


# 便捷函数别名
formatdate = format_date
gettimeago = get_time_ago
issameday = is_same_day
getdaterange = get_date_range
addtime = add_time
datediff = date_diff
getfirstdayofmonth = get_first_day_of_month
getlastdayofmonth = get_last_day_of_month
isleapyear = is_leap_year
getquarterinfo = get_quarter_info
