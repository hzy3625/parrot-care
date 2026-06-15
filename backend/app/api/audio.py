"""
闊抽 API 璺敱
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

router = APIRouter()

@router.post("/upload", response_model=EventResponse)
async def upload_audio(
    parrot_id: str,
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 楠岃瘉楣﹂箟褰掑睘
    result = await db.execute(
        select(Parrot).where(
            Parrot.parrot_id == parrot_id,
            Parrot.user_id == current_user.user_id
        )
    )
    parrot = result.scalar_one_or_none()
    if not parrot:
        raise HTTPException(status_code=404, detail="楣﹂箟涓嶅瓨鍦?)
    
    # 淇濆瓨闊抽鏂囦欢
    audio_id = generate_id()
    audio_path = f"media/{audio_id}.wav"
    
    async with aiofiles.open(audio_path, "wb") as f:
        content = await audio_file.read()
        await f.write(content)
    
    # AI 鍒嗙被
    event_type, confidence, is_abnormal, risk_level = classify_audio(audio_path)
    
    # 鍒涘缓浜嬩欢
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
    
    # 鐢熸垚寤鸿
    suggestion = None
    if is_abnormal:
        suggestion = generate_suggestion(event_type, risk_level)
    
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
        "night_scream": "鐤戜技澶滄儕锛屽缓璁鏌ュ厜绾裤€佸櫔澹板拰绗煎竷閬尅鎯呭喌銆?,
        "high_frequency_scream": "楂橀灏栧彨锛屽彲鑳藉簲婵€鎴栨眰鍏虫敞锛岃瀵熺幆澧冨彉鍖栥€?,
        "violent_flapping": "鍓х儓鎵戠繀锛屽彲鑳藉彈鎯婂悡锛屾鏌ュ懆鍥村共鎵版簮銆?,
        "cage_collision": "鎾炵锛屽彲鑳藉簲婵€鎴栫┖闂翠笉瓒筹紝瑙傚療琛屼负鐘舵€併€?
    }
    return suggestions.get(event_type, "寤鸿瑙傚療楣﹂箟鐘舵€侊紝蹇呰鏃跺挩璇㈠吔鍖汇€?)