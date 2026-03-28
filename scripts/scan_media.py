"""
媒体文件扫描核心模块
递归扫描目录，读取EXIF，计算哈希去重
"""
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from loguru import logger

# 支持的媒体格式
IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp', 'tif', 'tiff', 'raf', 'arw', 'dng', 'cr2', 'nef'}
VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv', 'webm', 'm4v', 'mpg', 'mpeg'}


def scan_directory(
    root_path: str,
    extensions: List[str] = None,
    recursive: bool = True,
    calculate_hash: bool = True
) -> List[Dict[str, Any]]:
    """
    扫描目录下的所有媒体文件
    
    Args:
        root_path: 根目录路径
        extensions: 支持的扩展名列表
        recursive: 是否递归扫描
        calculate_hash: 是否计算文件哈希
        
    Returns:
        媒体文件信息列表
    """
    if extensions is None:
        extensions = list(IMAGE_EXTENSIONS | VIDEO_EXTENSIONS)
    
    media_files = []
    
    # 标准化路径
    root_path = os.path.abspath(root_path)
    
    if not os.path.exists(root_path):
        logger.warning(f"路径不存在: {root_path}")
        return media_files
    
    if not os.path.isdir(root_path):
        logger.warning(f"不是有效目录: {root_path}")
        return media_files
    
    logger.info(f"🔍 开始扫描: {root_path}")
    
    try:
        if recursive:
            for dirpath, dirnames, filenames in os.walk(root_path):
                # 跳过隐藏目录
                dirnames[:] = [d for d in dirnames if not d.startswith('.')]
                
                for filename in filenames:
                    file_info = process_file(dirpath, filename, extensions, calculate_hash)
                    if file_info:
                        media_files.append(file_info)
        else:
            # 非递归，只扫描当前目录
            for filename in os.listdir(root_path):
                file_path = os.path.join(root_path, filename)
                if os.path.isfile(file_path):
                    file_info = process_file(root_path, filename, extensions, calculate_hash)
                    if file_info:
                        media_files.append(file_info)
        
        logger.info(f"📁 扫描完成: 找到 {len(media_files)} 个媒体文件")
        
    except Exception as e:
        logger.error(f"扫描目录失败: {e}")
    
    return media_files


