#!/usr/bin/env python3
"""
核心 API 自动化测试 — 个人信息管理
覆盖: 更新手机号（重复检测）、更新邮箱（重复检测）、通知偏好开关、profile 完整更新、边界情况

运行: pytest apps/api/tests/test_profile_management.py -v
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from main import app
from app.models.database import Base, User, generate_id
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
async def other_user(db_session):
    """第二个用户，用于测试重复检测"""
    user = User(
        user_id=generate_id(),
        phone="13900139000",
        password_hash=hash_password("Pass1234"),
        nickname="其他用户",
        email="other@example.com",
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


# ─── 获取个人信息测试 ───────────────────────────────────────


@pytest.mark.asyncio
async def test_get_profile_default_notifications(auth_client):
    """获取 profile — 默认通知偏好为 True"""
    resp = await auth_client.get("/api/users/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["notification_email"] is True
    assert data["notification_browser"] is True
    assert data["phone"] == "13800138000"
    assert data["email"] == "test@example.com"
    assert data["nickname"] == "测试用户"


# ─── 更新手机号测试 ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_phone_success(auth_client):
    """更新手机号 — 正常"""
    resp = await auth_client.put("/api/users/profile", json={
        "phone": "13700137000",
    })
    assert resp.status_code == 200
    assert resp.json()["phone"] == "13700137000"


@pytest.mark.asyncio
async def test_update_phone_duplicate(auth_client, other_user):
    """更新手机号 — 与其他用户重复"""
    resp = await auth_client.put("/api/users/profile", json={
        "phone": "13900139000",  # other_user 的手机号
    })
    assert resp.status_code == 400
    assert "手机号" in resp.json()["detail"]
    assert "已被使用" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_update_phone_same_as_own(auth_client, test_user):
    """更新手机号 — 与自己当前手机号相同（不应报错）"""
    resp = await auth_client.put("/api/users/profile", json={
        "phone": "13800138000",  # 自己的手机号
    })
    assert resp.status_code == 200
    assert resp.json()["phone"] == "13800138000"


# ─── 更新邮箱测试 ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_email_success(auth_client):
    """更新邮箱 — 正常"""
    resp = await auth_client.put("/api/users/profile", json={
        "email": "newemail@example.com",
    })
    assert resp.status_code == 200
    assert resp.json()["email"] == "newemail@example.com"


@pytest.mark.asyncio
async def test_update_email_duplicate(auth_client, other_user):
    """更新邮箱 — 与其他用户重复"""
    resp = await auth_client.put("/api/users/profile", json={
        "email": "other@example.com",  # other_user 的邮箱
    })
    assert resp.status_code == 400
    assert "邮箱" in resp.json()["detail"]
    assert "已被使用" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_update_email_same_as_own(auth_client, test_user):
    """更新邮箱 — 与自己当前邮箱相同（不应报错）"""
    resp = await auth_client.put("/api/users/profile", json={
        "email": "test@example.com",
    })
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"


# ─── 通知偏好开关测试 ───────────────────────────────────────


@pytest.mark.asyncio
async def test_update_notification_email_off(auth_client):
    """关闭邮件通知"""
    resp = await auth_client.put("/api/users/profile", json={
        "notification_email": False,
    })
    assert resp.status_code == 200
    assert resp.json()["notification_email"] is False
    assert resp.json()["notification_browser"] is True  # 其他保持不变


@pytest.mark.asyncio
async def test_update_notification_browser_off(auth_client):
    """关闭浏览器通知"""
    resp = await auth_client.put("/api/users/profile", json={
        "notification_browser": False,
    })
    assert resp.status_code == 200
    assert resp.json()["notification_browser"] is False
    assert resp.json()["notification_email"] is True  # 其他保持不变


@pytest.mark.asyncio
async def test_update_both_notifications_off(auth_client):
    """同时关闭两种通知"""
    resp = await auth_client.put("/api/users/profile", json={
        "notification_email": False,
        "notification_browser": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["notification_email"] is False
    assert data["notification_browser"] is False


@pytest.mark.asyncio
async def test_update_both_notifications_on(auth_client):
    """先关闭再打开通知"""
    # 关闭
    await auth_client.put("/api/users/profile", json={
        "notification_email": False,
        "notification_browser": False,
    })
    # 再打开
    resp = await auth_client.put("/api/users/profile", json={
        "notification_email": True,
        "notification_browser": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["notification_email"] is True
    assert data["notification_browser"] is True


@pytest.mark.asyncio
async def test_notification_toggle_persistence(auth_client):
    """通知偏好持久化 — 更新后重新获取"""
    # 更新偏好
    resp = await auth_client.put("/api/users/profile", json={
        "notification_email": False,
    })
    assert resp.status_code == 200

    # 重新获取验证
    resp = await auth_client.get("/api/users/profile")
    assert resp.status_code == 200
    assert resp.json()["notification_email"] is False


# ─── Profile 完整更新测试 ───────────────────────────────────


@pytest.mark.asyncio
async def test_update_full_profile(auth_client):
    """完整更新 profile — 所有字段同时更新"""
    resp = await auth_client.put("/api/users/profile", json={
        "nickname": "新昵称",
        "email": "new@example.com",
        "phone": "13700137000",
        "notification_email": False,
        "notification_browser": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["nickname"] == "新昵称"
    assert data["email"] == "new@example.com"
    assert data["phone"] == "13700137000"
    assert data["notification_email"] is False
    assert data["notification_browser"] is False


@pytest.mark.asyncio
async def test_update_full_profile_and_verify(auth_client):
    """完整更新后重新获取验证"""
    await auth_client.put("/api/users/profile", json={
        "nickname": "完整用户",
        "email": "complete@example.com",
        "phone": "13600136000",
        "notification_email": True,
        "notification_browser": False,
    })

    resp = await auth_client.get("/api/users/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["nickname"] == "完整用户"
    assert data["email"] == "complete@example.com"
    assert data["phone"] == "13600136000"
    assert data["notification_email"] is True
    assert data["notification_browser"] is False


@pytest.mark.asyncio
async def test_update_profile_empty_nickname(auth_client):
    """更新昵称为空字符串"""
    resp = await auth_client.put("/api/users/profile", json={
        "nickname": "",
    })
    assert resp.status_code == 200
    assert resp.json()["nickname"] == ""


# ─── 边界情况测试 ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_profile_empty_body(auth_client):
    """空请求体更新 — 不修改任何字段"""
    resp = await auth_client.put("/api/users/profile", json={})
    assert resp.status_code == 200
    data = resp.json()
    # 所有字段保持不变
    assert data["phone"] == "13800138000"
    assert data["email"] == "test@example.com"
    assert data["nickname"] == "测试用户"


@pytest.mark.asyncio
async def test_update_profile_duplicate_both(auth_client, other_user):
    """同时更新手机号和邮箱 — 两个都与其他用户重复"""
    resp = await auth_client.put("/api/users/profile", json={
        "phone": "13900139000",
        "email": "other@example.com",
    })
    # 应该在第一个重复检测时就报错
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_phone_then_email(auth_client, other_user):
    """分步更新手机号和邮箱 — 先更新一个再更新另一个"""
    # 更新手机号
    resp = await auth_client.put("/api/users/profile", json={
        "phone": "13700137000",
    })
    assert resp.status_code == 200

    # 更新邮箱
    resp = await auth_client.put("/api/users/profile", json={
        "email": "new@example.com",
    })
    assert resp.status_code == 200

    # 验证最终状态
    resp = await auth_client.get("/api/users/profile")
    data = resp.json()
    assert data["phone"] == "13700137000"
    assert data["email"] == "new@example.com"


@pytest.mark.asyncio
async def test_update_profile_nickname_only(auth_client):
    """仅更新昵称 — 其他字段不受影响"""
    original = (await auth_client.get("/api/users/profile")).json()

    resp = await auth_client.put("/api/users/profile", json={
        "nickname": "仅改昵称",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["nickname"] == "仅改昵称"
    # 其他字段不变
    assert data["phone"] == original["phone"]
    assert data["email"] == original["email"]
    assert data["notification_email"] == original["notification_email"]
    assert data["notification_browser"] == original["notification_browser"]


@pytest.mark.asyncio
async def test_profile_no_auth(client):
    """无认证获取 profile"""
    resp = await client.get("/api/users/profile")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_profile_no_auth(client):
    """无认证更新 profile"""
    resp = await client.put("/api/users/profile", json={
        "nickname": "hack",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_profile_invalid_email_format(auth_client):
    """更新邮箱 — 格式无效"""
    resp = await auth_client.put("/api/users/profile", json={
        "email": "not-an-email",
    })
    assert resp.status_code == 422  # Pydantic validation error
