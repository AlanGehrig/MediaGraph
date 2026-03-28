"""
日期时间处理工具
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import re


def parse_exif_datetime(date_str: str) -> Optional[datetime]:
    """解析EXIF日期时间格式"""
    formats = [
        '%Y:%m:%d %H:%M:%S',
        '%Y:%m:%d %H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def format_datetime(dt: datetime, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """格式化日期时间"""
    return dt.strftime(fmt)


def get_date_range(days: int = 30) -> Tuple[str, str]:
    """获取最近N天的日期范围"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


def parse_relative_date(date_str: str) -> Optional[datetime]:
    """解析相对日期"""
    now = datetime.now()
    
    patterns = {
        r'去年': 365,
        r'去年夏天': 180,
        r'去年冬天': 270,
        r'今年': 0,
        r'今年夏天': 90,
        r'今年冬天': 0,
        r'上个月': 30,
        r'这个月': 0,
        r'上周': 7,
        r'本周': 0,
        r'昨天': 1,
        r'今天': 0,
    }
    
    for pattern, days_ago in patterns.items():
        if pattern in date_str:
            if days_ago > 0:
                return now - timedelta(days=days_ago)
            return now
    
    return None


def extract_year_month(date_str: str) -> Tuple[Optional[int], Optional[int]]:
    """从字符串提取年月"""
    year_match = re.search(r'(\d{4})年', date_str)
    month_match = re.search(r'(\d{1,2})月', date_str)
    
    year = int(year_match.group(1)) if year_match else None
    month = int(month_match.group(1)) if month_match else None
    
    return year, month


def time_ago(dt: datetime) -> str:
    """返回相对时间描述"""
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years}年前"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months}个月前"
    elif diff.days > 0:
        return f"{diff.days}天前"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}小时前"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}分钟前"
    else:
        return "刚刚"
