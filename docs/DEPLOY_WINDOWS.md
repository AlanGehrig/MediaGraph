# MediaGraph 部署手册 (Windows)

## 前置条件

### 1. 安装 Python
- Python 3.9+ 
- 下载地址: https://www.python.org/downloads/windows/

### 2. 安装 Neo4j

#### 方法一: Windows 安装包
1. 下载 Neo4j Desktop: https://neo4j.com/download/
2. 安装并启动
3. 创建数据库，设置密码为 `password123`

#### 方法二: Windows 服务
```powershell
# 使用 chocolatey 安装
choco install neo4j -y

# 启动 Neo4j
neo4j.bat console
```

### 3. 安装 Redis
```powershell
# 使用 chocolatey 安装
choco install redis-64 -y

# 启动 Redis
redis-server
```

### 4. 安装 FFmpeg (可选，用于视频处理)
```powershell
choco install ffmpeg -y
```

### 5. 安装 AI 模型 (可选)
CLIP 和 InsightFace 模型会在首次运行时自动下载。

## 安装步骤

### 1. 克隆或下载项目
```
E:\openclaw\data\MediaGraph\
```

### 2. 创建虚拟环境
```powershell
cd E:\openclaw\data\MediaGraph
python -m venv venv
.\venv\Scripts\activate
```

### 3. 安装依赖
```powershell
pip install -r requirements.txt
```

### 4. 初始化数据库
```powershell
python -m database.init_db
```

### 5. 配置扫描路径
编辑 `config/env.windows.yaml`，修改 `media.scan_paths` 为你的素材目录。

## 启动

### 一键启动
```powershell
.\start_media_graph.bat
```

### 手动启动

1. **启动 Neo4j**
```powershell
"C:\neo4j\bin\neo4j.bat" console
```

2. **启动 Redis**
```powershell
redis-server
```

3. **启动后端**
```powershell
cd backend
python main.py
```

4. **启动前端** (可选，有静态文件服务)
```powershell
cd frontend
python -m http.server 3000
```

## 验证安装

访问以下地址:
- API文档: http://localhost:8000/docs
- 前端: http://localhost:3000
- Neo4j Browser: http://localhost:7474

## 常见问题

### Q: Neo4j 连接失败
A: 确保 Neo4j 已启动，密码正确。检查 `config/neo4j.yaml` 配置。

### Q: CLIP 模型加载失败
A: 首次运行会自动下载模型。如有问题，检查网络连接。

### Q: 人脸检测不工作
A: 确保已安装 InsightFace。Windows 上可能需要安装 Visual C++ Redistributable。

### Q: 视频解析失败
A: 确保已安装 FFmpeg，并将其添加到 PATH。

## 卸载

1. 停止所有服务
2. 删除虚拟环境: `rmdir /s /q venv`
3. 删除数据目录: `rmdir /s /q data`
4. 删除备份目录: `rmdir /s /q backups`
