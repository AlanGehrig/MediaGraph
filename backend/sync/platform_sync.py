"""
社交平台素材同步模块
支持抖音、小红书等平台的素材同步
"""
import os
import re
import json
import hashlib
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

import httpx
from loguru import logger

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.loader import load_config


class PlatformSync:
    """社交平台素材同步基类"""
    
    def __init__(self, platform: str):
        self.platform = platform
        self.cookies: Optional[str] = None
        self.headers: Dict[str, str] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
    
    def set_cookies(self, cookies_str: str):
        """设置cookies"""
        self.cookies = cookies_str
        # 解析cookies并更新headers
        cookie_dict = {}
        for part in cookies_str.split(';'):
            if '=' in part:
                key, value = part.strip().split('=', 1)
                cookie_dict[key.strip()] = value.strip()
        self.headers['Cookie'] = cookies_str
    
    async def fetch_user_info(self) -> Dict[str, Any]:
        """获取用户信息"""
        raise NotImplementedError
    
    async def fetch_media_list(self, user_id: str, max_count: int = 100) -> List[Dict]:
        """获取媒体列表"""
        raise NotImplementedError
    
    async def download_media(self, media_url: str, save_dir: str) -> str:
        """下载媒体文件"""
        raise NotImplementedError


class DouyinSync(PlatformSync):
    """抖音素材同步"""
    
    def __init__(self):
        super().__init__('douyin')
        self.api_base = 'https://www.douyin.com/aweme/v1'
    
    async def fetch_user_info(self) -> Dict[str, Any]:
        """获取抖音用户信息"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    'https://www.douyin.com/aweme/v1/user/profile/self/',
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'uid': data.get('user', {}).get('uid'),
                        'nickname': data.get('user', {}).get('nickname'),
                        'following_count': data.get('user', {}).get('following_count'),
                        'follower_count': data.get('user', {}).get('follower_count'),
                        'aweme_count': data.get('user', {}).get('aweme_count'),
                    }
                else:
                    logger.warning(f"获取抖音用户信息失败: {response.status_code}")
                    return {}
                    
        except Exception as e:
            logger.error(f"获取抖音用户信息异常: {e}")
            return {}
    
    async def fetch_media_list(
        self, 
        user_id: Optional[str] = None, 
        max_count: int = 100
    ) -> List[Dict]:
        """
        获取用户的作品列表
        抖音API限制，实际能获取的数量取决于登录状态
        """
        media_list = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 尝试获取用户作品列表
                url = f'{self.api_base}/aweme/post/'
                params = {
                    'user_id': user_id or 'self',
                    'max_cursor': 0,
                    'count': 20,
                }
                
                response = await client.get(url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    aweme_list = data.get('aweme_list', [])
                    
                    for aweme in aweme_list[:max_count]:
                        video_info = aweme.get('video', {})
                        cover = video_info.get('cover', {}).get('url_list', [''])[0]
                        
                        media_item = {
                            'platform': 'douyin',
                            'media_id': aweme.get('aweme_id'),
                            'title': aweme.get('desc', ''),
                            'create_time': datetime.fromtimestamp(
                                aweme.get('create_time', 0)
                            ).isoformat(),
                            'video_url': video_info.get('play_addr', {}).get('url_list', [''])[0],
                            'cover_url': cover,
                            'width': video_info.get('width'),
                            'height': video_info.get('height'),
                            'duration': video_info.get('duration', 0) / 1000,  # 毫秒转秒
                            'statistics': aweme.get('statistics', {}),
                            'tags': [tag.get('hashtag_name') for tag in aweme.get('text_extra', []) if tag.get('hashtag_name')],
                        }
                        media_list.append(media_item)
                        
        except Exception as e:
            logger.error(f"获取抖音作品列表失败: {e}")
        
        return media_list
    
    async def download_media(self, media_url: str, save_dir: str) -> str:
        """下载抖音视频"""
        try:
            os.makedirs(save_dir, exist_ok=True)
            
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                response = await client.get(media_url, headers=self.headers)
                
                if response.status_code == 200:
                    # 生成文件名
                    file_hash = hashlib.md5(media_url.encode()).hexdigest()[:12]
                    filename = f"douyin_{file_hash}.mp4"
                    filepath = os.path.join(save_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    return filepath
                    
        except Exception as e:
            logger.error(f"下载抖音视频失败: {e}")
        
        return None
    
    async def sync_to_local(
        self, 
        cookies: str, 
        save_dir: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行完整同步流程
        """
        self.set_cookies(cookies)
        
        # 获取用户信息
        user_info = await self.fetch_user_info()
        
        # 获取作品列表
        media_list = await self.fetch_media_list(user_id or user_info.get('uid'))
        
        # 下载视频
        downloaded = []
        for media in media_list:
            video_url = media.get('video_url')
            if video_url:
                filepath = await self.download_media(video_url, save_dir)
                if filepath:
                    media['local_path'] = filepath
                    downloaded.append(media)
        
        return {
            'status': 'success',
            'user_info': user_info,
            'total_found': len(media_list),
            'downloaded': len(downloaded),
            'media_list': media_list,
            'save_dir': save_dir
        }


