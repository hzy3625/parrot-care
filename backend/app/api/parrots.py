"""
鹦鹉 API 路由
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, date

from app.models.database import Parrot, MediaEvent, BehaviorDailyStat, generate_id
from app.models.schemas import ParrotCreate, ParrotResponse, ParrotSummary
from app.api.users import get_current_user, User
from app.db import get_db

router = APIRouter()

@router.post("", response_model=ParrotResponse)
async def create_parrot(
    parrot_data: ParrotCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    parrot = Parrot(
        parrot_id=generate_id(),
        user_id=current_user.user_id,
        name=parrot_data.name,
        species=parrot_data.species,
        age=parrot_data.age,
        gender=parrot_data.gender,
        weight=parrot_data.weight,
        has_plucking_history=parrot_data.has_plucking_history,
        has_night_fright_history=parrot_data.has_night_fright_history
    )
    db.add(parrot)
    await db.commit()
    await db.refresh(parrot)
    
    return ParrotResponse(
        parrot_id=parrot.parrot_id,
        user_id=parrot.user_id,
        name=parrot.name,
        species=parrot.species,
        age=parrot.age,
        gender=parrot.gender,
        weight=parrot.weight,
        has_plucking_history=parrot.has_plucking_history,
        has_night_fright_history=parrot.has_night_fright_history,
        created_at=parrot.created_at
    )

@router.get("", response_model=list[ParrotResponse])
async def list_parrots(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Parrot).where(Parrot.user_id == current_user.user_id)
    )
    parrots = result.scalars().all()
    
    return [
        ParrotResponse(
            parrot_id=p.parrot_id,
            user_id=p.user_id,
            name=p.name,
            species=p.species,
            age=p.age,
            gender=p.gender,
            weight=p.weight,
            has_plucking_history=p.has_plucking_history,
            has_night_fright_history=p.has_night_fright_history,
            created_at=p.created_at
        ) for p in parrots
    ]

@router.get("/{parrot_id}/today-summary", response_model=ParrotSummary)
async def get_today_summary(
    parrot_id: str,
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
    
    # 获取今日统计
    today = date.today()
    result = await db.execute(
        select(BehaviorDailyStat).where(
            BehaviorDailyStat.parrot_id == parrot_id,
            BehaviorDailyStat.stat_date == today
        )
    )
    stat = result.scalar_one_or_none()
    
    if not stat:
        return ParrotSummary(
            health_score=100,
            status="正常",
            chirp_count=0,
            scream_count=0,
            night_activity_count=0,
            abnormal_event_count=0,
            summary="今日暂无数据"
        )
    
    # 计算状态
    status = "正常"
    if stat.abnormal_event_count > 0:
        status = "轻度异常" if stat.abnormal_event_count < 3 else "异常"
    if stat.health_score < 70:
        status = "健康风险"
    
    summary = f"今日鸣叫{stat.chirp_count}次，尖叫{stat.scream_count}次"
    if stat.night_activity_count > 0:
        summary += f"，夜间异常活动{stat.night_activity_count}次"
    
    return ParrotSummary(
        health_score=stat.health_score,
        status=status,
        chirp_count=stat.chirp_count,
        scream_count=stat.scream_count,
        night_activity_count=stat.night_activity_count,
        abnormal_event_count=stat.abnormal_event_count,
        summary=summary
    )