"""
中间件模块
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class TimingMiddleware(BaseHTTPMiddleware):
    """请求计时中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)"
        )
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        logger.debug(f"Request: {request.method} {request.url}")
        
        response = await call_next(request)
        
        logger.debug(f"Response: {response.status_code}")
        
        return response
