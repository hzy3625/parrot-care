#!/usr/bin/env python3
"""
核心 API 自动化测试 — 消息归档功能
覆盖: Notification 模型 expires_at 字段、过期消息查询过滤

运行: pytest backend/tests/test_message_archive.py -v
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy import select, and_
from datetime import datetime, timedelta, timezone

from main import app
from app.models.database import Base, User, Notification, generate_id
from app.api.users import hash_password, create_token
from app.db import get_db

# ─── Fixtures ───────────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
test_session_maker = async_sessionmaker(
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


# ─── Notification 模型 expires_at 字段测试 ──────────────────


@pytest.mark.asyncio
async def test_notification_model_has_expires_at(db_session, test_user):
    """验证 Notification 模型支持 expires_at 字段"""
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=7)

    notification = Notification(
        notification_id=generate_id(),
        user_id=test_user.user_id,
        notification_type="system",
        title="带过期时间的消息",
        content="此消息将在7天后过期",
        expires_at=future,
    )
    db_session.add(notification)
    await db_session.commit()
    await db_session.refresh(notification)

    assert notification.expires_at is not None
    # SQLite may strip timezone info, compare without tz
    stored_expires = notification.expires_at
    if stored_expires.tzinfo is None:
        stored_expires = stored_expires.replace(tzinfo=timezone.utc)
    assert stored_expires > now


@pytest.mark.asyncio
async def test_notification_expires_at_nullable(db_session, test_user):
    """验证 expires_at 字段可为空（默认无过期）"""
    notification = Notification(
        notification_id=generate_id(),
        user_id=test_user.user_id,
        notification_type="system",
        title="永不过期的消息",
        content="此消息没有过期时间",
        expires_at=None,
    )
    db_session.add(notification)
    await db_session.commit()
    await db_session.refresh(notification)

    assert notification.expires_at is None


@pytest.mark.asyncio
async def test_notification_expired_vs_active(db_session, test_user):
    """验证过期消息和有效消息的区分"""
    now = datetime.now(timezone.utc)
    past = now - timedelta(days=1)
    future = now + timedelta(days=7)

    # 过期消息
    expired_notif = Notification(
        notification_id=generate_id(),
        user_id=test_user.user_id,
        notification_type="system",
        title="已过期消息",
        content="此消息已过期",
        expires_at=past,
    )
    db_session.add(expired_notif)

    # 有效消息
    active_notif = Notification(
        notification_id=generate_id(),
        user_id=test_user.user_id,
        notification_type="system",
        title="有效消息",
        content="此消息未过期",
        expires_at=future,
    )
    db_session.add(active_notif)

    # 无过期时间的消息
    no_expiry_notif = Notification(
        notification_id=generate_id(),
        user_id=test_user.user_id,
        notification_type="system",
        title="永久消息",
        content="此消息无过期时间",
        expires_at=None,
    )
    db_session.add(no_expiry_notif)

    await db_session.commit()

    # 查询未过期的消息: expires_at IS NULL OR expires_at > now
    result = await db_session.execute(
        select(Notification).where(
            and_(
                Notification.user_id == test_user.user_id,
                (Notification.expires_at.is_(None))
                | (Notification.expires_at > now),
            )
        )
    )
    active_notifications = result.scalars().all()
    assert len(active_notifications) == 2
    titles = {n.title for n in active_notifications}
    assert titles == {"有效消息", "永久消息"}

    # 查询已过期的消息: expires_at IS NOT NULL AND expires_at <= now
    result = await db_session.execute(
        select(Notification).where(
            and_(
                Notification.user_id == test_user.user_id,
                Notification.expires_at.is_not(None),
                Notification.expires_at <= now,
            )
        )
    )
    expired_notifications = result.scalars().all()
    assert len(expired_notifications) == 1
    assert expired_notifications[0].title == "已过期消息"


# ─── 消息创建 + expires_at 测试 ──────────────────────────────


@pytest.mark.asyncio
async def test_create_notification_with_expiry(auth_client):
    """通过 API 创建带过期时间的消息"""
    future = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    resp = await auth_client.post("/api/notifications", json={
        "notification_type": "feature_update",
        "title": "限时活动",
        "content": "此活动3天后结束",
        "expires_at": future,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "限时活动"
    assert "notification_id" in data


@pytest.mark.asyncio
async def test_create_notification_without_expiry(auth_client):
    """通过 API 创建不带过期时间的消息"""
    resp = await auth_client.post("/api/notifications", json={
        "notification_type": "system",
        "title": "系统消息",
        "content": "此消息不会过期",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "系统消息"


# ─── 过期消息过滤逻辑测试 ───────────────────────────────────


@pytest.mark.asyncio
async def test_expired_notification_still_in_list(auth_client, db_session, test_user):
    """过期消息仍然出现在列表中（当前API未过滤过期，仅验证字段存储）"""
    now = datetime.now(timezone.utc)
    past = now - timedelta(hours=1)

    notif = Notification(
        notification_id=generate_id(),
        user_id=test_user.user_id,
        notification_type="system",
        title="过期消息",
        content="已过期但仍在列表中",
        expires_at=past,
    )
    db_session.add(notif)
    await db_session.commit()

    resp = await auth_client.get("/api/notifications")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    titles = [n["title"] for n in data["notifications"]]
    assert "过期消息" in titles


@pytest.mark.asyncio
async def test_notification_with_different_expiry_times(db_session, test_user):
    """验证多条消息的不同过期时间"""
    now = datetime.now(timezone.utc)

    notifications = [
        Notification(
            notification_id=generate_id(),
            user_id=test_user.user_id,
            notification_type="system",
            title="1小时后过期",
            content="即将过期",
            expires_at=now + timedelta(hours=1),
        ),
        Notification(
            notification_id=generate_id(),
            user_id=test_user.user_id,
            notification_type="system",
            title="7天后过期",
            content="一周后过期",
            expires_at=now + timedelta(days=7),
        ),
        Notification(
            notification_id=generate_id(),
            user_id=test_user.user_id,
            notification_type="system",
            title="已过期1天",
            content="昨天过期",
            expires_at=now - timedelta(days=1),
        ),
        Notification(
            notification_id=generate_id(),
            user_id=test_user.user_id,
            notification_type="system",
            title="永久消息",
            content="不会过期",
            expires_at=None,
        ),
    ]

    for n in notifications:
        db_session.add(n)
    await db_session.commit()
    for n in notifications:
        await db_session.refresh(n)

    # 验证所有消息都能被查询到
    result = await db_session.execute(
        select(Notification).where(Notification.user_id == test_user.user_id)
    )
    all_notifs = result.scalars().all()
    assert len(all_notifs) == 4

    # 手动过滤：只获取未过期的
    result = await db_session.execute(
        select(Notification).where(
            and_(
                Notification.user_id == test_user.user_id,
                (Notification.expires_at.is_(None))
                | (Notification.expires_at > now),
            )
        )
    )
    active = result.scalars().all()
    assert len(active) == 3
    active_titles = {n.title for n in active}
    assert "已过期1天" not in active_titles


# ─── Notification 模型完整性测试 ─────────────────────────────


@pytest.mark.asyncio
async def test_notification_all_fields(db_session, test_user):
    """验证 Notification 所有字段完整存储"""
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=30)

    notif = Notification(
        notification_id=generate_id(),
        user_id=test_user.user_id,
        notification_type="health_alert",
        title="健康警报",
        content="检测到异常行为",
        is_read=False,
        related_parrot_id=None,
        related_event_id=None,
        expires_at=future,
    )
    db_session.add(notif)
    await db_session.commit()
    await db_session.refresh(notif)

    assert notif.notification_id is not None
    assert notif.user_id == test_user.user_id
    assert notif.notification_type == "health_alert"
    assert notif.title == "健康警报"
    assert notif.content == "检测到异常行为"
    assert notif.is_read is False
    # SQLite may strip timezone info, compare without tz
    stored_expires = notif.expires_at
    if stored_expires.tzinfo is None:
        stored_expires = stored_expires.replace(tzinfo=timezone.utc)
    assert stored_expires == future
    assert notif.created_at is not None
    assert notif.read_at is None

    # 标记已读后验证 read_at 被设置
    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    await db_session.commit()
    await db_session.refresh(notif)
    assert notif.read_at is not None


@pytest.mark.asyncio
async def test_notification_expires_at_boundary(db_session, test_user):
    """过期时间边界测试：刚好过期 vs 刚好未过期"""
    now = datetime.now(timezone.utc)

    # 刚好过期（expires_at == now - 1 second）
    just_expired = Notification(
        notification_id=generate_id(),
        user_id=test_user.user_id,
        notification_type="system",
        title="刚好过期",
        content="边界测试",
        expires_at=now - timedelta(seconds=1),
    )
    db_session.add(just_expired)

    # 刚好未过期（expires_at == now + 1 second）
    just_active = Notification(
        notification_id=generate_id(),
        user_id=test_user.user_id,
        notification_type="system",
        title="刚好未过期",
        content="边界测试",
        expires_at=now + timedelta(seconds=1),
    )
    db_session.add(just_active)
    await db_session.commit()

    # 查询未过期消息
    result = await db_session.execute(
        select(Notification).where(
            and_(
                Notification.user_id == test_user.user_id,
                (Notification.expires_at.is_(None))
                | (Notification.expires_at > now),
            )
        )
    )
    active = result.scalars().all()
    active_titles = {n.title for n in active}
    assert "刚好未过期" in active_titles
    assert "刚好过期" not in active_titles
