用户 API 路由 - Sprint 1 增强版
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import hashlib
import secrets
import logging
from jose import jwt, JWTError
from datetime import datetime, timedelta
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

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def create_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
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
    # 检查手机号是否已存在
    result = await db.execute(select(User).where(User.phone == user_data.phone))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="手机号已注册")
    
    # 创建用户
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

# Sprint 1: 密码重置请求
@router.post("/reset-password", response_model=PasswordResetResponse)
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """请求密码重置 - 发送重置链接到邮箱"""
    # 查找用户
    result = await db.execute(select(User).where(User.email == reset_data.email))
    user = result.scalar_one_or_none()
    
    if not user:
        # 安全考虑：不透露邮箱是否存在
        logger.info(f"密码重置请求 - 邮箱不存在: {reset_data.email}")
        return PasswordResetResponse(
            message="如果邮箱存在，重置链接已发送",
            success=True
        )
    
    # 生成重置 Token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    token_record = PasswordResetToken(
        token_id=generate_id(),
        user_id=user.user_id,
        token=reset_token,
        email=user.email,
        expires_at=expires_at
    )
    db.add(token_record)
    await db.commit()
    
    # Mock 发送邮件（开发环境打印日志）
    reset_link = f"http://localhost:8000/reset-password?token={reset_token}"
    logger.info(f"""
    ========== 密码重置邮件 (Mock) ==========
    收件人: {user.email}
    用户: {user.nickname or user.phone}
    重置链接: {reset_link}
    有效期: 1 小时
    ========================================
    """)
    
    return PasswordResetResponse(
        message="如果邮箱存在，重置链接已发送",
        success=True
    )

# Sprint 1: 密码重置确认
@router.post("/reset-password/{token}", response_model=PasswordResetResponse)
async def confirm_password_reset(
    token: str,
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """确认密码重置 - 使用 Token 设置新密码"""
    # 查找 Token
    result = await db.execute(
        select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token == token,
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > datetime.utcnow()
            )
        )
    )
    token_record = result.scalar_one_or_none()
    
    if not token_record:
        raise HTTPException(status_code=400, detail="重置链接无效或已过期")
    
    # 查找用户
    result = await db.execute(select(User).where(User.user_id == token_record.user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新密码
    user.password_hash = hash_password(reset_data.new_password)
    token_record.is_used = True
    token_record.used_at = datetime.utcnow()
    
    await db.commit()
    
    logger.info(f"密码重置成功 - 用户: {user.phone}")
    
    return PasswordResetResponse(
        message="密码已重置，请使用新密码登录",
        success=True
    )

# Sprint 1: 个人信息管理 - 获取详情
@router.get("/profile", response_model=ProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取个人信息"""
    return ProfileResponse(
        user_id=current_user.user_id,
        nickname=current_user.nickname,
        email=current_user.email,
        phone=current_user.phone,
        subscription_status=current_user.subscription_status,
        avatar_url=None  # 暂不支持头像
    )

# Sprint 1: 个人信息管理 - 更新
@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新个人信息"""
    # 检查邮箱是否已被其他用户使用
    if profile_data.email:
        result = await db.execute(
            select(User).where(
                and_(
                    User.email == profile_data.email,
                    User.user_id != current_user.user_id
                )
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="邮箱已被使用")
    
    # 检查手机号是否已被其他用户使用
    if profile_data.phone:
        result = await db.execute(
            select(User).where(
                and_(
                    User.phone == profile_data.phone,
                    User.user_id != current_user.user_id
                )
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="手机号已被使用")
    
    # 更新信息
    if profile_data.nickname:
        current_user.nickname = profile_data.nickname
    if profile_data.email:
        current_user.email = profile_data.email
    if profile_data.phone:
        current_user.phone = profile_data.phone
    
    await db.commit()
    await db.refresh(current_user)
    
    return ProfileResponse(
        user_id=current_user.user_id,
        nickname=current_user.nickname,
        email=current_user.email,
        phone=current_user.phone,
        subscription_status=current_user.subscription_status,
        avatar_url=None
    )
