#!/bin/bash
# Docker 容器启动入口
# 1. 等待 PostgreSQL 就绪
# 2. 初始化数据库
# 3. 启动应用

set -e

echo "🦜 ParrotCare Backend 启动中..."

# 等待 PostgreSQL 就绪
if echo "$DATABASE_URL" | grep -q "postgresql"; then
    echo "⏳ 等待 PostgreSQL..."
    while ! python -c "
import urllib.parse, asyncpg, asyncio
url = '${DATABASE_URL}'
parsed = urllib.parse.urlparse(url)
asyncio.run(asyncpg.connect(
    host=parsed.hostname,
    port=parsed.port or 5432,
    user=parsed.username,
    password=parsed.password,
    database=parsed.path.lstrip('/')
))
" 2>/dev/null; do
        sleep 2
    done
    echo "✅ PostgreSQL 已就绪"
fi

# 初始化数据库表
echo "📋 初始化数据库..."
python -c "
import asyncio
from app.db import init_db
asyncio.run(init_db())
print('✅ 数据库初始化完成')
"

# 启动应用
echo "🚀 启动 FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
