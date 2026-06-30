"""
数据库连接 - 支持 SQLite 和 PostgreSQL
根据 DATABASE_URL 前缀自动选择连接方式
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.config import settings
from app.models.database import Base

# 根据数据库类型选择不同的引擎配置
if settings.is_sqlite:
    # SQLite 需要 StaticPool 和 check_same_thread
    engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
elif settings.is_postgres:
    # PostgreSQL - 使用连接池
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # 自动检测断开连接
    )
else:
    raise ValueError(
        f"不支持的数据库类型。DATABASE_URL 必须以 'sqlite' 或 'postgresql' 开头: {settings.DATABASE_URL}"
    )

async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库（创建所有表）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接池"""
    await engine.dispose()
