"""
AI 模型配置模块
管理 CLIP、InsightFace 等模型的加载和配置
"""
import os
import platform
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

from loguru import logger


@dataclass
class ModelConfig:
    """AI模型配置"""
    
    # CLIP模型
    clip_model_name: str = "ViT-L/14"
    clip_model_path: str = "models/clip"
    clip_device: str = "cuda"  # cuda 或 cpu
    clip_batch_size: int = 8
    
    # InsightFace模型
    insightface_model_path: str = "models/insightface"
    insightface_device: str = "cuda"
    insightface_detector: str = "retinaface"  # retinaface, scrfd, yolov8face
    insightface_recognizer: str = "arcface"    # arcface
    
    # 视频处理
    max_video_fps: int = 1
    video_frame_interval: float = 1.0  # 秒
    
    # 其他设置
    thumbnail_size: tuple = (256, 256)
    max_image_size: int = 2048
    
    def __post_init__(self):
        """后处理初始化"""
        # 自动检测设备
        if self.is_windows():
            self.clip_device = "cpu"
            self.insightface_device = "cpu"
        else:
            try:
                import torch
                if torch.cuda.is_available():
                    self.clip_device = "cuda"
                    self.insightface_device = "cuda"
            except ImportError:
                logger.warning("PyTorch未安装，使用CPU模式")
                self.clip_device = "cpu"
                self.insightface_device = "cpu"
    
    @staticmethod
    def is_windows() -> bool:
        """是否Windows系统"""
        return platform.system() == "Windows"
    
    @staticmethod
    def is_mac() -> bool:
        """是否macOS系统"""
        return platform.system() == "Darwin"
    
    def get_clip_config(self) -> Dict[str, Any]:
        """获取CLIP配置"""
        return {
            'model_name': self.clip_model_name,
            'model_path': self.clip_model_path,
            'device': self.clip_device,
            'batch_size': self.clip_batch_size,
        }
    
    def get_insightface_config(self) -> Dict[str, Any]:
        """获取InsightFace配置"""
        return {
            'model_path': self.insightface_model_path,
            'device': self.insightface_device,
            'detector': self.insightface_detector,
            'recognizer': self.insightface_recognizer,
        }


class ModelLoader:
    """模型加载器"""
    
    _instance = None
    _clip_model = None
    _insightface_model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_clip(self, config: ModelConfig):
        """加载CLIP模型"""
        if self._clip_model is not None:
            return self._clip_model
        
        try:
            import clip
            import torch
            
            device = config.clip_device
            self._clip_model, _ = clip.load(
                config.clip_model_name,
                device=device,
                download_root=config.clip_model_path
            )
            
            logger.info(f"✅ CLIP模型加载成功: {config.clip_model_name} on {device}")
            return self._clip_model
            
        except Exception as e:
            logger.error(f"❌ CLIP模型加载失败: {e}")
            # 返回模拟模型用于测试
            return MockCLIPModel()
    
    def load_insightface(self, config: ModelConfig):
        """加载InsightFace模型"""
        if self._insightface_model is not None:
            return self._insightface_model
        
        try:
            import insightface
            from insightface.app import FaceAnalysis
            
            app = FaceAnalysis(
                name=config.insightface_recognizer,
                providers=['CUDAExecutionProvider', 'CPUExecutionProvider'] 
                if config.insightface_device == 'cuda' 
                else ['CPUExecutionProvider']
            )
            app.prepare(ctx_id=0, det_size=(640, 640))
            
            logger.info(f"✅ InsightFace模型加载成功 on {config.insightface_device}")
            self._insightface_model = app
            return self._insightface_model
            
        except Exception as e:
            logger.error(f"❌ InsightFace模型加载失败: {e}")
            # 返回模拟模型用于测试
            return MockInsightFaceModel()
    
    def get_clip(self):
        """获取CLIP模型"""
        return self._clip_model
    
    def get_insightface(self):
        """获取InsightFace模型"""
        return self._insightface_model


class MockCLIPModel:
    """CLIP模型模拟（用于测试）"""
    
    def __init__(self):
        self.name = "mock-clip"
    
    def encode_image(self, image):
        """模拟图像编码"""
        import numpy as np
        return np.random.randn(512).astype(np.float32)
    
    def encode_text(self, text):
        """模拟文本编码"""
        import numpy as np
        return np.random.randn(512).astype(np.float32)
    
    def __call__(self, image, text):
        """模拟前向传播"""
        import numpy as np
        return np.random.rand(1, len(text))


class MockInsightFaceModel:
    """InsightFace模型模拟（用于测试）"""
    
    def __init__(self):
        self.name = "mock-insightface"
    
    def get(self, img, max_num=10):
        """模拟人脸检测"""
        return []


# 全局模型加载器实例
model_loader = ModelLoader()
