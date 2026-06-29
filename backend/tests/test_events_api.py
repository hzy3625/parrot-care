#!/usr/bin/env python3
"""
核心 API 自动化测试 — Events 模块
覆盖: 创建事件(通过音频上传间接)、获取事件列表、获取事件详情、用户反馈

运行: pytest backend/tests/test_events_api.py -v
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone

from main import app
from app.models.database import (
    Base, User, Parrot, MediaEvent, UserFeedback, generate_id
)
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


@pytest_asyncio.fixture(scope="function")
async def test_parrot(db_session, test_user):
    """创建测试鹦鹉"""
    parrot = Parrot(
        parrot_id=generate_id(),
        user_id=test_user.user_id,
        name="小白",
        species="虎皮鹦鹉",
        age=2,
    )
    db_session.add(parrot)
    await db_session.commit()
    await db_session.refresh(parrot)
    return parrot


@pytest_asyncio.fixture(scope="function")
async def test_events(db_session, test_parrot):
    """创建多条测试事件"""
    events = []
    for i in range(5):
        event = MediaEvent(
            event_id=generate_id(),
            parrot_id=test_parrot.parrot_id,
            event_time=datetime.now(timezone.utc),
            event_type="normal_chirp" if i < 3 else "scream",
            media_type="audio",
            audio_url=f"media/test_{i}.wav",
            duration=5.0 + i,
            confidence=0.85 + i * 0.02,
            is_abnormal=(i >= 3),
            risk_level="low" if i < 3 else "medium",
        )
        db_session.add(event)
        events.append(event)
    await db_session.commit()
    for e in events:
        await db_session.refresh(e)
    return events


# ─── 获取事件列表测试 ───────────────────────────────────────


@pytest.mark.asyncio
async def test_list_events_success(auth_client, test_events):
    """获取事件列表 — 正常"""
    resp = await auth_client.get("/api/events")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    # 验证字段完整性
    first = data[0]
    assert "event_id" in first
    assert "parrot_id" in first
    assert "event_type" in first
    assert "is_abnormal" in first
    assert "risk_level" in first
    assert "confidence" in first


@pytest.mark.asyncio
async def test_list_events_empty(auth_client, test_parrot):
    """获取事件列表 — 无数据"""
    resp = await auth_client.get("/api/events")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_events_filter_parrot(auth_client, test_events, test_parrot):
    """按鹦鹉 ID 过滤事件"""
    resp = await auth_client.get("/api/events", params={"parrot_id": test_parrot.parrot_id})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    assert all(e["parrot_id"] == test_parrot.parrot_id for e in data)


@pytest.mark.asyncio
async def test_list_events_filter_abnormal(auth_client, test_events):
    """按异常状态过滤事件"""
    resp = await auth_client.get("/api/events", params={"is_abnormal": True})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2  # 后两条是异常的
    assert all(e["is_abnormal"] is True for e in data)


@pytest.mark.asyncio
async def test_list_events_filter_normal(auth_client, test_events):
    """按正常状态过滤事件"""
    resp = await auth_client.get("/api/events", params={"is_abnormal": False})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert all(e["is_abnormal"] is False for e in data)


@pytest.mark.asyncio
async def test_list_events_limit(auth_client, test_events):
    """限制返回数量"""
    resp = await auth_client.get("/api/events", params={"limit": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_events_order_by_time(auth_client, test_events):
    """验证事件按时间倒序排列"""
    resp = await auth_client.get("/api/events")
    assert resp.status_code == 200
    data = resp.json()
    timestamps = [e["event_time"] for e in data]
    assert timestamps == sorted(timestamps, reverse=True)


@pytest.mark.asyncio
async def test_list_events_no_auth(client):
    """无认证获取事件列表"""
    resp = await client.get("/api/events")
    assert resp.status_code == 401


# ─── 获取事件详情测试 ───────────────────────────────────────


@pytest.mark.asyncio
async def test_get_event_detail_success(auth_client, test_events):
    """获取事件详情 — 正常"""
    event_id = test_events[0].event_id
    resp = await auth_client.get(f"/api/events/{event_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["event_id"] == event_id
    assert data["event_type"] == "normal_chirp"
    assert data["parrot_id"] == test_events[0].parrot_id
    assert "audio_url" in data
    assert "duration" in data


@pytest.mark.asyncio
async def test_get_event_detail_not_found(auth_client):
    """获取事件详情 — 不存在"""
    resp = await auth_client.get("/api/events/nonexistent-event-id")
    assert resp.status_code == 404
    assert "不存在" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_get_event_detail_no_auth(client, test_events):
    """无认证获取事件详情"""
    resp = await client.get(f"/api/events/{test_events[0].event_id}")
    assert resp.status_code == 401


# ─── 用户反馈测试 ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_feedback_success(auth_client, test_events):
    """创建用户反馈 — 正常"""
    event_id = test_events[0].event_id
    resp = await auth_client.post(
        f"/api/events/{event_id}/feedback",
        json={
            "feedback_type": "misclassification",
            "feedback_label": "应为尖叫",
            "comment": "这段录音应该是尖叫而不是正常鸣叫",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["event_id"] == event_id
    assert data["feedback_type"] == "misclassification"
    assert data["feedback_label"] == "应为尖叫"
    assert "feedback_id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_feedback_minimal(auth_client, test_events):
    """创建用户反馈 — 仅必填字段"""
    event_id = test_events[1].event_id
    resp = await auth_client.post(
        f"/api/events/{event_id}/feedback",
        json={"feedback_type": "confirm"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["feedback_type"] == "confirm"
    assert data["feedback_label"] is None
    assert data["comment"] is None


@pytest.mark.asyncio
async def test_create_feedback_event_not_found(auth_client):
    """创建反馈 — 事件不存在"""
    resp = await auth_client.post(
        "/api/events/nonexistent-id/feedback",
        json={"feedback_type": "confirm"},
    )
    assert resp.status_code == 404
    assert "不存在" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_create_feedback_no_auth(client, test_events):
    """无认证创建反馈"""
    resp = await client.post(
        f"/api/events/{test_events[0].event_id}/feedback",
        json={"feedback_type": "confirm"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_feedback_missing_type(auth_client, test_events):
    """创建反馈 — 缺少必填字段"""
    event_id = test_events[0].event_id
    resp = await auth_client.post(
        f"/api/events/{event_id}/feedback",
        json={"comment": "缺少 feedback_type"},
    )
    assert resp.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_create_multiple_feedbacks(auth_client, test_events, db_session):
    """同一事件创建多条反馈"""
    event_id = test_events[0].event_id

    # 第一条反馈
    resp1 = await auth_client.post(
        f"/api/events/{event_id}/feedback",
        json={"feedback_type": "confirm", "comment": "分类正确"},
    )
    assert resp1.status_code == 200

    # 第二条反馈
    resp2 = await auth_client.post(
        f"/api/events/{event_id}/feedback",
        json={"feedback_type": "misclassification", "comment": "分类错误"},
    )
    assert resp2.status_code == 200

    # 验证数据库中有两条反馈
    from sqlalchemy import select

    result = await db_session.execute(
        select(UserFeedback).where(UserFeedback.event_id == event_id)
    )
    feedbacks = result.scalars().all()
    assert len(feedbacks) == 2


# ─── 跨用户隔离测试 ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_event_isolation_between_users(auth_client, test_events, db_session, test_parrot):
    """不同用户的事件隔离 — 不能访问其他用户的鹦鹉事件"""
    # 创建第二个用户和鹦鹉
    user2 = User(
        user_id=generate_id(),
        phone="13900139000",
        password_hash=hash_password("Pass1234"),
        nickname="用户2",
    )
    db_session.add(user2)

    parrot2 = Parrot(
        parrot_id=generate_id(),
        user_id=user2.user_id,
        name="小黑",
        species="牡丹鹦鹉",
    )
    db_session.add(parrot2)

    event2 = MediaEvent(
        event_id=generate_id(),
        parrot_id=parrot2.parrot_id,
        event_time=datetime.now(timezone.utc),
        event_type="scream",
        media_type="audio",
        is_abnormal=True,
        risk_level="high",
    )
    db_session.add(event2)
    await db_session.commit()

    # 用户1 不应看到用户2的事件
    resp = await auth_client.get("/api/events")
    assert resp.status_code == 200
    data = resp.json()
    event_ids = {e["event_id"] for e in data}
    assert event2.event_id not in event_ids

    # 直接访问用户2的事件详情应返回404
    resp = await auth_client.get(f"/api/events/{event2.event_id}")
    assert resp.status_code == 404
