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
from app.services.email_service import EmailService, send_password_reset_email
