# MediaGraph 一键安装启动脚本
# 使用方式：右键 -> 使用 PowerShell 运行（或双击后选择）

param(
    [string]$ScanPath = ""
)

$ErrorActionPreference = "Continue"
$ProjectRoot = $PSScriptRoot
$ConfigFile = Join-Path $ProjectRoot "config\env.windows.yaml"
$VenvPath = Join-Path $ProjectRoot "venv"
$BackendMain = Join-Path $ProjectRoot "backend\main.py"
$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"

function Write-Success { param($msg) Write-Host "[✓] $msg" -ForegroundColor Green }
function Write-Warn   { param($msg) Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Err    { param($msg) Write-Host "[✗] $msg" -ForegroundColor Red }
function Write-Info  { param($msg) Write-Host "[*] $msg" -ForegroundColor Cyan }

Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "   MediaGraph 一键安装启动脚本" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

# -----------------------------------------------
# 1. 询问照片文件夹路径
# -----------------------------------------------
if ([string]::IsNullOrWhiteSpace($ScanPath)) {
    Write-Info "请输入要扫描的照片文件夹路径"
    Write-Info "例如: E:\Photos"
    $ScanPath = Read-Host "路径"
}

if ([string]::IsNullOrWhiteSpace($ScanPath)) {
    Write-Err "路径不能为空，脚本退出"
    exit 1
}

# 转换为 YAML 兼容格式（正斜杠）
$ScanPathYaml = $ScanPath -replace '\\', '/'
if (-not $ScanPathYaml.EndsWith("/")) { $ScanPathYaml += "/" }

Write-Success "扫描路径: $ScanPath"

# -----------------------------------------------
# 2. 修改 config/env.windows.yaml 中的 scan_paths
# -----------------------------------------------
Write-Info "正在修改配置文件..."

if (-not (Test-Path $ConfigFile)) {
    Write-Err "配置文件不存在: $ConfigFile"
    exit 1
}

$configContent = Get-Content $ConfigFile -Raw -Encoding UTF8

# 使用正则替换 scan_paths 部分
$newScanSection = @"
  scan_paths:
    - `"$($ScanPathYaml -replace '/$', '')`"
"@

# 匹配并替换 scan_paths: 下面的所有路径行
$pattern = '(?s)  scan_paths:\s*\n(?:    - .+\n)+'
if ($configContent -match $pattern) {
    $configContent = $configContent -replace $pattern, $newScanSection
    $configContent | Set-Content $ConfigFile -Encoding UTF8 -NoNewline
    Write-Success "配置文件已更新: scan_paths -> $ScanPath"
} else {
    # 尝试更宽松的匹配
    $pattern2 = '(?s)scan_paths:\s*\n(\s*)-[^\n]+\n'
    if ($configContent -match $pattern2) {
        $replacement = "scan_paths:`n`$1""$($ScanPathYaml -replace '/$', '')""`n"
        $configContent = $configContent -replace $pattern2, $replacement
        $configContent | Set-Content $ConfigFile -Encoding UTF8 -NoNewline
        Write-Success "配置文件已更新: scan_paths -> $ScanPath"
    } else {
        Write-Warn "无法自动修改 scan_paths，请手动编辑: $ConfigFile"
    }
}

# -----------------------------------------------
# 3. 检查 Python 版本
# -----------------------------------------------
Write-Info "检查 Python 版本..."
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    $pythonVersion = py --version 2>&1
}
if ($LASTEXITCODE -ne 0) {
    Write-Err "未找到 Python，请先安装 Python 3.10+"
    Write-Host "下载地址: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}
Write-Success "Python 版本: $pythonVersion"

# -----------------------------------------------
# 4. 创建 venv（如果不存在）
# -----------------------------------------------
if (-not (Test-Path $VenvPath)) {
    Write-Info "正在创建虚拟环境..."
    python -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Err "虚拟环境创建失败"
        exit 1
    }
    Write-Success "虚拟环境已创建"
} else {
    Write-Success "虚拟环境已存在，跳过创建"
}

# 激活 venv
$VenvActivate = Join-Path $VenvPath "Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    & $VenvActivate
    Write-Success "虚拟环境已激活"
} else {
    Write-Err "虚拟环境激活脚本不存在"
    exit 1
}

# -----------------------------------------------
# 5. 安装依赖（跳过 Neo4j/Redis）
# -----------------------------------------------
Write-Info "正在安装依赖（跳过 Neo4j/Redis）..."

# 读取 requirements.txt，过滤掉 neo4j 和 redis
$reqLines = Get-Content $RequirementsFile
$filteredReqFile = Join-Path $ProjectRoot "requirements_filtered.txt"
$reqLines | Where-Object {
    $_ -notmatch '^\s*#' -and
    $_ -notmatch '^\s*$' -and
    $_ -notmatch '^\s*neo4j' -and
    $_ -notmatch '^\s*redis'
} | Set-Content $filteredReqFile -Encoding UTF8

pip install --upgrade pip --quiet
pip install -r $filteredReqFile --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Warn "部分依赖安装可能失败，继续尝试..."
} else {
    Write-Success "依赖安装完成"
}

# 清理临时文件
Remove-Item $filteredReqFile -ErrorAction SilentlyContinue

# -----------------------------------------------
# 6. 检查 OpenCV/CLIP/PyTorch
# -----------------------------------------------
Write-Info "检查关键依赖..."

$checkPyTorch = python -c "import torch; print(torch.__version__)" 2>&1
if ($LASTEXITCODE -eq 0) { Write-Success "PyTorch: $checkPyTorch" } else { Write-Warn "PyTorch: 未安装或导入失败" }

$checkOpenCV = python -c "import cv2; print(cv2.__version__)" 2>&1
if ($LASTEXITCODE -eq 0) { Write-Success "OpenCV: $checkOpenCV" } else { Write-Warn "OpenCV: 未安装或导入失败" }

$checkCLIP = python -c "import clip; print('CLIP OK')" 2>&1
if ($LASTEXITCODE -eq 0) { Write-Success "CLIP: 已安装" } else { Write-Warn "CLIP: 未安装或导入失败" }

$checkPillow = python -c "from PIL import Image; print('Pillow OK')" 2>&1
if ($LASTEXITCODE -eq 0) { Write-Success "Pillow: 已安装" } else { Write-Warn "Pillow: 未安装" }

# -----------------------------------------------
# 7. 启动后端
# -----------------------------------------------
Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "   启动 MediaGraph 后端服务" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""
Write-Success "后端启动中..."
Write-Info "访问地址: http://localhost:8000"
Write-Info "API 文档: http://localhost:8000/docs"
Write-Host ""

if (-not (Test-Path $BackendMain)) {
    Write-Err "后端入口文件不存在: $BackendMain"
    exit 1
}

# 启动后端（保持在 PowerShell 中运行）
python $BackendMain

# 如果后端退出，显示错误
Write-Err "后端服务已退出，按任意键关闭..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
