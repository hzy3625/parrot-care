"""鹦鹉 API 路由 - Sprint 1 增强版
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, date, timedelta, timezone
from typing import List
from collections import defaultdict

from app.models.database import Parrot, MediaEvent, BehaviorDailyStat, generate_id
from app.models.schemas import ParrotCreate, ParrotResponse, ParrotSummary, HealthOverview
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

@router.get("", response_model=List[ParrotResponse])
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

# Sprint 1: 健康档案总览
@router.get("/{parrot_id}/health-overview", response_model=HealthOverview)
async def get_health_overview(
    parrot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取鹦鹉健康档案总览"""
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

    # 获取最近统计数据
    today = date.today()
    seven_days_ago = today - timedelta(days=7)
    thirty_days_ago = today - timedelta(days=30)

    # 7天统计
    result = await db.execute(
        select(BehaviorDailyStat).where(
            and_(
                BehaviorDailyStat.parrot_id == parrot_id,
                BehaviorDailyStat.stat_date >= seven_days_ago
            )
        ).order_by(desc(BehaviorDailyStat.stat_date))
    )
    stats_7days = result.scalars().all()

    # 30天统计
    result = await db.execute(
        select(BehaviorDailyStat).where(
            and_(
                BehaviorDailyStat.parrot_id == parrot_id,
                BehaviorDailyStat.stat_date >= thirty_days_ago
            )
        ).order_by(desc(BehaviorDailyStat.stat_date))
    )
    stats_30days = result.scalars().all()

    # 计算平均值
    def avg_health(stats):
        if not stats:
            return 100.0
        return sum(s.health_score for s in stats) / len(stats)

    def count_abnormal(stats):
        return sum(s.abnormal_event_count for s in stats)

    avg_7days = avg_health(stats_7days)
    avg_30days = avg_health(stats_30days)
    abnormal_7days = count_abnormal(stats_7days)
    abnormal_30days = count_abnormal(stats_30days)

    # 当前健康评分
    current_score = stats_7days[0].health_score if stats_7days else 100

    # 健康趋势
    if len(stats_7days) >= 3:
        recent_avg = sum(s.health_score for s in stats_7days[:3]) / 3
        earlier_avg = sum(s.health_score for s in stats_7days[3:7]) / max(1, len(stats_7days[3:7]))
        if recent_avg > earlier_avg + 5:
            trend = "improving"
        elif recent_avg < earlier_avg - 5:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"

    # 健康状态
    if current_score >= 80:
        health_status = "健康"
    elif current_score >= 60:
        health_status = "轻度异常"
    elif current_score >= 40:
        health_status = "中度异常"
    else:
        health_status = "健康风险"

    # 生成建议
    recommendations = []
    if abnormal_7days > 5:
        recommendations.append("近期异常事件较多，建议检查鹦鹉生活环境")
    if parrot.has_plucking_history:
        recommendations.append("有拔羽历史，建议定期检查羽毛状态")
    if parrot.has_night_fright_history:
        recommendations.append("有夜惊历史，建议夜间保持安静环境")
    if current_score < 70:
        recommendations.append("健康评分偏低，建议咨询兽医")
    if not recommendations:
        recommendations.append("继续保持良好的养护习惯")

    last_check = stats_7days[0].stat_date if stats_7days else datetime.now(timezone.utc)

    return HealthOverview(
        parrot_id=parrot_id,
        parrot_name=parrot.name,
        species=parrot.species,
        current_health_score=current_score,
        health_status=health_status,
        avg_health_score_7days=round(avg_7days, 1),
        avg_health_score_30days=round(avg_30days, 1),
        total_abnormal_events_7days=abnormal_7days,
        total_abnormal_events_30days=abnormal_30days,
        health_trend=trend,
        last_check_date=last_check,
        recommendations=recommendations
    )

# Sprint 1: 全鹦鹉健康总览
@router.get("/health-overview", response_model=List[HealthOverview])
async def get_all_health_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取所有鹦鹉健康档案总览"""
    result = await db.execute(
        select(Parrot).where(Parrot.user_id == current_user.user_id)
    )
    parrots = result.scalars().all()

    overviews = []
    for parrot in parrots:
        # 递归调用单个鹦鹉的健康总览
        overview = await get_health_overview(parrot.parrot_id, current_user, db)
        overviews.append(overview)

    return overviews
