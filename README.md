# MediaGraph
# 摄影师个人影像知识图谱系统
# 用自然语言搜索你的所有照片和视频

![MediaGraph](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

> 🎬 摄影师个人影像知识图谱系统
> 用自然语言搜索你的所有照片和视频

## 核心功能

- 🔍 **自然语言搜索**：输入"去年夏天在海边的照片"，直接出结果
- 👤 **人脸聚类**：自动识别同一人物的所有照片
- 🗂️ **知识图谱**：人物-时间-地点-场景关系可视化
- 🎬 **视频解析**：自动抽帧，分析视频内容
- 📊 **多模态AI**：场景/人物/情绪/光线/构图全维度提取

## 技术栈

- **AI**: CLIP + InsightFace（本地运行）
- **图数据库**: Neo4j
- **向量库**: Chroma
- **后端**: FastAPI
- **前端**: HTML/JS
- **平台**: Windows (Linux/Mac兼容)

## 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/AlanGehrig/MediaGraph.git
cd MediaGraph

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

编辑 `config/env.windows.yaml`:

```yaml
media:
  scan_paths:
    - E:/Photos
    - E:/Videos
```

### 3. 初始化数据库

```bash
python -m database.init_db
```

### 4. 启动

**Windows:**
```powershell
.\start_media_graph.bat
```

**Linux/Mac:**
```bash
chmod +x start_media_graph.sh
./start_media_graph.sh
```

### 5. 访问

- 前端界面: http://localhost:3000
- API文档: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474

## API 示例

### 自然语言搜索

```bash
curl "http://localhost:8000/api/search?q=海边照片"
```

### 扫描素材

```bash
curl -X POST "http://localhost:8000/api/media/scan"
```

### 获取人物

```bash
curl "http://localhost:8000/api/graph/persons"
```

## 项目结构

```
MediaGraph/
├── backend/              # FastAPI 后端
│   ├── api/             # API 路由
│   ├── models/          # 数据模型
│   └── sync/            # 平台同步
├── ai_core/             # AI 核心模块
│   ├── media_parser.py  # CLIP 多模态解析
│   ├── face_cluster.py  # InsightFace 人脸聚类
│   └── video_parser.py  # 视频关键帧抽帧
├── database/            # 数据库模块
│   ├── kg_builder.py    # Neo4j 图谱构建
│   └── vector_store.py  # Chroma 向量存储
├── scripts/             # 工具脚本
├── config/              # 配置文件
├── frontend/            # 前端界面
└── docs/                # 文档
```

## 系统要求

- Python 3.9+
- Neo4j 4.4+
- Redis 6+
- FFmpeg (视频处理可选)
- 16GB+ RAM (AI模型)
- NVIDIA GPU (可选，用于GPU加速)

## 文档

- [部署手册 (Windows)](docs/DEPLOY_WINDOWS.md)
- [API 文档](docs/API.md)
- [用户指南](docs/USER_GUIDE.md)

## 示例查询

| 查询 | 说明 |
|------|------|
| `去年夏天的海边照片` | 时间+地点+场景 |
| `逆光人像` | 光线+类型 |
| `开心的合照` | 情绪+人物数量 |
| `城市夜景` | 地点+时间 |
| `金秋十月的户外` | 时间+场景 |

## 作者

**AlanGehrig** | GitHub: [@AlanGehrig](https://github.com/AlanGehrig)

## License

MIT License - see [LICENSE](LICENSE)

---

*让 AI 成为你最好的摄影助理*
