锘縋arrotCare AI Backend - FastAPI Application - V0.4 Sprint 1
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

from app.api import users, parrots, events, audio, notifications
from app.config import settings
from app.db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 鍚姩鏃跺垵濮嬪寲鏁版嵁搴?
    await init_db()
    yield
    # 鍏抽棴鏃舵竻鐞?

app = FastAPI(
    title="ParrotCare AI",
    description="楣﹂箟鍋ュ悍琛屼负鐩戞祴绯荤粺 API - V0.4 Sprint 1",
    version="0.4.0",
    lifespan=lifespan
)

# CORS 閰嶇疆
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 娉ㄥ唽璺敱
app.include_router(users.router, prefix="/api/users", tags=["鐢ㄦ埛"])
app.include_router(parrots.router, prefix="/api/parrots", tags=["楣﹂箟"])
app.include_router(events.router, prefix="/api/events", tags=["浜嬩欢"])
app.include_router(audio.router, prefix="/api/audio", tags=["闊抽"])
# Sprint 1: 绔欏唴娑堟伅
app.include_router(notifications.router, prefix="/api/notifications", tags=["娑堟伅涓績"])

@app.get("/")
async def root():
    return {"message": "ParrotCare AI Backend", "version": "0.4.0"}

@app.get("/health")
async def health():
    return {"status": "ok", "features": ["password_reset", "notification_center", "health_overview", "profile_management"]}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )
