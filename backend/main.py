"""
MediaGraph - 摄影师个人影像知识图谱系统
FastAPI 主入口
"""
import os
import sys
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.api import media, search, graph, face, stats
from backend.models.schemas import HealthResponse, ScanRequest
from database.kg_builder import KGBuilder
from database.vector_store import VectorStore
from ai_core.model_config import ModelConfig
from config.loader import load_config


# 全局实例
kg_builder: KGBuilder = None
vector_store: VectorStore = None
config: dict = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global kg_builder, vector_store, config
    
    logger.info("🚀 MediaGraph 启动中...")
    
    # 加载配置
    config = load_config()
    logger.info(f"📁 配置加载完成: {config['api']['backend_port']}端口")
    
    # 初始化Neo4j连接
    try:
        neo4j_config = config['neo4j']
        kg_builder = KGBuilder(
            uri=neo4j_config['uri'],
            user=neo4j_config['user'],
            password=neo4j_config['password']
        )
        logger.info("✅ Neo4j 连接成功")
    except Exception as e:
        logger.error(f"❌ Neo4j 连接失败: {e}")
        kg_builder = None
    
    # 初始化Chroma向量存储
    try:
        chroma_config = config['chroma']
        vector_store = VectorStore(persist_dir=chroma_config['persist_dir'])
        logger.info("✅ Chroma 向量存储初始化成功")
    except Exception as e:
        logger.error(f"❌ Chroma 初始化失败: {e}")
        vector_store = None
    
    # 初始化AI模型
    try:
        model_config = ModelConfig()
        logger.info("✅ AI 模型配置加载成功")
    except Exception as e:
        logger.error(f"❌ AI 模型配置加载失败: {e}")
    
    logger.info("🎬 MediaGraph 启动完成!")
    
    yield
    
    # 关闭连接
    logger.info("🛑 MediaGraph 关闭中...")
    if kg_builder:
        kg_builder.close()
    logger.info("👋 MediaGraph 已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="MediaGraph API",
    description="摄影师个人影像知识图谱系统 - 用自然语言搜索你的所有照片和视频",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(media.router, prefix="/api/media", tags=["媒体管理"])
app.include_router(search.router, prefix="/api/search", tags=["搜索"])
app.include_router(graph.router, prefix="/api/graph", tags=["知识图谱"])
app.include_router(face.router, prefix="/api/face", tags=["人脸聚类"])
app.include_router(stats.router, prefix="/api/stats", tags=["数据统计"])


@app.get("/api/health", response_model=HealthResponse, tags=["系统"])
async def health_check():
    """健康检查接口"""
    neo4j_status = "connected" if kg_builder else "disconnected"
    chroma_status = "connected" if vector_store else "disconnected"
    
    return HealthResponse(
        status="healthy" if (kg_builder and vector_store) else "degraded",
        neo4j=neo4j_status,
        chroma=chroma_status,
        version="1.0.0"
    )


@app.get("/", tags=["首页"])
async def root():
    """首页"""
    return {
        "name": "MediaGraph",
        "description": "摄影师个人影像知识图谱系统",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


# 挂载前端静态文件
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


if __name__ == "__main__":
    port = config['api']['backend_port'] if config else 8000
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
