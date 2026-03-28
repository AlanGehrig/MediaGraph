"""
知识图谱 API
提供人物、时间线、地点等图谱查询功能
"""
from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.schemas import (
    GraphPersonsResponse, GraphTimelineResponse, PersonNode, TimelineNode
)
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


@router.get("/persons", response_model=GraphPersonsResponse)
async def get_persons(
    min_media_count: int = Query(1, ge=1, description="最少出现媒体数")
):
    """
    获取所有人物节点
    按出现媒体数排序
    """
    try:
        kg = get_kg_builder()
        persons_data = kg.get_all_persons(min_media_count=min_media_count)
        
        persons = [
            PersonNode(
                id=p['id'],
                name=p['name'],
                face_count=p.get('face_count', 0),
                media_count=p.get('media_count', 0),
                thumbnail=p.get('thumbnail'),
                metadata=p.get('metadata', {})
            )
            for p in persons_data
        ]
        
        kg.close()
        
        return GraphPersonsResponse(
            total=len(persons),
            persons=persons
        )
        
    except Exception as e:
        logger.error(f"获取人物列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取人物列表失败: {str(e)}")


@router.get("/persons/{person_id}")
async def get_person_detail(person_id: str):
    """
    获取人物详情
    包括该人物的所有媒体、出现时间线等信息
    """
    try:
        kg = get_kg_builder()
        detail = kg.get_person_detail(person_id)
        kg.close()
        
        if not detail:
            raise HTTPException(status_code=404, detail="人物不存在")
        
        return detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取人物详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取人物详情失败: {str(e)}")


@router.get("/persons/{person_id}/media")
async def get_person_media(
    person_id: str,
    limit: int = Query(50, ge=1, le=200, description="返回数量")
):
    """
    获取某人物的所有媒体
    """
    try:
        kg = get_kg_builder()
        media_list = kg.get_person_media(person_id, limit=limit)
        kg.close()
        
        return {
            "person_id": person_id,
            "total": len(media_list),
            "media": media_list
        }
        
    except Exception as e:
        logger.error(f"获取人物媒体失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取人物媒体失败: {str(e)}")


@router.get("/timeline", response_model=GraphTimelineResponse)
async def get_timeline(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    granularity: str = Query("day", description="时间粒度: day/month/year")
):
    """
    获取媒体时间线
    按日期聚合显示媒体分布
    """
    try:
        kg = get_kg_builder()
        timeline_data = kg.get_timeline(start_date, end_date, granularity)
        kg.close()
        
        timeline = [
            TimelineNode(
                date=t['date'],
                count=t['count'],
                media_ids=t.get('media_ids', [])
            )
            for t in timeline_data
        ]
        
        return GraphTimelineResponse(
            total=len(timeline),
            timeline=timeline
        )
        
    except Exception as e:
        logger.error(f"获取时间线失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取时间线失败: {str(e)}")


@router.get("/locations")
async def get_locations(
    min_count: int = Query(1, ge=1, description="最少媒体数")
):
    """
    获取所有地点节点
    """
    try:
        kg = get_kg_builder()
        locations = kg.get_all_locations(min_count=min_count)
        kg.close()
        
        return {
            "total": len(locations),
            "locations": locations
        }
        
    except Exception as e:
        logger.error(f"获取地点列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取地点列表失败: {str(e)}")


@router.get("/locations/{location_id}/media")
async def get_location_media(
    location_id: str,
    limit: int = Query(50, ge=1, le=200)
):
    """
    获取某地点的所有媒体
    """
    try:
        kg = get_kg_builder()
        media_list = kg.get_location_media(location_id, limit=limit)
        kg.close()
        
        return {
            "location_id": location_id,
            "total": len(media_list),
            "media": media_list
        }
        
    except Exception as e:
        logger.error(f"获取地点媒体失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取地点媒体失败: {str(e)}")


@router.get("/relations")
async def get_relations(
    media_id: Optional[str] = Query(None, description="媒体ID(可选)"),
    person_id: Optional[str] = Query(None, description="人物ID(可选)"),
    max_depth: int = Query(2, ge=1, le=5, description="关系深度")
):
    """
    获取关系网络
    可指定某个媒体或人物为中心查看关联
    """
    try:
        kg = get_kg_builder()
        relations = kg.get_relations(
            center_id=media_id or person_id,
            center_type='media' if media_id else 'person',
            max_depth=max_depth
        )
        kg.close()
        
        return relations
        
    except Exception as e:
        logger.error(f"获取关系失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取关系失败: {str(e)}")


@router.get("/stats")
async def get_graph_stats():
    """
    获取图谱统计信息
    节点数、边数、关系类型分布等
    """
    try:
        kg = get_kg_builder()
        stats = kg.get_graph_stats()
        kg.close()
        
        return stats
        
    except Exception as e:
        logger.error(f"获取图谱统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取图谱统计失败: {str(e)}")
