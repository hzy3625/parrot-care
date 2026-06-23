#!/usr/bin/env python3
"""
核心 API 自动化测试 — Users 模块
覆盖: 注册、登录、获取用户信息、密码重置、修改密码、个人信息管理

运行: pytest backend/tests/test_users_api.py -v
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


# ─── 注册测试 ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client):
    """正常注册"""
    resp = await client.post("/api/users/register", json={
        "phone": "13900139000",
        "password": "Pass1234",
        "nickname": "新用户",
        "email": "new@example.com"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_phone(client, test_user):
    """重复手机号注册"""
    resp = await client.post("/api/users/register", json={
        "phone": "13800138000",
        "password": "Pass1234",
        "nickname": "重复用户"
    })
    assert resp.status_code == 400
    assert "已注册" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_register_missing_password(client):
    """缺少密码字段"""
    resp = await client.post("/api/users/register", json={
        "phone": "13900139000"
    })
    assert resp.status_code == 422  # Pydantic validation error


# ─── 登录测试 ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client, test_user):
    """正常登录"""
    resp = await client.post("/api/users/login", json={
        "phone": "13800138000",
        "password": "TestPass123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client, test_user):
    """密码错误"""
    resp = await client.post("/api/users/login", json={
        "phone": "13800138000",
        "password": "WrongPass999"
    })
    assert resp.status_code == 401
    assert "错误" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_phone(client):
    """不存在的手机号"""
    resp = await client.post("/api/users/login", json={
        "phone": "99999999999",
        "password": "Pass1234"
    })
    assert resp.status_code == 401


# ─── 获取用户信息测试 ────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_success(auth_client):
    """获取当前用户信息"""
    resp = await auth_client.get("/api/users/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["phone"] == "13800138000"
    assert data["nickname"] == "测试用户"
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_me_no_token(client):
    """无 token 访问"""
    resp = await client.get("/api/users/me")
    assert resp.status_code == 401  # No credentials provided


@pytest.mark.asyncio
async def test_get_me_invalid_token(client):
    """无效 token"""
    client.headers.update({"Authorization": "Bearer invalid_token_123"})
    resp = await client.get("/api/users/me")
    assert resp.status_code == 401


# ─── 密码重置测试 ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_request_password_reset_existing_email(client, test_user):
    """请求密码重置 - 邮箱存在"""
    resp = await client.post("/api/users/reset-password", json={
        "email": "test@example.com"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "重置链接" in data["message"]


@pytest.mark.asyncio
async def test_request_password_reset_nonexistent_email(client):
    """请求密码重置 - 邮箱不存在（不应暴露邮箱是否存在）"""
    resp = await client.post("/api/users/reset-password", json={
        "email": "nonexistent@example.com"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True  # 安全考虑: 不暴露邮箱是否存在


@pytest.mark.asyncio
async def test_password_reset_flow(client, test_user, db_session):
    """完整密码重置流程: 请求 -> 获取 token -> 重置 -> 新密码登录"""
    from app.models.database import PasswordResetToken
    from sqlalchemy import select
    from datetime import datetime, timedelta, timezone

    # 1. 请求重置
    resp = await client.post("/api/users/reset-password", json={
        "email": "test@example.com"
    })
    assert resp.status_code == 200

    # 2. 从数据库获取 token
    result = await db_session.execute(
        select(PasswordResetToken).where(PasswordResetToken.user_id == test_user.user_id)
    )
    token_record = result.scalars().first()
    assert token_record is not None
    assert token_record.is_used == False

    # 3. 确认重置
    resp = await client.post(f"/api/users/reset-password/{token_record.token}", json={
        "token": token_record.token,
        "new_password": "NewPass456"
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # 4. 用新密码登录
    resp = await client.post("/api/users/login", json={
        "phone": "13800138000",
        "password": "NewPass456"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()

    # 5. 旧密码应该失败
    resp = await client.post("/api/users/login", json={
        "phone": "13800138000",
        "password": "TestPass123"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_password_reset_weak_password(client, test_user, db_session):
    """重置密码 - 密码强度不足"""
    from app.models.database import PasswordResetToken
    from sqlalchemy import select

    resp = await client.post("/api/users/reset-password", json={
        "email": "test@example.com"
    })
    result = await db_session.execute(
        select(PasswordResetToken).where(PasswordResetToken.user_id == test_user.user_id)
    )
    token_record = result.scalars().first()

    # 密码太短
    resp = await client.post(f"/api/users/reset-password/{token_record.token}", json={
        "token": token_record.token,
        "new_password": "abc123"
    })
    assert resp.status_code == 400
    assert "8位" in resp.json()["detail"]

    # 密码只有字母没数字
    resp = await client.post(f"/api/users/reset-password/{token_record.token}", json={
        "token": token_record.token,
        "new_password": "abcdefgh"
    })
    assert resp.status_code == 400
    assert "字母和数字" in resp.json()["detail"]

    # 密码只有数字没字母
    resp = await client.post(f"/api/users/reset-password/{token_record.token}", json={
        "token": token_record.token,
        "new_password": "12345678"
    })
    assert resp.status_code == 400
    assert "字母和数字" in resp.json()["detail"]


# ─── 修改密码测试 ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_change_password_success(auth_client):
    """修改密码 - 正常"""
    resp = await auth_client.post("/api/users/me/change-password", params={
        "old_password": "TestPass123",
        "new_password": "NewPass789"
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_change_password_wrong_old(auth_client):
    """修改密码 - 旧密码错误"""
    resp = await auth_client.post("/api/users/me/change-password", params={
        "old_password": "WrongOldPass",
        "new_password": "NewPass789"
    })
    assert resp.status_code == 400
    assert "旧密码" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_change_password_weak(auth_client):
    """修改密码 - 新密码强度不足"""
    resp = await auth_client.post("/api/users/me/change-password", params={
        "old_password": "TestPass123",
        "new_password": "short1"
    })
    assert resp.status_code == 400


# ─── 个人信息管理测试 ───────────────────────────────────────

@pytest.mark.asyncio
async def test_get_profile(auth_client):
    """获取个人信息"""
    resp = await auth_client.get("/api/users/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["phone"] == "13800138000"
    assert data["nickname"] == "测试用户"
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_update_profile_nickname(auth_client):
    """更新昵称"""
    resp = await auth_client.put("/api/users/profile", json={
        "nickname": "新昵称"
    })
    assert resp.status_code == 200
    assert resp.json()["nickname"] == "新昵称"


@pytest.mark.asyncio
async def test_update_profile_email(auth_client):
    """更新邮箱"""
    resp = await auth_client.put("/api/users/profile", json={
        "email": "newemail@example.com"
    })
    assert resp.status_code == 200
    assert resp.json()["email"] == "newemail@example.com"


@pytest.mark.asyncio
async def test_update_profile_notification_prefs(auth_client):
    """更新通知偏好"""
    resp = await auth_client.put("/api/users/profile", json={
        "notification_email": False,
        "notification_browser": False
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["notification_email"] is False
    assert data["notification_browser"] is False
