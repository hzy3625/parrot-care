"""
用户 API 路由
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib
from jose import jwt, JWTError
from datetime import datetime, timedelta

from app.models.database import User, generate_id
from app.models.schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from app.config import settings
from app.db import get_db

router = APIRouter()
security = HTTPBearer()

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