"""
实时音频分析 API - REQ-PARROT-003
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db import get_db
from app.services.realtime_analyzer import AudioAnalyzer
from app.api.users import get_current_user, User

router = APIRouter()
analyzer = AudioAnalyzer()

class RealtimeAnalyzeRequest(BaseModel):
    parrot_id: str
    audio_data: str  # base64 encoded

class RealtimeAnalyzeResponse(BaseModel):
    audio_type: str
    classification: str
    confidence: float
    is_night: bool
    risk_level: int
    timestamp: str
    event_id: str | None

@router.on_event("startup")
async def startup():
    await analyzer.load_model()

@router.post("/realtime-analyze", response_model=RealtimeAnalyzeResponse)
async def realtime_analyze(
    request: RealtimeAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """实时音频分析"""
    # 解码 base64
    import base64
    audio_data = base64.b64decode(request.audio_data)
    
    result = await analyzer.analyze_audio_chunk(audio_data, request.parrot_id)
    
    return RealtimeAnalyzeResponse(
        audio_type=result.audio_type,
        classification=result.classification,
        confidence=result.confidence,
        is_night=result.is_night,
        risk_level=result.risk_level,
        timestamp=result.timestamp.isoformat(),
        event_id=result.event_id
    )

@router.get("/parrots/{parrot_id}/stats")
async def get_parrot_stats(
    parrot_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取鹦鹉实时统计"""
    stats = await analyzer.get_parrot_stats(parrot_id)
    return stats