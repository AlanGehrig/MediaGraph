"""
CLIP 多模态媒体解析模块
使用 OpenAI CLIP 模型提取图像/视频的语义特征
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

import numpy as np
from PIL import Image
from loguru import logger

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_core.model_config import ModelConfig, model_loader


class MediaParser:
    """
    媒体文件AI解析器
    使用CLIP模型提取场景、物体、情绪、光线、构图等特征
    """
    
    # 预定义的场景标签
    SCENE_LABELS = [
        'beach', 'mountain', 'forest', 'desert', 'city', 'urban', 'rural',
        'indoor', 'outdoor', 'studio', 'office', 'home', 'restaurant',
        'street', 'park', 'garden', 'lake', 'ocean', 'river', 'sky',
        'sunset', 'sunrise', 'night', 'day', 'golden_hour', 'blue_hour'
    ]
    
    # 情绪标签
    MOOD_LABELS = [
        'happy', 'sad', 'romantic', 'dramatic', 'peaceful', 'energetic',
        'melancholic', 'joyful', 'nostalgic', 'mysterious', 'serene',
        'vibrant', 'dark', 'light', 'warm', 'cool', 'cozy', 'eerie'
    ]
    
    # 光线标签
    LIGHTING_LABELS = [
        'natural', 'artificial', 'soft', 'hard', 'backlight', 'frontlight',
        'sidelight', 'rim_light', 'golden_hour', 'blue_hour', 'low_light',
        'high_key', 'low_key', 'dramatic', 'diffused', 'direct', 'warm', 'cool'
    ]
    
    # 构图标签
    COMPOSITION_LABELS = [
        'centered', 'rule_of_thirds', 'symmetrical', 'leading_lines',
        'frame_within_frame', 'close_up', 'wide_shot', 'medium_shot',
        'full_body', 'portrait', 'landscape', 'macro', 'birds_eye', 'worms_eye'
    ]
    
    # 物体类别
    OBJECT_LABELS = [
        'person', 'people', 'dog', 'cat', 'car', 'tree', 'flower', 'food',
        'building', 'water', 'sky', 'cloud', 'mountain', 'animal', 'bird',
        'furniture', 'electronic', 'clothing', 'book', 'art', 'music_instrument'
    ]
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化媒体解析器
        
        Args:
            model_path: CLIP模型路径
        """
        self.config = ModelConfig()
        if model_path:
            self.config.clip_model_path = model_path
        
        # 尝试加载CLIP模型
        self.clip_model = None
        self.clip_preprocess = None
        self._load_clip_model()
    
    def _load_clip_model(self):
        """加载CLIP模型"""
        try:
            import clip
            import torch
            
            device = self.config.clip_device
            model_path = self.config.clip_model_path
            
            self.clip_model, self.clip_preprocess = clip.load(
                self.config.clip_model_name,
                device=device,
                download_root=model_path
            )
            
            logger.info(f"✅ CLIP模型加载成功: {self.config.clip_model_name}")
            
        except Exception as e:
            logger.warning(f"CLIP模型加载失败，使用模拟模式: {e}")
            self.clip_model = None
            self.clip_preprocess = None
    
    def parse_image(self, image_path: str) -> Dict[str, Any]:
        """
        解析单张图片
        
        Args:
            image_path: 图片路径
            
        Returns:
            解析结果字典，包含:
            - scene: 场景描述
            - objects: 检测到的物体列表
            - colors: 主色调列表
            - lighting: 光线条件
            - mood: 情绪/氛围
            - composition: 构图分析
            - tags: 标签列表
        """
        try:
            # 加载图片
            image = Image.open(image_path).convert('RGB')
            
            # 提取特征
            features = self._extract_features(image)
            
            # 构建结果
            result = {
                'scene': self._classify_scene(features['image_features']),
                'objects': self._detect_objects(features['image_features']),
                'colors': self._analyze_colors(image),
                'lighting': self._classify_lighting(features['image_features']),
                'mood': self._classify_mood(features['image_features']),
                'composition': self._classify_composition(features['image_features']),
                'tags': self._generate_tags(features),
                'features': features['image_features'].tolist() if hasattr(features['image_features'], 'tolist') else list(features['image_features']),
                'width': image.width,
                'height': image.height,
                'aspect_ratio': round(image.width / image.height, 2),
            }
            
            return result
            
        except Exception as e:
            logger.error(f"图片解析失败 {image_path}: {e}")
            return self._get_empty_result(str(e))
    
    def parse_video(self, video_path: str, fps: int = 1) -> List[Dict[str, Any]]:
        """
        解析视频文件
        
        Args:
            video_path: 视频路径
            fps: 每秒采样帧数
            
        Returns:
            每帧的解析结果列表
        """
        try:
            import cv2
            
            results = []
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                logger.error(f"无法打开视频: {video_path}")
                return []
            
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / video_fps if video_fps > 0 else 0
            
            # 计算采样间隔
            frame_interval = max(1, int(video_fps / fps))
            
            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_idx % frame_interval == 0:
                    # 转换为PIL Image
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(frame_rgb)
                    
                    # 解析帧
                    frame_result = self.parse_image(video_path)
                    frame_result['timestamp'] = frame_idx / video_fps
                    frame_result['frame_index'] = frame_idx
                    results.append(frame_result)
                
                frame_idx += 1
            
            cap.release()
            
            # 添加视频汇总信息
            if results:
                results[0]['video_duration'] = duration
                results[0]['total_frames'] = total_frames
                results[0]['sampled_frames'] = len(results)
            
            return results
            
        except Exception as e:
            logger.error(f"视频解析失败 {video_path}: {e}")
            return []
    
    def _extract_features(self, image: Image.Image) -> Dict[str, Any]:
        """提取图像特征"""
        if self.clip_model is None:
            # 返回模拟特征
            return {
                'image_features': np.random.randn(512).astype(np.float32),
                'text_features': np.random.randn(512).astype(np.float32),
            }
        
        import torch
        import clip
        
        # 预处理图片
        image_input = self.clip_preprocess(image).unsqueeze(0).to(self.config.clip_device)
        
        with torch.no_grad():
            image_features = self.clip_model.encode_image(image_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)
        
        return {
            'image_features': image_features.cpu().numpy().flatten(),
        }
    
    def _classify_scene(self, features: np.ndarray) -> str:
        """分类场景"""
        if self.clip_model is None:
            return np.random.choice(self.SCENE_LABELS)
        
        import torch
        import clip
        
        text_inputs = torch.cat([clip.tokenize(f"a photo of a {label}") 
                                 for label in self.SCENE_LABELS]).to(self.config.clip_device)
        
        with torch.no_grad():
            text_features = self.clip_model.encode_text(text_inputs)
            text_features /= text_features.norm(dim=-1, keepdim=True)
        
        # 计算相似度
        similarity = np.dot(features, text_features.cpu().numpy().T)
        best_idx = np.argmax(similarity)
        
        return self.SCENE_LABELS[best_idx]
    
    def _detect_objects(self, features: np.ndarray) -> List[str]:
        """检测物体"""
        if self.clip_model is None:
            return np.random.choice(self.OBJECT_LABELS, size=3).tolist()
        
        import torch
        import clip
        
        text_inputs = torch.cat([clip.tokenize(f"a photo containing a {label}") 
                                 for label in self.OBJECT_LABELS]).to(self.config.clip_device)
        
        with torch.no_grad():
            text_features = self.clip_model.encode_text(text_inputs)
            text_features /= text_features.norm(dim=-1, keepdim=True)
        
        similarity = np.dot(features, text_features.cpu().numpy().T)
        # 返回相似度超过阈值的物体
        threshold = 0.25
        detected = [self.OBJECT_LABELS[i] for i in range(len(similarity)) 
                   if similarity[i] > threshold]
        
        return detected[:5] if detected else [self.OBJECT_LABELS[np.argmax(similarity)]]
    
    def _analyze_colors(self, image: Image.Image) -> List[str]:
        """分析主色调"""
        img = image.resize((100, 100))
        pixels = np.array(img)
        
        # 简单K-means聚类
        pixels = pixels.reshape(-1, 3)
        
        # 计算平均颜色
        avg_color = pixels.mean(axis=0)
        
        # 判断色调
        r, g, b = avg_color
        colors = []
        
        if r > 150 and g > 150 and b > 150:
            colors.append('light')
        elif r < 80 and g < 80 and b < 80:
            colors.append('dark')
        
        if r > g + 20 and r > b + 20:
            colors.append('warm_red')
        elif b > r + 20 and b > g + 20:
            colors.append('cool_blue')
        elif g > r + 10 and g > b + 10:
            colors.append('green')
        
        if not colors:
            colors.append('neutral')
        
        return colors
    
    def _classify_lighting(self, features: np.ndarray) -> str:
        """分类光线条件"""
        if self.clip_model is None:
            return np.random.choice(self.LIGHTING_LABELS)
        
        import torch
        import clip
        
        text_inputs = torch.cat([clip.tokenize(f"a photo with {label} lighting") 
                                 for label in self.LIGHTING_LABELS]).to(self.config.clip_device)
        
        with torch.no_grad():
            text_features = self.clip_model.encode_text(text_inputs)
            text_features /= text_features.norm(dim=-1, keepdim=True)
        
        similarity = np.dot(features, text_features.cpu().numpy().T)
        best_idx = np.argmax(similarity)
        
        return self.LIGHTING_LABELS[best_idx]
    
    def _classify_mood(self, features: np.ndarray) -> str:
        """分类情绪/氛围"""
        if self.clip_model is None:
            return np.random.choice(self.MOOD_LABELS)
        
        import torch
        import clip
        
        text_inputs = torch.cat([clip.tokenize(f"a photo with a {label} mood") 
                                 for label in self.MOOD_LABELS]).to(self.config.clip_device)
        
        with torch.no_grad():
            text_features = self.clip_model.encode_text(text_inputs)
            text_features /= text_features.norm(dim=-1, keepdim=True)
        
        similarity = np.dot(features, text_features.cpu().numpy().T)
        best_idx = np.argmax(similarity)
        
        return self.MOOD_LABELS[best_idx]
    
    def _classify_composition(self, features: np.ndarray) -> str:
        """分析构图"""
        if self.clip_model is None:
            return np.random.choice(self.COMPOSITION_LABELS)
        
        import torch
        import clip
        
        text_inputs = torch.cat([clip.tokenize(f"a photo with {label} composition") 
                                 for label in self.COMPOSITION_LABELS]).to(self.config.clip_device)
        
        with torch.no_grad():
            text_features = self.clip_model.encode_text(text_inputs)
            text_features /= text_features.norm(dim=-1, keepdim=True)
        
        similarity = np.dot(features, text_features.cpu().numpy().T)
        best_idx = np.argmax(similarity)
        
        return self.COMPOSITION_LABELS[best_idx]
    
    def _generate_tags(self, features: Dict[str, Any]) -> List[str]:
        """生成标签"""
        tags = []
        
        # 从各分类结果生成标签
        # 实际实现会综合各项结果
        
        return tags
    
    def _get_empty_result(self, error: str = "") -> Dict[str, Any]:
        """返回空结果"""
        return {
            'scene': 'unknown',
            'objects': [],
            'colors': ['unknown'],
            'lighting': 'unknown',
            'mood': 'unknown',
            'composition': 'unknown',
            'tags': [],
            'error': error,
        }
    
    def extract_text(self, path: str) -> str:
        """
        从媒体文件提取文本
        对于图片返回EXIF中的描述，对于视频返回字幕(如有)
        """
        try:
            if path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                # 图片：提取EXIF
                from PIL import Image
                from PIL.ExifTags import TAGS
                
                img = Image.open(path)
                exif = img._getexif()
                
                if exif:
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag in ['ImageDescription', 'XPComment', 'UserComment']:
                            return str(value)
                
                return ""
                
            elif path.lower().endswith(('.mp4', '.mov', '.avi')):
                # 视频：暂不支持字幕提取
                return ""
            else:
                return ""
                
        except Exception as e:
            logger.warning(f"文本提取失败 {path}: {e}")
            return ""
