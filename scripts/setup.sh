#!/usr/bin/env bash
# 初始化开发环境
set -euo pipefail

echo "=== SAIL 开发环境初始化 ==="

echo "[1/5] 检查 Python 版本..."
python3 --version || { echo "需要 Python 3.11+"; exit 1; }

echo "[2/5] 安装依赖..."
pip install -e ".[dev]"

echo "[3/5] 启动基础设施..."
cd docker && docker-compose up -d mysql redis minio && cd ..

echo "[4/5] 等待 MySQL 就绪..."
sleep 5

echo "[5/5] 执行数据库迁移..."
alembic upgrade head || echo "迁移失败，请检查 MySQL 是否就绪"

echo "=== 完成 ==="
echo "API: http://localhost:8000"
echo "Flower: http://localhost:5555"
echo "MinIO Console: http://localhost:9001"
