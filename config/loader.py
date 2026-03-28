"""
配置加载模块
统一管理所有配置文件
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any
from loguru import logger


_config_cache: Dict[str, Any] = {}


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent.parent


def load_yaml(filename: str) -> Dict[str, Any]:
    """加载YAML配置文件"""
    project_root = get_project_root()
    config_path = project_root / "config" / filename
    
    if not config_path.exists():
        logger.warning(f"配置文件不存在: {config_path}")
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"加载配置文件失败 {filename}: {e}")
        return {}


def load_config() -> Dict[str, Any]:
    """加载完整配置"""
    global _config_cache
    
    if _config_cache:
        return _config_cache
    
    # 确定环境
    is_windows = os.name == 'nt'
    env_file = 'env.windows.yaml' if is_windows else 'env.linux.yaml'
    
    # 加载各配置文件
    _config_cache = {
        'env': load_yaml(env_file),
        'neo4j': load_yaml('neo4j.yaml'),
        'model': load_yaml('model_config.yaml'),
    }
    
    # 合并配置
    base_config = _config_cache['env'].copy()
    base_config.update(_config_cache.get('overrides', {}))
    
    _config_cache = base_config
    
    return _config_cache


def get_neo4j_config() -> Dict[str, Any]:
    """获取Neo4j配置"""
    config = load_config()
    return config.get('neo4j', {
        'uri': 'bolt://localhost:7687',
        'user': 'neo4j',
        'password': 'password123'
    })


def get_chroma_config() -> Dict[str, Any]:
    """获取Chroma配置"""
    config = load_config()
    return config.get('chroma', {
        'persist_dir': 'E:/openclaw/data/MediaGraph/data/chroma'
    })


def get_media_config() -> Dict[str, Any]:
    """获取媒体配置"""
    config = load_config()
    return config.get('media', {
        'scan_paths': ['E:/Photos', 'E:/Videos'],
        'supported_formats': ['jpg', 'png', 'mp4', 'mov', 'raf', 'arw'],
        'max_video_fps': 1
    })


def get_api_config() -> Dict[str, Any]:
    """获取API配置"""
    config = load_config()
    return config.get('api', {
        'backend_port': 8000,
        'frontend_port': 3000
    })


def reload_config():
    """重新加载配置"""
    global _config_cache
    _config_cache = {}
    return load_config()
