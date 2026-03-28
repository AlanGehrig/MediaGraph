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
from config.loader import load_config


# 全局实例
kg_builder = None
vector_store = None
config = None


def check_neo4j_connection():
    """检查 Neo4j 连接状态"""
    global kg_builder
    if kg_builder is None:
        return False
    try:
        if kg_builder.driver is None:
            return False
        with kg_builder.driver.session() as session:
            result = session.run("RETURN 1")
            result.single()
        return True
    except Exception:
        return False


def check_chroma_connection():
    """检查 Chroma 连接状态"""
    global vector_store
    if vector_store is None:
        return False
    try:
        if vector_store.collection is None:
            return False
        vector_store.collection.count()
        return True
    except Exception:
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global kg_builder, vector_store, config
    
    logger.info("🚀 MediaGraph 启动中...")
    
    # 加载配置
    config = load_config()
    logger.info(f"📁 配置加载完成: {config.get('api', {}).get('backend_port', 8000)} 端口")
    
    # 初始化 Neo4j 连接
    try:
        neo4j_config = config.get('neo4j', {})
        uri = neo4j_config.get('uri', 'bolt://localhost:7687')
        user = neo4j_config.get('user', 'neo4j')
        password = neo4j_config.get('password', 'password123')
        
        logger.info(f"🔌 连接 Neo4j: {uri}")
        kg_builder = KGBuilder(uri=uri, user=user, password=password)
        
        if kg_builder.driver is not None:
            # 创建必要的索引
            _create_neo4j_indexes()
            logger.info("✅ Neo4j 连接成功")
        else:
            logger.warning("⚠️ Neo4j 未连接，将使用模拟模式")
            
    except Exception as e:
        logger.error(f"❌ Neo4j 连接失败: {e}")
        kg_builder = None
    
    # 初始化 Chroma 向量存储
    try:
        chroma_config = config.get('chroma', {})
        persist_dir = chroma_config.get('persist_dir', 'E:/openclaw/data/MediaGraph/data/chroma')
        
        logger.info(f"📦 初始化 Chroma: {persist_dir}")
        vector_store = VectorStore(persist_dir=persist_dir)
        
        if vector_store.collection is not None:
            logger.info("✅ Chroma 向量存储初始化成功")
        else:
            logger.warning("⚠️ Chroma 未连接，将使用模拟模式")
            
    except Exception as e:
        logger.error(f"❌ Chroma 初始化失败: {e}")
        vector_store = None
    
    # 初始化 AI 模型配置
    try:
        from ai_core.model_config import ModelConfig
        model_config = ModelConfig()
        logger.info(f"✅ AI 模型配置加载成功 (设备: {model_config.clip_device})")
    except Exception as e:
        logger.error(f"❌ AI 模型配置加载失败: {e}")
    
    logger.info("🎬 MediaGraph 启动完成!")
    
    yield
    
    # 关闭连接
    logger.info("🛑 MediaGraph 关闭中...")
    if kg_builder is not None:
        kg_builder.close()
        logger.info("👋 Neo4j 连接已关闭")
    
    if vector_store is not None:
        try:
            vector_store.save()
            logger.info("👋 Chroma 数据已保存")
        except Exception as e:
            logger.error(f"Chroma 保存失败: {e}")
    
    logger.info("👋 MediaGraph 已关闭")


def _create_neo4j_indexes():
    """在 Neo4j 中创建必要的索引"""
    global kg_builder
    if kg_builder is None or kg_builder.driver is None:
        return
    
    try:
        from neo4j import GraphDatabase
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (m:Media) ON (m.media_id)",
            "CREATE INDEX IF NOT EXISTS FOR (m:Media) ON (m.path)",
            "CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.person_id)",
            "CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.name)",
            "CREATE INDEX IF NOT EXISTS FOR (l:Location) ON (l.location_id)",
            "CREATE INDEX IF NOT EXISTS FOR (t:Time) ON (t.time_id)",
            "CREATE INDEX IF NOT EXISTS FOR (t:Time) ON (t.date)",
        ]
        
        with kg_builder.driver.session() as session:
            for idx_query in indexes:
                try:
                    session.run(idx_query)
                except Exception as e:
                    # 索引可能已存在，忽略错误
                    logger.debug(f"索引创建: {e}")
        
        logger.info("✅ Neo4j 索引创建完成")
        
    except Exception as e:
        logger.warning(f"⚠️ Neo4j 索引创建失败: {e}")


# 延迟导入 KGBuilder 和 VectorStore（避免循环导入）
def _get_kg_builder():
    global kg_builder
    if kg_builder is None:
        try:
            from database.kg_builder import KGBuilder
            from config.loader import load_config
            cfg = load_config()
            neo4j_cfg = cfg.get('neo4j', {})
            kg_builder = KGBuilder(
                uri=neo4j_cfg.get('uri', 'bolt://localhost:7687'),
                user=neo4j_cfg.get('user', 'neo4j'),
                password=neo4j_cfg.get('password', 'password123')
            )
        except Exception as e:
            logger.error(f"KGBuilder 初始化失败: {e}")
    return kg_builder


def _get_vector_store():
    global vector_store
    if vector_store is None:
        try:
            from database.vector_store import VectorStore
            from config.loader import load_config
            cfg = load_config()
            chroma_cfg = cfg.get('chroma', {})
            vector_store = VectorStore(persist_dir=chroma_cfg.get('persist_dir', 'E:/openclaw/data/MediaGraph/data/chroma'))
        except Exception as e:
            logger.error(f"VectorStore 初始化失败: {e}")
    return vector_store


# 导入 KGBuilder 和 VectorStore 以便在路由中使用
try:
    from database.kg_builder import KGBuilder
    from database.vector_store import VectorStore
except ImportError as e:
    logger.error(f"数据库模块导入失败: {e}")
    KGBuilder = None
    VectorStore = None


# 创建 FastAPI 应用
app = FastAPI(
    title="MediaGraph API",
    description="摄影师个人影像知识图谱系统 - 用自然语言搜索你的所有照片和视频",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
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
    """健康检查接口 - 检查 Neo4j 和 Chroma 连接状态"""
    neo4j_ok = check_neo4j_connection()
    chroma_ok = check_chroma_connection()
    
    status = "healthy" if (neo4j_ok and chroma_ok) else "degraded"
    
    return HealthResponse(
        status=status,
        neo4j="connected" if neo4j_ok else "disconnected",
        chroma="connected" if chroma_ok else "disconnected",
        version="1.0.0"
    )


@app.get("/health", tags=["系统"])
async def simple_health_check():
    """简化健康检查（供负载均衡器使用）"""
    neo4j_ok = check_neo4j_connection()
    chroma_ok = check_chroma_connection()
    
    return {
        "status": "healthy" if (neo4j_ok and chroma_ok) else "degraded",
        "neo4j": "connected" if neo4j_ok else "disconnected",
        "chroma": "connected" if chroma_ok else "disconnected"
    }


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
    # 获取端口配置
    port = 8000
    if config is not None:
        port = config.get('api', {}).get('backend_port', 8000)
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
