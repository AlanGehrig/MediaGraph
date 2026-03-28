"""
数据统计 API
提供系统整体数据统计和分析功能
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.schemas import StatsOverview
from database.kg_builder import KGBuilder
from config.loader import load_config


router = APIRouter()


def get_kg_builder() -> KGBuilder:
    config = load_config()
    neo4j_config = config['neo4j']
    return KGBuilder(
        uri=neo4j_config['uri'],
        user=neo4j_config['user'],
        password=neo4j_config['password']
    )


@router.get("/overview", response_model=StatsOverview)
async def get_stats_overview():
    """
    获取数据统计概览
    包括媒体数量、人脸数量、地点数量等核心指标
    """
    try:
        config = load_config()
        
        # 从Neo4j获取图谱统计
        kg = get_kg_builder()
        graph_stats = kg.get_graph_stats()
        kg.close()
        
        # 媒体统计 (从配置和扫描路径估算)
        media_stats = get_media_stats()
        
        return StatsOverview(
            total_media=graph_stats.get('total_media', media_stats['total']),
            total_images=media_stats.get('images', 0),
            total_videos=media_stats.get('videos', 0),
            total_persons=graph_stats.get('total_persons', 0),
            total_faces=graph_stats.get('total_faces', 0),
            total_locations=graph_stats.get('total_locations', 0),
            total_tags=graph_stats.get('total_tags', 0),
            parse_completed=media_stats.get('parsed', 0),
            parse_pending=media_stats.get('pending', 0),
            storage_size_gb=media_stats.get('storage_gb', 0.0),
            db_stats=graph_stats
        )
        
    except Exception as e:
        logger.error(f"获取统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


def get_media_stats() -> dict:
    """获取媒体统计信息"""
    # 这里应该从数据库读取，实际从配置估算
    config = load_config()
    scan_paths = config['media']['scan_paths']
    
    total = 0
    images = 0
    videos = 0
    storage_gb = 0.0
    parsed = 0
    pending = 0
    
    import os
    extensions = config['media']['supported_formats']
    
    for path in scan_paths:
        if not os.path.exists(path):
            continue
        
        for root, dirs, files in os.walk(path):
            for f in files:
                ext = f.split('.')[-1].lower() if '.' in f else ''
                if ext in extensions:
                    total += 1
                    file_path = os.path.join(root, f)
                    try:
                        size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        storage_gb += size_mb / 1024
                        if ext in ['jpg', 'jpeg', 'png', 'webp', 'tif', 'bmp']:
                            images += 1
                        else:
                            videos += 1
                    except:
                        pass
    
    return {
        'total': total,
        'images': images,
        'videos': videos,
        'storage_gb': round(storage_gb, 2),
        'parsed': int(parsed),
        'pending': total - parsed
    }


@router.get("/timeline")
async def get_media_timeline_stats(
    granularity: str = Query("month", description="时间粒度: day/week/month/year")
):
    """
    获取媒体时间分布统计
    """
    try:
        kg = get_kg_builder()
        timeline = kg.get_timeline(granularity=granularity)
        kg.close()
        
        return {
            "granularity": granularity,
            "data": timeline
        }
        
    except Exception as e:
        logger.error(f"获取时间线统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取时间线统计失败: {str(e)}")


@router.get("/scenes")
async def get_scene_distribution():
    """
    获取场景分布统计
    """
    try:
        kg = get_kg_builder()
        scenes = kg.get_scene_distribution()
        kg.close()
        
        return {
            "total_scenes": len(scenes),
            "scenes": scenes
        }
        
    except Exception as e:
        logger.error(f"获取场景分布失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取场景分布失败: {str(e)}")


@router.get("/tags")
async def get_tag_stats(
    limit: int = Query(50, ge=1, le=200, description="返回数量")
):
    """
    获取标签统计
    按使用频率排序
    """
    try:
        kg = get_kg_builder()
        tags = kg.get_tag_stats(limit=limit)
        kg.close()
        
        return {
            "total": len(tags),
            "tags": tags
        }
        
    except Exception as e:
        logger.error(f"获取标签统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取标签统计失败: {str(e)}")


@router.get("/mood")
async def get_mood_distribution():
    """
    获取情绪/氛围分布统计
    """
    try:
        kg = get_kg_builder()
        moods = kg.get_mood_distribution()
        kg.close()
        
        return {
            "total_moods": len(moods),
            "moods": moods
        }
        
    except Exception as e:
        logger.error(f"获取情绪分布失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取情绪分布失败: {str(e)}")


@router.get("/persons/top")
async def get_top_persons(
    limit: int = Query(10, ge=1, le=50, description="返回数量")
):
    """
    获取出现频率最高的人物
    """
    try:
        kg = get_kg_builder()
        persons = kg.get_all_persons(min_media_count=2)
        persons.sort(key=lambda x: x.get('media_count', 0), reverse=True)
        persons = persons[:limit]
        kg.close()
        
        return {
            "total": len(persons),
            "persons": persons
        }
        
    except Exception as e:
        logger.error(f"获取热门人物失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取热门人物失败: {str(e)}")


@router.get("/locations/top")
async def get_top_locations(
    limit: int = Query(10, ge=1, le=50, description="返回数量")
):
    """
    获取出现频率最高的地点
    """
    try:
        kg = get_kg_builder()
        locations = kg.get_all_locations(min_count=2)
        locations.sort(key=lambda x: x.get('media_count', 0), reverse=True)
        locations = locations[:limit]
        kg.close()
        
        return {
            "total": len(locations),
            "locations": locations
        }
        
    except Exception as e:
        logger.error(f"获取热门地点失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取热门地点失败: {str(e)}")
