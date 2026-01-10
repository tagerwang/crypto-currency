#!/usr/bin/env python3
"""
工具函数 - 格式化、转换等辅助功能
"""

from typing import Any
from datetime import datetime


def format_number(num: float, decimals: int = 2) -> str:
    """格式化数字显示"""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.{decimals}f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.{decimals}f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.{decimals}f}K"
    return f"{num:.{decimals}f}"


def timestamp_to_datetime(ts: int) -> str:
    """时间戳转日期时间字符串"""
    return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S")


def safe_float(value: Any, default: float = 0.0) -> float:
    """安全转换为浮点数"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def calculate_time_remaining(end_time_str: str) -> str:
    """计算剩余时间"""
    try:
        end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        
        if end_time < now:
            return "已结束"
        
        delta = end_time - now
        days = delta.days
        hours = delta.seconds // 3600
        
        if days > 0:
            return f"{days}天{hours}小时"
        elif hours > 0:
            minutes = (delta.seconds % 3600) // 60
            return f"{hours}小时{minutes}分钟"
        else:
            minutes = delta.seconds // 60
            return f"{minutes}分钟"
    except:
        return "未知"


