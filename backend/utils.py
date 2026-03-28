"""
媒体处理工具函数
"""
import os
import hashlib
from pathlib import Path
from typing import Optional, Tuple


def get_file_hash(filepath: str, algorithm: str = 'md5') -> str:
    """计算文件哈希"""
    if algorithm == 'md5':
        hasher = hashlib.md5()
    elif algorithm == 'sha1':
        hasher = hashlib.sha1()
    else:
        hasher = hashlib.sha256()
    
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def format_duration(seconds: float) -> str:
    """格式化时长"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def get_media_type(filename: str) -> str:
    """根据扩展名判断媒体类型"""
    image_exts = {'jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp', 'tif', 'tiff', 'raf', 'arw', 'dng'}
    video_exts = {'mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv', 'webm', 'm4v'}
    
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if ext in image_exts:
        return 'image'
    elif ext in video_exts:
        return 'video'
    return 'unknown'


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def ensure_dir(dirpath: str) -> str:
    """确保目录存在"""
    path = Path(dirpath)
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def get_relative_path(filepath: str, base_dir: str) -> str:
    """获取相对路径"""
    try:
        return os.path.relpath(filepath, base_dir)
    except ValueError:
        return filepath
