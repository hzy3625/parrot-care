# ParrotCare Sprint 3 需求文档

**文档版本**: V1.0
**撰写日期**: 2026-06-17
**状态**: 待开发
**Sprint 周期**: 2026-06-17 ~ 2026-06-20
**Sprint Goal**: 补全前端交互逻辑 + 实现 WebSocket 实时推送 + 修复 Sprint 1/2 遗留技术债务

---

## 一、Sprint 3 目标

Sprint 1 和 Sprint 2 的后端 API 和业务逻辑已 100% 完成，但**前端交互逻辑（app.js）大量缺失**，导致用户无法在浏览器中使用已有功能。Sprint 3 聚焦于 **前后端打通**，让用户真正能用起来。

| 需求 ID | 标题 | 优先级 | 故事点 | 说明 |
|---------|------|--------|--------|------|
| REQ-PARROT-015 | 前端交互逻辑补全 | P0 | 13 | 补全 app.js，实现所有前端页面交互（登录、密码重置、消息中心、音频上传、设置面板等） |
| REQ-PARROT-016 | WebSocket 实时推送 | P0 | 8 | 实现 WebSocket 服务，替代前端轮询，实现通知/事件实时推送 |
| REQ-PARROT-017 | 浏览器通知集成 | P1 | 5 | 前端调用 Notification API，接收并展示推送通知 |
| REQ-PARROT-018 | 技术债务修复 | P2 | 3 | datetime.utcnow() 全局迁移 + bcrypt 密码加密替换 SHA-256 |

**Sprint 3 总故事点**: 29 pts

---

## 二、REQ-PARROT-015：前端交互逻辑补全（P0，13 pts）

### 2.1 用户故事

> 作为一名鹦鹉主人，我希望能在浏览器中完成所有操作——登录、查看消息、上传音频、管理设置——而不是只看到静态页面却无法交互。

### 2.2 背景问题

Sprint 1 验收报告显示：`web_app/app.js` **完全不存在**，导致：
- 密码重置：有 HTML 表单但无 JS 调用逻辑
- 站内消息中心：有列表页面但无法加载/标记已读
- 健康档案总览：有页面但无数据加载
- 个人信息管理：无法修改资料/密码
- 音频上传：无法上传和查看结果

Sprint 2 虽然部分更新了 `index.html`（设置面板 UI），但对应的 JS 逻辑也未实现。

### 2.3 验收标准 (AC)

| AC ID | 描述 | 类型 |
|-------|------|------|
| AC-015-1 | **登录/注册**：表单提交 → API 调用 → token 存储 → 页面跳转 | 功能 |
| AC-015-2 | **密码重置-发起**：输入邮箱 → POST /api/reset-password → 提示已发送 | 功能 |
| AC-015-3 | **密码重置-确认**：URL 含 token → 显示设置新密码表单 → POST /api/reset-password/{token} → 跳转登录 | 功能 |
| AC-015-4 | **密码强度前端校验**：密码至少 8 位，含字母+数字，前端实时提示 | 功能 |
| AC-015-5 | **站内消息中心**：加载消息列表 → 标记已读 → 删除消息 | 功能 |
| AC-015-6 | **健康档案总览**：加载鹦鹉列表 → 显示健康状态卡片 → 支持按时间排序 | 功能 |
| AC-015-7 | **音频上传**：选择文件 → POST /api/audio/upload → 显示分类结果（类别、置信度、建议） | 功能 |
| AC-015-8 | **推送设置**：GET/PUT /api/settings/push → 开关切换实时保存 | 功能 |
| AC-015-9 | **DND 设置**：GET/PUT /api/settings/dnd → 时间选择器 → 保存 | 功能 |
| AC-015-10 | **个人信息管理**：加载个人信息 → 修改 → PUT 更新 | 功能 |
| AC-015-11 | **修改密码**：旧密码验证 → 新密码输入（含强度校验）→ 更新 | 功能 |
| AC-015-12 | **页面导航**：侧边栏/Tab 切换不同功能页面 | 功能 |
| AC-015-13 | **错误处理**：API 失败时显示友好错误提示，不白屏 | 非功能 |
| AC-015-14 | **Token 管理**：token 过期自动跳转登录页 | 非功能 |

### 2.4 技术方案

#### 2.4.1 文件结构

