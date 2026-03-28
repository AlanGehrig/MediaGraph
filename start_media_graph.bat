@echo off
REM MediaGraph 一键启动脚本 (Windows)
REM 确保所有依赖已安装: pip install -r requirements.txt

echo ========================================
echo MediaGraph 摄影师影像知识图谱系统
echo ========================================
echo.

REM 设置项目路径
set PROJECT_DIR=E:\openclaw\data\MediaGraph
cd /d %PROJECT_DIR%

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python 未安装或未添加到PATH
    pause
    exit /b 1
)

REM 启动 Neo4j (如果未运行)
echo [1/4] 检查 Neo4j...
netstat -an | findstr "7687" >nul
if errorlevel 1 (
    echo 启动 Neo4j...
    start "" "C:\neo4j\bin\neo4j.bat" console
    echo 等待 Neo4j 启动...
    timeout /t 15 /nobreak >nul
) else (
    echo Neo4j 已运行
)

REM 启动 Redis (如果未运行)
echo.
echo [2/4] 检查 Redis...
netstat -an | findstr "6379" >nul
if errorlevel 1 (
    echo 启动 Redis...
    start redis-server
    timeout /t 5 /nobreak >nul
) else (
    echo Redis 已运行
)

REM 启动后端服务
echo.
echo [3/4] 启动后端服务 (端口 8000)...
cd /d %PROJECT_DIR%\backend
start "MediaGraph Backend" python main.py
timeout /t 5 /nobreak >nul

REM 启动前端 (可选)
echo.
echo [4/4] 启动前端 (端口 3000)...
cd /d %PROJECT_DIR%\frontend
start "MediaGraph Frontend" python -m http.server 3000

REM 完成
echo.
echo ========================================
echo MediaGraph 启动完成!
echo ========================================
echo.
echo 访问地址:
echo   前端界面: http://localhost:3000
echo   API文档:  http://localhost:8000/docs
echo   Neo4j:    http://localhost:7474
echo.
echo 按任意键打开浏览器...
pause >nul

start http://localhost:3000
