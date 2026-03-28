"""
自然语言搜索 API
将自然语言查询转换为向量相似度搜索和图数据库查询
"""
import time
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.schemas import SearchResponse, SearchResult, MediaType
from database.vector_store import VectorStore
from database.kg_builder import KGBuilder
from ai_core.media_parser import MediaParser
from config.loader import load_config


router = APIRouter()

# 自然语言到Cypher查询的转换规则
NL_TO_CYPHER_RULES = [
    # 人物相关
    (r"(?:有|包含|出现).{0,10}?(person|人|人物|某人)", "PERSON"),
    (r"(.+)的照片", "PERSON=$1"),
    (r"(.+)的影像", "PERSON=$1"),
    
    # 时间相关
    (r"去年|去年夏天|去年冬天", "TIME=<2024-01-01"),
    (r"今年|今年夏天|今年冬天", "TIME>=2024-01-01"),
    (r"(\d{4})年", "TIME contains $1"),
    (r"(\d{1,2})月", "TIME contains $1"),
    
    # 地点相关
    (r"在(.+)拍", "LOCATION contains $1"),
    (r"(.+)拍摄", "LOCATION contains $1"),
    (r"去(.+)玩", "LOCATION contains $1"),
    
    # 情绪/氛围
    (r"开心|快乐|高兴|愉快的", "mood contains 'happy'"),
    (r"悲伤|难过|忧伤的", "mood contains 'sad'"),
    (r"浪漫的?", "mood contains 'romantic'"),
    
    # 光线
    (r"逆光|背光", "lighting contains 'backlight'"),
    (r"柔光|柔和", "lighting contains 'soft'"),
    (r"硬光|强烈", "lighting contains 'hard'"),
    (r"夜景|晚上", "lighting contains 'night'"),
    
    # 场景
    (r"海边|海洋|沙滩|海滩", "scene contains 'beach'"),
    (r"室内|房间|屋内", "scene contains 'indoor'"),
    (r"户外|室外|外面", "scene contains 'outdoor'"),
    (r"城市|街头|都市", "scene contains 'urban'"),
    (r"自然|森林|树林|山里", "scene contains 'nature'"),
    
    # 构图
    (r"特写|近拍|大头", "composition contains 'close-up'"),
    (r"全身|长镜头|远景", "composition contains 'full-body'"),
    (r"对称|居中", "composition contains 'centered'"),
    (r"三分法|黄金比例", "composition contains 'rule-of-thirds'"),
]

# 同义词映射
SYNONYM_MAP = {
    'beach': ['海边', '海洋', '沙滩', '海滩', ' seaside', 'coast'],
    'indoor': ['室内', '房间', '屋内', ' inside', 'home'],
    'outdoor': ['户外', '室外', '外面', 'outside', 'exterior'],
    'urban': ['城市', '街头', '都市', 'city', 'street'],
    'nature': ['自然', '森林', '树林', '山里', '森林', 'mountain'],
    'happy': ['开心', '快乐', '高兴', '愉快的', 'joyful'],
    'sad': ['悲伤', '难过', '忧伤的', 'sorrowful'],
    'romantic': ['浪漫的', 'love', 'couple'],
}


def parse_nl_query(query: str) -> dict:
    """
    将自然语言查询解析为结构化查询参数
    返回: {type: 'vector'|'cypher'|'hybrid', params: {...}}
    """
    query_lower = query.lower().strip()
    
    result = {
        'original_query': query,
        'scene': [],
        'mood': [],
        'lighting': [],
        'person': None,
        'location': None,
        'time_range': None,
        'tags': []
    }
    
    # 场景检测
    for scene_key, synonyms in SYNONYM_MAP.items():
        for syn in synonyms:
            if syn in query_lower:
                result['scene'].append(scene_key)
                break
    
    # 情绪检测
    mood_synonyms = {
        'happy': ['开心', '快乐', '高兴', '笑'],
        'sad': ['悲伤', '难过', '哭'],
        'romantic': ['浪漫', '甜蜜'],
        'dramatic': ['戏剧性', '张力'],
    }
    for mood, synonyms in mood_synonyms.items():
        for syn in synonyms:
            if syn in query_lower:
                result['mood'].append(mood)
                break
    
    # 光线检测
    lighting_synonyms = {
        'backlight': ['逆光', '背光', '轮廓光'],
        'soft': ['柔光', '柔和', '散射光'],
        'hard': ['硬光', '强烈', '直射光'],
        'golden': ['黄金时刻', '金色', '夕阳'],
        'blue': ['蓝色时刻', '蓝调', '夜景'],
    }
    for light, synonyms in lighting_synonyms.items():
        for syn in synonyms:
            if syn in query_lower:
                result['lighting'].append(light)
                break
    
    # 人物检测 (简单模式匹配)
    import re
    person_patterns = [
        r'([A-Za-z]+)的照片',
        r'([A-Za-z]+)的影像',
        r'包含(.+)的照片',
        r'有(.+)的照片',
    ]
    for pattern in person_patterns:
        match = re.search(pattern, query)
        if match:
            result['person'] = match.group(1)
            break
    
    # 地点检测
    location_patterns = [
        r'在(.+?)拍',
        r'去(.+?)玩',
        r'(.+)拍摄',
    ]
    for pattern in location_patterns:
        match = re.search(pattern, query)
        if match:
            result['location'] = match.group(1)
            break
    
    # 判断查询类型
    if result['scene'] or result['mood'] or result['lighting'] or result['person'] or result['location']:
        result['type'] = 'hybrid'
    else:
        result['type'] = 'vector'
    
    return result


