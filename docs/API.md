# MediaGraph API 文档

## 基础信息

- 基础URL: `http://localhost:8000`
- API文档: `http://localhost:8000/docs` (Swagger UI)
- API文档: `http://localhost:8000/redoc` (ReDoc)

## 认证

当前版本无需认证。

---

## 系统接口

### 健康检查

```
GET /api/health
```

**响应示例:**
```json
{
  "status": "healthy",
  "neo4j": "connected",
  "chroma": "connected",
  "version": "1.0.0"
}
```

---

## 媒体管理

### 扫描素材

```
POST /api/media/scan
```

**请求体:**
```json
{
  "paths": ["E:/Photos", "E:/Videos"],
  "recursive": true,
  "force_rescan": false
}
```

**响应:**
```json
{
  "status": "success",
  "total_found": 150,
  "new_added": 50,
  "total_in_db": 150
}
```

### 获取媒体列表

```
GET /api/media/list
```

**参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量 |
| media_type | string | null | 过滤: image/video |
| parse_status | string | null | 过滤: pending/completed/failed |

### 获取单个媒体

```
GET /api/media/{media_id}
```

### AI解析媒体

```
POST /api/media/{media_id}/parse
```

**响应:**
```json
{
  "media_id": "abc123",
  "scene": "beach",
  "objects": ["person", "sky", "water"],
  "colors": ["blue", "warm"],
  "lighting": "natural",
  "mood": "happy",
  "composition": "rule_of_thirds",
  "tags": ["summer", "vacation"]
}
```

### 批量解析

```
POST /api/media/batch_parse
```

**请求体:**
```json
{
  "media_ids": ["id1", "id2", "id3"],
  "force": false
}
```

---

## 搜索

### 自然语言搜索

```
GET /api/search?q={query}
```

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| q | string | 搜索查询 (必填) |
| top_k | int | 返回数量 (默认10) |
| media_type | string | 过滤: image/video |

**示例查询:**
- `去年夏天的海边照片`
- `逆光人像`
- `开心的人`
- `城市夜景`

**响应:**
```json
{
  "query": "海边照片",
  "total": 25,
  "time_ms": 45.2,
  "results": [
    {
      "media_id": "abc123",
      "path": "E:/Photos/beach.jpg",
      "filename": "beach.jpg",
      "media_type": "image",
      "similarity": 0.95
    }
  ]
}
```

### 搜索建议

```
GET /api/search/suggestions?q={prefix}
```

---

## 知识图谱

### 获取人物列表

```
GET /api/graph/persons
```

**参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| min_media_count | int | 1 | 最少出现媒体数 |

### 获取人物详情

```
GET /api/graph/persons/{person_id}
```

### 获取人物媒体

```
GET /api/graph/persons/{person_id}/media
```

### 获取时间线

```
GET /api/graph/timeline
```

**参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| start_date | string | null | 开始日期 YYYY-MM-DD |
| end_date | string | null | 结束日期 YYYY-MM-DD |
| granularity | string | day | 时间粒度: day/month/year |

### 获取地点列表

```
GET /api/graph/locations
```

### 获取关系网络

```
GET /api/graph/relations
```

---

## 人脸聚类

### 获取聚类列表

```
GET /api/face/clusters
```

**参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| min_faces | int | 1 | 聚类最少人脸数 |
| force_refresh | bool | false | 是否强制刷新 |

### 获取聚类详情

```
GET /api/face/clusters/{cluster_id}
```

### 设置人物名称

```
POST /api/face/clusters/{cluster_id}/name?name={name}
```

### 人脸检测

```
POST /api/face/detect?media_id={id}&media_path={path}
```

### 人脸匹配

```
POST /api/face/match?media_id={id}&media_path={path}
```

### 重新聚类

```
POST /api/face/recluster?threshold={0.6}
```

---

## 数据统计

### 统计概览

```
GET /api/stats/overview
```

**响应:**
```json
{
  "total_media": 1500,
  "total_images": 1200,
  "total_videos": 300,
  "total_persons": 45,
  "total_faces": 230,
  "total_locations": 28,
  "storage_size_gb": 45.6
}
```

### 热门人物

```
GET /api/stats/persons/top?limit=10
```

### 热门地点

```
GET /api/stats/locations/top?limit=10
```

### 场景分布

```
GET /api/stats/scenes
```

### 情绪分布

```
GET /api/stats/mood
```

---

## 平台同步

### 同步抖音素材

```
POST /api/sync/douyin
```

**请求体:**
```json
{
  "cookies": "你的抖音cookies字符串",
  "user_id": null
}
```

**注意:** 需要在浏览器中登录抖音后获取cookies。

### 同步小红书素材

```
POST /api/sync/xiaohongshu
```

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
