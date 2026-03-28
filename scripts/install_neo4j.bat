@echo off
REM MediaGraph Neo4j 自动安装脚本
REM 检测并自动安装 Neo4j Community Edition (Windows版)
REM
REM 功能：
REM 1. 检测 Neo4j 是否已安装
REM 2. 如果未安装，自动下载并解压 Neo4j Community Edition
REM 3. 配置 Neo4j（关闭认证、设置路径）
REM 4. 启动 Neo4j 服务
REM
REM 作者: AlanGehrig
REM 版本: 1.0.0

setlocal enabledelayedexpansion

echo ========================================
echo MediaGraph - Neo4j 自动安装程序
echo ========================================
echo.

REM 设置项目根目录
set PROJECT_DIR=%~dp0..
cd /d "%PROJECT_DIR%"
set PROJECT_DIR=%CD%

REM 设置 Neo4j 安装路径
set NEO4J_HOME=%PROJECT_DIR%\neo4j
set NEO4J_VERSION=5.14.0
set NEO4J_URL=https://dist.neo4j.org/neo4j-community-%NEO4J_VERSION%-windows.zip
set NEO4J_ZIP=%PROJECT_DIR%\neo4j-community-%NEO4J_VERSION%-windows.zip

REM 检查 Neo4j 是否已安装
echo [检查] 查找 Neo4j 安装...
if exist "%NEO4J_HOME%\bin\neo4j.bat" (
    echo [OK] 发现已有的 Neo4j 安装: %NEO4J_HOME%
    set NEO4J_FOUND=1
    goto :check_service
)

if exist "C:\neo4j\bin\neo4j.bat" (
    echo [OK] 发现系统 Neo4j: C:\neo4j
    set NEO4J_HOME=C:\neo4j
    set NEO4J_FOUND=1
    goto :check_service
)

REM 未找到，询问是否安装
echo [未找到] 未检测到 Neo4j
echo.
set /p INSTALL_NEO4J="是否自动下载安装 Neo4j Community Edition 5.14.0? (Y/N): "
if /i not "%INSTALL_NEO4J%"=="Y" (
    echo [跳过] 跳过 Neo4j 安装
    echo [提示] 您可以手动安装 Neo4j: https://neo4j.com/download/
    exit /b 0
)

REM ========== 开始安装 ==========
echo.
echo [下载] 正在下载 Neo4j Community Edition...
echo        URL: %NEO4J_URL%
echo        目标: %NEO4J_ZIP%
echo.

REM 创建临时目录
if not exist "%PROJECT_DIR%\temp" mkdir "%PROJECT_DIR%\temp"

REM 使用 PowerShell 下载（支持进度显示）
powershell -Command "& {try { Start-BitsTransfer -Source '%NEO4J_URL%' -Destination '%NEO4J_ZIP%' -Description 'Neo4j Community Edition' -DisplayName 'Neo4j下载'; Write-Host '下载完成' } catch { Write-Host '下载失败:' $_; exit 1 } }"

if not exist "%NEO4J_ZIP%" (
    echo [错误] 下载失败，文件不存在
    exit /b 1
)

echo.
echo [解压] 正在解压 Neo4j...
powershell -Command "Expand-Archive -Path '%NEO4J_ZIP%' -DestinationPath '%PROJECT_DIR%' -Force"

REM 移动到正确位置
set EXTRACTED_DIR=%PROJECT_DIR%\neo4j-community-%NEO4J_VERSION%
if exist "%EXTRACTED_DIR%" (
    if exist "%NEO4J_HOME%" (
        REM 备份旧版本
        powershell -Command "Rename-Item -Path '%NEO4J_HOME%' -NewName 'neo4j_old_%date:~0,4%%date:~5,2%%date:~8,2%' -Force"
    )
    move "%EXTRACTED_DIR%" "%NEO4J_HOME%"
    echo [OK] Neo4j 解压到: %NEO4J_HOME%
)

REM 删除压缩包
del /f /q "%NEO4J_ZIP%" 2>nul

REM ========== 配置 Neo4j ==========
echo.
echo [配置] 配置 Neo4j...