@router.get("", response_model=SearchResponse)
async def search_media(
    q: str = Query(..., description="自然语言搜索查询", min_length=1),
    top_k: int = Query(10, ge=1, le=100, description="返回结果数量"),
    media_type: Optional[str] = Query(None, description="媒体类型过滤")
):
    """
    自然语言搜索媒体文件
    
    示例查询:
    - "去年夏天在海边的照片"
    - "逆光人像"
    - "开心的照片"
    - "城市夜景"
    """
    start_time = time.time()
    
    try:
        config = load_config()
        
        # 解析自然语言查询
        parsed_query = parse_nl_query(q)
        logger.info(f"解析查询: {parsed_query}")
        
        results = []
        
        # 1. 向量相似度搜索
        try:
            vector_store = VectorStore(persist_dir=config['chroma']['persist_dir'])
            vector_results = vector_store.search(q, top_k=top_k * 2)
            
            for vr in vector_results:
                results.append(SearchResult(
                    media_id=vr.get('media_id', ''),
                    path=vr.get('path', ''),
                    filename=vr.get('filename', ''),
                    media_type=MediaType.IMAGE if vr.get('type') == 'image' else MediaType.VIDEO,
                    similarity=vr.get('similarity', 0),
                    snippet=vr.get('snippet', ''),
                    highlight=vr.get('highlight', '')
                ))
        except Exception as e:
            logger.warning(f"向量搜索失败: {e}")
        
        # 2. 如果有结构化参数，查询Neo4j
        if parsed_query['type'] == 'hybrid':
            try:
                kg_builder = KGBuilder(
                    uri=config['neo4j']['uri'],
                    user=config['neo4j']['user'],
                    password=config['neo4j']['password']
                )
                
                # 构建Cypher查询
                cypher_results = kg_builder.query_by_nl(parsed_query)
                
                # 合并结果
                existing_ids = {r.media_id for r in results}
                for cr in cypher_results:
                    if cr['media_id'] not in existing_ids:
                        results.append(SearchResult(
                            media_id=cr['media_id'],
                            path=cr.get('path', ''),
                            filename=cr.get('filename', ''),
                            media_type=MediaType.IMAGE if cr.get('type') == 'image' else MediaType.VIDEO,
                            similarity=cr.get('similarity', 0.5),
                            snippet=cr.get('snippet', ''),
                            highlight=cr.get('highlight', '')
                        ))
                
                kg_builder.close()
            except Exception as e:
                logger.warning(f"图数据库搜索失败: {e}")
        
        # 3. 类型过滤
        if media_type:
            results = [r for r in results if r.media_type.value == media_type]
        
        # 4. 排序并限制数量
        results.sort(key=lambda x: x.similarity, reverse=True)
        results = results[:top_k]
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return SearchResponse(
            query=q,
            total=len(results),
            results=results,
            time_ms=round(elapsed_ms, 2)
        )
        
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., description="搜索前缀")
):
    """获取搜索建议"""
    suggestions = [
        "去年夏天的海边照片",
        "逆光人像",
        "室内柔光",
        "城市夜景",
        "自然风光",
        "开心的人",
        "黄金时刻",
    ]
    
    q_lower = q.lower()
    filtered = [s for s in suggestions if q_lower in s.lower()]
    
    return {"suggestions": filtered[:5]}
