"""
启动脚本
"""

import asyncio
from app.db import init_db
from main import app
import uvicorn

async def startup():
    print("初始化数据库...")
    await init_db()
    print("数据库初始化完成")

if __name__ == "__main__":
    asyncio.run(startup())
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)