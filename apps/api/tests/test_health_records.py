#!/usr/bin/env python3
"""
核心 API 自动化测试 — 健康档案功能
覆盖: 健康趋势计算、健康建议生成、健康评分区间状态判定、7天/30天统计

运行: pytest apps/api/tests/test_health_records.py -v
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from datetime import date, timedelta, datetime, timezone

from main import app
from app.models.database import (
    Base, User, Parrot, BehaviorDailyStat, generate_id,
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
session_maker = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with session_maker() as session:
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
        has_plucking_history=False,
        has_night_fright_history=False,
    )
    db_session.add(parrot)
    await db_session.commit()
    await db_session.refresh(parrot)
    return parrot


# ─── 辅助函数 ───────────────────────────────────────────────


async def create_stats(db_session, parrot_id, days, base_score=80, trend_delta=0):
    """创建 N 天的统计数据

    Args:
        base_score: 最近一天的 health_score
        trend_delta: 每天变化量（正=改善，负=恶化）
    """
    today = date.today()
    for i in range(days):
        stat = BehaviorDailyStat(
            stat_id=generate_id(),
            parrot_id=parrot_id,
            stat_date=today - timedelta(days=i),
            health_score=base_score - trend_delta * i,
            chirp_count=20,
            scream_count=2,
            night_activity_count=0,
            abnormal_event_count=1,
            active_minutes=120,
            quiet_minutes=60,
        )
        db_session.add(stat)
    await db_session.commit()


# ─── 7天和30天统计数据测试 ───────────────────────────────────


@pytest.mark.asyncio
async def test_health_overview_7day_stats(auth_client, db_session, test_parrot):
    """健康总览 — 7天统计数据"""
    await create_stats(db_session, test_parrot.parrot_id, days=7, base_score=85, trend_delta=0)

    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()

    assert data["current_health_score"] == 85
    assert data["avg_health_score_7days"] == 85.0
    assert data["total_abnormal_events_7days"] == 7  # 7 entries created, all within window
    assert data["health_trend"] == "stable"


@pytest.mark.asyncio
async def test_health_overview_30day_stats(auth_client, db_session, test_parrot):
    """健康总览 — 30天统计数据"""
    await create_stats(db_session, test_parrot.parrot_id, days=30, base_score=75, trend_delta=0)

    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()

    assert data["current_health_score"] == 75
    assert data["avg_health_score_30days"] == 75.0
    assert data["total_abnormal_events_30days"] == 30
    assert data["total_abnormal_events_7days"] == 8  # 7-day window catches 8 of 30 entries


@pytest.mark.asyncio
async def test_health_overview_7day_vs_30day(auth_client, db_session, test_parrot):
    """健康总览 — 7天和30天数据同时存在"""
    today = date.today()

    # 7天数据: 分数较高
    for i in range(7):
        stat = BehaviorDailyStat(
            stat_id=generate_id(),
            parrot_id=test_parrot.parrot_id,
            stat_date=today - timedelta(days=i),
            health_score=90,
            chirp_count=30,
            scream_count=1,
            night_activity_count=0,
            abnormal_event_count=0,
            active_minutes=180,
            quiet_minutes=30,
        )
        db_session.add(stat)

    # 8-30天数据: 分数较低（模拟之前状态不好，后来改善）
    for i in range(7, 30):
        stat = BehaviorDailyStat(
            stat_id=generate_id(),
            parrot_id=test_parrot.parrot_id,
            stat_date=today - timedelta(days=i),
            health_score=60,
            chirp_count=15,
            scream_count=5,
            night_activity_count=2,
            abnormal_event_count=3,
            active_minutes=90,
            quiet_minutes=120,
        )
        db_session.add(stat)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()

    # 当前分数（最近一天）
    assert data["current_health_score"] == 90
    # 7-day window catches 8 entries (>= today-7): 7 from 7-day data + 1 from 30-day data
    avg_expected = (90 * 7 + 60) / 8
    assert abs(data["avg_health_score_7days"] - round(avg_expected, 1)) < 0.1
    # 7-day abnormal: 0*7 + 3*1 = 3 (day 7 has 3 abnormal events)
    assert data["total_abnormal_events_7days"] == 3
    # 30-day abnormal: 0*7 + 3*23 = 69
    assert data["total_abnormal_events_30days"] == 69


# ─── 健康趋势计算测试 ───────────────────────────────────────


@pytest.mark.asyncio
async def test_health_trend_improving(auth_client, db_session, test_parrot):
    """健康趋势 — 改善中（最近几天分数高于之前）"""
    today = date.today()
    # 最近3天分数高，4-7天前分数低
    scores = [90, 88, 85, 70, 68, 65, 60]
    for i, score in enumerate(scores):
        stat = BehaviorDailyStat(
            stat_id=generate_id(),
            parrot_id=test_parrot.parrot_id,
            stat_date=today - timedelta(days=i),
            health_score=score,
            chirp_count=20,
            scream_count=2,
            night_activity_count=0,
            abnormal_event_count=1,
            active_minutes=120,
            quiet_minutes=60,
        )
        db_session.add(stat)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["health_trend"] == "improving"


@pytest.mark.asyncio
async def test_health_trend_declining(auth_client, db_session, test_parrot):
    """健康趋势 — 恶化中（最近几天分数低于之前）"""
    today = date.today()
    # 最近3天分数低，4-7天前分数高
    scores = [60, 62, 65, 80, 82, 85, 90]
    for i, score in enumerate(scores):
        stat = BehaviorDailyStat(
            stat_id=generate_id(),
            parrot_id=test_parrot.parrot_id,
            stat_date=today - timedelta(days=i),
            health_score=score,
            chirp_count=20,
            scream_count=2,
            night_activity_count=0,
            abnormal_event_count=1,
            active_minutes=120,
            quiet_minutes=60,
        )
        db_session.add(stat)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["health_trend"] == "declining"


@pytest.mark.asyncio
async def test_health_trend_stable(auth_client, db_session, test_parrot):
    """健康趋势 — 稳定（分数波动不大）"""
    today = date.today()
    scores = [80, 82, 78, 81, 79, 80, 82]
    for i, score in enumerate(scores):
        stat = BehaviorDailyStat(
            stat_id=generate_id(),
            parrot_id=test_parrot.parrot_id,
            stat_date=today - timedelta(days=i),
            health_score=score,
            chirp_count=20,
            scream_count=2,
            night_activity_count=0,
            abnormal_event_count=1,
            active_minutes=120,
            quiet_minutes=60,
        )
        db_session.add(stat)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["health_trend"] == "stable"


@pytest.mark.asyncio
async def test_health_trend_stable_with_less_than_3_days(auth_client, db_session, test_parrot):
    """健康趋势 — 数据不足3天时默认 stable"""
    today = date.today()
    for i in range(2):
        stat = BehaviorDailyStat(
            stat_id=generate_id(),
            parrot_id=test_parrot.parrot_id,
            stat_date=today - timedelta(days=i),
            health_score=50,
            chirp_count=10,
            scream_count=5,
            night_activity_count=2,
            abnormal_event_count=3,
            active_minutes=80,
            quiet_minutes=120,
        )
        db_session.add(stat)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["health_trend"] == "stable"


# ─── 健康评分区间状态判定测试 ───────────────────────────────


@pytest.mark.asyncio
async def test_health_status_healthy(auth_client, db_session, test_parrot):
    """健康状态 — 健康（score >= 80）"""
    today = date.today()
    stat = BehaviorDailyStat(
        stat_id=generate_id(),
        parrot_id=test_parrot.parrot_id,
        stat_date=today,
        health_score=85,
        chirp_count=30,
        scream_count=1,
        night_activity_count=0,
        abnormal_event_count=0,
        active_minutes=180,
        quiet_minutes=30,
    )
    db_session.add(stat)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["health_status"] == "健康"
    assert data["current_health_score"] == 85


@pytest.mark.asyncio
async def test_health_status_mild_abnormal(auth_client, db_session, test_parrot):
    """健康状态 — 轻度异常（60 <= score < 80）"""
    today = date.today()
    stat = BehaviorDailyStat(
        stat_id=generate_id(),
        parrot_id=test_parrot.parrot_id,
        stat_date=today,
        health_score=70,
        chirp_count=15,
        scream_count=3,
        night_activity_count=1,
        abnormal_event_count=2,
        active_minutes=100,
        quiet_minutes=80,
    )
    db_session.add(stat)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["health_status"] == "轻度异常"


@pytest.mark.asyncio
async def test_health_status_moderate_abnormal(auth_client, db_session, test_parrot):
    """健康状态 — 中度异常（40 <= score < 60）"""
    today = date.today()
    stat = BehaviorDailyStat(
        stat_id=generate_id(),
        parrot_id=test_parrot.parrot_id,
        stat_date=today,
        health_score=50,
        chirp_count=10,
        scream_count=6,
        night_activity_count=3,
        abnormal_event_count=5,
        active_minutes=60,
        quiet_minutes=150,
    )
    db_session.add(stat)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["health_status"] == "中度异常"


@pytest.mark.asyncio
async def test_health_status_risk(auth_client, db_session, test_parrot):
    """健康状态 — 健康风险（score < 40）"""
    today = date.today()
    stat = BehaviorDailyStat(
        stat_id=generate_id(),
        parrot_id=test_parrot.parrot_id,
        stat_date=today,
        health_score=30,
        chirp_count=5,
        scream_count=10,
        night_activity_count=5,
        abnormal_event_count=8,
        active_minutes=30,
        quiet_minutes=200,
    )
    db_session.add(stat)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["health_status"] == "健康风险"


@pytest.mark.asyncio
async def test_health_status_boundary_80(auth_client, db_session, test_parrot):
    """健康状态 — 边界值 score=80 应为健康"""
    today = date.today()
    stat = BehaviorDailyStat(
        stat_id=generate_id(),
        parrot_id=test_parrot.parrot_id,
        stat_date=today,
        health_score=80,
        chirp_count=20,
        scream_count=2,
        night_activity_count=0,
        abnormal_event_count=1,
        active_minutes=120,
        quiet_minutes=60,
    )
    db_session.add(stat)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["health_status"] == "健康"


@pytest.mark.asyncio
async def test_health_status_boundary_60(auth_client, db_session, test_parrot):
    """健康状态 — 边界值 score=60 应为轻度异常"""
    today = date.today()
    stat = BehaviorDailyStat(
        stat_id=generate_id(),
        parrot_id=test_parrot.parrot_id,
        stat_date=today,
        health_score=60,
        chirp_count=15,
        scream_count=3,
        night_activity_count=1,
        abnormal_event_count=2,
        active_minutes=100,
        quiet_minutes=80,
    )
    db_session.add(stat)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["health_status"] == "轻度异常"


@pytest.mark.asyncio
async def test_health_status_boundary_40(auth_client, db_session, test_parrot):
    """健康状态 — 边界值 score=40 应为中度异常"""
    today = date.today()
    stat = BehaviorDailyStat(
        stat_id=generate_id(),
        parrot_id=test_parrot.parrot_id,
        stat_date=today,
        health_score=40,
        chirp_count=8,
        scream_count=7,
        night_activity_count=4,
        abnormal_event_count=6,
        active_minutes=50,
        quiet_minutes=160,
    )
    db_session.add(stat)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["health_status"] == "中度异常"


@pytest.mark.asyncio
async def test_health_status_no_data(auth_client, db_session, test_parrot):
    """健康状态 — 无数据时默认健康"""
    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_health_score"] == 100
    assert data["health_status"] == "健康"


# ─── 健康建议生成逻辑测试 ───────────────────────────────────


@pytest.mark.asyncio
async def test_recommendations_many_abnormal_events(auth_client, db_session, test_parrot):
    """健康建议 — 异常事件多"""
    await create_stats(db_session, test_parrot.parrot_id, days=7, base_score=70, trend_delta=0)
    # 手动增加 abnormal_event_count
    today = date.today()
    for i in range(7):
        stat = BehaviorDailyStat(
            stat_id=generate_id(),
            parrot_id=test_parrot.parrot_id,
            stat_date=today - timedelta(days=i),
            health_score=70,
            chirp_count=10,
            scream_count=5,
            night_activity_count=2,
            abnormal_event_count=2,  # 每天2个异常 → 7天共14个 > 5
            active_minutes=80,
            quiet_minutes=120,
        )
        db_session.add(stat)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert any("异常事件" in r or "生活环境" in r for r in data["recommendations"])


@pytest.mark.asyncio
async def test_recommendations_plucking_history(auth_client, db_session, test_user):
    """健康建议 — 有啄羽历史"""
    parrot = Parrot(
        parrot_id=generate_id(),
        user_id=test_user.user_id,
        name="拔羽鸟",
        species="灰鹦鹉",
        age=3,
        has_plucking_history=True,
        has_night_fright_history=False,
    )
    db_session.add(parrot)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert any("羽毛" in r or "拔羽" in r for r in data["recommendations"])


@pytest.mark.asyncio
async def test_recommendations_night_fright_history(auth_client, db_session, test_user):
    """健康建议 — 有夜惊历史"""
    parrot = Parrot(
        parrot_id=generate_id(),
        user_id=test_user.user_id,
        name="夜惊鸟",
        species="虎皮鹦鹉",
        age=2,
        has_plucking_history=False,
        has_night_fright_history=True,
    )
    db_session.add(parrot)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert any("夜惊" in r or "安静" in r for r in data["recommendations"])


@pytest.mark.asyncio
async def test_recommendations_low_health_score(auth_client, db_session, test_parrot):
    """健康建议 — 健康评分低"""
    today = date.today()
    stat = BehaviorDailyStat(
        stat_id=generate_id(),
        parrot_id=test_parrot.parrot_id,
        stat_date=today,
        health_score=50,
        chirp_count=5,
        scream_count=8,
        night_activity_count=3,
        abnormal_event_count=5,
        active_minutes=40,
        quiet_minutes=180,
    )
    db_session.add(stat)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert any("兽医" in r for r in data["recommendations"])


@pytest.mark.asyncio
async def test_recommendations_healthy_parrot(auth_client, db_session, test_parrot):
    """健康建议 — 健康鹦鹉默认建议"""
    today = date.today()
    stat = BehaviorDailyStat(
        stat_id=generate_id(),
        parrot_id=test_parrot.parrot_id,
        stat_date=today,
        health_score=95,
        chirp_count=30,
        scream_count=1,
        night_activity_count=0,
        abnormal_event_count=0,
        active_minutes=180,
        quiet_minutes=20,
    )
    db_session.add(stat)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{test_parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    # 应该有默认的良好建议
    assert len(data["recommendations"]) > 0
    assert any("保持" in r or "良好" in r for r in data["recommendations"])


@pytest.mark.asyncio
async def test_recommendations_multiple_conditions(auth_client, db_session, test_user):
    """健康建议 — 多条件同时满足"""
    parrot = Parrot(
        parrot_id=generate_id(),
        user_id=test_user.user_id,
        name="多问题鸟",
        species="灰鹦鹉",
        age=5,
        has_plucking_history=True,
        has_night_fright_history=True,
    )
    db_session.add(parrot)

    today = date.today()
    for i in range(7):
        stat = BehaviorDailyStat(
            stat_id=generate_id(),
            parrot_id=parrot.parrot_id,
            stat_date=today - timedelta(days=i),
            health_score=50,
            chirp_count=5,
            scream_count=8,
            night_activity_count=3,
            abnormal_event_count=2,
            active_minutes=40,
            quiet_minutes=180,
        )
        db_session.add(stat)
    await db_session.commit()

    resp = await auth_client.get(f"/api/parrots/{parrot.parrot_id}/health-overview")
    assert resp.status_code == 200
    data = resp.json()
    recs = data["recommendations"]
    # 应该有多条建议
    assert len(recs) >= 3
    # 检查各类建议都存在
    all_recs = " ".join(recs)
    assert "羽毛" in all_recs or "拔羽" in all_recs
    assert "夜惊" in all_recs or "安静" in all_recs
    assert "兽医" in all_recs
    assert "异常事件" in all_recs or "生活环境" in all_recs
