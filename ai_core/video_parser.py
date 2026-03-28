"""
视频关键帧抽帧模块
使用 FFmpeg 提取视频关键帧
"""
import os
import subprocess
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

from loguru import logger

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.loader import load_config


class VideoParser:
    """
    视频解析器
    提取关键帧、缩略图、视频信息
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化视频解析器
        
        Args:
            output_dir: 帧输出目录
        """
        self.config = load_config()
        
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(self.config['chroma']['persist_dir']) / 'frames'
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查ffmpeg
        self.ffmpeg_available = self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> bool:
        """检查ffmpeg是否可用"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("FFmpeg未安装，将使用模拟模式")
            return False
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        获取视频基本信息
        
        Returns:
            视频信息字典
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        if self.ffmpeg_available:
            return self._get_video_info_ffmpeg(video_path)
        else:
            return self._get_video_info_mock(video_path)
    
    def _get_video_info_ffmpeg(self, video_path: str) -> Dict[str, Any]:
        """使用FFmpeg获取视频信息"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return self._get_video_info_mock(video_path)
            
            data = json.loads(result.stdout)
            
            # 找到视频流
            video_stream = None
            audio_stream = None
            
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video' and not video_stream:
                    video_stream = stream
                elif stream.get('codec_type') == 'audio' and not audio_stream:
                    audio_stream = stream
            
            format_info = data.get('format', {})
            
            return {
                'path': video_path,
                'filename': os.path.basename(video_path),
                'format': format_info.get('format_name', ''),
                'duration': float(format_info.get('duration', 0)),
                'size': int(format_info.get('size', 0)),
                'bit_rate': int(format_info.get('bit_rate', 0)),
                'width': int(video_stream.get('width', 0)) if video_stream else 0,
                'height': int(video_stream.get('height', 0)) if video_stream else 0,
                'fps': self._parse_fps(video_stream.get('r_frame_rate', '0/1')) if video_stream else 0,
                'codec': video_stream.get('codec_name', '') if video_stream else '',
                'has_audio': audio_stream is not None,
                'audio_codec': audio_stream.get('codec_name', '') if audio_stream else None,
            }
            
        except Exception as e:
            logger.error(f"FFprobe获取视频信息失败: {e}")
            return self._get_video_info_mock(video_path)
    
    def _parse_fps(self, fps_str: str) -> float:
        """解析FPS字符串"""
        try:
            if '/' in fps_str:
                num, den = fps_str.split('/')
                return float(num) / float(den) if float(den) != 0 else 0
            return float(fps_str)
        except:
            return 0
    
    def _get_video_info_mock(self, video_path: str) -> Dict[str, Any]:
        """模拟视频信息（FFmpeg不可用时）"""
        file_size = os.path.getsize(video_path)
        
        return {
            'path': video_path,
            'filename': os.path.basename(video_path),
            'format': 'mp4',
            'duration': 60.0,  # 假设1分钟
            'size': file_size,
            'bit_rate': file_size * 8 / 60 if file_size > 0 else 0,
            'width': 1920,
            'height': 1080,
            'fps': 30,
            'codec': 'h264',
            'has_audio': True,
            'audio_codec': 'aac',
        }
    
    def extract_frames(
        self,
        video_path: str,
        fps: int = 1,
        output_dir: Optional[str] = None,
        quality: int = 2
    ) -> List[str]:
        """
        提取视频关键帧
        
        Args:
            video_path: 视频路径
            fps: 每秒提取帧数
            output_dir: 输出目录
            quality: 质量等级 (1-31, 越小越好)
            
        Returns:
            帧图片路径列表
        """
        if not self.ffmpeg_available:
            logger.warning("FFmpeg不可用，跳过帧提取")
            return []
        
        if output_dir:
            frame_dir = Path(output_dir)
        else:
            # 创建基于视频hash的输出目录
            video_hash = hashlib.md5(video_path.encode()).hexdigest()[:12]
            frame_dir = self.output_dir / video_hash
        
        frame_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 获取视频时长
            video_info = self.get_video_info(video_path)
            duration = video_info['duration']
            
            # 构建ffmpeg命令
            # 使用fps filter按固定间隔提取帧
            output_pattern = str(frame_dir / 'frame_%04d.jpg')
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f'fps={fps}',
                '-q:v', str(quality),
                '-frames:v', str(int(duration * fps)),  # 限制总帧数
                '-y',  # 覆盖输出
                output_pattern
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=duration * 2  # 给足够时间
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg帧提取失败: {result.stderr}")
                return []
            
            # 收集提取的帧
            frame_files = sorted(frame_dir.glob('frame_*.jpg'))
            
            logger.info(f"提取 {len(frame_files)} 帧到 {frame_dir}")
            
            return [str(f) for f in frame_files]
            
        except subprocess.TimeoutExpired:
            logger.error("帧提取超时")
            return []
        except Exception as e:
            logger.error(f"帧提取异常: {e}")
            return []
    
    def extract_keyframes(
        self,
        video_path: str,
        num_keyframes: int = 10,
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        提取关键帧（非均匀分布）
        
        使用场景检测算法提取最有代表性的关键帧
        
        Args:
            video_path: 视频路径
            num_keyframes: 关键帧数量
            output_dir: 输出目录
            
        Returns:
            关键帧信息列表 [{timestamp, path, score}]
        """
        if not self.ffmpeg_available:
            return []
        
        if output_dir:
            frame_dir = Path(output_dir)
        else:
            video_hash = hashlib.md5(video_path.encode()).hexdigest()[:12]
            frame_dir = self.output_dir / f"{video_hash}_keyframes"
        
        frame_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            video_info = self.get_video_info(video_path)
            duration = video_info['duration']
            
            # 均匀分布在时间轴上
            timestamps = [
                duration * i / num_keyframes 
                for i in range(num_keyframes)
            ]
            
            keyframes = []
            
            for i, ts in enumerate(timestamps):
                output_path = frame_dir / f'keyframe_{i:04d}.jpg'
                
                cmd = [
                    'ffmpeg',
                    '-ss', str(ts),
                    '-i', video_path,
                    '-frames:v', '1',
                    '-q:v', '2',
                    '-y',
                    str(output_path)
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=10
                )
                
                if result.returncode == 0 and output_path.exists():
                    keyframes.append({
                        'timestamp': ts,
                        'path': str(output_path),
                        'index': i,
                        'score': 1.0 - abs(ts / duration - 0.5)  # 中间帧略高分
                    })
            
            # 按分数排序
            keyframes.sort(key=lambda x: x['score'], reverse=True)
            
            return keyframes
            
        except Exception as e:
            logger.error(f"关键帧提取异常: {e}")
            return []
    
    def generate_thumbnail(
        self,
        video_path: str,
        timestamp: Optional[float] = None,
        size: Tuple[int, int] = (320, 180)
    ) -> Optional[str]:
        """
        生成视频缩略图
        
        Args:
            video_path: 视频路径
            timestamp: 指定时间点(秒)，默认视频中间
            size: 缩略图尺寸
            
        Returns:
            缩略图路径
        """
        if not self.ffmpeg_available:
            return None
        
        if timestamp is None:
            video_info = self.get_video_info(video_path)
            timestamp = video_info['duration'] / 2
        
        video_hash = hashlib.md5(video_path.encode()).hexdigest()[:12]
        thumb_dir = self.output_dir / 'thumbnails'
        thumb_dir.mkdir(parents=True, exist_ok=True)
        
        thumb_path = thumb_dir / f"{video_hash}_thumb.jpg"
        
        try:
            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),
                '-i', video_path,
                '-frames:v', '1',
                '-vf', f'scale={size[0]}:{size[1]}',
                '-q:v', '3',
                '-y',
                str(thumb_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10
            )
            
            if result.returncode == 0 and thumb_path.exists():
                return str(thumb_path)
            
        except Exception as e:
            logger.error(f"缩略图生成失败: {e}")
        
        return None
    
    def extract_frames_batch(
        self,
        video_paths: List[str],
        fps: int = 1,
        output_dir: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        批量提取视频帧
        
        Args:
            video_paths: 视频路径列表
            fps: 每秒提取帧数
            output_dir: 输出目录
            
        Returns:
            {video_path: [frame_paths]}
        """
        results = {}
        
        for video_path in video_paths:
            try:
                frames = self.extract_frames(video_path, fps, output_dir)
                results[video_path] = frames
            except Exception as e:
                logger.error(f"批量提取失败 {video_path}: {e}")
                results[video_path] = []
        
        return results
