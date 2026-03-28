"""
验证器模块
"""
import re
from typing import Optional
from pathlib import Path


def validate_media_path(path: str) -> bool:
    """验证媒体路径"""
    if not path:
        return False
    
    p = Path(path)
    
    # 检查扩展名
    valid_exts = {
        'jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp', 'tif', 'tiff',
        'raf', 'arw', 'dng', 'cr2', 'nef',
        'mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv', 'webm', 'm4v'
    }
    
    if p.suffix.lower().lstrip('.') not in valid_exts:
        return False
    
    return True


def validate_person_name(name: str) -> bool:
    """验证人物名称"""
    if not name or len(name) > 100:
        return False
    
    # 允许中文、英文、日文、数字、空格
    pattern = r'^[\w\s\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+$'
    return bool(re.match(pattern, name))


def validate_search_query(query: str) -> bool:
    """验证搜索查询"""
    if not query or len(query) > 500:
        return False
    return True


def validate_cluster_threshold(threshold: float) -> bool:
    """验证聚类阈值"""
    return 0.3 <= threshold <= 0.95


def validate_page_params(page: int, page_size: int) -> tuple:
    """验证分页参数"""
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    return page, page_size


def sanitize_sql_input(text: str) -> str:
    """清理SQL输入"""
    if not text:
        return ""
    
    # 移除可能的SQL注入字符
    dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
    
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()
