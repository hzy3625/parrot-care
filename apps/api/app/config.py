"""
应用配置 - 支持环境变量覆盖
优先级: 环境变量 > .env 文件 > 默认值
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件（如果存在）
_env_path = Path(__file__).parent.parent / ".env"
_project_root = Path(__file__).resolve().parents[3]
if _env_path.exists():
    load_dotenv(_env_path)

class Settings:
    # 数据库 - 默认 SQLite（开发），Docker 环境使用 PostgreSQL
    # 通过环境变量 DATABASE_URL 覆盖，例如：
    #   SQLite:     sqlite+aiosqlite:///./parrotcare.db
    #   PostgreSQL: postgresql+asyncpg://postgres:password@db:5432/parrotcare
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{Path(__file__).parent.parent}/parrotcare.db"
    )

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60 * 24

    # MinIO
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "parrot-media")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"

    # AI
    AUDIO_MODEL_PATH: str = os.getenv(
        "AUDIO_MODEL_PATH",
        str(_project_root / "ml" / "models" / "audio_classifier.pt")
    )

    # 邮件 SMTP 配置
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    SMTP_FROM_EMAIL: Optional[str] = os.getenv("SMTP_FROM_EMAIL")

    # 应用
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    @property
    def is_postgres(self) -> bool:
        return self.DATABASE_URL.startswith("postgresql")

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

settings = Settings()
