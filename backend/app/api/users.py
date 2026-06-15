# -*- coding: utf-8 -*-
"""用户 API 路由 - Sprint 1 增强版"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from passlib.context import CryptContext
import secrets
import logging
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.models.database import User, PasswordResetToken, generate_id
from app.models.schemas import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    PasswordResetRequest, PasswordResetConfirm, PasswordResetResponse,
    ProfileUpdate, ProfileResponse
)
from app.config import settings
from app.db import get_db

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    payload = {"user_id": user_id, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="无效的token")
        
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="token验证失败")

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone == user_data.phone))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="手机号已注册")
    
    user = User(
        user_id=generate_id(),
        phone=user_data.phone,
        password_hash=hash_password(user_data.password),
        nickname=user_data.nickname,
        email=user_data.email
    )
    db.add(user)
    await db.commit()
    
    return TokenResponse(access_token=create_token(user.user_id))

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone == login_data.phone))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="手机号或密码错误")
    
    return TokenResponse(access_token=create_token(user.user_id))

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        user_id=current_user.user_id,
        nickname=current_user.nickname,
        phone=current_user.phone,
        email=current_user.email,
        subscription_status=current_user.subscription_status,
        created_at=current_user.created_at
    )

@router.post("/reset-password", response_model=PasswordResetResponse)
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """请求密码重置（1小时内最多3次）"""
    result = await db.execute(select(User).where(User.email == reset_data.email))
    user = result.scalar_one_or_none()
    
    if not user:
        logger.info(f"密码重置请求 - 邮箱不存在: {reset_data.email}")
        return PasswordResetResponse(message="如果邮箱存在，重置链接已发送", success=True)
    
    # 频率限制：1小时内最多3次
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    count_result = await db.execute(
        select(func.count(PasswordResetToken.token_id)).where(
            and_(
                PasswordResetToken.user_id == user.user_id,
                PasswordResetToken.created_at >= one_hour_ago
            )
        )
    )
    request_count = count_result.scalar() or 0
    if request_count >= 3:
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试（1小时内最多3次）")
    
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    token_record = PasswordResetToken(
        token_id=generate_id(),
        user_id=user.user_id,
        token=reset_token,
        email=user.email,
        expires_at=expires_at
    )
    db.add(token_record)
    await db.commit()
    
    reset_link = f"http://localhost:8000/reset-password?token={reset_token}"
    logger.info(f"\n========== 密码重置邮件 (Mock) ==========\n收件人: {user.email}\n链接: {reset_link}\n========================================\n")
    
    return PasswordResetResponse(message="如果邮箱存在，重置链接已发送", success=True)

@router.post("/reset-password/{token}", response_model=PasswordResetResponse)
async def confirm_password_reset(
    token: str,
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """确认密码重置"""
    now_utc = datetime.now(timezone.utc)
    result = await db.execute(
        select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token == token,
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > now_utc
            )
        )
    )
    token_record = result.scalar_one_or_none()
    
    if not token_record:
        raise HTTPException(status_code=400, detail="重置链接无效或已过期")
    
    result = await db.execute(select(User).where(User.user_id == token_record.user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.password_hash = hash_password(reset_data.new_password)
    token_record.is_used = True
    token_record.used_at = now_utc
    
    await db.commit()
    logger.info(f"密码重置成功 - 用户: {user.phone}")
    
    return PasswordResetResponse(message="密码已重置，请使用新密码登录", success=True)

@router.post("/me/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="旧密码不正确")
    
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="密码至少8位，需包含字母和数字")
    
    has_letter = any(c.isalpha() for c in new_password)
    has_digit = any(c.isdigit() for c in new_password)
    if not has_letter or not has_digit:
        raise HTTPException(status_code=400, detail="密码必须包含字母和数字")
    
    current_user.password_hash = hash_password(new_password)
    await db.commit()
    
    logger.info(f"密码修改成功 - 用户: {current_user.phone}")
    return {"message": "密码已修改", "success": True}

@router.get("/profile", response_model=ProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取个人信息"""
    return ProfileResponse(
        user_id=current_user.user_id,
        nickname=current_user.nickname,
        email=current_user.email,
        phone=current_user.phone,
        subscription_status=current_user.subscription_status,
        avatar_url=None,
        notification_email=getattr(current_user, 'notification_email', True),
        notification_browser=getattr(current_user, 'notification_browser', True),
    )

@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新个人信息"""
    if profile_data.email:
        result = await db.execute(
            select(User).where(
                and_(User.email == profile_data.email, User.user_id != current_user.user_id)
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="邮箱已被使用")
    
    if profile_data.phone:
        result = await db.execute(
            select(User).where(
                and_(User.phone == profile_data.phone, User.user_id != current_user.user_id)
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="手机号已被使用")
    
    if profile_data.nickname is not None:
        current_user.nickname = profile_data.nickname
    if profile_data.email is not None:
        current_user.email = profile_data.email
    if profile_data.phone is not None:
        current_user.phone = profile_data.phone
    if hasattr(current_user, 'notification_email') and profile_data.notification_email is not None:
        current_user.notification_email = profile_data.notification_email
    if hasattr(current_user, 'notification_browser') and profile_data.notification_browser is not None:
        current_user.notification_browser = profile_data.notification_browser
    
    await db.commit()
    await db.refresh(current_user)
    
    return ProfileResponse(
        user_id=current_user.user_id,
        nickname=current_user.nickname,
        email=current_user.email,
        phone=current_user.phone,
        subscription_status=current_user.subscription_status,
        avatar_url=None,
        notification_email=getattr(current_user, 'notification_email', True),
        notification_browser=getattr(current_user, 'notification_browser', True),
    )
