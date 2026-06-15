ParrotCare AI Backend - FastAPI Application - V0.4 Sprint 1
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
    # 启动时初始化数据库
    await init_db()
    yield
    # 关闭时清理

app = FastAPI(
    title="ParrotCare AI",
    description="鹦鹉健康行为监测系统 API - V0.4 Sprint 1",
    version="0.4.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(users.router, prefix="/api/users", tags=["用户"])
app.include_router(parrots.router, prefix="/api/parrots", tags=["鹦鹉"])
app.include_router(events.router, prefix="/api/events", tags=["事件"])
app.include_router(audio.router, prefix="/api/audio", tags=["音频"])
# Sprint 1: 站内消息
app.include_router(notifications.router, prefix="/api/notifications", tags=["消息中心"])

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
