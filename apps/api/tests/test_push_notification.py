# -*- coding: utf-8 -*-
"""
推送通知服务测试 - Sprint 2 P0-1
测试 DND 逻辑、推送分发、邮件发送等
"""

import pytest
import pytest_asyncio
from datetime import datetime, time
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.push_notification_service import PushNotificationService
from app.models.database import User, Parrot, MediaEvent, generate_id


# ==================== DND 逻辑测试 ====================

class TestDndLogic:
    """免打扰时段逻辑测试"""

    def setup_method(self):
        self.service = PushNotificationService()

    def test_no_dnd_settings(self):
        """未设置 DND → 不在 DND 时段"""
        assert self.service.is_in_dnd(None, None) is False

    def test_dnd_within_range(self):
        """DND 14:00-16:00，当前 15:00 → 在 DND"""
        dnd_start = time(14, 0)
        dnd_end = time(16, 0)
        check_time = datetime(2026, 6, 16, 15, 0)
        assert self.service.is_in_dnd(dnd_start, dnd_end, check_time) is True

    def test_dnd_before_range(self):
        """DND 14:00-16:00，当前 13:00 → 不在 DND"""
        dnd_start = time(14, 0)
        dnd_end = time(16, 0)
        check_time = datetime(2026, 6, 16, 13, 0)
        assert self.service.is_in_dnd(dnd_start, dnd_end, check_time) is False

    def test_dnd_after_range(self):
        """DND 14:00-16:00，当前 17:00 → 不在 DND"""
        dnd_start = time(14, 0)
        dnd_end = time(16, 0)
        check_time = datetime(2026, 6, 16, 17, 0)
        assert self.service.is_in_dnd(dnd_start, dnd_end, check_time) is False

    def test_dnd_cross_midnight_within(self):
        """DND 23:00-07:00，当前 02:00 → 在 DND"""
        dnd_start = time(23, 0)
        dnd_end = time(7, 0)
        check_time = datetime(2026, 6, 16, 2, 0)
        assert self.service.is_in_dnd(dnd_start, dnd_end, check_time) is True

    def test_dnd_cross_midnight_before(self):
        """DND 23:00-07:00，当前 22:00 → 不在 DND"""
        dnd_start = time(23, 0)
        dnd_end = time(7, 0)
        check_time = datetime(2026, 6, 16, 22, 0)
        assert self.service.is_in_dnd(dnd_start, dnd_end, check_time) is False

    def test_dnd_cross_midnight_after(self):
        """DND 23:00-07:00，当前 08:00 → 不在 DND"""
        dnd_start = time(23, 0)
        dnd_end = time(7, 0)
        check_time = datetime(2026, 6, 16, 8, 0)
        assert self.service.is_in_dnd(dnd_start, dnd_end, check_time) is False

    def test_dnd_cross_midnight_boundary_start(self):
        """DND 23:00-07:00，当前 23:00 → 在 DND"""
        dnd_start = time(23, 0)
        dnd_end = time(7, 0)
        check_time = datetime(2026, 6, 16, 23, 0)
        assert self.service.is_in_dnd(dnd_start, dnd_end, check_time) is True

    def test_dnd_cross_midnight_boundary_end(self):
        """DND 23:00-07:00，当前 07:00 → 在 DND"""
        dnd_start = time(23, 0)
        dnd_end = time(7, 0)
        check_time = datetime(2026, 6, 16, 7, 0)
        assert self.service.is_in_dnd(dnd_start, dnd_end, check_time) is True


# ==================== 推送分发测试 ====================

