"""
音频 API 路由
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from pathlib import Path
import aiofiles
import os
import uuid

from app.models.database import Parrot, Device, MediaEvent, generate_id
from app.models.schemas import (
    AudioUpload, EventResponse,
    RecordUploadResponse, CollectionProgressItem, CollectionProgressResponse
)
from app.api.users import get_current_user, User
from app.config import settings
from app.db import get_db
from app.services.audio_classifier import classify_audio
from app.services.push_notification_service import get_push_service
from app.api.websocket import push_event

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
        event_time=datetime.now(timezone.utc),
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
        
        # Sprint 3 REQ-016: WebSocket 实时推送
        try:
            await push_event({
                'event_id': event.event_id,
                'parrot_id': parrot_id,
                'parrot_name': parrot.name,
                'event_type': event_type,
                'risk_level': risk_level,
                'confidence': confidence,
                'timestamp': event.event_time.isoformat(),
                'is_abnormal': is_abnormal
            })
        except Exception as e:
            # WebSocket 推送失败不应影响主流程
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


# REQ-019a: 录音标注上传

# 5 类别定义（与模型对齐）
EVENT_CATEGORIES = {
    "normal_chirp": {"label_cn": "正常鸣叫", "label_en": "normal_chirp"},
    "scream": {"label_cn": "尖叫", "label_en": "scream"},
    "night_fright": {"label_cn": "夜间惊飞", "label_en": "night_fright"},
    "plucking": {"label_cn": "啄羽", "label_en": "plucking"},
    "silence": {"label_cn": "安静", "label_en": "silence"},
}

COLLECTION_TARGET = 40  # 每类别目标段数

# 音频保存根目录
AUDIO_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "audio"


@router.post("/record-upload", response_model=RecordUploadResponse)
async def record_upload(
    parrot_id: str = Form(...),
    event_type: str = Form(...),
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """带标注的音频上传接口 — 用户手动录音 + 类别标注"""
    # 验证 event_type 合法
    if event_type not in EVENT_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的 event_type: {event_type}，允许值: {list(EVENT_CATEGORIES.keys())}"
        )

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

    # 确保目录存在
    save_dir = AUDIO_DATA_DIR / event_type
    save_dir.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名
    file_ext = os.path.splitext(audio_file.filename or "")[1] or ".webm"
    file_id = uuid.uuid4().hex[:12]
    file_name = f"{event_type}_{file_id}{file_ext}"
    file_path = save_dir / file_name

    # 保存音频文件
    async with aiofiles.open(str(file_path), "wb") as f:
        content = await audio_file.read()
        await f.write(content)

    # 创建事件记录
    event = MediaEvent(
        event_id=generate_id(),
        parrot_id=parrot_id,
        event_time=datetime.now(timezone.utc),
        event_type=event_type,
        media_type="audio",
        audio_url=str(file_path),
        is_abnormal=event_type not in ("normal_chirp", "silence"),
        risk_level="low" if event_type in ("normal_chirp", "silence") else "medium",
        confidence=1.0  # 用户标注，置信度为 1
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    return RecordUploadResponse(
        event_id=event.event_id,
        event_type=event_type,
        saved=True,
        message=f"音频已保存到 {event_type} 类别"
    )


@router.get("/collection-progress", response_model=CollectionProgressResponse)
async def collection_progress(
    current_user: User = Depends(get_current_user)
):
    """查询各类别音频采集进度"""
    categories = []
    total_count = 0

    for event_type, info in EVENT_CATEGORIES.items():
        dir_path = AUDIO_DATA_DIR / event_type
        if dir_path.exists():
            count = len([
                f for f in dir_path.iterdir()
                if f.is_file() and f.suffix in (".wav", ".webm", ".mp3", ".m4a", ".ogg")
            ])
        else:
            count = 0

        categories.append(CollectionProgressItem(
            event_type=event_type,
            label_cn=info["label_cn"],
            label_en=info["label_en"],
            count=count,
            target=COLLECTION_TARGET
        ))
        total_count += count

    return CollectionProgressResponse(
        categories=categories,
        total_count=total_count,
        total_target=COLLECTION_TARGET * len(EVENT_CATEGORIES)
    )