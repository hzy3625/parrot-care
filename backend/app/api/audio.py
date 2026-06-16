"""
音频 API 路由
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import aiofiles
import os

from app.models.database import Parrot, Device, MediaEvent, generate_id
from app.models.schemas import AudioUpload, EventResponse
from app.api.users import get_current_user, User
from app.config import settings
from app.db import get_db
from app.services.audio_classifier import classify_audio
from app.services.push_notification_service import get_push_service

router = APIRouter()

@router.post("/upload", response_model=EventResponse)
async def upload_audio(
    parrot_id: str,
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 验证鹦鹉归属
    result = await db.execute(
        select(Parrot).where(
            Parrot.parrot_id == parrot_id,
            Parrot.user_id == current_user.user_id
        )
    )
    parrot = result.scalar_one_or_none()
    if not parrot:
        raise HTTPException(status_code=404, detail="鹦鹉不存在")
    
    # 保存音频文件
    audio_id = generate_id()
    audio_path = f"media/{audio_id}.wav"
    
    async with aiofiles.open(audio_path, "wb") as f:
        content = await audio_file.read()
        await f.write(content)
    
    # AI 分类
    event_type, confidence, is_abnormal, risk_level = classify_audio(audio_path)
    
    # 创建事件
    event = MediaEvent(
        event_id=generate_id(),
        parrot_id=parrot_id,
        event_time=datetime.utcnow(),
        event_type=event_type,
        media_type="audio",
        audio_url=audio_path,
        is_abnormal=is_abnormal,
        risk_level=risk_level,
        confidence=confidence
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    
    # 生成建议
    suggestion = None
    if is_abnormal:
        suggestion = generate_suggestion(event_type, risk_level)
        # Sprint 2: 触发推送通知
        try:
            push_service = get_push_service()
            await push_service.dispatch_for_event(event, db)
        except Exception as e:
            # 推送失败不应影响主流程
            pass
    
    return EventResponse(
        event_id=event.event_id,
        event_type=event_type,
        is_abnormal=is_abnormal,
        risk_level=risk_level,
        confidence=confidence,
        suggestion=suggestion
    )

def generate_suggestion(event_type: str, risk_level: str) -> str:
    suggestions = {
        "night_scream": "疑似夜惊，建议检查光线、噪声和笼布遮挡情况。",
        "high_frequency_scream": "高频尖叫，可能应激或求关注，观察环境变化。",
        "violent_flapping": "剧烈扑翅，可能受惊吓，检查周围干扰源。",
        "cage_collision": "撞笼，可能应激或空间不足，观察行为状态。"
    }
    return suggestions.get(event_type, "建议观察鹦鹉状态，必要时咨询兽医。")