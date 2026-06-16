# -*- coding: utf-8 -*-
"""
推送设置 API 测试 - Sprint 2 P0-1
测试推送配置和 DND 设置的 CRUD
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.models.database import Base, User, generate_id
from app.api.users import hash_password, create_token
from app.db import get_db


# 内存数据库引擎
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

test_session_maker = async_session_maker = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with test_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session):
    user = User(
        user_id=generate_id(),
        phone="13800138000",
        password_hash=hash_password("TestPass123"),
        nickname="测试用户",
        email="test@example.com",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def auth_token(test_user):
    return create_token(test_user.user_id)


@pytest_asyncio.fixture(scope="function")
async def auth_client(client, auth_token):
    client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return client


# ==================== 推送设置测试 ====================

@pytest.mark.asyncio
class TestPushSettings:
    
    async def test_get_push_settings_default(self, auth_client):
        """获取推送设置 - 默认值"""
        resp = await auth_client.get("/api/settings/push")
        assert resp.status_code == 200
        data = resp.json()
        assert data["notification_email"] is True
        assert data["notification_browser"] is True
    
    async def test_update_push_settings_email_off(self, auth_client):
        """关闭邮件通知"""
        resp = await auth_client.put("/api/settings/push", json={
            "notification_email": False
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["notification_email"] is False
        assert data["notification_browser"] is True  # 不变
    
    async def test_update_push_settings_browser_off(self, auth_client):
        """关闭浏览器通知"""
        resp = await auth_client.put("/api/settings/push", json={
            "notification_browser": False
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["notification_email"] is True  # 不变
        assert data["notification_browser"] is False
    
    async def test_update_push_settings_both(self, auth_client):
        """同时关闭两个通知"""
        resp = await auth_client.put("/api/settings/push", json={
            "notification_email": False,
            "notification_browser": False
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["notification_email"] is False
        assert data["notification_browser"] is False
    
    async def test_update_push_settings_partial(self, auth_client):
        """部分更新 - 只传一个字段"""
        # 先关 email
        await auth_client.put("/api/settings/push", json={"notification_email": False})
        # 再关 browser
        resp = await auth_client.put("/api/settings/push", json={"notification_browser": False})
        assert resp.status_code == 200
        data = resp.json()
        assert data["notification_email"] is False  # 保持之前的状态
        assert data["notification_browser"] is False
    
    async def test_get_push_settings_unauthorized(self, client):
        """未认证访问 → 403"""
        resp = await client.get("/api/settings/push")
        assert resp.status_code in (403, 401)


# ==================== DND 设置测试 ====================

@pytest.mark.asyncio
class TestDndSettings:
    
    async def test_get_dnd_settings_default(self, auth_client):
        """获取 DND 设置 - 默认空"""
        resp = await auth_client.get("/api/settings/dnd")
        assert resp.status_code == 200
        data = resp.json()
        assert data["dnd_start"] is None
        assert data["dnd_end"] is None
    
    async def test_update_dnd_settings_cross_midnight(self, auth_client):
        """设置跨午夜 DND: 23:00-07:00"""
        resp = await auth_client.put("/api/settings/dnd", json={
            "dnd_start": "23:00",
            "dnd_end": "07:00"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["dnd_start"] == "23:00"
        assert data["dnd_end"] == "07:00"
    
    async def test_update_dnd_settings_daytime(self, auth_client):
        """设置日间 DND: 14:00-16:00"""
        resp = await auth_client.put("/api/settings/dnd", json={
            "dnd_start": "14:00",
            "dnd_end": "16:00"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["dnd_start"] == "14:00"
        assert data["dnd_end"] == "16:00"
    
    async def test_update_dnd_settings_clear(self, auth_client):
        """清空 DND 设置"""
        # 先设置
        await auth_client.put("/api/settings/dnd", json={
            "dnd_start": "23:00",
            "dnd_end": "07:00"
        })
        # 再清空
        resp = await auth_client.put("/api/settings/dnd", json={
            "dnd_start": None,
            "dnd_end": None
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["dnd_start"] is None
        assert data["dnd_end"] is None
    
    async def test_update_dnd_settings_invalid_format(self, auth_client):
        """无效时间格式 → 400"""
        resp = await auth_client.put("/api/settings/dnd", json={
            "dnd_start": "25:00",  # 无效
            "dnd_end": "07:00"
        })
        assert resp.status_code == 400
    
    async def test_update_dnd_settings_partial(self, auth_client):
        """部分更新 DND - 只传 dnd_start"""
        resp = await auth_client.put("/api/settings/dnd", json={
            "dnd_start": "22:00"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["dnd_start"] == "22:00"
        assert data["dnd_end"] is None
    
    async def test_get_dnd_settings_unauthorized(self, client):
        """未认证访问 → 403"""
        resp = await client.get("/api/settings/dnd")
        assert resp.status_code in (403, 401)
