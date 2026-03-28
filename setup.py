"""
MediaGraph - 摄影师个人影像知识图谱系统
安装配置文件
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取 README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# 读取 requirements.txt
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip() 
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="mediagraph",
    version="1.0.0",
    author="AlanGehrig",
    author_email="",
    description="摄影师个人影像知识图谱系统 - 用自然语言搜索你的所有照片和视频",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AlanGehrig/MediaGraph",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21",
            "black>=23.0",
            "ruff>=0.1",
        ],
        "gpu": [
            "torch>=2.0",
            "torchvision>=0.15",
        ],
    },
    entry_points={
        "console_scripts": [
            "mediagraph=backend.main:main",
            "mediagraph-scan=scripts.scan_media:main",
            "mediagraph-init=database.init_db:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/*.yaml", "config/*.json"],
    },
    zip_safe=False,
)
