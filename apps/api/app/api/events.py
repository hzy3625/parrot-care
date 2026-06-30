"""
事件 API 路由
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime

from app.models.database import Parrot, MediaEvent, UserFeedback, generate_id
from app.models.schemas import EventDetail, FeedbackCreate, FeedbackResponse
from app.api.users import get_current_user, User
from app.db import get_db

router = APIRouter()

@router.get("", response_model=list[EventDetail])
async def list_events(
    parrot_id: str = None,
    is_abnormal: bool = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 构建查询
    query = select(MediaEvent).join(Parrot).where(Parrot.user_id == current_user.user_id)

    if parrot_id:
        query = query.where(MediaEvent.parrot_id == parrot_id)
    if is_abnormal is not None:
        query = query.where(MediaEvent.is_abnormal == is_abnormal)

    query = query.order_by(desc(MediaEvent.event_time)).limit(limit)
    result = await db.execute(query)
    events = result.scalars().all()

    return [
        EventDetail(
            event_id=e.event_id,
            parrot_id=e.parrot_id,
            event_time=e.event_time,
            event_type=e.event_type,
            duration=e.duration,
            audio_url=e.audio_url,
            video_url=e.video_url,
            is_abnormal=e.is_abnormal,
            risk_level=e.risk_level,
            confidence=e.confidence,
            created_at=e.created_at
        ) for e in events
    ]

@router.get("/{event_id}", response_model=EventDetail)
async def get_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MediaEvent).join(Parrot).where(
            MediaEvent.event_id == event_id,
            Parrot.user_id == current_user.user_id
        )
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")

    return EventDetail(
        event_id=event.event_id,
        parrot_id=event.parrot_id,
        event_time=event.event_time,
        event_type=event.event_type,
        duration=event.duration,
        audio_url=event.audio_url,
        video_url=event.video_url,
        is_abnormal=event.is_abnormal,
        risk_level=event.risk_level,
        confidence=event.confidence,
        created_at=event.created_at
    )

@router.post("/{event_id}/feedback", response_model=FeedbackResponse)
async def create_feedback(
    event_id: str,
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 验证事件归属
    result = await db.execute(
        select(MediaEvent).join(Parrot).where(
            MediaEvent.event_id == event_id,
            Parrot.user_id == current_user.user_id
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")

    feedback = UserFeedback(
        feedback_id=generate_id(),
        event_id=event_id,
        user_id=current_user.user_id,
        feedback_type=feedback_data.feedback_type,
        feedback_label=feedback_data.feedback_label,
        comment=feedback_data.comment
    )
    db.add(feedback)
    await db.commit()

    return FeedbackResponse(
        feedback_id=feedback.feedback_id,
        event_id=feedback.event_id,
        feedback_type=feedback.feedback_type,
        feedback_label=feedback.feedback_label,
        comment=feedback.comment,
        created_at=feedback.created_at
    )