REM 配置 Neo4j 关闭认证
set NEO4J_CONF=%NEO4J_HOME%\conf\neo4j.conf
if exist "%NEO4J_CONF%" (
    echo [配置] 设置 Neo4j 认证...
    
    REM 备份原配置文件
    copy /y "%NEO4J_CONF%" "%NEO4J_CONF%.bak" >nul
    
    REM 查找并替换 dbms.security.auth_enabled=true 为 false
    powershell -Command "(Get-Content '%NEO4J_CONF%') -replace 'dbms.security.auth_enabled=true', 'dbms.security.auth_enabled=false' | Set-Content '%NEO4J_CONF%'"
    
    REM 确保 serveruris 配置正确
    powershell -Command "$c = Get-Content '%NEO4J_CONF%'; if (-not ($c -match 'server.bolt.enabled')) { Add-Content '%NEO4J_CONF%' 'server.bolt.enabled=true' }; if (-not ($c -match 'server.http.enabled')) { Add-Content '%NEO4J_CONF%' 'server.http.enabled=true' }"
    
    echo [OK] 认证已禁用（仅用于本地开发）
) else (
    echo [警告] 未找到配置文件，跳过配置
)

REM 设置环境变量（可选）
echo [配置] 设置环境变量（可选）...
setx NEO4J_HOME "%NEO4J_HOME%" >nul 2>&1
setx PATH "%NEO4J_HOME%\bin;%PATH%" >nul 2>&1

echo [OK] 环境变量已设置

REM ========== 启动 Neo4j ==========
:check_service
echo.
echo [启动] 检查 Neo4j 服务状态...

REM 检查端口 7687 (Bolt) 和 7474 (HTTP)
netstat -an | findstr "7687" | findstr "LISTENING" >nul
if !errorlevel!==0 (
    echo [OK] Neo4j Bolt 端口(7687)已在监听
    set BOLT_RUNNING=1
) else (
    set BOLT_RUNNING=0
)

netstat -an | findstr "7474" | findstr "LISTENING" >nul
if !errorlevel!==0 (
    echo [OK] Neo4j HTTP 端口(7474)已在监听
    set HTTP_RUNNING=1
) else (
    set HTTP_RUNNING=0
)

if "!BOLT_RUNNING!"=="1" (
    echo.
    echo [完成] Neo4j 已在运行中！
    echo        Bolt:   bolt://localhost:7687
    echo        HTTP:   http://localhost:7474
    echo        用户:   neo4j (默认)
    echo        密码:   password123 (见配置文件)
    exit /b 0
)

echo [启动] 正在启动 Neo4j 服务...
echo        (首次启动可能需要1-2分钟初始化)
echo.

REM 启动 Neo4j (console模式，会在前台运行日志)
REM 使用 start "" 以新窗口启动
start "Neo4j Server" cmd /k "cd /d %NEO4J_HOME%\bin && neo4j console"

REM 等待启动
echo [等待] Neo4j 启动中，请稍候...
timeout /t 20 /nobreak >nul

REM 再次检查
netstat -an | findstr "7687" | findstr "LISTENING" >nul
if !errorlevel!==0 (
    echo.
    echo ========================================
    echo [完成] Neo4j 启动成功！
    echo ========================================
    echo.
    echo Neo4j 信息:
    echo   安装目录: %NEO4J_HOME%
    echo   Bolt:     bolt://localhost:7687
    echo   HTTP:     http://localhost:7474
    echo   Browser:  http://localhost:7474/browser
    echo.
    echo 连接参数:
    echo   用户名: neo4j
    echo   密码:   password123
    echo.
    echo 提示: Neo4j Browser 首次登录请使用默认用户名 neo4j
    echo       新安装的 Neo4j 默认密码是 neo4j，请及时修改
    echo.
) else (
    echo.
    echo [警告] Neo4j 可能启动较慢，请手动检查
    echo.
    echo 检查方法:
    echo   1. 查看 "Neo4j Server" 窗口是否有错误
    echo   2. 运行: netstat -an ^| findstr "7687"
    echo   3. 访问: http://localhost:7474
    echo.
)

exit /b 0
