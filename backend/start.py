"""
启动脚本 - 支持本地开发和 Docker 部署
自动检测数据库类型并初始化
"""

import asyncio
from app.db import init_db
from app.config import settings
from main import app
import uvicorn

async def startup():
    print(f"数据库: {settings.DATABASE_URL[:50]}...")
    print("初始化数据库...")
    await init_db()
    print("数据库初始化完成")

if __name__ == "__main__":
    asyncio.run(startup())
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=not settings.is_postgres  # 开发模式（SQLite）启用热重载
    )