```
web_app/
├── index.html        # 已有，基本结构完成
├── app.js            # ⚠️ 需要从头创建，约 800-1200 行
└── styles.css        # 已有，可能需要补充
```

#### 2.4.2 技术选型

- **纯 Vanilla JS**（无框架），与现有 HTML 结构匹配
- **fetch API** 进行 HTTP 请求
- **localStorage** 存储 JWT token
- **事件委托** 处理动态元素

#### 2.4.3 API 调用封装

```javascript
const api = {
  base: '',  // 同源部署
  async request(method, path, body) { ... },
  async login(email, password) { ... },
  async getParrots() { ... },
  async uploadAudio(file) { ... },
  async getNotifications() { ... },
  async markNotificationRead(id) { ... },
  async getPushSettings() { ... },
  async updatePushSettings(data) { ... },
  async getDndSettings() { ... },
  async updateDndSettings(data) { ... },
  async requestPasswordReset(email) { ... },
  async confirmPasswordReset(token, newPassword) { ... },
  async getProfile() { ... },
  async updateProfile(data) { ... },
  async changePassword(oldPwd, newPwd) { ... },
};
```

### 2.5 新增/变更文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `web_app/app.js` | 新增 | 全部前端交互逻辑（核心交付物） |
| `web_app/index.html` | 变更 | 补充缺失的 DOM 元素（如密码重置确认页） |
| `web_app/styles.css` | 变更 | 补充缺失样式 |

---

## 三、REQ-PARROT-016：WebSocket 实时推送（P0，8 pts）

### 3.1 用户故事

> 作为一名鹦鹉主人，我希望当我在线时，系统能**实时推送**鹦鹉的异常事件通知，而不是我手动刷新页面或轮询才能看到。

### 3.2 验收标准 (AC)

| AC ID | 描述 | 类型 |
|-------|------|------|
| AC-016-1 | **WebSocket 服务端**：FastAPI 集成 WebSocket，支持客户端连接 | 功能 |
| AC-016-2 | **认证握手**：WebSocket 连接时验证 JWT token，未认证拒绝连接 | 安全 |
| AC-016-3 | **事件推送**：异常事件发生时，向连接的用户推送消息 | 功能 |
| AC-016-4 | **消息格式**：推送 JSON 消息 `{type: "event", data: {event_id, parrot_name, event_type, risk_level, timestamp}}` | 功能 |
| AC-016-5 | **心跳保活**：客户端每 30 秒发送 ping，服务端回复 pong，超时 60 秒断开 | 非功能 |
| AC-016-6 | **断线重连**：客户端断线后自动重连（指数退避，最大 30 秒） | 非功能 |
| AC-016-7 | **多端连接**：同一用户可在多个浏览器窗口连接，所有窗口都收到推送 | 功能 |
| AC-016-8 | **前端集成**：app.js 中建立 WebSocket 连接，收到事件后展示通知 | 功能 |
| AC-016-9 | **降级兼容**：WebSocket 不可用时，前端不崩溃，静默降级 | 非功能 |

### 3.3 技术方案

#### 3.3.1 服务端架构

```python
# backend/app/services/websocket_manager.py
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}  # user_id → connections

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.setdefault(user_id, []).append(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: str):
        self.active_connections[user_id].remove(websocket)

    async def send_personal(self, user_id: str, message: dict):
        for ws in self.active_connections.get(user_id, []):
            await ws.send_json(message)
```

```python
# backend/app/api/websocket.py
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    # JWT 验证
    user_id = decode_token(token)
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # 处理心跳
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(websocket, user_id)
```

#### 3.3.2 与推送服务集成

在 `PushNotificationService.dispatch_for_event()` 中增加 WebSocket 推送：

```python
# 推送流程增加 WebSocket
await websocket_manager.send_personal(user_id, {
    "type": "event",
    "data": {
        "event_id": event.id,
        "parrot_name": parrot.name,
        "event_type": event.event_type,
        "risk_level": event.risk_level,
        "timestamp": event.created_at.isoformat(),
    }
})
```

#### 3.3.3 前端 WebSocket 客户端

