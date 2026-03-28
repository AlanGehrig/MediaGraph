@echo off
chcp 65001 >nul 2>&1
title MediaGraph

echo.
echo ========================================
echo    MediaGraph 极简启动脚本
echo ========================================
echo.

cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
    echo [✓] 激活虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo [!] 虚拟环境不存在，正在安装依赖...
    pip install -r requirements.txt
)

echo.
echo [✓] 启动后端服务...
echo [*] 访问地址: http://localhost:8000
echo [*] API 文档:  http://localhost:8000/docs
echo.
python backend\main.py

echo.
echo [✗] 后端已退出，按任意键关闭...
pause >nul