class XiaohongshuSync(PlatformSync):
    """小红书素材同步"""
    
    def __init__(self):
        super().__init__('xiaohongshu')
        self.api_base = 'https://www.xiaohongshu.com'
    
    async def fetch_user_info(self) -> Dict[str, Any]:
        """获取小红书用户信息"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f'{self.api_base}/user/profile/self',
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    # 小红书页面是JS渲染的，解析HTML获取基本信息
                    html = response.text
                    # 实际需要通过API，这里简化处理
                    return {}
                else:
                    return {}
                    
        except Exception as e:
            logger.error(f"获取小红书用户信息异常: {e}")
            return {}
    
    async def fetch_media_list(
        self, 
        user_id: Optional[str] = None, 
        max_count: int = 100
    ) -> List[Dict]:
        """获取小红书笔记列表"""
        # 小红书API需要更复杂的签名验证
        # 这里提供接口框架，实际调用需要逆向API
        return []
    
    async def download_media(self, media_url: str, save_dir: str) -> str:
        """下载小红书图片/视频"""
        try:
            os.makedirs(save_dir, exist_ok=True)
            
            ext = '.jpg' if 'image' in media_url else '.mp4'
            file_hash = hashlib.md5(media_url.encode()).hexdigest()[:12]
            filename = f"xhs_{file_hash}{ext}"
            filepath = os.path.join(save_dir, filename)
            
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                response = await client.get(media_url, headers=self.headers)
                
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    return filepath
                    
        except Exception as e:
            logger.error(f"下载小红书媒体失败: {e}")
        
        return None


# API路由
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/douyin")
async def sync_douyin(
    cookies: str,
    user_id: Optional[str] = None,
    save_dir: Optional[str] = None
):
    """
    同步抖音素材
    
    参数:
    - cookies: 抖音登录后的cookies字符串
    - user_id: 指定用户ID(可选，默认同步自己的)
    - save_dir: 保存目录(可选)
    """
    try:
        config = load_config()
        
        # 确定保存目录
        if not save_dir:
            save_dir = os.path.join(
                config['media']['scan_paths'][0] if config['media']['scan_paths'] else 'E:/Videos',
                'douyin_sync'
            )
        
        syncer = DouyinSync()
        result = await syncer.sync_to_local(cookies, save_dir, user_id)
        
        return {
            "status": result['status'],
            "synced_count": result['downloaded'],
            "total_found": result['total_found'],
            "user_nickname": result.get('user_info', {}).get('nickname'),
            "save_dir": result['save_dir'],
            "message": f"成功同步 {result['downloaded']} 个作品"
        }
        
    except Exception as e:
        logger.error(f"抖音同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.post("/xiaohongshu")
async def sync_xiaohongshu(
    cookies: str,
    user_id: Optional[str] = None
):
    """
    同步小红书素材
    
    注意: 小红书API需要复杂的签名验证，此接口仅提供框架
    """
    try:
        syncer = XiaohongshuSync()
        syncer.set_cookies(cookies)
        
        return {
            "status": "limited",
            "message": "小红书同步需要额外的API验证，请使用抖音同步",
            "note": "小红书API需要逆向签名机制"
        }
        
    except Exception as e:
        logger.error(f"小红书同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.get("/status")
async def get_sync_status():
    """获取同步服务状态"""
    return {
        "supported_platforms": ["douyin", "xiaohongshu"],
        "douyin": "available",
        "xiaohongshu": "limited",
        "note": "抖音同步完整支持，小红书需要额外配置"
    }
