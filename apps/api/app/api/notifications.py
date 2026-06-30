"""站内消息 API 路由 - Sprint 1
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timezone
from typing import List, Optional

from app.models.database import Notification, generate_id
from app.models.schemas import (
    NotificationCreate, NotificationResponse,
    NotificationListResponse, NotificationMarkRead
)
from app.api.users import get_current_user, User
from app.db import get_db

router = APIRouter()

@router.post("", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建站内消息"""
    notification = Notification(
        notification_id=generate_id(),
        user_id=current_user.user_id,
        notification_type=notification_data.notification_type,
        title=notification_data.title,
        content=notification_data.content,
        related_parrot_id=notification_data.related_parrot_id,
        related_event_id=notification_data.related_event_id
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    return NotificationResponse(
        notification_id=notification.notification_id,
        notification_type=notification.notification_type,
        title=notification.title,
        content=notification.content,
        is_read=notification.is_read,
        related_parrot_id=notification.related_parrot_id,
        related_event_id=notification.related_event_id,
        created_at=notification.created_at,
        read_at=notification.read_at
    )

@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    notification_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取消息列表（分页）"""
    # 构建查询条件
    conditions = [Notification.user_id == current_user.user_id]
    if unread_only:
        conditions.append(Notification.is_read == False)
    if notification_type:
        conditions.append(Notification.notification_type == notification_type)

    # 统计总数和未读数
    total_query = select(func.count()).where(and_(*conditions))
    total_result = await db.execute(total_query)
    total = total_result.scalar()

    unread_query = select(func.count()).where(
        and_(Notification.user_id == current_user.user_id, Notification.is_read == False)
    )
    unread_result = await db.execute(unread_query)
    unread_count = unread_result.scalar()

    # 分页查询
    offset = (page - 1) * page_size
    query = select(Notification).where(and_(*conditions)).order_by(desc(Notification.created_at)).offset(offset).limit(page_size)
    result = await db.execute(query)
    notifications = result.scalars().all()

    return NotificationListResponse(
        notifications=[
            NotificationResponse(
                notification_id=n.notification_id,
                notification_type=n.notification_type,
                title=n.title,
                content=n.content,
                is_read=n.is_read,
                related_parrot_id=n.related_parrot_id,
                related_event_id=n.related_event_id,
                created_at=n.created_at,
                read_at=n.read_at
            ) for n in notifications
        ],
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size
    )

@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取未读消息数量"""
    query = select(func.count()).where(
        and_(Notification.user_id == current_user.user_id, Notification.is_read == False)
    )
    result = await db.execute(query)
    count = result.scalar()
    return {"unread_count": count}

@router.patch("/mark-read", response_model=dict)
async def mark_notifications_read(
    mark_data: NotificationMarkRead,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """批量标记消息已读"""
    if not mark_data.notification_ids:
        raise HTTPException(status_code=400, detail="消息ID列表不能为空")

    now = datetime.now(timezone.utc)
    query = select(Notification).where(
        and_(
            Notification.notification_id.in_(mark_data.notification_ids),
            Notification.user_id == current_user.user_id
        )
    )
    result = await db.execute(query)
    notifications = result.scalars().all()

    updated_count = 0
    for n in notifications:
        if not n.is_read:
            n.is_read = True
            n.read_at = now
            updated_count += 1

    await db.commit()
    return {"message": "标记成功", "updated_count": updated_count}

@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_single_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """标记单个消息已读"""
    result = await db.execute(
        select(Notification).where(
            Notification.notification_id == notification_id,
            Notification.user_id == current_user.user_id
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="消息不存在")

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(notification)

    return NotificationResponse(
        notification_id=notification.notification_id,
        notification_type=notification.notification_type,
        title=notification.title,
        content=notification.content,
        is_read=notification.is_read,
        related_parrot_id=notification.related_parrot_id,
        related_event_id=notification.related_event_id,
        created_at=notification.created_at,
        read_at=notification.read_at
    )

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除消息"""
    result = await db.execute(
        select(Notification).where(
            Notification.notification_id == notification_id,
            Notification.user_id == current_user.user_id
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="消息不存在")

    await db.delete(notification)
    await db.commit()
    return {"message": "删除成功", "notification_id": notification_id}