```javascript
class WSClient {
  constructor(token) {
    this.token = token;
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
  }

  connect() {
    const ws = new WebSocket(`ws://${location.host}/ws?token=${this.token}`);
    ws.onmessage = (e) => this.onMessage(JSON.parse(e.data));
    ws.onclose = () => this.reconnect();
    ws.onerror = () => {}; // 静默降级
    // 心跳
    this.heartbeat = setInterval(() => ws.send('ping'), 30000);
  }

  reconnect() {
    clearInterval(this.heartbeat);
    setTimeout(() => this.connect(), this.reconnectDelay);
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
  }

  onMessage(data) {
    if (data.type === 'event') {
      // 展示浏览器通知 + 刷新消息列表
      this.showNotification(data.data);
      this.refreshNotifications();
    }
  }
}
```

### 3.4 新增/变更文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/services/websocket_manager.py` | 新增 | WebSocket 连接管理器 |
| `backend/app/api/websocket.py` | 新增 | WebSocket 端点 |
| `backend/main.py` | 变更 | 注册 WebSocket 路由 |
| `backend/app/services/push_notification_service.py` | 变更 | 集成 WebSocket 推送 |
| `web_app/app.js` | 变更 | WebSocket 客户端（与 REQ-015 一起实现） |
| `backend/tests/test_websocket.py` | 新增 | WebSocket 服务测试 |

---

## 四、REQ-PARROT-017：浏览器通知集成（P1，5 pts）

### 4.1 用户故事

> 作为一名鹦鹉主人，即使我打开了 ParrotCare 页面但在做其他事情（如看别的 Tab），我也希望鹦鹉异常时能**在桌面右上角弹出通知**提醒我。

### 4.2 验收标准 (AC)

| AC ID | 描述 | 类型 |
|-------|------|------|
| AC-017-1 | **权限请求**：页面加载时检查 Notification 权限，未授权时引导用户授权 | 功能 |
| AC-017-2 | **通知展示**：收到异常事件后调用 `new Notification()` 展示桌面通知 | 功能 |
| AC-017-3 | **通知内容**：标题 = "🦜 {鹦鹉名} 异常行为"，正文 = 事件类型 + 严重程度 | 功能 |
| AC-017-4 | **通知点击**：点击通知后跳转到对应事件详情页 | 功能 |
| AC-017-5 | **DND 前端配合**：后端已处理 DND 逻辑，前端收到浏览器通知数据后直接展示即可 | 功能 |
| AC-017-6 | **权限被拒**：用户拒绝权限时显示友好提示，不报错 | 非功能 |
| AC-017-7 | **与 WebSocket 集成**：WebSocket 推送的事件同时触发浏览器通知 | 功能 |

### 4.3 技术方案

在 `app.js` 中实现：

```javascript
async function initBrowserNotification() {
  if (!('Notification' in window)) {
    showInfo('您的浏览器不支持桌面通知');
    return;
  }

  if (Notification.permission === 'granted') return;

  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission();
    if (permission === 'denied') {
      showInfo('通知权限已被拒绝，请在浏览器设置中重新授权');
    }
  }
}

function showBrowserNotification(title, body, event_id) {
  if (Notification.permission !== 'granted') return;
  const notification = new Notification(title, {
    body: body,
    icon: '/favicon.ico',
    tag: event_id,  // 去重
  });
  notification.onclick = () => {
    window.focus();
    navigateToEvent(event_id);
  };
}
```

### 4.4 新增/变更文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `web_app/app.js` | 变更 | 浏览器通知逻辑（与 REQ-015 一起实现） |

---

## 五、REQ-PARROT-018：技术债务修复（P2，3 pts）

### 5.1 背景

Sprint 1/2 验收报告中多次提到以下技术债务：
- `datetime.utcnow()` 在多处使用（Python 3.12+ 已废弃）
- 密码加密使用 SHA-256 而非 bcrypt

### 5.2 验收标准 (AC)

| AC ID | 描述 | 类型 |
|-------|------|------|
| AC-018-1 | **datetime 迁移**：全局搜索 `datetime.utcnow()` 和 `datetime.utcnow`，替换为 `datetime.now(datetime.timezone.utc)` | 功能 |
| AC-018-2 | **bcrypt 替换**：`hash_password` 和 `verify_password` 使用 bcrypt 替代 SHA-256 | 功能 |
| AC-018-3 | **密码强度校验**：后端 PasswordResetConfirm schema 增加 @field_validator，要求密码 ≥8 位且含字母+数字 | 功能 |
| AC-018-4 | **频率限制**：密码重置 API 增加频率限制（同一邮箱 1 小时最多 3 次） | 功能 |
| AC-018-5 | **所有测试通过**：迁移后 68+ 个测试全部通过 | 非功能 |

