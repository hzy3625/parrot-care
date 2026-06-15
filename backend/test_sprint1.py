# -*- coding: utf-8 -*-
"""
Sprint 1 鑷姩鍖栨祴璇?- ParrotCare API
pytest + httpx + pytest-asyncio
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta, date
import secrets

from app.models.database import User, PasswordResetToken, Notification, Parrot, BehaviorDailyStat, generate_id
from app.api.users import hash_password


# ==================== 鐢ㄦ埛璁よ瘉娴嬭瘯 ====================

@pytest.mark.asyncio
async def test_register_new_user(client):
    response = await client.post(
        "/api/users/register",
        json={"phone": "13900139000", "password": "NewPass123", "nickname": "鏂扮敤鎴?}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_phone(client, test_user):
    response = await client.post(
        "/api/users/register",
        json={"phone": "13800138000", "password": "AnotherPass123"}
    )
    assert response.status_code == 400
    assert "宸叉敞鍐? in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client, test_user):
    response = await client.post(
        "/api/users/login",
        json={"phone": "13800138000", "password": "TestPass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client, test_user):
    response = await client.post(
        "/api/users/login",
        json={"phone": "13800138000", "password": "WrongPassword123"}
    )
    assert response.status_code == 401
    assert "閿欒" in response.json()["detail"]


# ==================== 瀵嗙爜閲嶇疆娴嬭瘯 ====================

@pytest.mark.asyncio
async def test_request_password_reset(client, test_user, db_session):
    response = await client.post(
        "/api/users/reset-password",
        json={"email": "test@example.com"}
    )
    assert response.status_code == 200
    assert response.json()["success"]


@pytest.mark.asyncio
async def test_password_reset_frequency_limit(client, test_user, db_session):
    for i in range(3):
        await client.post(
            "/api/users/reset-password",
            json={"email": "test@example.com"}
        )
    
    response = await client.post(
        "/api/users/reset-password",
        json={"email": "test@example.com"}
    )
    assert response.status_code == 429
    assert "棰戠箒" in response.json()["detail"]


@pytest.mark.asyncio
async def test_confirm_password_reset(client, test_user, db_session):
    reset_token = secrets.token_urlsafe(32)
    token_record = PasswordResetToken(
        token_id=generate_id(),
        user_id=test_user.user_id,
        token=reset_token,
        email=test_user.email,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    db_session.add(token_record)
    await db_session.commit()
    
    response = await client.post(
        f"/api/users/reset-password/{reset_token}",
        json={"token": reset_token, "new_password": "NewSecurePass123"}
    )
    assert response.status_code == 200
    assert "宸查噸缃? in response.json()["message"]


@pytest.mark.asyncio
async def test_confirm_expired_token(client, test_user, db_session):
    expired_token = secrets.token_urlsafe(32)
    token_record = PasswordResetToken(
        token_id=generate_id(),
        user_id=test_user.user_id,
        token=expired_token,
        email=test_user.email,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    db_session.add(token_record)
    await db_session.commit()
    
    response = await client.post(
        f"/api/users/reset-password/{expired_token}",
        json={"token": expired_token, "new_password": "AnotherPass123"}
    )
    assert response.status_code == 400
    assert "杩囨湡" in response.json()["detail"]


@pytest.mark.asyncio
async def test_password_strength_validation(client, test_user, db_session):
    reset_token = secrets.token_urlsafe(32)
    token_record = PasswordResetToken(
        token_id=generate_id(),
        user_id=test_user.user_id,
        token=reset_token,
        email=test_user.email,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    db_session.add(token_record)
    await db_session.commit()
    
    response = await client.post(
        f"/api/users/reset-password/{reset_token}",
        json={"token": reset_token, "new_password": "weak"}
    )
    assert response.status_code == 400
    
    response2 = await client.post(
        f"/api/users/reset-password/{reset_token}",
        json={"token": reset_token, "new_password": "12345678"}
    )
    assert response2.status_code == 400


# ==================== 涓汉淇℃伅娴嬭瘯 ====================

@pytest.mark.asyncio
async def test_get_profile(auth_client):
    response = await auth_client.get("/api/users/profile")
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert data["phone"] == "13800138000"


@pytest.mark.asyncio
async def test_update_profile(auth_client):
    response = await auth_client.put(
        "/api/users/profile",
        json={"nickname": "鏇存柊鏄电О", "email": "updated@example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nickname"] == "鏇存柊鏄电О"
    assert data["email"] == "updated@example.com"


@pytest.mark.asyncio
async def test_update_duplicate_email(auth_client, db_session):
    other_user = User(
        user_id=generate_id(),
        phone="13900139001",
        password_hash=hash_password("OtherPass123"),
        email="other@example.com"
    )
    db_session.add(other_user)
    await db_session.commit()
    
    response = await auth_client.put(
        "/api/users/profile",
        json={"email": "other@example.com"}
    )
    assert response.status_code == 400
    assert "宸茶浣跨敤" in response.json()["detail"]


@pytest.mark.asyncio
async def test_change_password(auth_client):
    response = await auth_client.post(
        "/api/users/me/change-password?old_password=TestPass123&new_password=NewPass456"
    )
    assert response.status_code == 200
    assert "宸蹭慨鏀? in response.json()["message"]


@pytest.mark.asyncio
async def test_change_password_wrong_old(auth_client):
    response = await auth_client.post(
        "/api/users/me/change-password?old_password=WrongOldPass&new_password=NewPass789"
    )
    assert response.status_code == 400
    assert "涓嶆纭? in response.json()["detail"]


# ==================== 娑堟伅涓績娴嬭瘯 ====================

@pytest.mark.asyncio
async def test_create_notification(auth_client):
    response = await auth_client.post(
        "/api/notifications",
        json={
            "notification_type": "system",
            "title": "娴嬭瘯娑堟伅",
            "content": "杩欐槸涓€鏉℃祴璇曢€氱煡"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "娴嬭瘯娑堟伅"
    assert data["is_read"] == False


@pytest.mark.asyncio
async def test_list_notifications(auth_client):
    for i in range(5):
        await auth_client.post(
            "/api/notifications",
            json={
                "notification_type": "system",
                "title": f"娑堟伅{i}",
                "content": f"鍐呭{i}"
            }
        )
    
    response = await auth_client.get("/api/notifications?page=1&page_size=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data["notifications"]) == 3
    assert data["total"] >= 5


@pytest.mark.asyncio
async def test_unread_count(auth_client):
    await auth_client.post(
        "/api/notifications",
        json={"notification_type": "system", "title": "鏈", "content": "test"}
    )
    
    response = await auth_client.get("/api/notifications/unread-count")
    assert response.status_code == 200
    assert response.json()["unread_count"] >= 1


@pytest.mark.asyncio
async def test_mark_notification_read(auth_client):
    create_resp = await auth_client.post(
        "/api/notifications",
        json={"notification_type": "system", "title": "寰呮爣璁?, "content": "test"}
    )
    notification_id = create_resp.json()["notification_id"]
    
    response = await auth_client.patch(f"/api/notifications/{notification_id}/read")
    assert response.status_code == 200
    assert response.json()["is_read"] == True


@pytest.mark.asyncio
async def test_mark_all_read(auth_client):
    ids = []
    for i in range(3):
        resp = await auth_client.post(
            "/api/notifications",
            json={"notification_type": "system", "title": f"鎵归噺{i}", "content": "test"}
        )
        ids.append(resp.json()["notification_id"])
    
    response = await auth_client.patch(
        "/api/notifications/mark-read",
        json={"notification_ids": ids}
    )
    assert response.status_code == 200
    assert response.json()["updated_count"] == 3


# ==================== 鍋ュ悍妗ｆ娴嬭瘯 ====================

@pytest.mark.asyncio
async def test_health_overview_single(auth_client, db_session, test_user):
    parrot = Parrot(
        parrot_id=generate_id(),
        user_id=test_user.user_id,
        name="灏忕豢",
        species="缁跨繀楣﹂箟"
    )
    db_session.add(parrot)
    await db_session.commit()
    await db_session.refresh(parrot)
    
    stat = BehaviorDailyStat(
        stat_id=generate_id(),
        parrot_id=parrot.parrot_id,
        stat_date=date.today(),
        health_score=85,
        chirp_count=50,
        scream_count=2,
        night_activity_count=0,
        abnormal_event_count=1
    )
    db_session.add(stat)
    await db_session.commit()
    
    response = await auth_client.get(f"/api/parrots/{parrot.parrot_id}/health-overview")
    assert response.status_code == 200
    data = response.json()
    assert data["parrot_name"] == "灏忕豢"
    assert data["current_health_score"] == 85


@pytest.mark.asyncio
async def test_health_overview_all(auth_client, db_session, test_user):
    for i in range(2):
        parrot = Parrot(
            parrot_id=generate_id(),
            user_id=test_user.user_id,
            name=f"楣﹂箟{i}",
            species="铏庣毊楣﹂箟"
        )
        db_session.add(parrot)
        await db_session.commit()
        await db_session.refresh(parrot)
        
        stat = BehaviorDailyStat(
            stat_id=generate_id(),
            parrot_id=parrot.parrot_id,
            stat_date=date.today(),
            health_score=90 - i * 10,
            chirp_count=30,
            scream_count=1,
            night_activity_count=0,
            abnormal_event_count=0
        )
        db_session.add(stat)
        await db_session.commit()
    
    response = await auth_client.get("/api/parrots/health-overview")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1