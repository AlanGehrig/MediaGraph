"""
异常处理模块
"""
from typing import Optional, Any, Dict
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from loguru import logger


class MediaGraphException(Exception):
    """MediaGraph基础异常"""
    
    def __init__(self, message: str, code: str = "MEDIAGRAPH_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class MediaNotFoundException(MediaGraphException):
    """媒体文件未找到"""
    
    def __init__(self, media_id: str):
        super().__init__(
            message=f"媒体文件未找到: {media_id}",
            code="MEDIA_NOT_FOUND"
        )


class PersonNotFoundException(MediaGraphException):
    """人物未找到"""
    
    def __init__(self, person_id: str):
        super().__init__(
            message=f"人物未找到: {person_id}",
            code="PERSON_NOT_FOUND"
        )


class DatabaseConnectionException(MediaGraphException):
    """数据库连接异常"""
    
    def __init__(self, db_type: str, details: str = ""):
        super().__init__(
            message=f"{db_type}连接失败: {details}",
            code="DB_CONNECTION_ERROR"
        )


class ModelLoadException(MediaGraphException):
    """模型加载异常"""
    
    def __init__(self, model_name: str, details: str = ""):
        super().__init__(
            message=f"模型加载失败 [{model_name}]: {details}",
            code="MODEL_LOAD_ERROR"
        )


class ParseException(MediaGraphException):
    """解析异常"""
    
    def __init__(self, media_id: str, details: str = ""):
        super().__init__(
            message=f"媒体解析失败 [{media_id}]: {details}",
            code="PARSE_ERROR"
        )


async def media_graph_exception_handler(
    request: Request,
    exc: MediaGraphException
) -> JSONResponse:
    """MediaGraph异常处理器"""
    logger.error(f"MediaGraphException: {exc.code} - {exc.message}")
    
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.code,
            "message": exc.message,
            "path": str(request.url)
        }
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "path": str(request.url)
        }
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """通用异常处理器"""
    logger.exception(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "服务器内部错误",
            "path": str(request.url)
        }
    )
