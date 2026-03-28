@echo off
REM MediaGraph 媒体文件扫描脚本
REM 用于后台扫描本地素材目录

echo ========================================
echo MediaGraph 媒体扫描工具
echo ========================================
echo.

REM 设置Python路径
set PYTHONPATH=%~dp0..
set SCRIPT_DIR=%~dp0

REM 默认扫描路径
set SCAN_PATH=E:\Photos

REM 检查是否指定了路径
if not "%1"=="" set SCAN_PATH=%1

echo 扫描路径: %SCAN_PATH%
echo.

REM 检查路径是否存在
if not exist "%SCAN_PATH%" (
    echo 错误: 路径不存在!
    echo %SCAN_PATH%
    pause
    exit /b 1
)

REM 运行扫描脚本
echo 开始扫描...
python "%SCRIPT_DIR%scan_media.py" "%SCAN_PATH%"

echo.
echo 扫描完成!
pause