@pytest.mark.asyncio
class TestPushDispatch:
    """推送通知分发测试"""

    @pytest.fixture
    def mock_user(self):
        user = MagicMock(spec=User)
        user.user_id = "test-user-001"
        user.email = "test@example.com"
        user.notification_email = True
        user.notification_browser = True
        user.dnd_start = None
        user.dnd_end = None
        return user

    @pytest.fixture
    def mock_parrot(self):
        parrot = MagicMock(spec=Parrot)
        parrot.parrot_id = "test-parrot-001"
        parrot.user_id = "test-user-001"
        parrot.name = "小绿"
        parrot.species = "虎皮鹦鹉"
        return parrot

    @pytest.fixture
    def mock_abnormal_event(self):
        event = MagicMock(spec=MediaEvent)
        event.event_id = "test-event-001"
        event.parrot_id = "test-parrot-001"
        event.event_type = "night_fright"
        event.is_abnormal = True
        event.risk_level = "high"
        event.event_time = datetime(2026, 6, 16, 10, 0)
        return event

    @pytest.fixture
    def mock_normal_event(self):
        event = MagicMock(spec=MediaEvent)
        event.event_id = "test-event-002"
        event.parrot_id = "test-parrot-001"
        event.event_type = "chirp"
        event.is_abnormal = False
        event.risk_level = None
        event.event_time = datetime(2026, 6, 16, 10, 0)
        return event

    @pytest.fixture
    def service(self):
        mock_email = AsyncMock()
        mock_email.send_email = AsyncMock(return_value=True)
        return PushNotificationService(email_service=mock_email)

    async def test_skip_normal_event(self, service, mock_normal_event):
        """正常事件不触发推送"""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

        result = await service.dispatch_for_event(mock_normal_event, mock_db)

        assert result["email_sent"] is False
        assert result["in_app_created"] is False
        assert result["browser_notification"] is None

    async def test_dispatch_abnormal_event(self, service, mock_abnormal_event, mock_user, mock_parrot):
        """异常事件正常触发推送"""
        # Mock DB queries
        mock_db = AsyncMock()
        call_count = {"execute": 0}

        async def mock_execute(stmt):
            call_count["execute"] += 1
            result_mock = MagicMock()
            if call_count["execute"] == 1:
                result_mock.scalar_one_or_none = MagicMock(return_value=mock_parrot)
            elif call_count["execute"] == 2:
                result_mock.scalar_one_or_none = MagicMock(return_value=mock_user)
            else:
                result_mock.scalar_one_or_none = MagicMock(return_value=None)
            return result_mock

        mock_db.execute = mock_execute
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        result = await service.dispatch_for_event(mock_abnormal_event, mock_db)

        assert result["email_sent"] is True
        assert result["in_app_created"] is True
        assert result["browser_notification"] is not None
        assert result["browser_notification"]["title"] == "🦜 小绿 异常行为提醒"
        assert result["dnd_suppressed_browser"] is False
        assert result["dnd_suppressed_email"] is False

    async def test_dnd_suppresses_browser_not_email(self, service, mock_abnormal_event, mock_user, mock_parrot):
        """DND 时段内：抑制浏览器通知，邮件正常发送"""
        mock_user.dnd_start = time(23, 0)
        mock_user.dnd_end = time(7, 0)

        # 事件发生在凌晨 2 点
        mock_abnormal_event.event_time = datetime(2026, 6, 16, 2, 0)
        mock_abnormal_event.risk_level = "high"  # 非紧急

        mock_db = AsyncMock()
        call_count = {"execute": 0}

        async def mock_execute(stmt):
            call_count["execute"] += 1
            result_mock = MagicMock()
            if call_count["execute"] == 1:
                result_mock.scalar_one_or_none = MagicMock(return_value=mock_parrot)
            elif call_count["execute"] == 2:
                result_mock.scalar_one_or_none = MagicMock(return_value=mock_user)
            return result_mock

        mock_db.execute = mock_execute
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        result = await service.dispatch_for_event(mock_abnormal_event, mock_db)

        assert result["email_sent"] is True  # 邮件不抑制（非跨午夜场景）
        assert result["in_app_created"] is True
        assert result["browser_notification"] is None  # 浏览器通知被抑制
        assert result["dnd_suppressed_browser"] is True

    async def test_critical_event_bypasses_dnd(self, service, mock_abnormal_event, mock_user, mock_parrot):
        """紧急事件 (critical) 不受 DND 限制"""
        mock_user.dnd_start = time(23, 0)
        mock_user.dnd_end = time(7, 0)

        mock_abnormal_event.event_time = datetime(2026, 6, 16, 2, 0)
        mock_abnormal_event.risk_level = "critical"  # 紧急事件

        mock_db = AsyncMock()
        call_count = {"execute": 0}

        async def mock_execute(stmt):
            call_count["execute"] += 1
            result_mock = MagicMock()
            if call_count["execute"] == 1:
                result_mock.scalar_one_or_none = MagicMock(return_value=mock_parrot)
            elif call_count["execute"] == 2:
                result_mock.scalar_one_or_none = MagicMock(return_value=mock_user)
            return result_mock

        mock_db.execute = mock_execute
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        result = await service.dispatch_for_event(mock_abnormal_event, mock_db)

        assert result["browser_notification"] is not None  # 浏览器通知正常发送
        assert result["dnd_suppressed_browser"] is False
        assert result["dnd_suppressed_email"] is False

    async def test_email_switch_off(self, service, mock_abnormal_event, mock_user, mock_parrot):
        """用户关闭邮件通知开关 → 不发送邮件"""
        mock_user.notification_email = False

        mock_db = AsyncMock()
        call_count = {"execute": 0}

        async def mock_execute(stmt):
            call_count["execute"] += 1
            result_mock = MagicMock()
            if call_count["execute"] == 1:
                result_mock.scalar_one_or_none = MagicMock(return_value=mock_parrot)
            elif call_count["execute"] == 2:
                result_mock.scalar_one_or_none = MagicMock(return_value=mock_user)
            return result_mock

        mock_db.execute = mock_execute
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        result = await service.dispatch_for_event(mock_abnormal_event, mock_db)

        assert result["email_sent"] is False
        assert result["in_app_created"] is True  # 站内消息仍然创建

    async def test_browser_switch_off(self, service, mock_abnormal_event, mock_user, mock_parrot):
        """用户关闭浏览器通知开关 → 不发送浏览器通知"""
        mock_user.notification_browser = False

        mock_db = AsyncMock()
        call_count = {"execute": 0}

        async def mock_execute(stmt):
            call_count["execute"] += 1
            result_mock = MagicMock()
            if call_count["execute"] == 1:
                result_mock.scalar_one_or_none = MagicMock(return_value=mock_parrot)
            elif call_count["execute"] == 2:
                result_mock.scalar_one_or_none = MagicMock(return_value=mock_user)
            return result_mock

        mock_db.execute = mock_execute
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        result = await service.dispatch_for_event(mock_abnormal_event, mock_db)

        assert result["browser_notification"] is None


# ==================== 事件类型标签测试 ====================

class TestEventLabels:
    """事件类型和严重程度标签测试"""

    def test_event_type_labels(self):
        """所有事件类型有中文标签"""
        service = PushNotificationService()
        assert service.EVENT_TYPE_LABELS["night_fright"] == "夜间惊飞"
        assert service.EVENT_TYPE_LABELS["scream"] == "持续尖叫"
        assert service.EVENT_TYPE_LABELS.get("unknown_type", "未知异常") == "未知异常"

    def test_risk_level_labels(self):
        """所有严重程度有中文标签"""
        service = PushNotificationService()
        assert service.RISK_LEVEL_LABELS["low"] == "低"
        assert service.RISK_LEVEL_LABELS["medium"] == "中"
        assert service.RISK_LEVEL_LABELS["high"] == "高"
        assert service.RISK_LEVEL_LABELS["critical"] == "紧急"
