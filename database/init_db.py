"""
数据库初始化模块
初始化 Neo4j 和 Chroma 数据库
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from database.kg_builder import KGBuilder
from database.vector_store import VectorStore
from config.loader import load_config


def init_neo4j():
    """初始化 Neo4j 数据库"""
    logger.info("🔧 初始化 Neo4j 数据库...")
    
    config = load_config()
    neo4j_config = config['neo4j']
    
    try:
        kg = KGBuilder(
            uri=neo4j_config['uri'],
            user=neo4j_config['user'],
            password=neo4j_config['password']
        )
        
        # 创建约束和索引
        with kg._get_session() as session:
            # 媒体节点唯一约束
            session.run("""
                CREATE CONSTRAINT media_id IF NOT EXISTS
                FOR (m:Media) REQUIRE m.media_id IS UNIQUE
            """)
            
            # 人物节点唯一约束
            session.run("""
                CREATE CONSTRAINT person_id IF NOT EXISTS
                FOR (p:Person) REQUIRE p.person_id IS UNIQUE
            """)
            
            # 地点节点唯一约束
            session.run("""
                CREATE CONSTRAINT location_id IF NOT EXISTS
                FOR (l:Location) REQUIRE l.location_id IS UNIQUE
            """)
            
            # 创建索引
            session.run("CREATE INDEX media_scene IF NOT EXISTS FOR (m:Media) ON (m.scene)")
            session.run("CREATE INDEX media_mood IF NOT EXISTS FOR (m:Media) ON (m.mood)")
            session.run("CREATE INDEX media_lighting IF NOT EXISTS FOR (m:Media) ON (m.lighting)")
            session.run("CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name)")
            session.run("CREATE INDEX time_date IF NOT EXISTS FOR (t:Time) ON (t.date)")
            
            logger.info("✅ Neo4j 索引创建成功")
        
        kg.close()
        logger.info("✅ Neo4j 初始化完成")
        
    except Exception as e:
        logger.error(f"❌ Neo4j 初始化失败: {e}")
        raise


def init_chroma():
    """初始化 Chroma 数据库"""
    logger.info("🔧 初始化 Chroma 数据库...")
    
    config = load_config()
    chroma_config = config['chroma']
    
    try:
        vector_store = VectorStore(persist_dir=chroma_config['persist_dir'])
        
        # Chroma会自动创建集合，这里只是验证
        count = vector_store.count()
        logger.info(f"📊 Chroma 向量数量: {count}")
        
        vector_store.save()
        logger.info("✅ Chroma 初始化完成")
        
    except Exception as e:
        logger.error(f"❌ Chroma 初始化失败: {e}")
        raise


def init_all():
    """初始化所有数据库"""
    logger.info("=" * 50)
    logger.info("🚀 MediaGraph 数据库初始化")
    logger.info("=" * 50)
    
    try:
        init_neo4j()
        init_chroma()
        
        logger.info("=" * 50)
        logger.info("✅ 所有数据库初始化完成!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        raise


if __name__ == "__main__":
    init_all()
