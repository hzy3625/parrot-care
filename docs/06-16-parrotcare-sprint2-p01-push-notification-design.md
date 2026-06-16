# ParrotCare Sprint 2 - P0-1 推送通知系统设计文档

> 版本: v1.0 | 日期: 2026-06-16 | 状态: 已实现

## 1. 需求概述

当鹦鹉异常行为事件（夜间惊飞、持续尖叫等）被检测到时，系统自动通过邮件和浏览器通知推送给用户。用户可配置推送开关和免打扰时段。

## 2. 验收标准 (AC)

### AC-1: 异常事件触发推送
- **Given** 系统中产生一个 `is_abnormal=true` 的 MediaEvent
- **When** 该事件所属用户的推送开关开启
- **Then** 系统自动发送邮件通知和创建站内消息

### AC-2: 推送内容完整
- **Given** 一个异常事件
- **When** 生成推送内容
- **Then** 包含：鹦鹉名称、异常类型（event_type）、事件时间、严重程度（risk_level）

### AC-3: 用户可配置推送开关
- **Given** 用户已登录
- **When** 用户访问 `/api/settings/push` 接口
- **Then** 可独立开关 `notification_email` 和 `notification_browser`

### AC-4: 免打扰时段 (DND)
- **Given** 用户设置了 DND 时段（如 23:00-07:00）
- **When** 异常事件发生在 DND 时段内
- **Then** 浏览器通知被抑制，邮件仍正常发送（紧急事件不抑制）
- **Given** risk_level 为 "critical"
- **When** 即使在 DND 时段
- **Then** 所有通知正常发送（紧急事件不受 DND 限制）

### AC-5: 浏览器通知支持
- **Given** 用户开启了 `notification_browser` 开关
- **When** 用户在前端页面且已授权浏览器通知权限
- **Then** 通过 WebSocket 或 SSE 实时推送浏览器通知

### AC-6: 邮件通知
- **Given** 用户开启了 `notification_email` 且有有效邮箱
- **When** 异常事件触发
- **Then** 发送 HTML 格式邮件通知

## 3. 技术方案

### 3.1 架构

```
MediaEvent (is_abnormal=true)
    ↓
PushNotificationService.dispatch()
    ├── DND check (suppress browser if in DND, except critical)
    ├── Email Service → send_email()
    ├── In-App Notification → notifications table
    └── WebSocket Broadcast → frontend browser notification
```

### 3.2 新增文件

| 文件 | 说明 |
|------|------|
| `backend/app/services/push_notification_service.py` | 推送通知核心服务 |
| `backend/app/api/settings.py` | 用户设置 API（推送配置、DND） |
| `backend/app/api/realtime.py` | 增强：事件触发时调用推送服务 |
| `backend/tests/test_push_notification.py` | 测试用例 |
| `backend/tests/test_settings.py` | 设置 API 测试 |
| `web_app/index.html` | 增强：浏览器通知请求 + 显示 |
| `web_app/app.js` | 增强：浏览器通知逻辑 |

### 3.3 数据库变更

无需新增表，复用现有字段：
- `users.notification_email` (Boolean)
- `users.notification_browser` (Boolean)
- `users.dnd_start` (Time)
- `users.dnd_end` (Time)
- `users.email` (String)
- `media_events.is_abnormal` (Boolean)
- `media_events.risk_level` (String)

### 3.4 DND 逻辑

```python
def is_in_dnd(dnd_start, dnd_end, current_time):
    if not dnd_start or not dnd_end:
        return False
    if dnd_start <= dnd_end:
        return dnd_start <= current_time <= dnd_end
    else:  # 跨午夜，如 23:00-07:00
        return current_time >= dnd_start or current_time <= dnd_end
```

### 3.5 API 端点

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/settings/push` | 获取推送设置 |
| PUT | `/api/settings/push` | 更新推送设置 |
| GET | `/api/settings/dnd` | 获取 DND 设置 |
| PUT | `/api/settings/dnd` | 更新 DND 设置 |
