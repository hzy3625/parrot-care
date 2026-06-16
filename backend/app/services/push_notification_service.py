# -*- coding: utf-8 -*-
"""推送通知服务 - 异常事件触发邮件 + 站内消息 + 浏览器通知"""

import logging
from datetime import datetime, time
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import User, Notification, MediaEvent, Parrot, generate_id
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class PushNotificationService:
    """推送通知核心服务
    
    负责：
    1. 检测异常事件并触发推送
    2. 检查用户 DND 设置
    3. 发送邮件通知
    4. 创建站内消息
    5. 返回浏览器通知数据
    """
    
    # 异常类型中文映射
    EVENT_TYPE_LABELS = {
        "night_fright": "夜间惊飞",
        "scream": "持续尖叫",
        "plucking": "啄羽行为",
        "aggression": "攻击行为",
        "lethargy": "活动异常减少",
        "abnormal_sound": "异常声音",
    }
    
    # 严重程度中文映射
    RISK_LEVEL_LABELS = {
        "low": "低",
        "medium": "中",
        "high": "高",
        "critical": "紧急",
    }
    
    def __init__(self, email_service: Optional[EmailService] = None):
        self.email_service = email_service
    
    def is_in_dnd(self, dnd_start: Optional[time], dnd_end: Optional[time], 
                  check_time: Optional[datetime] = None) -> bool:
        """检查当前时间是否在用户免打扰时段内
        
        Args:
            dnd_start: DND 开始时间
            dnd_end: DND 结束时间
            check_time: 检查的时间点，默认当前时间
        
        Returns:
            True 表示在 DND 时段内
        """
        if dnd_start is None or dnd_end is None:
            return False
        
        if check_time is None:
            check_time = datetime.utcnow()
        
        current = check_time.time()
        
        if dnd_start <= dnd_end:
            # 不跨午夜，如 14:00-16:00
            return dnd_start <= current <= dnd_end
        else:
            # 跨午夜，如 23:00-07:00
            return current >= dnd_start or current <= dnd_end
    
    async def dispatch_for_event(
        self,
        event: MediaEvent,
        db: AsyncSession,
        event_time: Optional[datetime] = None
    ) -> dict:
        """为单个异常事件分发推送通知
        
        Args:
            event: MediaEvent 实例
            db: 数据库会话
            event_time: 事件时间（用于 DND 判断）
        
        Returns:
            推送结果字典: {email_sent, in_app_created, browser_notification, dnd_suppressed}
        """
        result = {
            "email_sent": False,
            "in_app_created": False,
            "browser_notification": None,
            "dnd_suppressed_browser": False,
            "dnd_suppressed_email": False,
        }
        
        if not event.is_abnormal:
            logger.info(f"事件 {event.event_id} 非异常，跳过推送")
            return result
        
        # 获取用户信息
        parrot_result = await db.execute(
            select(Parrot).where(Parrot.parrot_id == event.parrot_id)
        )
        parrot = parrot_result.scalar_one_or_none()
        if not parrot:
            logger.warning(f"事件 {event.event_id} 关联的鹦鹉不存在")
            return result
        
        user_result = await db.execute(
            select(User).where(User.user_id == parrot.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            logger.warning(f"事件 {event.event_id} 关联的用户不存在")
            return result
        
        check_time = event_time or event.event_time or datetime.utcnow()
        in_dnd = self.is_in_dnd(user.dnd_start, user.dnd_end, check_time)
        is_critical = (event.risk_level or "").lower() == "critical"
        
        # 构建通知内容
        event_label = self.EVENT_TYPE_LABELS.get(
            event.event_type or "unknown", event.event_type or "未知异常"
        )
        risk_label = self.RISK_LEVEL_LABELS.get(
            event.risk_level or "unknown", event.risk_level or "未知"
        )
        time_str = check_time.strftime("%Y-%m-%d %H:%M") if check_time else "未知时间"
        
        title = f"🦜 {parrot.name} 异常行为提醒"
        content = (
            f"您的鹦鹉 **{parrot.name}** 在 {time_str} 检测到异常行为：\n\n"
            f"- **异常类型**：{event_label}\n"
            f"- **严重程度**：{risk_label}\n"
            f"- **事件 ID**：{event.event_id}\n\n"
            f"请及时查看鹦鹉状况。"
        )
        
        # 1. 邮件通知（DND 时段仍发送，邮件不抑制）
        if getattr(user, 'notification_email', True) and user.email:
            email_sent = await self._send_email_notification(
                user, parrot, event, event_label, risk_label, time_str
            )
            result["email_sent"] = email_sent
        
        # 2. 站内消息（始终创建，作为记录）
        notification = Notification(
            notification_id=generate_id(),
            user_id=user.user_id,
            notification_type="health_alert",
            title=title,
            content=content,
            related_parrot_id=parrot.parrot_id,
            related_event_id=event.event_id,
        )
        db.add(notification)
        await db.commit()
        result["in_app_created"] = True
        
        # 3. 浏览器通知
        if getattr(user, 'notification_browser', True):
            if in_dnd and not is_critical:
                logger.info(
                    f"用户 {user.user_id} 在 DND 时段，非紧急事件抑制浏览器通知"
                )
                result["dnd_suppressed_browser"] = True
            else:
                result["browser_notification"] = {
                    "title": title,
                    "body": f"{parrot.name} 检测到 {event_label}，严重程度：{risk_label}",
                    "event_id": event.event_id,
                    "risk_level": event.risk_level,
                    "timestamp": check_time.isoformat() if check_time else None,
                }
        
        return result
    
    async def dispatch_for_events(
        self,
        events: List[MediaEvent],
        db: AsyncSession,
    ) -> List[dict]:
        """批量分发推送通知
        
        Args:
            events: MediaEvent 列表
            db: 数据库会话
        
        Returns:
            每个事件的推送结果列表
        """
        results = []
        for event in events:
            result = await self.dispatch_for_event(event, db)
            results.append(result)
        return results
    
    async def _send_email_notification(
        self,
        user: User,
        parrot: Parrot,
        event: MediaEvent,
        event_label: str,
        risk_label: str,
        time_str: str
    ) -> bool:
        """发送异常事件邮件通知"""
        if not self.email_service:
            logger.info("邮件服务未配置，跳过邮件发送")
            return False
        
        if not user.email:
            logger.warning(f"用户 {user.user_id} 没有邮箱地址")
            return False
        
        is_critical = (event.risk_level or "").lower() == "critical"
        priority_icon = "🔴" if is_critical else "🟡"
        
        subject = f"{priority_icon} ParrotCare 异常提醒 - {parrot.name}"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {"#f44336" if is_critical else "#ff9800"}; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px 20px; background: #f9f9f9; }}
        .info-row {{ padding: 10px 0; border-bottom: 1px solid #eee; }}
        .info-label {{ font-weight: bold; color: #555; }}
        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{priority_icon} ParrotCare 异常行为提醒</h1>
        </div>
        <div class="content">
            <p>您好，</p>
            <p>系统检测到您的鹦鹉出现异常行为，请及时关注：</p>
            
            <div class="info-row">
                <span class="info-label">鹦鹉名称：</span>{parrot.name}
            </div>
            <div class="info-row">
                <span class="info-label">品种：</span>{parrot.species or "未知"}
            </div>
            <div class="info-row">
                <span class="info-label">异常类型：</span>{event_label}
            </div>
            <div class="info-row">
                <span class="info-label">严重程度：</span>{risk_label}
            </div>
            <div class="info-row">
                <span class="info-label">检测时间：</span>{time_str}
            </div>
            {"<div class='info-row'><span class='info-label' style='color:#f44336;'>⚠️ 紧急事件，请立即查看！</span></div>" if is_critical else ""}
            
            <p style="margin-top: 20px;">请登录 ParrotCare 平台查看详情。</p>
        </div>
        <div class="footer">
            <p>© {datetime.utcnow().year} ParrotCare - 智能鹦鹉健康管理平台</p>
            <p>此邮件由系统自动发送，请勿回复</p>
        </div>
    </div>
</body>
</html>
"""
        
        return await self.email_service.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
        )


# 全局单例（在 API 层通过 get_push_service 依赖注入）
_push_service: Optional[PushNotificationService] = None


def get_push_service() -> PushNotificationService:
    """获取推送通知服务单例"""
    global _push_service
    if _push_service is None:
        from app.services.email_service import EmailService
        from app.config import settings
        
        email_service = EmailService(
            smtp_host=settings.SMTP_HOST,
            smtp_port=settings.SMTP_PORT,
            smtp_username=settings.SMTP_USERNAME,
            smtp_password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_USE_TLS,
            from_email=settings.SMTP_FROM_EMAIL,
        )
        _push_service = PushNotificationService(email_service=email_service)
    return _push_service
