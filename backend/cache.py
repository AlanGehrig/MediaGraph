"""
缓存管理模块
"""
import json
import time
from typing import Any, Optional, Callable
from functools import wraps
from cachetools import TTLCache
from loguru import logger


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, maxsize: int = 1000, ttl: int = 3600):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        return self.cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存"""
        if ttl:
            self.cache[key] = value
        else:
            self.cache[key] = value
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
    
    def has(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self.cache
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)


def cached(cache: CacheManager, ttl: Optional[int] = None):
    """缓存装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试获取缓存
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


# 全局缓存实例
global_cache = CacheManager(maxsize=500, ttl=1800)
