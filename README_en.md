# MediaGraph
# Personal Media Knowledge Graph System for Photographers
# Natural language search for all your photos and videos

![MediaGraph](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

> 🎬 Personal Media Knowledge Graph System for Photographers
> Search all your photos and videos with natural language

## Core Features

- 🔍 **Natural Language Search**: "photos from last summer at the beach" → instant results
- 👤 **Face Clustering**: Automatically identify the same person across all photos
- 🗂️ **Knowledge Graph**: Person-Time-Location-Scene relationship visualization
- 🎬 **Video Parsing**: Auto frame extraction, analyze video content
- 📊 **Multi-modal AI**: Scene/People/Mood/Lighting/Composition extraction

## Tech Stack

- **AI**: CLIP + InsightFace (local running)
- **Graph Database**: Neo4j
- **Vector Store**: Chroma
- **Backend**: FastAPI
- **Frontend**: HTML/JS
- **Platform**: Windows (Linux/Mac compatible)

## Quick Start

### 1. Install Dependencies

```bash
# Clone project
git clone https://github.com/AlanGehrig/MediaGraph.git
cd MediaGraph

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

Edit `config/env.windows.yaml`:

```yaml
media:
  scan_paths:
    - E:/Photos
    - E:/Videos
```

### 3. Initialize Database

```bash
python -m database.init_db
```

### 4. Start

**Windows:**
```powershell
.\start_media_graph.bat
```

**Linux/Mac:**
```bash
chmod +x start_media_graph.sh
./start_media_graph.sh
```

### 5. Access

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474

## API Examples

### Natural Language Search

```bash
curl "http://localhost:8000/api/search?q=beach photos"
```

### Scan Media

```bash
curl -X POST "http://localhost:8000/api/media/scan"
```

### Get Persons

```bash
curl "http://localhost:8000/api/graph/persons"
```

## Project Structure

```
MediaGraph/
├── backend/              # FastAPI backend
│   ├── api/             # API routes
│   ├── models/          # Data models
│   └── sync/            # Platform sync
├── ai_core/             # AI core modules
│   ├── media_parser.py  # CLIP multi-modal parsing
│   ├── face_cluster.py  # InsightFace face clustering
│   └── video_parser.py  # Video keyframe extraction
├── database/            # Database modules
│   ├── kg_builder.py    # Neo4j graph builder
│   └── vector_store.py # Chroma vector store
├── scripts/             # Utility scripts
├── config/              # Configuration files
├── frontend/            # Frontend UI
└── docs/                # Documentation
```

## System Requirements

- Python 3.9+
- Neo4j 4.4+
- Redis 6+
- FFmpeg (optional for video processing)
- 16GB+ RAM (for AI models)
- NVIDIA GPU (optional for GPU acceleration)

## Documentation

- [Deployment Guide (Windows)](docs/DEPLOY_WINDOWS.md)
- [API Documentation](docs/API.md)
- [User Guide](docs/USER_GUIDE.md)

## Example Queries

| Query | Description |
|-------|-------------|
| `beach photos from last summer` | Time+Location+Scene |
| `backlit portrait` | Lighting+Type |
| `happy group photos` | Mood+People count |
| `city night scene` | Location+Time |
| `outdoor photos from golden October` | Scene+Time |

## Author

**AlanGehrig** | GitHub: [@AlanGehrig](https://github.com/AlanGehrig)

## License

MIT License - see [LICENSE](LICENSE)

---

*Let AI be your best photography assistant*
