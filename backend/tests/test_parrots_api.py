#!/usr/bin/env python3
"""
核心 API 自动化测试 — Parrots 模块
覆盖: 创建鹦鹉、列表查询、今日摘要、健康档案总览

运行: pytest backend/tests/test_parrots_api.py -v
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone

from main import app
from app.models.database import Base, User, Parrot, BehaviorDailyStat, generate_id
from app.api.users import hash_password, create_token
from app.db import get_db

# ─── Fixtures ───────────────────────────────────────────────

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


# ─── 创建鹦鹉测试 ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_parrot_success(auth_client):
    """正常创建鹦鹉"""
    resp = await auth_client.post("/api/parrots", json={
        "name": "小白",
        "species": "虎皮鹦鹉",
        "age": 2,
        "gender": "male",
        "weight": "35.5",
        "has_plucking_history": False,
        "has_night_fright_history": False
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "小白"
    assert data["species"] == "虎皮鹦鹉"
    assert data["age"] == 2
    assert "parrot_id" in data


@pytest.mark.asyncio
async def test_create_parrot_minimal(auth_client):
    """创建鹦鹉 - 仅必填字段"""
    resp = await auth_client.post("/api/parrots", json={
        "name": "小绿",
        "species": "牡丹鹦鹉"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "小绿"
    assert data["age"] is None


@pytest.mark.asyncio
async def test_create_parrot_missing_name(auth_client):
    """创建鹦鹉 - 缺少必填字段"""
    resp = await auth_client.post("/api/parrots", json={
        "species": "虎皮鹦鹉"
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_parrot_no_auth(client):
    """未认证创建鹦鹉"""
    resp = await client.post("/api/parrots", json={
        "name": "小白",
        "species": "虎皮鹦鹉"
    })
    assert resp.status_code == 401  # No auth provided


# ─── 列表查询测试 ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_parrots_empty(auth_client):
    """查询鹦鹉列表 - 空"""
    resp = await auth_client.get("/api/parrots")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_parrots_with_data(auth_client):
    """查询鹦鹉列表 - 有数据"""
    # 创建两只鹦鹉
    await auth_client.post("/api/parrots", json={"name": "小白", "species": "虎皮鹦鹉"})
    await auth_client.post("/api/parrots", json={"name": "小绿", "species": "牡丹鹦鹉"})

    resp = await auth_client.get("/api/parrots")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    names = {p["name"] for p in data}
    assert names == {"小白", "小绿"}


# ─── 今日摘要测试 ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_today_summary_no_data(auth_client):
    """今日摘要 - 无数据"""
    create_resp = await auth_client.post("/api/parrots", json={
        "name": "小白", "species": "虎皮鹦鹉"
    })
    parrot_id = create_resp.json()["parrot_id"]

    resp = await auth_client.get(f"/api/parrots/{parrot_id}/today-summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["health_score"] == 100
    assert data["chirp_count"] == 0
    assert data["status"] == "正常"


@pytest.mark.asyncio
async def test_today_summary_nonexistent_parrot(auth_client):
    """今日摘要 - 鹦鹉不存在"""
    resp = await auth_client.get("/api/parrots/nonexistent-id/today-summary")
    assert resp.status_code == 404


# ─── 健康档案总览测试 ───────────────────────────────────────

@pytest.mark.asyncio
async def test_health_overview_no_data(auth_client):
    """健康总览 - 无统计数据"""
    create_resp = await auth_client.post("/api/parrots", json={
        "name": "小白", "species": "虎皮鹦鹉"
    })
    parrot_id = create_resp.json()["parrot_id"]

    resp = await auth_client.get(f"/api/parrots/{parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_health_score"] == 100
    assert data["health_status"] == "健康"
    assert data["health_trend"] == "stable"
    assert len(data["recommendations"]) > 0


@pytest.mark.asyncio
async def test_health_overview_nonexistent_parrot(auth_client):
    """健康总览 - 鹦鹉不存在"""
    resp = await auth_client.get("/api/parrots/nonexistent-id/health-overview")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_health_overview_with_stats(auth_client, db_session, test_user):
    """健康总览 - 有统计数据"""
    from datetime import date, timedelta

    # 创建鹦鹉
    parrot = Parrot(
        parrot_id=generate_id(),
        user_id=test_user.user_id,
        name="小白",
        species="虎皮鹦鹉",
        age=2,
        has_plucking_history=True,
        has_night_fright_history=False
    )
    db_session.add(parrot)

    # 添加7天统计数据
    today = date.today()
    for i in range(7):
        stat = BehaviorDailyStat(
            stat_id=generate_id(),
            parrot_id=parrot.parrot_id,
            stat_date=today - timedelta(days=i),
            health_score=80 - i * 2,  # 递减趋势
            chirp_count=20,
            scream_count=2 + i,
            night_activity_count=0,
            abnormal_event_count=1 + i,
            active_minutes=120,
            quiet_minutes=60,
        )
        db_session.add(stat)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["parrot_name"] == "小白"
    assert data["current_health_score"] == 80
    assert data["total_abnormal_events_7days"] == sum(1 + i for i in range(7))
    # 健康趋势应该是 improving（最近几天比之前高）
    assert data["health_trend"] == "improving"
    # 有啄羽历史应该出现在建议中
    assert any("拔羽" in r or "羽毛" in r for r in data["recommendations"])


# ─── 全鹦鹉健康总览测试 ─────────────────────────────────────

@pytest.mark.asyncio
async def test_all_health_overview_empty(auth_client):
    """全鹦鹉健康总览 - 无鹦鹉"""
    resp = await auth_client.get("/api/parrots/health-overview")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_all_health_overview_with_parrots(auth_client):
    """全鹦鹉健康总览 - 有鹦鹉"""
    await auth_client.post("/api/parrots", json={"name": "小白", "species": "虎皮鹦鹉"})
    await auth_client.post("/api/parrots", json={"name": "小绿", "species": "牡丹鹦鹉"})

    resp = await auth_client.get("/api/parrots/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
