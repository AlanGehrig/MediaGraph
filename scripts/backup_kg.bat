@echo off
REM MediaGraph 知识图谱备份脚本
REM 备份 Neo4j 数据库和 Chroma 向量存储

echo ========================================
echo MediaGraph 知识图谱备份
echo ========================================
echo.

REM 设置时间戳
for /f "tokens=2 delims==" %%a in ('wmic os get localdatetime /value') do set "dt=%%a"
set TIMESTAMP=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%_%dt:~8,2%-%dt:~10,2%

REM 备份目录
set BACKUP_DIR=E:\openclaw\data\MediaGraph\backups\%TIMESTAMP%

echo 创建备份目录: %BACKUP_DIR%
mkdir "%BACKUP_DIR%" 2>nul

REM 备份 Neo4j (如果Neo4j支持)
echo.
echo [1/2] 备份 Neo4j...
echo 注意: 请确保Neo4j服务正在运行
echo.
echo 请手动执行以下命令备份Neo4j:
echo   bin\neo4j-admin backup --from=localhost --database=graph.db --backup-dir="%BACKUP_DIR%\neo4j" --type=full
echo.

REM 备份 Chroma
echo [2/2] 备份 Chroma...
set CHROMA_DIR=E:\openclaw\data\MediaGraph\data\chroma

if exist "%CHROMA_DIR%" (
    xcopy /E /I /Y "%CHROMA_DIR%" "%BACKUP_DIR%\chroma\"
    echo Chroma 备份完成!
) else (
    echo Chroma 目录不存在，跳过
)

REM 备份配置
echo.
echo [3/3] 备份配置...
xcopy /I /Y "%~dp0..\config" "%BACKUP_DIR%\config\" 2>nul
echo 配置备份完成!

echo.
echo ========================================
echo 备份完成!
echo 备份位置: %BACKUP_DIR%
echo ========================================
echo.
echo 建议定期执行此备份脚本保护数据安全
echo.

pause