### 5.3 技术方案

#### 5.3.1 datetime 迁移

```bash
# 搜索所有使用位置
grep -rn "utcnow" backend/

# 替换方案
# 旧: datetime.utcnow()
# 新: datetime.now(datetime.timezone.utc)

# 旧: datetime.utcnow() + timedelta(hours=1)
# 新: datetime.now(datetime.timezone.utc) + timedelta(hours=1)
```

涉及文件（预估）：
- `backend/app/services/push_notification_service.py`
- `backend/app/services/email_service.py`
- `backend/app/models/database.py`
- `backend/app/api/users.py`
- `backend/tests/` 相关测试文件

#### 5.3.2 bcrypt 替换

```python
# 旧 (SHA-256)
import hashlib
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# 新 (bcrypt)
import bcrypt
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())
```

**注意**：迁移后需处理存量用户密码（可保持旧 hash 兼容，用户下次登录时自动升级）。

### 5.4 新增/变更文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/models/database.py` | 变更 | bcrypt 替换 SHA-256 |
| `backend/app/models/schemas.py` | 变更 | 密码强度校验 |
| `backend/app/api/users.py` | 变更 | 频率限制 + datetime 迁移 |
| `backend/app/services/push_notification_service.py` | 变更 | datetime 迁移 |
| `backend/app/services/email_service.py` | 变更 | datetime 迁移 |
| `backend/requirements.txt` | 变更 | 新增 `bcrypt` 依赖 |
| `backend/tests/` | 变更 | 适配 bcrypt 的测试 |

---

## 六、故事点估算

| 需求 | 故事点 | 估算依据 |
|------|--------|---------|
| **REQ-PARROT-015 前端交互逻辑补全** | **13** | |
| ├─ app.js 核心框架（API 封装、路由、状态管理） | 3 | 基础架构 |
| ├─ 登录/注册/密码重置 | 2 | 3 个页面流程 |
| ├─ 消息中心 | 2 | 列表加载、标记已读、删除 |
| ├─ 健康档案 + 音频上传 | 2 | 数据展示、文件上传、结果解析 |
| ├─ 设置面板（推送+DND） | 1 | 开关、时间选择器 |
| ├─ 个人信息 + 修改密码 | 1 | 表单加载、提交、校验 |
| └─ 错误处理 + Token 管理 | 2 | 全局拦截、过期跳转 |
| **REQ-PARROT-016 WebSocket 实时推送** | **8** | |
| ├─ WebSocket 服务端（连接管理、认证） | 3 | 核心逻辑 |
| ├─ 心跳 + 断线重连 | 1 | 保活机制 |
| ├─ 与推送服务集成 | 1 | dispatch 增加 WS 推送 |
| ├─ 前端 WS 客户端 | 2 | 连接、重连、消息处理 |
| └─ 测试 | 1 | 连接管理 + 消息推送测试 |
| **REQ-PARROT-017 浏览器通知集成** | **5** | |
| ├─ 权限请求 + 通知展示 | 3 | Notification API 封装 |
| ├─ 与 WebSocket 集成 | 1 | WS 事件触发通知 |
| └─ 权限被拒友好提示 | 1 | 用户体验 |
| **REQ-PARROT-018 技术债务修复** | **3** | |
| ├─ datetime 全局迁移 | 1 | 搜索替换 + 测试验证 |
| ├─ bcrypt 替换 + 存量兼容 | 1 | 密码模块重构 |
| └─ 密码强度 + 频率限制 | 1 | 校验 + 限流 |
| **Sprint 3 总计** | **29** | |

---

## 七、开发顺序建议

1. **REQ-018 技术债务**（1-2h）→ 先还债，避免后续代码继续使用废弃 API
2. **REQ-015 前端交互逻辑**（4-6h）→ 核心打通，让系统真正可用
3. **REQ-016 WebSocket**（3-4h）→ 实时能力
4. **REQ-017 浏览器通知**（1-2h）→ 体验提升

---

**文档撰写人**: BA (小A)
**审阅状态**: 待确认
