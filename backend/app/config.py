"""
应用配置 - MVP 测试版本
"""

import os
from pathlib import Path

class Settings:
    # 数据库 - 使用 SQLite 进行 MVP 测试
    DATABASE_URL: str = f"sqlite+aiosqlite:///{Path(__file__).parent.parent}/parrotcare.db"
    
    # JWT
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60 * 24
    
    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "parrot-media"
    
    # AI
    AUDIO_MODEL_PATH: str = "models/audio_classifier.pt"

settings = Settings()