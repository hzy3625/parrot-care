"""
Pydantic Schemas for API
"""

from pydantic import BaseModel
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