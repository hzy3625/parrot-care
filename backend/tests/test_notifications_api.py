#!/usr/bin/env python3
"""
核心 API 自动化测试 — Notifications 模块
覆盖: 创建消息、列表查询、未读数、标记已读、删除消息

运行: pytest backend/tests/test_notifications_api.py -v
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from main import app
from app.models.database import Base, User, Notification, generate_id
from app.api.users import hash_password, create_token
from app.db import get_db

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
test_session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


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
        email="test@example.com"
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


@pytest_asyncio.fixture(scope="function")
async def test_notifications(db_session, test_user):
    """创建多条测试消息"""
    notifs = []
    for i in range(5):
        n = Notification(
            notification_id=generate_id(),
            user_id=test_user.user_id,
            notification_type="abnormal_behavior" if i < 2 else "system",
            title=f"测试消息{i+1}",
            content=f"这是第{i+1}条测试消息",
            is_read=(i >= 3),
        )
        db_session.add(n)
        notifs.append(n)
    await db_session.commit()
    for n in notifs:
        await db_session.refresh(n)
    return notifs


# ─── 创建消息测试 ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_notification(auth_client):
    """创建站内消息"""
    resp = await auth_client.post("/api/notifications", json={
        "notification_type": "abnormal_behavior",
        "title": "尖叫警报",
        "content": "检测到您的鹦鹉持续尖叫5分钟"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "尖叫警报"
    assert data["is_read"] is False
    assert "notification_id" in data


# ─── 列表查询测试 ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_notifications(auth_client, test_notifications):
    """获取消息列表"""
    resp = await auth_client.get("/api/notifications")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert data["unread_count"] == 3  # 前三条未读
    assert len(data["notifications"]) == 5


@pytest.mark.asyncio
async def test_list_notifications_unread_only(auth_client, test_notifications):
    """只获取未读消息"""
    resp = await auth_client.get("/api/notifications", params={"unread_only": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert all(not n["is_read"] for n in data["notifications"])


@pytest.mark.asyncio
async def test_list_notifications_filter_type(auth_client, test_notifications):
    """按类型过滤消息"""
    resp = await auth_client.get("/api/notifications", params={"notification_type": "system"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert all(n["notification_type"] == "system" for n in data["notifications"])


@pytest.mark.asyncio
async def test_list_notifications_pagination(auth_client, test_notifications):
    """分页测试"""
    resp = await auth_client.get("/api/notifications", params={"page": 1, "page_size": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["notifications"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2


# ─── 未读数测试 ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_unread_count(auth_client, test_notifications):
    """获取未读消息数量"""
    resp = await auth_client.get("/api/notifications/unread-count")
    assert resp.status_code == 200
    assert resp.json()["unread_count"] == 3


@pytest.mark.asyncio
async def test_get_unread_count_zero(auth_client):
    """无消息时未读数为0"""
    resp = await auth_client.get("/api/notifications/unread-count")
    assert resp.status_code == 200
    assert resp.json()["unread_count"] == 0


# ─── 标记已读测试 ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_mark_single_read(auth_client, test_notifications):
    """标记单条消息已读"""
    unread = [n for n in test_notifications if not n.is_read][0]
    resp = await auth_client.patch(f"/api/notifications/{unread.notification_id}/read")
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True


@pytest.mark.asyncio
async def test_mark_batch_read(auth_client, test_notifications):
    """批量标记已读"""
    unread_ids = [n.notification_id for n in test_notifications if not n.is_read]
    resp = await auth_client.patch("/api/notifications/mark-read", json={
        "notification_ids": unread_ids
    })
    assert resp.status_code == 200
    assert resp.json()["updated_count"] == 3


@pytest.mark.asyncio
async def test_mark_read_empty_list(auth_client):
    """空列表标记已读 - 应报错"""
    resp = await auth_client.patch("/api/notifications/mark-read", json={
        "notification_ids": []
    })
    assert resp.status_code == 400


# ─── 删除消息测试 ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_notification(auth_client, test_notifications):
    """删除消息"""
    notif_id = test_notifications[0].notification_id
    resp = await auth_client.delete(f"/api/notifications/{notif_id}")
    assert resp.status_code == 200

    # 验证已删除
    resp = await auth_client.get("/api/notifications")
    assert resp.json()["total"] == 4


@pytest.mark.asyncio
async def test_delete_nonexistent_notification(auth_client):
    """删除不存在的消息"""
    resp = await auth_client.delete("/api/notifications/nonexistent-id")
    assert resp.status_code == 404


# ─── 无认证测试 ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_token_list(client):
    """无 token 访问消息列表"""
    resp = await client.get("/api/notifications")
    assert resp.status_code == 401  # No auth


@pytest.mark.asyncio
async def test_no_token_create(client):
    """无 token 创建消息"""
    resp = await client.post("/api/notifications", json={
        "notification_type": "test",
        "title": "test",
        "content": "test"
    })
    assert resp.status_code == 401  # No auth
