"""
Chroma 向量数据库模块
管理 CLIP 特征的存储和相似度检索
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
from loguru import logger

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class VectorStore:
    """
    Chroma 向量存储封装
    用于存储和检索 CLIP 图像/文本特征
    """
    
    def __init__(self, persist_dir: str):
        """
        初始化向量存储
        
        Args:
            persist_dir: 持久化目录
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Chroma 客户端
        self.client = None
        self.collection = None
        
        self._connect()
    
    def _connect(self):
        """连接 Chroma"""
        try:
            import chromadb
            
            # Chroma 1.x API: 使用 PersistentClient
            self.client = chromadb.PersistentClient(
                path=str(self.persist_dir)
            )
            
            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name="media_embeddings",
                metadata={"hnsw:space": "cosine"}  # 余弦相似度
            )
            
            logger.info(f"✅ Chroma 连接成功: {self.persist_dir}")
            
        except ImportError:
            logger.warning("Chroma 未安装，使用模拟模式")
            self.client = None
            self.collection = None
        except Exception as e:
            logger.warning(f"Chroma 连接失败: {e}，使用模拟模式")
            self.client = None
            self.collection = None
    
    def add_image(
        self,
        media_id: str,
        clip_embedding: List[float],
        metadata: Optional[Dict] = None
    ):
        """
        添加图像向量
        
        Args:
            media_id: 媒体ID
            clip_embedding: 512维 CLIP 特征向量
            metadata: 附加元数据
        """
        if self.collection is None:
            return
        
        try:
            metadata = metadata or {}
            metadata['type'] = 'image'
            
            self.collection.add(
                ids=[media_id],
                embeddings=[clip_embedding],
                metadatas=[metadata],
                documents=[f"Image: {metadata.get('filename', media_id)}"]
            )
            
        except Exception as e:
            logger.error(f"添加图像向量失败: {e}")
    
    def add_video(
        self,
        media_id: str,
        clip_embedding: List[float],
        frame_index: int = 0,
        metadata: Optional[Dict] = None
    ):
        """
        添加视频帧向量
        
        Args:
            media_id: 媒体ID
            clip_embedding: CLIP 特征向量
            frame_index: 帧索引
            metadata: 附加元数据
        """
        if self.collection is None:
            return
        
        try:
            metadata = metadata or {}
            metadata['type'] = 'video'
            metadata['frame_index'] = frame_index
            
            # 使用 media_id_frame 作为唯一ID
            vector_id = f"{media_id}_frame_{frame_index}"
            
            self.collection.add(
                ids=[vector_id],
                embeddings=[clip_embedding],
                metadatas=[metadata],
                documents=[f"Video: {metadata.get('filename', media_id)} frame {frame_index}"]
            )
            
        except Exception as e:
            logger.error(f"添加视频向量失败: {e}")
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        向量相似度搜索
        
        Args:
            query: 搜索文本（将转换为向量）
            top_k: 返回数量
            filter_metadata: 元数据过滤条件
            
        Returns:
            [{media_id, similarity, metadata, path, filename}]
        """
        if self.collection is None:
            return self._mock_search(query, top_k)
        
        try:
            # 将文本转换为向量
            query_embedding = self._encode_text(query)
            
            if query_embedding is None:
                return []
            
            # 执行查询
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata,
                include=["metadatas", "distances"]
            )
            
            # 整理结果
            search_results = []
            
            if results['ids'] and len(results['ids']) > 0:
                ids = results['ids'][0]
                distances = results['distances'][0] if 'distances' in results else []
                metadatas = results['metadatas'][0] if 'metadatas' in results else []
                
                for i, vector_id in enumerate(ids):
                    distance = distances[i] if i < len(distances) else 0
                    similarity = 1 - distance  # cosine distance 转 similarity
                    
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    
                    search_results.append({
                        'media_id': metadata.get('media_id', vector_id),
                        'vector_id': vector_id,
                        'similarity': float(similarity),
                        'metadata': metadata,
                        'path': metadata.get('path', ''),
                        'filename': metadata.get('filename', ''),
                        'type': metadata.get('type', 'unknown'),
                    })
            
            return search_results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    def search_by_embedding(
        self,
        embedding: List[float],
        top_k: int = 10,
        media_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        基于已有向量搜索
        
        Args:
            embedding: 特征向量
            top_k: 返回数量
            media_type: 媒体类型过滤 (image/video)
            
        Returns:
            搜索结果列表
        """
        if self.collection is None:
            return []
        
        try:
            where_filter = {"type": media_type} if media_type else None
            
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                where=where_filter,
                include=["metadatas", "distances"]
            )
            
            search_results = []
            
            if results['ids'] and len(results['ids']) > 0:
                ids = results['ids'][0]
                distances = results['distances'][0] if 'distances' in results else []
                metadatas = results['metadatas'][0] if 'metadatas' in results else []
                
                for i, vector_id in enumerate(ids):
                    distance = distances[i] if i < len(distances) else 0
                    similarity = 1 - distance
                    
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    
                    search_results.append({
                        'media_id': metadata.get('media_id', vector_id),
                        'vector_id': vector_id,
                        'similarity': float(similarity),
                        'metadata': metadata,
                        'path': metadata.get('path', ''),
                        'filename': metadata.get('filename', ''),
                    })
            
            return search_results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    def get_by_media_id(self, media_id: str) -> Optional[Dict]:
        """获取媒体的向量和元数据"""
        if self.collection is None:
            return None
        
        try:
            results = self.collection.get(
                ids=[media_id],
                include=["metadatas"]
            )
            
            if results['ids'] and len(results['ids']) > 0:
                return {
                    'media_id': results['ids'][0],
                    'metadata': results['metadatas'][0] if results['metadatas'] else {}
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取向量失败: {e}")
            return None
    
    def delete_by_media_id(self, media_id: str):
        """删除媒体的向量"""
        if self.collection is None:
            return
        
        try:
            # 删除该 media_id 的所有向量
            self.collection.delete(where={"media_id": media_id})
        except Exception as e:
            logger.error(f"删除向量失败: {e}")
    
    def count(self) -> int:
        """获取向量总数"""
        if self.collection is None:
            return 0
        
        try:
            return self.collection.count()
        except:
            return 0
    
    def _encode_text(self, text: str) -> Optional[List[float]]:
        """将文本编码为向量"""
        try:
            import clip
            import torch
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model, _ = clip.load("ViT-L/14", device=device)
            
            text_input = clip.tokenize([text]).to(device)
            
            with torch.no_grad():
                text_features = model.encode_text(text_input)
                text_features /= text_features.norm(dim=-1, keepdim=True)
            
            return text_features.cpu().numpy().flatten().tolist()
            
        except Exception as e:
            logger.warning(f"文本编码失败: {e}")
            return None
    
    def _mock_search(self, query: str, top_k: int) -> List[Dict]:
        """模拟搜索（Chroma 不可用时）"""
        return []
    
    def save(self):
        """持久化存储"""
        # Chroma 1.x PersistentClient 自动持久化
        logger.info("向量存储已保存")
    
    def reset(self):
        """重置存储"""
        if self.client is not None:
            try:
                self.client.delete_collection("media_embeddings")
                self.collection = self.client.get_or_create_collection(
                    name="media_embeddings",
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("向量存储已重置")
            except Exception as e:
                logger.error(f"重置失败: {e}")
