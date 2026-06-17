from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, ForeignKey, Text, DECIMAL, Time
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
import uuid
from passlib.context import CryptContext

Base = declarative_base()

# 密码哈希上下文（bcrypt）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_id():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String(64), primary_key=True, default=generate_id)
    nickname = Column(String(100))
    phone = Column(String(30), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255))
    subscription_status = Column(String(30), default="free")
    
    # Sprint 1 新增字段
    notification_email = Column(Boolean, default=True)
    notification_browser = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    dnd_start = Column(Time, nullable=True)  # Do Not Disturb 开始时间
    dnd_end = Column(Time, nullable=True)    # Do Not Disturb 结束时间
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    parrots = relationship("Parrot", back_populates="user")
    devices = relationship("Device", back_populates="user")

class Parrot(Base):
    __tablename__ = "parrots"
    
    parrot_id = Column(String(64), primary_key=True, default=generate_id)
    user_id = Column(String(64), ForeignKey("users.user_id"))
    name = Column(String(100))
    species = Column(String(100))
    age = Column(Integer)
    gender = Column(String(30))
    weight = Column(DECIMAL(6, 2))
    has_plucking_history = Column(Boolean, default=False)
    has_night_fright_history = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="parrots")
    events = relationship("MediaEvent", back_populates="parrot")

class Device(Base):
    __tablename__ = "devices"
    
    device_id = Column(String(64), primary_key=True, default=generate_id)
    user_id = Column(String(64), ForeignKey("users.user_id"))
    device_type = Column(String(50))
    device_name = Column(String(100))
    status = Column(String(30), default="offline")
    last_online_time = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="devices")

class MediaEvent(Base):
    __tablename__ = "media_events"
    
    event_id = Column(String(64), primary_key=True, default=generate_id)
    parrot_id = Column(String(64), ForeignKey("parrots.parrot_id"))
    device_id = Column(String(64), ForeignKey("devices.device_id"))
    event_time = Column(DateTime, index=True)
    event_type = Column(String(100))
    media_type = Column(String(30))
    audio_url = Column(Text)
    video_url = Column(Text)
    duration = Column(DECIMAL(8, 2))
    confidence = Column(DECIMAL(5, 4))
    is_abnormal = Column(Boolean, default=False)
    risk_level = Column(String(30))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    parrot = relationship("Parrot", back_populates="events")
    feedbacks = relationship("UserFeedback", back_populates="event")

class UserFeedback(Base):
    __tablename__ = "user_feedback"
    
    feedback_id = Column(String(64), primary_key=True, default=generate_id)
    event_id = Column(String(64), ForeignKey("media_events.event_id"))
    user_id = Column(String(64), ForeignKey("users.user_id"))
    feedback_type = Column(String(50))
    feedback_label = Column(String(100))
    comment = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    event = relationship("MediaEvent", back_populates="feedbacks")

class BehaviorDailyStat(Base):
    __tablename__ = "behavior_daily_stats"
    
    stat_id = Column(String(64), primary_key=True, default=generate_id)
    parrot_id = Column(String(64), ForeignKey("parrots.parrot_id"))
    stat_date = Column(DateTime, index=True)
    chirp_count = Column(Integer, default=0)
    scream_count = Column(Integer, default=0)
    night_activity_count = Column(Integer, default=0)
    active_minutes = Column(Integer, default=0)
    quiet_minutes = Column(Integer, default=0)
    abnormal_event_count = Column(Integer, default=0)
    health_score = Column(Integer, default=100)

# Sprint 1: 站内消息通知
class Notification(Base):
    __tablename__ = "notifications"
    
    notification_id = Column(String(64), primary_key=True, default=generate_id)
    user_id = Column(String(64), ForeignKey("users.user_id"), index=True)
    notification_type = Column(String(50))  # system, health_alert, parrot_reminder, feature_update
    title = Column(String(200))
    content = Column(Text)
    is_read = Column(Boolean, default=False)
    related_parrot_id = Column(String(64), ForeignKey("parrots.parrot_id"), nullable=True)
    related_event_id = Column(String(64), ForeignKey("media_events.event_id"), nullable=True)
    
    # Sprint 1 新增字段
    expires_at = Column(DateTime, nullable=True)  # 消息过期时间
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    read_at = Column(DateTime, nullable=True)

# Sprint 1: 密码重置 Token 表
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    
    token_id = Column(String(64), primary_key=True, default=generate_id)
    user_id = Column(String(64), ForeignKey("users.user_id"), index=True)
    token = Column(String(128), unique=True, index=True)
    email = Column(String(100))
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    used_at = Column(DateTime, nullable=True)

# Sprint 1: 密码重置频率限制表
class PasswordResetRateLimit(Base):
    __tablename__ = "password_reset_rate_limits"
    
    limit_id = Column(String(64), primary_key=True, default=generate_id)
    email = Column(String(100), index=True)
    request_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
