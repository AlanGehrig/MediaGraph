#!/bin/bash
# MediaGraph 一键启动脚本 (Linux/Mac)

echo "========================================"
echo "MediaGraph 摄影师影像知识图谱系统"
echo "========================================"
echo ""

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    exit 1
fi

# 启动 Neo4j (如果未运行)
echo "[1/4] 检查 Neo4j..."
if ! nc -z localhost 7687 2>/dev/null; then
    echo "启动 Neo4j..."
    if command -v neo4j &> /dev/null; then
        neo4j start
    else
        echo "警告: Neo4j 未安装，请手动启动"
    fi
    sleep 15
else
    echo "Neo4j 已运行"
fi

# 启动 Redis (如果未运行)
echo ""
echo "[2/4] 检查 Redis..."
if ! nc -z localhost 6379 2>/dev/null; then
    echo "启动 Redis..."
    if command -v redis-server &> /dev/null; then
        redis-server --daemonize yes
    else
        echo "警告: Redis 未安装，请手动启动"
    fi
    sleep 5
else
    echo "Redis 已运行"
fi

# 启动后端服务
echo ""
echo "[3/4] 启动后端服务 (端口 8000)..."
cd "$PROJECT_DIR/backend"
nohup python3 main.py > "$PROJECT_DIR/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo "后端 PID: $BACKEND_PID"
sleep 5

# 启动前端
echo ""
echo "[4/4] 启动前端 (端口 3000)..."
cd "$PROJECT_DIR/frontend"
nohup python3 -m http.server 3000 > "$PROJECT_DIR/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "前端 PID: $FRONTEND_PID"

# 创建日志目录
mkdir -p "$PROJECT_DIR/logs"

# 完成
echo ""
echo "========================================"
echo "MediaGraph 启动完成!"
echo "========================================"
echo ""
echo "访问地址:"
echo "  前端界面: http://localhost:3000"
echo "  API文档:  http://localhost:8000/docs"
echo "  Neo4j:    http://localhost:7474"
echo ""
echo "日志文件:"
echo "  后端: $PROJECT_DIR/logs/backend.log"
echo "  前端: $PROJECT_DIR/logs/frontend.log"
echo ""
echo "停止服务: kill $BACKEND_PID $FRONTEND_PID"
echo ""

# 自动打开浏览器
if command -v open &> /dev/null; then
    open http://localhost:3000
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
fi
