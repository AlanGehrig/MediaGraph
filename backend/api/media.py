"""
媒体管理 API
处理素材上传、扫描、列表、解析等功能
"""
import os
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from loguru import logger

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.schemas import (
    MediaItem, MediaListResponse, MediaType, ParseStatus,
    ScanRequest, ParseResult, BatchParseRequest, BatchParseResponse
)
from ai_core.media_parser import MediaParser
from ai_core.face_cluster import FaceCluster
from scripts.scan_media import scan_directory, get_media_info, calculate_file_hash
from database.kg_builder import KGBuilder
from config.loader import load_config


router = APIRouter()

# 全局实例
media_parser: Optional[MediaParser] = None
face_cluster: Optional[FaceCluster] = None
media_db: dict = {}  # 简单的内存媒体数据库


def get_media_parser() -> MediaParser:
    global media_parser
    if media_parser is None:
        config = load_config()
        model_path = config.get('model', {}).get('clip_model_path', 'models/clip')
        media_parser = MediaParser(model_path)
    return media_parser


def get_face_cluster() -> FaceCluster:
    global face_cluster
    if face_cluster is None:
        face_cluster = FaceCluster()
    return face_cluster


def get_kg_builder() -> KGBuilder:
    config = load_config()
    neo4j_config = config['neo4j']
    return KGBuilder(
        uri=neo4j_config['uri'],
        user=neo4j_config['user'],
        password=neo4j_config['password']
    )


@router.post("/scan", response_model=dict)
async def scan_media(request: ScanRequest):
    """
    扫描本地素材目录
    递归扫描所有支持的媒体文件，提取EXIF信息，建立索引
    """
    try:
        config = load_config()
        scan_paths = request.paths if request.paths else config['media']['scan_paths']
        extensions = config['media']['supported_formats']
        
        all_media = []
        for path in scan_paths:
            if not os.path.exists(path):
                logger.warning(f"路径不存在: {path}")
                continue
                
            media_files = scan_directory(path, extensions, recursive=request.recursive)
            all_media.extend(media_files)
        
        # 去重
        seen_hashes = set()
        unique_media = []
        for media in all_media:
            file_hash = media.get('hash')
            if file_hash and file_hash not in seen_hashes:
                seen_hashes.add(file_hash)
                unique_media.append(media)
        
        # 存入内存数据库
        new_count = 0
        for media in unique_media:
            media_id = media.get('hash', media['path'])
            if media_id not in media_db:
                media_db[media_id] = {
                    'id': media_id,
                    'path': media['path'],
                    'filename': os.path.basename(media['path']),
                    'media_type': MediaType.VIDEO if media['is_video'] else MediaType.IMAGE,
                    'size': media.get('size', 0),
                    'width': media.get('width'),
                    'height': media.get('height'),
                    'duration': media.get('duration'),
                    'created_at': media.get('created_at'),
                    'modified_at': media.get('modified_at'),
                    'parse_status': ParseStatus.PENDING,
                    'parse_result': None,
                    'thumbnail': None,
                    'exif': media.get('exif', {})
                }
                new_count += 1
        
        return {
            "status": "success",
            "total_found": len(unique_media),
            "new_added": new_count,
            "total_in_db": len(media_db),
            "scanned_paths": scan_paths
        }
        
    except Exception as e:
        logger.error(f"扫描失败: {e}")
        raise HTTPException(status_code=500, detail=f"扫描失败: {str(e)}")


@router.get("/list", response_model=MediaListResponse)
async def list_media(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    media_type: Optional[str] = Query(None, description="媒体类型过滤: image/video"),
    parse_status: Optional[str] = Query(None, description="解析状态过滤")
):
    """
    获取媒体文件列表
    支持分页和过滤
    """
    try:
        items = list(media_db.values())
        
        # 过滤
        if media_type:
            items = [m for m in items if m['media_type'].value == media_type]
        if parse_status:
            items = [m for m in items if m['parse_status'].value == parse_status]
        
        # 排序(按修改时间倒序)
        items.sort(key=lambda x: x.get('modified_at', ''), reverse=True)
        
        # 分页
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = items[start:end]
        
        return MediaListResponse(
            total=total,
            items=[MediaItem(**m) for m in page_items],
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"获取列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")


