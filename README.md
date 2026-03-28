# MediaGraph
## 摄影师个人影像知识图谱系统

![Python](https://img.shields.io/badge/python-3.9+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

> 🎬 用自然语言搜索你的所有照片和视频
> 基于 Neo4j 知识图谱 + Chroma 向量检索 + CLIP/InsightFace AI 的本地媒体管理系统

---

## 核心功能（真实实现）

| 功能 | 技术实现 | 说明 |
|------|---------|------|
| **🔍 自然语言搜索** | CLIP 向量检索 + Neo4j 图查询 | 输入"去年夏天的海边照片"，直接出结果 |
| **👤 人脸聚类** | InsightFace 人脸检测 + 余弦相似度聚类 | 自动识别同一人物的所有照片 |
| **🗂️ 知识图谱** | Neo4j 图数据库 | 人物-时间-地点-场景关系可视化 |
| **🎬 视频解析** | FFmpeg 抽帧 + CLIP 特征提取 | 提取关键帧，分析视频内容 |
| **📊 多模态AI** | CLIP + InsightFace 本地推理 | 场景/人物/情绪/光线/构图全维度提取 |

---

## 技术栈

| 组件 | 技术 | 作用 |
|------|------|------|
| **AI 模型** | CLIP ViT-L/14 + InsightFace ArcFace | 本地多模态理解，无需云服务 |
| **图数据库** | Neo4j Community 5.x | 存储人物、媒体、时间、地点关系 |
| **向量库** | Chroma | CLIP 图像特征向量相似度检索 |
| **后端** | FastAPI + Uvicorn | 高性能 Python API 服务 |
| **前端** | HTML/JS (原生，无框架) | 轻量级媒体管理界面 |
| **平台** | Windows (Linux/Mac 兼容) | 优先 Windows 开发体验 |

---

## 快速开始

### 一键启动（Windows）

```powershell
# 克隆项目
git clone https://github.com/AlanGehrig/MediaGraph.git
cd MediaGraph

# 安装依赖
pip install -r requirements.txt

# 一键启动（自动安装 Neo4j）
.\start_dev.bat
```

### 手动分步启动

**1. 安装 Neo4j（自动安装脚本）**

```powershell
# 自动下载安装 Neo4j Community Edition
.\scripts\install_neo4j.bat

# 或手动安装: https://neo4j.com/download/
```

**2. 启动服务**

```powershell
# 终端 1: 启动 Neo4j
.\neo4j\bin\neo4j console

# 终端 2: 启动后端
cd backend
python main.py

# 终端 3: 启动前端
cd frontend
python -m http.server 3000
```

### 3. 访问服务

- 前端界面: http://localhost:3000
- API 文档: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474

---

## 配置说明

编辑 `config/env.windows.yaml`:

```yaml
# 扫描路径
media:
  scan_paths:
    - E:/Photos
    - E:/Videos
    - E:/素材

# Neo4j 连接（默认本地）
neo4j:
  uri: bolt://localhost:7687
  user: neo4j
  password: password123  # 请在 Neo4j Browser 中修改

# Chroma 向量存储路径
chroma:
  persist_dir: E:/openclaw/data/MediaGraph/data/chroma

# API 端口
api:
  backend_port: 8000
  frontend_port: 3000
```

---

## API 示例

### 健康检查

```bash
curl http://localhost:8000/api/health
```

### 扫描媒体文件

```bash
curl -X POST "http://localhost:8000/api/media/scan" \
  -H "Content-Type: application/json" \
  -d '{"paths": ["E:/Photos"], "recursive": true}'
```

### 自然语言搜索

```bash
curl "http://localhost:8000/api/search?q=海边照片"
curl "http://localhost:8000/api/search?q=逆光人像"
curl "http://localhost:8000/api/search?q=去年夏天的照片"
```

### 获取人物列表

```bash
curl "http://localhost:8000/api/graph/persons"
```

### 获取时间线

```bash
curl "http://localhost:8000/api/graph/timeline"
```

### 获取人脸聚类

```bash
curl "http://localhost:8000/api/face/clusters"
```

---

## 项目结构

```
MediaGraph/
├── backend/                    # FastAPI 后端
│   ├── api/                   # API 路由
│   │   ├── media.py          # 媒体扫描/解析
│   │   ├── search.py         # 自然语言搜索
│   │   ├── graph.py          # 知识图谱查询
│   │   ├── face.py           # 人脸聚类
│   │   └── stats.py          # 数据统计
│   ├── models/               # Pydantic 数据模型
│   └── main.py               # FastAPI 主入口
│
├── ai_core/                   # AI 核心模块
│   ├── media_parser.py       # CLIP 图像/视频解析
│   ├── face_cluster.py       # InsightFace 人脸聚类
│   ├── video_parser.py       # FFmpeg 视频抽帧
│   └── model_config.py       # 模型配置
│
├── database/                  # 数据库模块
│   ├── kg_builder.py         # Neo4j 图谱构建
│   └── vector_store.py       # Chroma 向量存储
│
├── scripts/                   # 工具脚本
│   ├── install_neo4j.bat     # Neo4j 自动安装
│   └── scan_media.py         # 媒体扫描核心
│
├── config/                    # 配置文件
│   ├── env.windows.yaml      # Windows 配置
│   ├── env.linux.yaml        # Linux 配置
│   └── neo4j.yaml            # Neo4j 连接配置
│
├── frontend/                  # 前端界面
│   └── index.html            # 单页应用
│
├── data/                      # 数据目录
│   └── chroma/               # Chroma 向量数据
│
├── start_dev.bat              # 一键启动脚本
├── requirements.txt           # Python 依赖
└── README.md                  # 本文件
```

---

## 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|---------|---------|
| Python | 3.9+ | 3.10+ |
| Neo4j | 5.14 Community | 5.14 Community |
| RAM | 8GB | 16GB+ |
| 磁盘 | 10GB 可用 | 50GB+ SSD |
| GPU | 可选 | NVIDIA RTX 3070+ (加速 AI 推理) |

### 可选组件

- **FFmpeg**: 视频抽帧必需（自动安装脚本会提示）
- **Redis**: 可选，用于后台任务队列
- **NVIDIA GPU**: 加速 CLIP/InsightFace 推理（自动检测，无 GPU 则用 CPU）

---

## 故障排除

### Neo4j 无法启动

```powershell
# 检查 Java 是否安装
java -version

# 如提示找不到 Java，下载 JRE:
# https://adoptium.net/temurin/releases/?version=17
```

### Neo4j 端口被占用

```powershell
netstat -an | findstr "7687"
# 找到占用进程并关闭，或修改 neo4j.yaml 中的端口
```

### CLIP 模型下载失败

```powershell
# 手动下载 CLIP 模型
pip install -e git+https://github.com/openai/CLIP.git
```

### 前端无法访问后端

检查 CORS 配置，确保 `backend/main.py` 中的 `allow_origins` 包含前端地址。

### Chroma 向量搜索无结果

确认已完成媒体解析（`/api/media/{media_id}/parse`），CLIP 特征向量需要先提取才能搜索。

---

## 自然语言查询示例

| 查询 | 说明 | 内部转换 |
|------|------|---------|
| `去年夏天的海边照片` | 时间+地点+场景 | TIME=2025夏季, LOC=海边, SCENE=beach |
| `逆光人像` | 光线+类型 | LIGHT=backlight, TYPE=portrait |
| `开心的合照` | 情绪+人物数量 | MOOD=happy, COUNT>1 |
| `城市夜景` | 地点+时间 | LOC=urban, TIME=night |
| `金秋十月的户外` | 时间+场景 | TIME=10月, SCENE=outdoor |
| `室内柔光人像` | 光线+场景+类型 | LIGHT=soft, SCENE=indoor |

---

## 文档

- [部署手册 (Windows)](docs/DEPLOY_WINDOWS.md)
- [API 文档](docs/API.md)
- [用户指南](docs/USER_GUIDE.md)

---

## 作者

**AlanGehrig** | GitHub: [@AlanGehrig](https://github.com/AlanGehrig)

---

## License

MIT License - see [LICENSE](LICENSE)

---

*让 AI 成为你最好的摄影助理*
