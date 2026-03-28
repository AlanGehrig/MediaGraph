"""
InsightFace 人脸检测与聚类模块
使用 InsightFace 进行人脸识别和聚类
"""
import os
import json
import uuid
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

import numpy as np
from PIL import Image
from loguru import logger

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_core.model_config import ModelConfig


class FaceCluster:
    """
    人脸检测与聚类引擎
    使用 InsightFace 进行人脸检测和特征提取
    使用余弦相似度进行人脸聚类
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化人脸聚类引擎
        
        Args:
            model_path: InsightFace模型路径
        """
        self.config = ModelConfig()
        if model_path:
            self.config.insightface_model_path = model_path
        
        # 内存中的人脸数据库
        self.faces_db: Dict[str, Dict] = {}
        self.clusters: Dict[str, Dict] = {}
        self.cluster_embeddings: Dict[str, List] = {}
        
        # 尝试加载模型
        self.face_app = None
        self._load_model()
    
    def _load_model(self):
        """加载InsightFace模型"""
        try:
            from insightface.app import FaceAnalysis
            
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] \
                if self.config.insightface_device == 'cuda' \
                else ['CPUExecutionProvider']
            
            self.face_app = FaceAnalysis(
                name=self.config.insightface_recognizer,
                providers=providers
            )
            self.face_app.prepare(ctx_id=0, det_size=(640, 640))
            
            logger.info("✅ InsightFace模型加载成功")
            
        except Exception as e:
            logger.warning(f"InsightFace模型加载失败，使用模拟模式: {e}")
            self.face_app = None
    
    def detect_faces(self, image_path: str, max_num: int = 10) -> List[Dict[str, Any]]:
        """
        检测图片中的人脸
        
        Args:
            image_path: 图片路径
            max_num: 最大检测数量
            
        Returns:
            人脸列表，每个包含:
            - face_id: 人脸唯一ID
            - embedding: 512维特征向量
            - bbox: 边界框 [x1, y1, x2, y2]
            - landmarks: 关键点
            - confidence: 置信度
        """
        try:
            # 加载图片
            img = Image.open(image_path).convert('RGB')
            img_array = np.array(img)
            
            faces = []
            
            if self.face_app is not None:
                # 使用真实模型检测
                face_results = self.face_app.get(img_array, max_num=max_num)
                
                for face in face_results:
                    face_id = str(uuid.uuid4())[:12]
                    
                    face_info = {
                        'face_id': face_id,
                        'embedding': face.embedding.tolist() if hasattr(face, 'embedding') else [],
                        'bbox': face.bbox.tolist() if hasattr(face, 'bbox') else [],
                        'landmarks': face.kps.tolist() if hasattr(face, 'kps') else [],
                        'confidence': float(face.det_score) if hasattr(face, 'det_score') else 0.0,
                        'age': int(face.age) if hasattr(face, 'age') else None,
                        'gender': 'male' if face.gender == 1 else 'female' if hasattr(face, 'gender') else None,
                    }
                    faces.append(face_info)
                    
            else:
                # 模拟检测（用于测试）
                h, w = img_array.shape[:2]
                face_id = str(uuid.uuid4())[:12]
                faces.append({
                    'face_id': face_id,
                    'embedding': np.random.randn(512).tolist(),
                    'bbox': [w*0.3, h*0.2, w*0.7, h*0.8],
                    'landmarks': [],
                    'confidence': 0.95,
                })
            
            return faces
            
        except Exception as e:
            logger.error(f"人脸检测失败 {image_path}: {e}")
            return []
    
    def cluster_faces(self, embeddings: List[List[float]], threshold: float = 0.6) -> Dict[str, List[str]]:
        """
        对人脸特征进行聚类
        
        Args:
            embeddings: 人脸特征列表
            threshold: 相似度阈值
            
        Returns:
            聚类结果 {cluster_id: [face_ids]}
        """
        if not embeddings:
            return {}
        
        embeddings_array = np.array(embeddings)
        
        # 计算余弦相似度矩阵
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        normalized = embeddings_array / (norms + 1e-8)
        similarity_matrix = np.dot(normalized, normalized.T)
        
        n = len(embeddings)
        cluster_labels = [-1] * n
        
        current_cluster = 0
        for i in range(n):
            if cluster_labels[i] != -1:
                continue
            
            # BFS扩展聚类
            queue = [i]
            cluster_labels[i] = current_cluster
            
            while queue:
                j = queue.pop(0)
                for k in range(n):
                    if cluster_labels[k] == -1 and similarity_matrix[j][k] >= threshold:
                        cluster_labels[k] = current_cluster
                        queue.append(k)
            
            current_cluster += 1
        
        # 构建返回结果
        clusters = {}
        for i, label in enumerate(cluster_labels):
            cluster_id = f"person_{label}"
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(f"face_{i}")
        
        return clusters
    
    def get_person_media(self, person_id: str) -> List[Dict[str, Any]]:
        """
        获取某人物的所有媒体
        
        Args:
            person_id: 人物ID
            
        Returns:
            媒体列表
        """
        # 从数据库查询
        media_list = []
        
        for face_id, face_data in self.faces_db.items():
            if face_data.get('cluster_id') == person_id:
                media_id = face_data.get('media_id')
                if media_id and media_id not in [m['media_id'] for m in media_list]:
                    media_list.append({
                        'media_id': media_id,
                        'path': face_data.get('path'),
                        'face_id': face_id,
                        'timestamp': face_data.get('timestamp')
                    })
        
        return media_list
    
    def get_all_clusters(self, min_faces: int = 1) -> List[Dict[str, Any]]:
        """
        获取所有聚类
        
        Args:
            min_faces: 最少人脸数
            
        Returns:
            聚类列表
        """
        clusters = []
        
        for cluster_id, face_ids in self.clusters.items():
            if len(face_ids) >= min_faces:
                # 获取涉及的媒体
                media_ids = list(set([
                    self.faces_db.get(fid, {}).get('media_id', '')
                    for fid in face_ids
                    if self.faces_db.get(fid, {}).get('media_id')
                ]))
                
                clusters.append({
                    'cluster_id': cluster_id,
                    'person_name': self.clusters.get(cluster_id, {}).get('name'),
                    'face_count': len(face_ids),
                    'media_count': len(media_ids),
                    'media_ids': media_ids,
                    'thumbnail': self._get_cluster_thumbnail(cluster_id)
                })
        
        # 按人脸数排序
        clusters.sort(key=lambda x: x['face_count'], reverse=True)
        
        return clusters
    
    def get_cluster_detail(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        """获取聚类详情"""
        if cluster_id not in self.clusters:
            return None
        
        face_ids = self.clusters[cluster_id]
        
        face_details = []
        for face_id in face_ids:
            if face_id in self.faces_db:
                face_details.append(self.faces_db[face_id])
        
        return {
            'cluster_id': cluster_id,
            'name': self.clusters[cluster_id].get('name'),
            'face_count': len(face_ids),
            'faces': face_details,
            'media_ids': list(set([f.get('media_id') for f in face_details if f.get('media_id')]))
        }
    
    def set_person_name(self, cluster_id: str, name: str) -> bool:
        """设置人物名称"""
        if cluster_id not in self.clusters:
            return False
        
        if 'name' not in self.clusters[cluster_id]:
            self.clusters[cluster_id] = {}
        self.clusters[cluster_id]['name'] = name
        
        return True
    
    def get_cluster_media(self, cluster_id: str, limit: int = 50) -> List[Dict]:
        """获取聚类相关的媒体"""
        if cluster_id not in self.clusters:
            return []
        
        face_ids = self.clusters[cluster_id]
        media_dict = {}
        
        for face_id in face_ids:
            if face_id in self.faces_db:
                media_id = self.faces_db[face_id].get('media_id')
                if media_id and media_id not in media_dict:
                    media_dict[media_id] = {
                        'media_id': media_id,
                        'path': self.faces_db[face_id].get('path'),
                        'thumbnail': self.faces_db[face_id].get('thumbnail'),
                    }
        
        return list(media_dict.values())[:limit]
    
    def match_embedding_to_cluster(self, embedding: List[float], cluster_id: str) -> float:
        """将人脸特征与指定聚类匹配"""
        if cluster_id not in self.cluster_embeddings:
            return 0.0
        
        cluster_embeddings = self.cluster_embeddings[cluster_id]
        if not cluster_embeddings:
            return 0.0
        
        # 计算与聚类中心的相似度
        query = np.array(embedding)
        centroid = np.mean(cluster_embeddings, axis=0)
        
        similarity = np.dot(query, centroid) / (np.linalg.norm(query) * np.linalg.norm(centroid) + 1e-8)
        
        return float(similarity)
    
    def match_embedding_to_all_clusters(self, embedding: List[float]) -> List[Dict]:
        """将人脸特征与所有聚类匹配"""
        matches = []
        
        for cluster_id in self.cluster_embeddings:
            similarity = self.match_embedding_to_cluster(embedding, cluster_id)
            if similarity > 0.5:
                matches.append({
                    'cluster_id': cluster_id,
                    'similarity': similarity,
                    'person_name': self.clusters.get(cluster_id, {}).get('name')
                })
        
        # 按相似度排序
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return matches[:5]
    
    def recluster_all(self, threshold: float = 0.6) -> List[str]:
        """重新聚类所有已知人脸"""
        if not self.faces_db:
            return []
        
        embeddings = []
        face_ids = []
        
        for face_id, face_data in self.faces_db.items():
            if 'embedding' in face_data:
                embeddings.append(face_data['embedding'])
                face_ids.append(face_id)
        
        if not embeddings:
            return []
        
        # 执行聚类
        new_clusters = self.cluster_faces(embeddings, threshold)
        
        # 更新数据库
        self.clusters = {}
        self.cluster_embeddings = {}
        
        for cluster_id, cluster_face_ids in new_clusters.items():
            self.clusters[cluster_id] = {'name': None}
            self.cluster_embeddings[cluster_id] = []
            
            for face_id in cluster_face_ids:
                idx = face_ids.index(face_id)
                self.faces_db[face_ids[idx]]['cluster_id'] = cluster_id
                self.cluster_embeddings[cluster_id].append(embeddings[idx])
        
        return list(new_clusters.keys())
    
    def get_face_detail(self, face_id: str) -> Optional[Dict]:
        """获取人脸详情"""
        return self.faces_db.get(face_id)
    
    def _get_cluster_thumbnail(self, cluster_id: str) -> Optional[str]:
        """获取聚类缩略图"""
        if cluster_id not in self.clusters:
            return None
        
        face_ids = self.clusters[cluster_id]
        for face_id in face_ids:
            if face_id in self.faces_db:
                return self.faces_db[face_id].get('thumbnail')
        
        return None
    
    def add_face_to_db(self, face_info: Dict, media_id: str, path: str):
        """添加人脸到数据库"""
        face_id = face_info.get('face_id')
        if face_id:
            face_info['media_id'] = media_id
            face_info['path'] = path
            face_info['timestamp'] = datetime.now().isoformat()
            self.faces_db[face_id] = face_info
            
            # 更新聚类
            cluster_id = face_info.get('cluster_id')
            if cluster_id:
                if cluster_id not in self.clusters:
                    self.clusters[cluster_id] = {'name': None}
                    self.cluster_embeddings[cluster_id] = []
                
                if face_id not in self.clusters[cluster_id]:
                    self.clusters[cluster_id] = {**self.clusters[cluster_id]}
                    self.cluster_embeddings[cluster_id].append(face_info.get('embedding', []))
    
    def save_db(self, db_path: str):
        """保存人脸数据库到文件"""
        try:
            data = {
                'faces': self.faces_db,
                'clusters': self.clusters,
            }
            
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"人脸数据库已保存: {db_path}")
            
        except Exception as e:
            logger.error(f"保存人脸数据库失败: {e}")
    
    def load_db(self, db_path: str):
        """从文件加载人脸数据库"""
        try:
            if not os.path.exists(db_path):
                return
            
            with open(db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.faces_db = data.get('faces', {})
            self.clusters = data.get('clusters', {})
            
            # 重建聚类嵌入
            for cluster_id, cluster_data in self.clusters.items():
                face_ids = cluster_data if isinstance(cluster_data, list) else cluster_data.get('face_ids', [])
                self.cluster_embeddings[cluster_id] = [
                    self.faces_db.get(fid, {}).get('embedding', [])
                    for fid in face_ids
                    if self.faces_db.get(fid, {}).get('embedding')
                ]
            
            logger.info(f"人脸数据库已加载: {db_path}")
            
        except Exception as e:
            logger.error(f"加载人脸数据库失败: {e}")