@router.get("/{media_id}", response_model=MediaItem)
async def get_media(media_id: str):
    """获取单个媒体文件详情"""
    if media_id not in media_db:
        raise HTTPException(status_code=404, detail="媒体文件不存在")
    return MediaItem(**media_db[media_id])


@router.post("/{media_id}/parse", response_model=ParseResult)
async def parse_single_media(media_id: str, background_tasks: BackgroundTasks):
    """
    AI解析单个媒体文件
    使用CLIP提取场景、物体、情绪、光线、构图等信息
    """
    if media_id not in media_db:
        raise HTTPException(status_code=404, detail="媒体文件不存在")
    
    media = media_db[media_id]
    media['parse_status'] = ParseStatus.PROCESSING
    
    try:
        parser = get_media_parser()
        media_path = media['path']
        
        if media['media_type'] == MediaType.IMAGE:
            result = parser.parse_image(media_path)
        else:
            # 视频取第一帧
            results = parser.parse_video(media_path, fps=1)
            result = results[0] if results else {}
        
        # 更新数据库
        media['parse_status'] = ParseStatus.COMPLETED
        media['parse_result'] = result
        
        # 存入Neo4j
        try:
            kg = get_kg_builder()
            node_id = kg.add_media(media_path, {
                'scene': result.get('scene', ''),
                'mood': result.get('mood', ''),
                'lighting': result.get('lighting', ''),
                'tags': ','.join(result.get('tags', []))
            })
            media['kg_node_id'] = node_id
        except Exception as e:
            logger.warning(f"Neo4j存储失败: {e}")
        
        # 人脸检测
        try:
            fc = get_face_cluster()
            faces = fc.detect_faces(media_path)
            result['faces'] = faces
        except Exception as e:
            logger.warning(f"人脸检测失败: {e}")
        
        return ParseResult(media_id=media_id, **result)
        
    except Exception as e:
        logger.error(f"解析失败: {e}")
        media['parse_status'] = ParseStatus.FAILED
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")


@router.post("/batch_parse", response_model=BatchParseResponse)
async def batch_parse_media(request: BatchParseRequest, background_tasks: BackgroundTasks):
    """
    批量解析媒体文件
    后台异步处理大量文件的AI解析
    """
    valid_ids = [mid for mid in request.media_ids if mid in media_db]
    
    if not valid_ids:
        raise HTTPException(status_code=400, detail="没有有效的媒体ID")
    
    # 添加到后台任务
    for media_id in valid_ids:
        if request.force or media_db[media_id]['parse_status'] == ParseStatus.PENDING:
            background_tasks.add_task(parse_media_task, media_id)
    
    return BatchParseResponse(
        total=len(request.media_ids),
        submitted=len(valid_ids),
        message=f"已提交 {len(valid_ids)} 个文件进行解析"
    )


async def parse_media_task(media_id: str):
    """后台解析任务"""
    try:
        parser = get_media_parser()
        media = media_db[media_id]
        media_path = media['path']
        
        if media['media_type'] == MediaType.IMAGE:
            result = parser.parse_image(media_path)
        else:
            results = parser.parse_video(media_path, fps=1)
            result = results[0] if results else {}
        
        media['parse_status'] = ParseStatus.COMPLETED
        media['parse_result'] = result
        
        # 存入Neo4j
        try:
            kg = get_kg_builder()
            kg.add_media(media_path, {
                'scene': result.get('scene', ''),
                'mood': result.get('mood', ''),
                'lighting': result.get('lighting', ''),
                'tags': ','.join(result.get('tags', []))
            })
        except:
            pass
            
    except Exception as e:
        logger.error(f"后台解析失败 {media_id}: {e}")
        media_db[media_id]['parse_status'] = ParseStatus.FAILED


@router.delete("/{media_id}")
async def delete_media(media_id: str):
    """删除媒体文件记录"""
    if media_id not in media_db:
        raise HTTPException(status_code=404, detail="媒体文件不存在")
    
    del media_db[media_id]
    return {"status": "success", "message": f"已删除 {media_id}"}
