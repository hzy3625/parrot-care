from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

# 用户
class UserCreate(BaseModel):
    phone: str
    password: str
    nickname: Optional[str] = None
    email: Optional[str] = None

class UserLogin(BaseModel):
    phone: str
    password: str

class UserResponse(BaseModel):
    user_id: str
    nickname: Optional[str]
    phone: str
    email: Optional[str]
    subscription_status: str
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Sprint 1: 密码重置
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码至少8位')
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not has_letter or not has_digit:
            raise ValueError('密码必须包含字母和数字')
        return v

class PasswordResetResponse(BaseModel):
    message: str
    success: bool

# Sprint 1: 个人信息更新
class ProfileUpdate(BaseModel):
    nickname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    notification_email: Optional[bool] = True
    notification_browser: Optional[bool] = True

class ProfileResponse(BaseModel):
    user_id: str
    nickname: Optional[str]
    email: Optional[str]
    phone: str
    subscription_status: str
    avatar_url: Optional[str] = None
    notification_email: bool = True
    notification_browser: bool = True

# 鹦鹉
class ParrotCreate(BaseModel):
    name: str
    species: str
    age: Optional[int] = None
    gender: Optional[str] = None
    weight: Optional[Decimal] = None
    has_plucking_history: Optional[bool] = False
    has_night_fright_history: Optional[bool] = False

class ParrotResponse(BaseModel):
    parrot_id: str
    user_id: str
    name: str
    species: str
    age: Optional[int]
    gender: Optional[str]
    weight: Optional[Decimal]
    has_plucking_history: bool
    has_night_fright_history: bool
    created_at: datetime

class ParrotSummary(BaseModel):
    health_score: int
    status: str
    chirp_count: int
    scream_count: int
    night_activity_count: int
    abnormal_event_count: int
    summary: str

# Sprint 1: 健康档案总览
class HealthOverview(BaseModel):
    parrot_id: str
    parrot_name: str
    species: str
    current_health_score: int
    health_status: str
    avg_health_score_7days: float
    avg_health_score_30days: float
    total_abnormal_events_7days: int
    total_abnormal_events_30days: int
    health_trend: str  # improving, stable, declining
    last_check_date: datetime
    recommendations: List[str]

# 音频事件
class AudioUpload(BaseModel):
    parrot_id: str
    device_id: Optional[str] = None
    event_time: datetime
    duration: Decimal
    audio_url: str

class EventResponse(BaseModel):
    event_id: str
    event_type: str
    is_abnormal: bool
    risk_level: Optional[str]
    confidence: Optional[Decimal]
    suggestion: Optional[str]

class EventDetail(BaseModel):
    event_id: str
    parrot_id: str
    event_time: datetime
    event_type: str
    duration: Optional[Decimal]
    audio_url: Optional[str]
    video_url: Optional[str]
    is_abnormal: bool
    risk_level: Optional[str]
    confidence: Optional[Decimal]
    created_at: datetime

# 用户反馈
class FeedbackCreate(BaseModel):
    feedback_type: str
    feedback_label: Optional[str] = None
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    feedback_id: str
    event_id: str
    feedback_type: str
    feedback_label: Optional[str]
    comment: Optional[str]
    created_at: datetime

# Sprint 1: 站内消息
class NotificationCreate(BaseModel):
    notification_type: str
    title: str
    content: str
    related_parrot_id: Optional[str] = None
    related_event_id: Optional[str] = None
    expires_at: Optional[datetime] = None

class NotificationResponse(BaseModel):
    notification_id: str
    notification_type: str
    title: str
    content: str
    is_read: bool
    related_parrot_id: Optional[str]
    related_event_id: Optional[str]
    created_at: datetime
    read_at: Optional[datetime]

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int

class NotificationMarkRead(BaseModel):
    notification_ids: List[str]
