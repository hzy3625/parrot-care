"""
鍚姩鑴氭湰
"""

import asyncio
from app.db import init_db
from main import app
import uvicorn

async def startup():
    print("鍒濆鍖栨暟鎹簱...")
    await init_db()
    print("鏁版嵁搴撳垵濮嬪寲瀹屾垚")

if __name__ == "__main__":
    asyncio.run(startup())
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)