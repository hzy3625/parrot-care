# -*- coding: utf-8 -*-
"""用户设置 API - 推送通知配置、免打扰时段"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import time
from typing import Optional

from app.api.users import get_current_user, User
from app.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


# --- Pydantic Schemas ---

class PushSettingsResponse(BaseModel):
    notification_email: bool = True
    notification_browser: bool = True


class PushSettingsUpdate(BaseModel):
    notification_email: Optional[bool] = None
    notification_browser: Optional[bool] = None


class DndSettingsResponse(BaseModel):
    dnd_start: Optional[str] = None  # HH:MM format
    dnd_end: Optional[str] = None


class DndSettingsUpdate(BaseModel):
    dnd_start: Optional[str] = None  # HH:MM format, e.g. "23:00"
    dnd_end: Optional[str] = None    # HH:MM format, e.g. "07:00"


# --- API Endpoints ---

@router.get("/push", response_model=PushSettingsResponse)
async def get_push_settings(
    current_user: User = Depends(get_current_user)
):
    """获取推送通知设置"""
    return PushSettingsResponse(
        notification_email=getattr(current_user, 'notification_email', True),
        notification_browser=getattr(current_user, 'notification_browser', True),
    )


@router.put("/push", response_model=PushSettingsResponse)
async def update_push_settings(
    settings_data: PushSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新推送通知设置
    
    可独立开关 email 和 browser 通知。
    """
    if settings_data.notification_email is not None:
        current_user.notification_email = settings_data.notification_email
    if settings_data.notification_browser is not None:
        current_user.notification_browser = settings_data.notification_browser
    
    await db.commit()
    await db.refresh(current_user)
    
    return PushSettingsResponse(
        notification_email=current_user.notification_email,
        notification_browser=current_user.notification_browser,
    )


@router.get("/dnd", response_model=DndSettingsResponse)
async def get_dnd_settings(
    current_user: User = Depends(get_current_user)
):
    """获取免打扰时段设置"""
    return DndSettingsResponse(
        dnd_start=current_user.dnd_start.strftime("%H:%M") if current_user.dnd_start else None,
        dnd_end=current_user.dnd_end.strftime("%H:%M") if current_user.dnd_end else None,
    )


@router.put("/dnd", response_model=DndSettingsResponse)
async def update_dnd_settings(
    settings_data: DndSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新免打扰时段设置
    
    时间格式：HH:MM（24小时制）
    示例：dnd_start="23:00", dnd_end="07:00" 表示 23:00 到次日 07:00 免打扰
    
    清空 DND：传 dnd_start=null 和 dnd_end=null
    """
    if settings_data.dnd_start is not None:
        try:
            current_user.dnd_start = time.fromisoformat(settings_data.dnd_start)
        except ValueError:
            raise HTTPException(status_code=400, detail="dnd_start 格式错误，应为 HH:MM")
    
    if settings_data.dnd_end is not None:
        try:
            current_user.dnd_end = time.fromisoformat(settings_data.dnd_end)
        except ValueError:
            raise HTTPException(status_code=400, detail="dnd_end 格式错误，应为 HH:MM")
    
    # 如果两个都传了 None，则清空 DND
    if settings_data.dnd_start is None and settings_data.dnd_end is None:
        current_user.dnd_start = None
        current_user.dnd_end = None
    
    await db.commit()
    await db.refresh(current_user)
    
    return DndSettingsResponse(
        dnd_start=current_user.dnd_start.strftime("%H:%M") if current_user.dnd_start else None,
        dnd_end=current_user.dnd_end.strftime("%H:%M") if current_user.dnd_end else None,
    )
