"""
人脸聚类 API
处理人脸检测、聚类、人物识别等功能
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from loguru import logger

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.schemas import FaceClustersResponse, FaceCluster
from ai_core.face_cluster import FaceCluster as FaceClusterEngine
from config.loader import load_config


router = APIRouter()

# 内存中的人脸聚类缓存
_face_clusters_cache: Optional[List[dict]] = None


def get_face_cluster_engine() -> FaceClusterEngine:
    return FaceClusterEngine()


@router.get("/clusters", response_model=FaceClustersResponse)
async def get_face_clusters(
    min_faces: int = Query(1, ge=1, description="聚类最少人脸数"),
    force_refresh: bool = Query(False, description="是否强制刷新聚类")
):
    """
    获取人脸聚类结果
    将相似人脸聚合成组，每组代表一个独立个体
    """
    global _face_clusters_cache
    
    try:
        if _face_clusters_cache is not None and not force_refresh:
            clusters = _face_clusters_cache
        else:
            fc = get_face_cluster_engine()
            clusters_data = fc.get_all_clusters(min_faces=min_faces)
            
            clusters = [
                {
                    'cluster_id': c['cluster_id'],
                    'person_name': c.get('person_name'),
                    'face_count': c.get('face_count', 0),
                    'media_count': c.get('media_count', 0),
                    'media_ids': c.get('media_ids', []),
                    'thumbnail': c.get('thumbnail')
                }
                for c in clusters_data
            ]
            
            _face_clusters_cache = clusters
        
        return FaceClustersResponse(
            total=len(clusters),
            clusters=[FaceCluster(**c) for c in clusters]
        )
        
    except Exception as e:
        logger.error(f"获取人脸聚类失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取人脸聚类失败: {str(e)}")


@router.get("/clusters/{cluster_id}")
async def get_cluster_detail(cluster_id: str):
    """
    获取聚类详情
    包括该聚类下所有人脸样本的详细信息
    """
    try:
        fc = get_face_cluster_engine()
        detail = fc.get_cluster_detail(cluster_id)
        
        if not detail:
            raise HTTPException(status_code=404, detail="聚类不存在")
        
        return detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取聚类详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取聚类详情失败: {str(e)}")


@router.post("/clusters/{cluster_id}/name")
async def name_cluster(
    cluster_id: str,
    name: str = Query(..., description="人物名称")
):
    """
    为聚类指定人物名称
    将无名称的聚类标记为具体人物
    """
    try:
        fc = get_face_cluster_engine()
        success = fc.set_person_name(cluster_id, name)
        
        if not success:
            raise HTTPException(status_code=404, detail="聚类不存在")
        
        # 清除缓存
        global _face_clusters_cache
        _face_clusters_cache = None
        
        return {"status": "success", "cluster_id": cluster_id, "name": name}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置人物名称失败: {e}")
        raise HTTPException(status_code=500, detail=f"设置人物名称失败: {str(e)}")


@router.get("/clusters/{cluster_id}/media")
async def get_cluster_media(
    cluster_id: str,
    limit: int = Query(50, ge=1, le=200)
):
    """
    获取聚类涉及的所有媒体
    """
    try:
        fc = get_face_cluster_engine()
        media_list = fc.get_cluster_media(cluster_id, limit=limit)
        
        return {
            "cluster_id": cluster_id,
            "total": len(media_list),
            "media": media_list
        }
        
    except Exception as e:
        logger.error(f"获取聚类媒体失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取聚类媒体失败: {str(e)}")


@router.post("/detect")
async def detect_faces_in_media(
    media_id: str = Query(..., description="媒体ID"),
    media_path: str = Query(..., description="媒体路径")
):
    """
    对指定媒体进行人脸检测
    返回检测到的所有人脸位置和特征
    """
    try:
        fc = get_face_cluster_engine()
        faces = fc.detect_faces(media_path)
        
        return {
            "media_id": media_id,
            "path": media_path,
            "face_count": len(faces),
            "faces": faces
        }
        
    except Exception as e:
        logger.error(f"人脸检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"人脸检测失败: {str(e)}")


@router.post("/match")
async def match_face(
    media_id: str = Query(..., description="媒体ID"),
    media_path: str = Query(..., description="媒体路径"),
    cluster_id: Optional[str] = Query(None, description="指定聚类ID进行匹配")
):
    """
    将媒体中的人脸与已知聚类进行匹配
    返回匹配结果（可能匹配到多个聚类）
    """
    try:
        fc = get_face_cluster_engine()
        
        # 检测人脸
        faces = fc.detect_faces(media_path)
        
        if not faces:
            return {
                "media_id": media_id,
                "matches": [],
                "message": "未检测到人脸"
            }
        
        # 与聚类匹配
        matches = []
        for face in faces:
            embedding = face.get('embedding')
            if embedding:
                if cluster_id:
                    similarity = fc.match_embedding_to_cluster(embedding, cluster_id)
                    if similarity > 0.6:
                        matches.append({
                            'cluster_id': cluster_id,
                            'similarity': similarity,
                            'face_index': faces.index(face)
                        })
                else:
                    # 全量匹配
                    cluster_matches = fc.match_embedding_to_all_clusters(embedding)
                    matches.extend(cluster_matches)
        
        return {
            "media_id": media_id,
            "face_count": len(faces),
            "matches": matches
        }
        
    except Exception as e:
        logger.error(f"人脸匹配失败: {e}")
        raise HTTPException(status_code=500, detail=f"人脸匹配失败: {str(e)}")


@router.post("/recluster")
async def recluster_faces(
    threshold: float = Query(0.6, ge=0.3, le=0.95, description="聚类相似度阈值")
):
    """
    重新执行人脸聚类
    使用新的阈值参数
    """
    try:
        fc = get_face_cluster_engine()
        new_clusters = fc.recluster_all(threshold=threshold)
        
        # 清除缓存
        global _face_clusters_cache
        _face_clusters_cache = None
        
        return {
            "status": "success",
            "new_cluster_count": len(new_clusters),
            "message": f"重新聚类完成，产生 {len(new_clusters)} 个聚类"
        }
        
    except Exception as e:
        logger.error(f"重新聚类失败: {e}")
        raise HTTPException(status_code=500, detail=f"重新聚类失败: {str(e)}")


@router.get("/faces/{face_id}")
async def get_face_detail(face_id: str):
    """
    获取单个人脸样本详情
    """
    try:
        fc = get_face_cluster_engine()
        detail = fc.get_face_detail(face_id)
        
        if not detail:
            raise HTTPException(status_code=404, detail="人脸不存在")
        
        return detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取人脸详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取人脸详情失败: {str(e)}")