def process_file(
    dirpath: str,
    filename: str,
    extensions: List[str],
    calculate_hash: bool = True
) -> Optional[Dict[str, Any]]:
    """处理单个文件"""
    
    file_path = os.path.join(dirpath, filename)
    
    # 检查扩展名
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    if ext not in extensions:
        return None
    
    # 检查是否是隐藏文件
    if filename.startswith('.'):
        return None
    
    try:
        # 获取文件信息
        stat = os.stat(file_path)
        
        file_info = {
            'path': file_path,
            'filename': filename,
            'extension': ext,
            'size': stat.st_size,
            'is_video': ext in VIDEO_EXTENSIONS,
            'is_image': ext in IMAGE_EXTENSIONS,
            'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
        
        # 计算文件哈希
        if calculate_hash:
            file_info['hash'] = calculate_file_hash(file_path)
        
        # 读取EXIF信息（仅图片）
        if file_info['is_image']:
            exif = read_exif(file_path)
            file_info['exif'] = exif
            
            # 从EXIF提取更多信息
            if exif:
                file_info['width'] = exif.get('width')
                file_info['height'] = exif.get('height')
                file_info['camera_make'] = exif.get('make')
                file_info['camera_model'] = exif.get('model')
                file_info['datetime'] = exif.get('datetime')
        
        # 读取视频信息（仅视频）
        if file_info['is_video']:
            video_info = get_video_info(file_path)
            file_info.update(video_info)
        
        return file_info
        
    except Exception as e:
        logger.debug(f"处理文件失败 {file_path}: {e}")
        return None


def calculate_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """
    计算文件哈希
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法 (md5/sha1/sha256)
        
    Returns:
        文件哈希值
    """
    try:
        if algorithm == 'md5':
            hasher = hashlib.md5()
        elif algorithm == 'sha1':
            hasher = hashlib.sha1()
        else:
            hasher = hashlib.sha256()
        
        # 分块读取，避免大文件内存问题
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        
        return hasher.hexdigest()
        
    except Exception as e:
        logger.debug(f"计算哈希失败 {file_path}: {e}")
        return hashlib.md5(file_path.encode()).hexdigest()[:32]


def read_exif(image_path: str) -> Dict[str, Any]:
    """读取图片EXIF信息"""
    exif_data = {}
    
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        
        with Image.open(image_path) as img:
            # 基本信息
            exif_data['width'] = img.width
            exif_data['height'] = img.height
            exif_data['format'] = img.format
            
            # EXIF信息
            if hasattr(img, '_getexif') and img._getexif():
                exif = img._getexif()
                
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    
                    # 过滤无效值
                    if value is None:
                        continue
                    
                    # 常见EXIF字段
                    if tag in ['Make', 'Model', 'DateTime', 'DateTimeOriginal',
                              'ExposureTime', 'FNumber', 'ISOSpeedRatings',
                              'FocalLength', 'LensModel', 'Software',
                              'ImageDescription', 'Artist', 'Copyright']:
                        
                        if isinstance(value, bytes):
                            try:
                                value = value.decode('utf-8', errors='ignore')
                            except:
                                continue
                        
                        # 标准化字段名
                        field_map = {
                            'Make': 'make',
                            'Model': 'model',
                            'DateTime': 'datetime',
                            'DateTimeOriginal': 'datetime_original',
                            'ExposureTime': 'exposure',
                            'FNumber': 'aperture',
                            'ISOSpeedRatings': 'iso',
                            'FocalLength': 'focal_length',
                            'LensModel': 'lens',
                            'Software': 'software',
                            'ImageDescription': 'description',
                            'Artist': 'artist',
                            'Copyright': 'copyright',
                        }
                        
                        field_name = field_map.get(tag, tag.lower())
                        exif_data[field_name] = value
                        
                        # 特殊处理：曝光时间格式化
                        if tag == 'ExposureTime' and isinstance(value, tuple):
                            num, denom = value
                            exif_data['exposure'] = f"1/{int(denom/num)}" if num > 0 else str(value)
                        
                        # 特殊处理：光圈格式化
                        if tag == 'FNumber' and isinstance(value, tuple):
                            num, denom = value
                            exif_data['aperture'] = f"f/{num/denom:.1f}" if denom > 0 else f"f/{value}"
                        
                        # 特殊处理：焦距格式化
                        if tag == 'FocalLength' and isinstance(value, tuple):
                            num, denom = value
                            exif_data['focal_length'] = f"{num/denom:.0f}mm" if denom > 0 else f"{value}mm"
    
    except ImportError:
        logger.debug("PIL未安装，无法读取EXIF")
    except Exception as e:
        logger.debug(f"读取EXIF失败 {image_path}: {e}")
    
    return exif_data


def get_video_info(video_path: str) -> Dict[str, Any]:
    """获取视频基本信息"""
    info = {}
    
    try:
        import cv2
        
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            info['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            info['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            info['fps'] = cap.get(cv2.CAP_PROP_FPS)
            info['frame_count'] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            info['duration'] = info['frame_count'] / info['fps'] if info['fps'] > 0 else 0
            info['codec'] = cap.get(cv2.CAP_PROP_FOURCC)
            
            fourcc = int(info['codec'])
            info['codec_name'] = (
                chr(fourcc & 0xFF) +
                chr((fourcc >> 8) & 0xFF) +
                chr((fourcc >> 16) & 0xFF) +
                chr((fourcc >> 24) & 0xFF)
            )
            
            cap.release()
            
    except ImportError:
        logger.debug("OpenCV未安装，无法读取视频信息")
    except Exception as e:
        logger.debug(f"读取视频信息失败 {video_path}: {e}")
    
    return info


def get_media_info(media_path: str) -> Dict[str, Any]:
    """
    获取单个媒体文件的信息
    
    Args:
        media_path: 媒体文件路径
        
    Returns:
        媒体信息字典
    """
    if not os.path.exists(media_path):
        return {}
    
    dirpath = os.path.dirname(media_path)
    filename = os.path.basename(media_path)
    
    extensions = list(IMAGE_EXTENSIONS | VIDEO_EXTENSIONS)
    return process_file(dirpath, filename, extensions, calculate_hash=True) or {}


def deduplicate_media(media_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    根据哈希值对媒体列表去重
    
    Args:
        media_list: 媒体列表
        
    Returns:
        去重后的列表
    """
    seen_hashes = set()
    unique_media = []
    
    for media in media_list:
        file_hash = media.get('hash')
        if file_hash and file_hash not in seen_hashes:
            seen_hashes.add(file_hash)
            unique_media.append(media)
    
    if len(media_list) > len(unique_media):
        logger.info(f"🔄 去重: {len(media_list)} -> {len(unique_media)}")
    
    return unique_media


if __name__ == "__main__":
    # 测试扫描
    import yaml
    
    # 加载配置
    config_path = Path(__file__).parent.parent / "config" / "env.windows.yaml"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        scan_paths = config.get('media', {}).get('scan_paths', ['E:/Photos', 'E:/Videos'])
        extensions = config.get('media', {}).get('supported_formats', list(IMAGE_EXTENSIONS | VIDEO_EXTENSIONS))
    else:
        scan_paths = ['E:/Photos', 'E:/Videos']
        extensions = list(IMAGE_EXTENSIONS | VIDEO_EXTENSIONS)
    
    # 执行扫描
    all_media = []
    for path in scan_paths:
        if os.path.exists(path):
            media = scan_directory(path, extensions)
            all_media.extend(media)
    
    # 去重
    unique_media = deduplicate_media(all_media)
    
    print(f"\n📊 扫描结果:")
    print(f"   总计: {len(all_media)}")
    print(f"   去重后: {len(unique_media)}")
    print(f"   图片: {len([m for m in unique_media if m.get('is_image')])}")
    print(f"   视频: {len([m for m in unique_media if m.get('is_video')])}")
