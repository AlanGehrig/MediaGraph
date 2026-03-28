"""
日志配置模块
"""
import sys
import logging
from pathlib import Path
from loguru import logger


def setup_logging(
    level: str = "INFO",
    log_file: str = None,
    rotation: str = "10 MB",
    retention: str = "7 days"
):
    """
    配置日志系统
    
    Args:
        level: 日志级别
        log_file: 日志文件路径
        rotation: 日志轮转大小
        retention: 日志保留时间
    """
    # 移除默认处理器
    logger.remove()
    
    # 添加控制台处理器
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )
    
    # 添加文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            rotation=rotation,
            retention=retention,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=level,
            compression="zip"
        )
    
    return logger


def get_logger(name: str = None):
    """获取日志记录器"""
    if name:
        return logger.bind(name=name)
    return logger
