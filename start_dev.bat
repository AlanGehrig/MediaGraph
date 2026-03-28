@echo off
REM MediaGraph 一键启动开发环境脚本
REM 自动安装 Neo4j（如需要）并启动所有服务
REM
REM 功能：
REM 1. 检测并自动安装 Neo4j（如未安装）
REM 2. 启动 Neo4j 数据库
REM 3. 启动 FastAPI 后端服务
REM 4. 打开前端界面
REM
REM 作者: AlanGehrig
REM 版本: 1.0.0

setlocal enabledelayedexpansion

echo ========================================
echo MediaGraph 开发环境一键启动
echo ========================================
echo.

REM 设置项目根目录
set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"
set PROJECT_DIR=%CD%

echo [信息] 项目目录: %PROJECT_DIR%
echo.

REM ========== 步骤 1: 检查并安装 Neo4j ==========
echo [步骤 1/4] 检查 Neo4j...
echo.

REM 检查 Neo4j 是否运行
netstat -an | findstr "7687" | findstr "LISTENING" >nul
if !errorlevel!==0 (
    echo [OK] Neo4j 已在运行 (端口 7687)
    set NEO4J_RUNNING=1
) else (
    echo [检查] Neo4j 未运行，尝试启动...
    
    REM 检查 Neo4j 是否已安装
    if exist "%PROJECT_DIR%\neo4j\bin\neo4j.bat" (
        echo [启动] 从项目目录启动 Neo4j...
        start "Neo4j Server - MediaGraph" cmd /k "cd /d "%PROJECT_DIR%\neo4j\bin" && neo4j console"
        set NEO4J_RUNNING=0
    ) else (
        if exist "C:\neo4j\bin\neo4j.bat" (
            echo [启动] 从系统目录启动 Neo4j...
            start "Neo4j Server - MediaGraph" cmd /k "cd /d C:\neo4j\bin && neo4j console"
            set NEO4J_RUNNING=0
        ) else (
            echo [安装] Neo4j 未安装，运行自动安装程序...
            call "%PROJECT_DIR%\scripts\install_neo4j.bat"
            set NEO4J_RUNNING=0
        )
    )
)

REM 等待 Neo4j 启动（如果刚才启动的话）
if "!NEO4J_RUNNING!"=="0" (
    echo.
    echo [等待] 等待 Neo4j 启动...
    echo        (首次启动需要约 20-30 秒)
    timeout /t 15 /nobreak >nul
    
    REM 验证启动
    netstat -an | findstr "7687" | findstr "LISTENING" >nul
    if !errorlevel!==0 (
        echo [OK] Neo4j 启动成功
    ) else (
        echo [警告] Neo4j 可能仍在启动中，继续后续步骤...
    )
)

REM ========== 步骤 2: 启动后端服务 ==========
echo.
echo [步骤 2/4] 启动后端服务 (FastAPI, 端口 8000)...
echo.

REM 检查端口 8000 是否被占用
netstat -an | findstr ":8000" | findstr "LISTENING" >nul
if !errorlevel!==0 (
    echo [警告] 端口 8000 已被占用，可能已有后端在运行
    set /p CONTINUE="是否继续? (Y/N): "
    if /i not "!CONTINUE!"=="Y" (
        echo [取消] 启动已取消
        exit /b 0
    )
)

REM 启动后端（在新窗口）
start "MediaGraph Backend" cmd /k "cd /d "%PROJECT_DIR%\backend" && python main.py"

echo [启动] 后端服务启动中，请稍候...
timeout /t 5 /nobreak >nul

REM 检查后端是否启动
netstat -an | findstr ":8000" | findstr "LISTENING" >nul
if !errorlevel!==0 (
    echo [OK] 后端服务已启动 (http://localhost:8000)
) else (
    echo [警告] 后端可能仍在启动中，继续...
)

REM ========== 步骤 3: 启动前端 ==========
echo.
echo [步骤 3/4] 启动前端界面 (端口 3000)...
echo.

REM 检查端口 3000
netstat -an | findstr ":3000" | findstr "LISTENING" >nul
if !errorlevel!==0 (
    echo [警告] 端口 3000 已被占用
) else (
    REM 启动简单 HTTP 服务器作为前端
    start "MediaGraph Frontend" cmd /k "cd /d "%PROJECT_DIR%\frontend" && python -m http.server 3000"
    echo [启动] 前端启动中...
)

timeout /t 3 /nobreak >nul

REM ========== 步骤 4: 打开浏览器 ==========
echo.
echo [步骤 4/4] 打开浏览器...
echo.

REM 检查并打开浏览器
start http://localhost:3000

REM ========== 完成 ==========
echo.
echo ========================================
echo MediaGraph 开发环境启动完成！
echo ========================================
echo.
echo 服务状态:
echo   前端界面:  http://localhost:3000
echo   API文档:   http://localhost:8000/docs
echo   Neo4j:     http://localhost:7474
echo.
echo 注意事项:
echo   1. Neo4j Browser 首次访问需要设置密码
echo   2. 首次启动 AI 模型需要下载（约 500MB）
echo   3. 如遇问题，查看各服务窗口的错误日志
echo.
echo 按任意键退出此窗口（服务继续运行）...
pause >nul
